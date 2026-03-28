"""Stdio MCP server for querying VictoriaLogs and VictoriaTraces."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

from mcp_obs.settings import Settings, resolve_settings


class LogsSearchArgs(BaseModel):
    query: str = Field(description="LogsQL query string")
    limit: int = Field(default=100, ge=1, le=1000, description="Max results to return")


class LogsErrorCountArgs(BaseModel):
    minutes: int = Field(default=60, ge=1, le=1440, description="Time window in minutes")
    service: str = Field(default="", description="Filter by service name (optional)")


class TracesListArgs(BaseModel):
    service: str = Field(description="Service name to search traces for")
    limit: int = Field(default=10, ge=1, le=100, description="Max traces to return")


class TracesGetArgs(BaseModel):
    trace_id: str = Field(description="Trace ID to fetch")


def _text(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, default=str))]


def create_server(settings: Settings) -> Server:
    server = Server("observability")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="logs_search",
                description="Search logs using LogsQL query. Returns matching log entries.",
                inputSchema=LogsSearchArgs.model_json_schema(),
            ),
            Tool(
                name="logs_error_count",
                description="Count errors per service over a time window. Returns error counts.",
                inputSchema=LogsErrorCountArgs.model_json_schema(),
            ),
            Tool(
                name="traces_list",
                description="List recent traces for a service. Returns trace summaries.",
                inputSchema=TracesListArgs.model_json_schema(),
            ),
            Tool(
                name="traces_get",
                description="Fetch a specific trace by ID. Returns full trace with spans.",
                inputSchema=TracesGetArgs.model_json_schema(),
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[TextContent]:
        try:
            if name == "logs_search":
                args = LogsSearchArgs.model_validate(arguments or {})
                return await _logs_search(settings, args)
            elif name == "logs_error_count":
                args = LogsErrorCountArgs.model_validate(arguments or {})
                return await _logs_error_count(settings, args)
            elif name == "traces_list":
                args = TracesListArgs.model_validate(arguments or {})
                return await _traces_list(settings, args)
            elif name == "traces_get":
                args = TracesGetArgs.model_validate(arguments or {})
                return await _traces_get(settings, args)
            else:
                return _text({"error": f"Unknown tool: {name}"})
        except Exception as exc:
            return _text({"error": f"{type(exc).__name__}: {exc}"})

    _ = list_tools, call_tool
    return server


async def _logs_search(settings: Settings, args: LogsSearchArgs) -> list[TextContent]:
    """Search logs using VictoriaLogs API."""
    url = f"{settings.victorialogs_url}/select/logsql/query"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            params={"query": args.query, "limit": args.limit},
            timeout=30.0,
        )
        response.raise_for_status()
        # VictoriaLogs returns JSONL or JSON depending on query
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw": response.text}
    return _text(data)


async def _logs_error_count(settings: Settings, args: LogsErrorCountArgs) -> list[TextContent]:
    """Count errors per service over a time window."""
    time_window = f"{args.minutes}m"
    base_query = f'_time:{time_window} severity:ERROR'
    if args.service:
        base_query += f' service.name:"{args.service}"'
    
    url = f"{settings.victorialogs_url}/select/logsql/stats_query"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            params={"query": f"{base_query} | stats by(service.name) count()"},
            timeout=30.0,
        )
        response.raise_for_status()
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"raw": response.text, "query": base_query}
    return _text(data)


async def _traces_list(settings: Settings, args: TracesListArgs) -> list[TextContent]:
    """List recent traces for a service using VictoriaTraces Jaeger API."""
    url = f"{settings.victoriatraces_url}/select/jaeger/api/traces"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params={"service": args.service, "limit": args.limit},
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
    # Extract trace summaries
    traces = data.get("data", [])
    summaries = []
    for trace in traces[:args.limit]:
        summaries.append({
            "trace_id": trace.get("traceID"),
            "spans": len(trace.get("spans", [])),
            "start_time": trace.get("startTime"),
            "duration": trace.get("duration"),
        })
    return _text({"traces": summaries, "total": len(traces)})


async def _traces_get(settings: Settings, args: TracesGetArgs) -> list[TextContent]:
    """Fetch a specific trace by ID."""
    url = f"{settings.victoriatraces_url}/select/jaeger/api/traces/{args.trace_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        data = response.json()
    return _text(data)


async def main() -> None:
    settings = resolve_settings()
    server = create_server(settings)
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
