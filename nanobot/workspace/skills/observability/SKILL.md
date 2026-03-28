---
name: observability
description: Use observability tools to investigate system health, errors, and traces
always: true
---

# Observability Skill

Use observability MCP tools to investigate system health, errors, and traces when the user asks about system status, errors, or failures.

## Available Tools

- `logs_search` — Search logs using LogsQL query. Returns matching log entries.
- `logs_error_count` — Count errors per service over a time window. Returns error counts.
- `traces_list` — List recent traces for a service. Returns trace summaries.
- `traces_get` — Fetch a specific trace by ID. Returns full trace with spans.

## Strategy

### When the user asks about errors or system health:

1. **Start with `logs_error_count`** — Get a quick overview of recent errors
   - Use a narrow time window (e.g., 10 minutes) for recent issues
   - Filter by service name if the user specifies one (e.g., "LMS backend")

2. **If errors are found, use `logs_search`** — Inspect the actual error messages
   - Extract `trace_id` from log entries if available
   - Focus on the most relevant service

3. **If a trace_id is available, use `traces_get`** — Get the full picture
   - Examine the span hierarchy to understand the failure path
   - Look for error spans and their messages

4. **Summarize findings concisely** — Don't dump raw JSON
   - Mention what service is affected
   - Explain what operation failed
   - Include relevant error messages
   - Suggest next steps if appropriate

### Query patterns:

**For LMS backend errors:**
```
_time:10m service.name:"Learning Management Service" severity:ERROR
```

**For all recent errors:**
```
_time:10m severity:ERROR
```

**To find traces in logs:**
Look for the `trace_id` field in log entries and use it with `traces_get`.

### Response style:

- Keep responses concise and focused on actionable information
- Highlight the root cause if identifiable
- Mention timestamps and affected services
- If no errors are found, say the system looks healthy
- Offer to investigate further if needed

## Examples

**User:** "Any errors in the last hour?"
**You:** Call `logs_error_count` with minutes=60, then summarize

**User:** "What went wrong with the backend?"
**You:** 
1. Call `logs_error_count` with service="Learning Management Service"
2. Call `logs_search` to get error details
3. If trace_id found, call `traces_get`
4. Summarize the failure

**User:** "Is the system healthy?"
**You:** Call `logs_error_count` with a recent time window and report findings
