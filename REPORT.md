# Lab 8 — Report

## Task 1A — Bare agent

**Question: "What is the agentic loop?"**

The agentic loop is the core feedback cycle that powers an autonomous AI agent. It repeatedly consists of four steps:

1. **Perceive** – The agent gathers data from its environment (e.g., user input, memory, API responses, sensor readings).
2. **Reason** – It evaluates that information, forms a plan, and decides which action will move it closer to its goal.
3. **Act** – The agent executes the chosen action, typically by calling a tool, running a command, or producing an output.
4. **Perceive again** – The result of the action is observed (success, failure, new information), and the cycle starts over.

By iterating through this loop, the agent can adapt its behavior, handle unexpected outcomes, and progressively achieve complex objectives.

**Question: "What labs are available in our LMS?"**

The agent returned real lab data from the LMS backend:
- Lab 01 – Products, Architecture & Roles
- Lab 02 — Run, Fix, and Deploy a Backend Service
- Lab 03 — Backend API: Explore, Debug, Implement, Deploy
- Lab 04 — Testing, Front-end, and AI Agents
- Lab 05 — Data Pipeline and Analytics Dashboard
- Lab 06 — Build Your Own Agent
- Lab 07 — Build a Client with an AI Coding Agent
- Lab 08

## Task 1B — Agent with LMS tools

**Question: "What labs are available?"**

The agent successfully called the `mcp_lms_lms_labs` MCP tool and returned real lab names from the backend database.

**Question: "Is the LMS backend healthy?"**

The agent called `mcp_lms_lms_health` and reported:
- Status: Healthy
- Item count: 56 items in the database

## Task 1C — Skill prompt

**Question: "Show me the scores" (without specifying a lab)**

The agent responded with pass rates for Lab 02, showing:
- Task 1: Run the web server - 67.9% avg score, 210 attempts
- Task 2: Identify, report, and fix a bug - 66.7% avg score, 216 attempts
- Task 4: Deploy the web server to the VM - 56.2% avg score, 84 attempts
- Optional tasks with lower completion rates

The LMS skill prompt (`nanobot/workspace/skills/lms/SKILL.md`) guides the agent to:
- Call `lms_labs` first when lab is not specified
- Use structured UI messages for lab selection
- Format numeric results nicely (percentages, counts)
- Keep responses concise

## Task 2A — Deployed agent

**Nanobot startup logs:**

```
Using config: /app/nanobot/config/config.resolved.json
🐈 Starting nanobot gateway version 0.1.4.post5 on port 18790...
✓ Channels enabled: webchat
✓ Heartbeat: every 1800s
MCP server 'lms': connected, 9 tools registered
MCP server 'webchat': connected, 1 tools registered
MCP server 'observability': connected, 4 tools registered
Agent loop started
```

## Task 2B — Web client

The Flutter web client is accessible at `http://<vm-ip>:42002/flutter`.

**Test conversation:**
- Question: "What can you do in this system?"
- Response: Agent explained its capabilities including LMS queries, observability tools, and scheduled tasks

- Question: "What labs are available?"
- Response: Agent listed all 8 labs from the LMS backend

The WebSocket endpoint at `/ws/chat` responds correctly when called with the access key.

## Task 3A — Structured logging

**Happy-path log excerpt (successful request):**

```
2026-03-28 10:50:19,493 INFO [lms_backend.main] - request_started [trace_id=62f7fdc766ec1bb80bcfdf6dce51161a]
2026-03-28 10:50:19,497 INFO [lms_backend.auth] - auth_success
2026-03-28 10:50:19,498 INFO [lms_backend.db.items] - db_query
2026-03-28 10:50:19,502 INFO [lms_backend.main] - request_completed
INFO: 172.21.0.10:39778 - "GET /items/ HTTP/1.1" 200 OK
```

**Error-path log excerpt (PostgreSQL stopped):**

```
2026-03-28 11:00:17,323 INFO [lms_backend.db.items] - db_query
2026-03-28 11:00:17,325 ERROR [lms_backend.db.items] - db_query
  File "/app/.venv/lib/python3.14/site-packages/asyncpg/connection.py", line 2443, in connect
    raise last_error
socket.gaierror: [Errno -2] Name or service not known
2026-03-28 11:00:17,325 WARNING [lms_backend.routers.items] - items_list_failed_as_not_found
INFO: 172.21.0.9:60458 - "GET /items/ HTTP/1.1" 404 Not Found
```

**VictoriaLogs query:**
Query: `_time:10m service.name:"Learning Management Service" severity:ERROR`
Returns error logs filtered by service and severity level.

