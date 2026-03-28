#!/usr/bin/env python3
"""Entrypoint for nanobot gateway in Docker.

Resolves environment variables into config.json at runtime,
then launches nanobot gateway.
"""

import json
import os
import sys
from pathlib import Path


def resolve_config():
    """Read config.json, inject env vars, write config.resolved.json."""
    config_path = Path("/app/nanobot/config.json")
    workspace_path = Path("/app/nanobot/workspace")
    resolved_path = Path("/app/nanobot/config/config.resolved.json")

    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    # Ensure config directory exists
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path) as f:
        config = json.load(f)

    # Inject LLM provider settings from env vars
    llm_api_key = os.environ.get("LLM_API_KEY")
    llm_api_base_url = os.environ.get("LLM_API_BASE_URL")
    llm_api_model = os.environ.get("LLM_API_MODEL")

    if llm_api_key:
        config["providers"]["custom"]["apiKey"] = llm_api_key
    if llm_api_base_url:
        config["providers"]["custom"]["apiBase"] = llm_api_base_url
    if llm_api_model:
        config["agents"]["defaults"]["model"] = llm_api_model

    # Inject gateway settings
    gateway_host = os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS")
    gateway_port = os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT")

    if gateway_host:
        config["gateway"]["host"] = gateway_host
    if gateway_port:
        config["gateway"]["port"] = int(gateway_port)

    # Inject MCP server env vars for LMS
    lms_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL")
    lms_api_key = os.environ.get("NANOBOT_LMS_API_KEY")

    if "tools" in config and "mcpServers" in config["tools"]:
        if "lms" in config["tools"]["mcpServers"]:
            if "env" not in config["tools"]["mcpServers"]["lms"]:
                config["tools"]["mcpServers"]["lms"]["env"] = {}
            if lms_backend_url:
                config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = lms_backend_url
            if lms_api_key:
                config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_API_KEY"] = lms_api_key

    # Inject webchat channel settings
    webchat_host = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_ADDRESS")
    webchat_port = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT")

    if webchat_host or webchat_port:
        if "channels" not in config:
            config["channels"] = {}
        if "webchat" not in config["channels"]:
            config["channels"]["webchat"] = {}
        config["channels"]["webchat"]["enabled"] = True
        config["channels"]["webchat"]["allowFrom"] = ["*"]
        if webchat_host:
            config["channels"]["webchat"]["host"] = webchat_host
        if webchat_port:
            config["channels"]["webchat"]["port"] = int(webchat_port)

    # Inject webchat MCP server settings
    webchat_relay_url = os.environ.get("NANOBOT_WEBSOCKET_RELAY_URL")
    webchat_token = os.environ.get("NANOBOT_ACCESS_KEY")

    if webchat_relay_url or webchat_token:
        if "tools" not in config:
            config["tools"] = {}
        if "mcpServers" not in config["tools"]:
            config["tools"]["mcpServers"] = {}
        if "webchat" not in config["tools"]["mcpServers"]:
            config["tools"]["mcpServers"]["webchat"] = {
                "command": "python",
                "args": ["-m", "mcp_webchat"]
            }
        if "env" not in config["tools"]["mcpServers"]["webchat"]:
            config["tools"]["mcpServers"]["webchat"]["env"] = {}
        if webchat_relay_url:
            config["tools"]["mcpServers"]["webchat"]["env"]["NANOBOT_WEBSOCKET_RELAY_URL"] = webchat_relay_url
        if webchat_token:
            config["tools"]["mcpServers"]["webchat"]["env"]["NANOBOT_ACCESS_KEY"] = webchat_token

    # Inject observability MCP server settings
    victorialogs_url = os.environ.get("NANOBOT_VICTORIALOGS_URL")
    victoriatraces_url = os.environ.get("NANOBOT_VICTORIATRACES_URL")

    if victorialogs_url or victoriatraces_url:
        if "tools" not in config:
            config["tools"] = {}
        if "mcpServers" not in config["tools"]:
            config["tools"]["mcpServers"] = {}
        if "observability" not in config["tools"]["mcpServers"]:
            config["tools"]["mcpServers"]["observability"] = {
                "command": "python",
                "args": ["-m", "mcp_obs"]
            }
        if "env" not in config["tools"]["mcpServers"]["observability"]:
            config["tools"]["mcpServers"]["observability"]["env"] = {}
        if victorialogs_url:
            config["tools"]["mcpServers"]["observability"]["env"]["NANOBOT_VICTORIALOGS_URL"] = victorialogs_url
        if victoriatraces_url:
            config["tools"]["mcpServers"]["observability"]["env"]["NANOBOT_VICTORIATRACES_URL"] = victoriatraces_url

    # Write resolved config
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Using config: {resolved_path}")
    return str(resolved_path), str(workspace_path)


def main():
    """Resolve config and exec nanobot gateway."""
    import os
    import os.path

    config_path, workspace_path = resolve_config()

    # Build command
    cmd = [
        "nanobot",
        "gateway",
        "--config",
        config_path,
        "--workspace",
        workspace_path,
    ]

    # Exec nanobot gateway (replaces this process)
    os.execvp("nanobot", cmd)


if __name__ == "__main__":
    main()
