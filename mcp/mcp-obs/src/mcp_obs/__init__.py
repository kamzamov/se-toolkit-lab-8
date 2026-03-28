"""Observability MCP server for querying VictoriaLogs and VictoriaTraces."""

from mcp_obs.server import main

__all__ = ["main"]

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