## Task 3B — Traces

Traces are available at `http://<vm-ip>:42002/utils/victoriatraces`.

**Healthy trace:** Shows span hierarchy with `request_started` → `auth_success` → `db_query` → `request_completed`

**Error trace:** Shows the failure point at `db_query` with the PostgreSQL connection error propagating through the span hierarchy.

## Task 3C — Observability MCP tools

**Question: "Any LMS backend errors in the last 10 minutes?" (normal conditions)**

Agent response: "I'll check for LMS backend errors in the last 10 minutes."

The agent called:
1. `mcp_observability_logs_error_count` with minutes=10, service="Learning Management Service"
2. `mcp_observability_logs_search` with LogsQL query

**Question: "Any LMS backend errors in the last 10 minutes?" (with PostgreSQL stopped)**

Agent response: "Yes, there are **2 errors** in the LMS backend in the last 10 minutes. Both are database connectivity issues."

The observability MCP server (`mcp/mcp-obs/`) provides four tools:
- `logs_search` — Search logs using LogsQL query
- `logs_error_count` — Count errors per service over a time window
- `traces_list` — List recent traces for a service
- `traces_get` — Fetch a specific trace by ID

## Task 4A — Multi-step investigation

**Question: "What went wrong?" (with PostgreSQL stopped)**

Agent investigation flow:
1. Called `logs_error_count` to find recent errors
2. Called `logs_search` to inspect error details
3. Extracted trace_id from logs
4. Called `traces_get` to fetch the full trace

**Agent response:**

"Based on my investigation, here's what went wrong:

## Root Cause: Database Connection Failure

The LMS backend cannot connect to the PostgreSQL database. The error shows:
- **Error type:** `socket.gaierror: [Errno -2] Name or service not known`
- **Affected service:** Learning Management Service
- **Failed operation:** Database query in `read_items()` function
- **Impact:** All item-related endpoints return 404 errors

The database container appears to be stopped or unreachable."

## Task 4B — Proactive health check

**Created scheduled health check:**

Request: "Create a health check for this chat that runs every 2 minutes using your cron tool."

Agent response: Created cron job with:
- Job ID: 9aa432d4
- Interval: 120 seconds (2 minutes)
- Action: Check for LMS/backend errors using `logs_error_count`

**Scheduled jobs listing:**

| Job | Interval | Next Run |
|-----|----------|----------|
| HEALTH CHECK: Check for LMS/backend errors... | Every 120s | [calculated] |

**Initial health report:**

```
🏥 Health Check Report (2026-03-28 11:16 UTC)

✅ System looks healthy

- LMS backend errors (last 2 min): 0
- All services operational
```

## Task 4C — Bug fix and recovery

### 1. Root Cause

**Planted bug location:** `backend/src/lms_backend/routers/items.py`

**Bug description:** The `get_items()` endpoint caught ALL exceptions (including database connection failures) and returned HTTP 404 "Items not found" instead of a proper 500 Internal Server Error. This hid the real cause of failures from users and monitoring systems.

```python
# BUGGY CODE:
except Exception as exc:
    logger.warning("items_list_failed_as_not_found", ...)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Items not found",
    ) from exc
```

### 2. Fix

**Changed file:** `backend/src/lms_backend/routers/items.py`

**Fix description:**
- Changed log level from `warning` to `error`
- Changed HTTP status from 404 to 500 Internal Server Error
- Added actual error type to the response detail
- Updated log message to include the actual error

```python
# FIXED CODE:
except Exception as exc:
    logger.error(
        "items_list_failed",
        extra={"event": "items_list_failed", "error": str(exc)},
    )
    # Re-raise as 500 Internal Server Error for database/connection issues
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to retrieve items: {type(exc).__name__}",
    ) from exc
```

### 3. Post-fix verification

After rebuilding and restarting:
- Agent health check: "Yes, the LMS backend is healthy! ✅"
- Status: Healthy
- Item count: 56 items
- Errors: None

### 4. Recovery confirmation

The system now correctly:
- Returns 500 errors for database failures (not misleading 404s)
- Logs the actual error details for debugging
- Reports healthy status when PostgreSQL is running

---

## Summary

All lab tasks completed successfully:
- ✅ Nanobot agent deployed as Docker service
- ✅ WebSocket channel and Flutter web client working
- ✅ LMS MCP tools providing real backend data
- ✅ Observability MCP tools for logs and traces
- ✅ Proactive health checks via cron
- ✅ Planted bug identified and fixed
