---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS Skill

Use LMS MCP tools to provide real-time information about the course, labs, learners, and performance metrics.

## Available Tools

- `lms_health` — Check if the LMS backend is healthy and report the item count
- `lms_labs` — List all labs available in the LMS
- `lms_learners` — List all learners registered in the LMS
- `lms_pass_rates` — Get pass rates (avg score and attempt count per task) for a lab
- `lms_timeline` — Get submission timeline (date + submission count) for a lab
- `lms_groups` — Get group performance (avg score + student count per group) for a lab
- `lms_top_learners` — Get top learners by average score for a lab
- `lms_completion_rate` — Get completion rate (passed / total) for a lab
- `lms_sync_pipeline` — Trigger the LMS sync pipeline

## Strategy

### When user asks about scores, pass rates, completion, groups, timeline, or top learners without naming a lab:

1. Call `lms_labs` first to get available labs
2. If multiple labs exist, use `mcp_webchat_ui_message` with `type: "choice"` to let the user pick
3. Provide short, readable lab labels using the lab title from the `lms_labs` response
4. Use the lab ID as the stable value for the follow-up tool call

### When user asks "what can you do?":

Explain your current capabilities clearly:
- You can query the LMS backend for information about labs, learners, and performance metrics
- You can check system health and trigger data sync
- You have access to observability tools for logs and traces (if configured)
- Be honest about what you can and cannot do

### Formatting responses:

- Format numeric results nicely: show percentages with `%` symbol, round to 1-2 decimal places
- Keep responses concise — summarize key findings, don't dump raw JSON
- When presenting multiple items (labs, learners), use bullet points or numbered lists
- Always mention the data source (e.g., "According to the LMS backend...")

### Error handling:

- If a tool call fails, explain what went wrong in plain language
- Suggest alternatives (e.g., "The backend is unavailable. Would you like me to check system logs?")
- If a lab parameter is needed and not provided, ask the user to specify which lab

## Examples

**User:** "Show me the scores"
**You:** Call `lms_labs`, then present a choice of labs using `mcp_webchat_ui_message`

**User:** "Which lab has the lowest pass rate?"
**You:** Call `lms_labs`, then call `lms_pass_rates` for each lab, compare results, and report the answer

**User:** "Is the backend healthy?"
**You:** Call `lms_health` and report the status and item count

**User:** "What can you do?"
**You:** Explain your LMS tools and observability capabilities clearly
