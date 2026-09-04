---
name: notion-add-task
description: Create one or more entries in the user's Notion Tasks database from free-form requests, URLs, pasted notes, documents, or meeting/action-item text. Use when the user asks to add, create, log, import, or schedule tasks, todos, reminders, due dates, priorities, assignees, projects, subtasks, or recurring tasks in Notion.
---

# Notion Add Task

Use the Notion MCP tools to create task pages in the user's `Tasks` database.

## Database

- Database: `Tasks`
- Database ID: `a45e5198-eb31-8227-8869-81caec7324ab`
- Data source: `collection://bd7e5198-eb31-8382-9818-87e37c4ac2e1`
- Title property: `Name`
- Common writable properties: `Name`, `Status`, `Priority`, `Description`, `date:Due:start`, `date:Due:end`, `date:Due:is_datetime`, `Project`, `Parent Task`, `Assignee`, `Recur Interval`, `Recur Unit`, `Days (Only if Set to 1 Day(s))`, `Smart List`
- Status values: `To Do`, `Doing`, `Done`
- Priority values: `Low`, `Medium`, `High`

Always fetch the database before writing if there is any chance the schema changed. Use the fetched property names exactly.

## Workflow

1. Parse the request into one task per concrete action.
2. Resolve relative dates against the user's current date and timezone from the conversation environment.
3. Search or query only when needed to resolve existing projects, parent tasks, assignees, or possible duplicates.
4. Create pages with `mcp__codex_apps__notion._notion_create_pages` and parent `{"data_source_id":"bd7e5198-eb31-8382-9818-87e37c4ac2e1"}`.
5. Verify important writes by fetching the created page or querying the task title/date when the tool response is not enough.

## Property Mapping

Build each page with these defaults unless the user says otherwise:

- `Name`: concise action title.
- `Status`: `To Do`.
- `Priority`: `Medium`; use `High` or `Low` only when explicit or strongly implied.
- `Description`: source context, links, constraints, or brief notes that should remain searchable.
- Due date: set `date:Due:start` to `YYYY-MM-DD` for all-day dates and `date:Due:is_datetime` to `0`.
- Due datetime: set `date:Due:start` to an ISO datetime and `date:Due:is_datetime` to `1`.
- Date range: also set `date:Due:end`; do not set an end date for single-date tasks.

Only set relation or people properties after resolving real Notion entities:

- `Project`: JSON string for a single related project page URL.
- `Parent Task`: JSON string for a single related task page URL.
- `Assignee`: JSON array of user IDs.

For recurring tasks, set recurrence properties only when the recurrence is explicit:

- `Recur Interval`: numeric interval.
- `Recur Unit`: one of `Day(s)`, `Week(s)`, `Month(s)`, `Month(s) on the First Weekday`, `Month(s) on the Last Weekday`, `Month(s) on the Last Day`, `Year(s)`.
- `Days (Only if Set to 1 Day(s))`: JSON array of weekday names when daily recurrence is limited to specific days.

## Creation Example

```json
{
  "parent": {"data_source_id": "bd7e5198-eb31-8382-9818-87e37c4ac2e1"},
  "pages": [
    {
      "properties": {
        "Name": "Submit reimbursement form",
        "Status": "To Do",
        "Priority": "Medium",
        "Description": "Include taxi receipts.",
        "date:Due:start": "2026-07-08",
        "date:Due:is_datetime": 0
      }
    }
  ]
}
```

## Guardrails

- Ask a concise clarification when the task title, due date, or target Notion entity is ambiguous enough that a wrong task would be harmful.
- Do not create duplicate tasks unless the user explicitly wants another copy.
- Do not update formula, rollup, created time, edited time, or other read-only properties.
- Do not apply templates unless the user asks for the template behavior.
