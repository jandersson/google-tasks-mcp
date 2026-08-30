# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "mcp>=1.2.0",
#     "google-api-python-client>=2.100.0",
#     "google-auth-oauthlib>=1.2.0",
# ]
# ///
"""Google Tasks MCP server.

Exposes Google Tasks as MCP tools over stdio. OAuth credentials live in
~/.config/google-tasks-mcp/ (credentials.json downloaded from Google Cloud
Console, token.json written after the first authorization).
"""

import datetime
import json
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from mcp.server.fastmcp import FastMCP

SCOPES = ["https://www.googleapis.com/auth/tasks"]
CONFIG_DIR = Path.home() / ".config" / "google-tasks-mcp"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.json"
TOKEN_FILE = CONFIG_DIR / "token.json"

mcp = FastMCP("google-tasks")

_service = None


def _get_service():
    global _service
    if _service is not None:
        return _service

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise RuntimeError(
                    f"OAuth client file not found: {CREDENTIALS_FILE}. "
                    "Create a Desktop-app OAuth client in Google Cloud Console "
                    "(with the Google Tasks API enabled) and save the downloaded "
                    "JSON to that path."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            # stdout carries the MCP protocol; suppress the console prompt.
            creds = flow.run_local_server(
                port=0, authorization_prompt_message=None
            )
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(creds.to_json())

    _service = build("tasks", "v1", credentials=creds)
    return _service


def _slim_task(task: dict) -> dict:
    return {
        k: task[k]
        for k in ("id", "title", "notes", "due", "status", "completed")
        if k in task
    }


@mcp.tool()
def list_tasklists() -> str:
    """List all Google Tasks task lists (id and title)."""
    result = _get_service().tasklists().list(maxResults=100).execute()
    lists = [
        {"id": tl["id"], "title": tl["title"]}
        for tl in result.get("items", [])
    ]
    return json.dumps(lists, indent=2, ensure_ascii=False)


@mcp.tool()
def list_tasks(tasklist_id: str = "@default", show_completed: bool = False) -> str:
    """List tasks in a task list.

    Args:
        tasklist_id: Task list id from list_tasklists, or "@default".
        show_completed: Include completed (and hidden) tasks.
    """
    result = (
        _get_service()
        .tasks()
        .list(
            tasklist=tasklist_id,
            maxResults=100,
            showCompleted=show_completed,
            showHidden=show_completed,
        )
        .execute()
    )
    tasks = [_slim_task(t) for t in result.get("items", [])]
    return json.dumps(tasks, indent=2, ensure_ascii=False)


@mcp.tool()
def create_task(
    title: str,
    notes: str = "",
    due_date: str = "",
    tasklist_id: str = "@default",
) -> str:
    """Create a single task.

    Args:
        title: Task title.
        notes: Optional task notes/description.
        due_date: Optional due date as YYYY-MM-DD (Google Tasks ignores the
            time portion).
        tasklist_id: Task list id, or "@default".
    """
    body: dict = {"title": title}
    if notes:
        body["notes"] = notes
    if due_date:
        body["due"] = f"{due_date}T00:00:00.000Z"
    task = _get_service().tasks().insert(tasklist=tasklist_id, body=body).execute()
    return json.dumps(_slim_task(task), indent=2, ensure_ascii=False)


@mcp.tool()
def create_recurring_tasks(
    title: str,
    start_date: str,
    every_days: int,
    count: int,
    notes: str = "",
    tasklist_id: str = "@default",
) -> str:
    """Create a series of dated tasks as a stand-in for a repeat rule.

    The Google Tasks API cannot set recurrence, so this creates `count`
    individual tasks starting at start_date, spaced every_days apart.

    Args:
        title: Title used for every task in the series.
        start_date: First due date as YYYY-MM-DD.
        every_days: Days between consecutive tasks.
        count: Number of tasks to create.
        notes: Optional notes applied to every task.
        tasklist_id: Task list id, or "@default".
    """
    if count < 1 or count > 100:
        raise ValueError("count must be between 1 and 100")
    if every_days < 1:
        raise ValueError("every_days must be at least 1")

    service = _get_service()
    start = datetime.date.fromisoformat(start_date)
    created = []
    for i in range(count):
        due = start + datetime.timedelta(days=i * every_days)
        body: dict = {"title": title, "due": f"{due.isoformat()}T00:00:00.000Z"}
        if notes:
            body["notes"] = notes
        task = service.tasks().insert(tasklist=tasklist_id, body=body).execute()
        created.append({"id": task["id"], "due": due.isoformat()})
    return json.dumps(
        {"created": len(created), "tasks": created}, indent=2, ensure_ascii=False
    )


@mcp.tool()
def update_task(
    task_id: str,
    title: str = "",
    notes: str = "",
    due_date: str = "",
    tasklist_id: str = "@default",
) -> str:
    """Update a task's title, notes, and/or due date (empty args are left unchanged).

    Args:
        task_id: Task id from list_tasks.
        title: New title, if changing.
        notes: New notes, if changing.
        due_date: New due date as YYYY-MM-DD, if changing.
        tasklist_id: Task list id, or "@default".
    """
    body: dict = {}
    if title:
        body["title"] = title
    if notes:
        body["notes"] = notes
    if due_date:
        body["due"] = f"{due_date}T00:00:00.000Z"
    if not body:
        raise ValueError("Nothing to update: pass title, notes, and/or due_date")
    task = (
        _get_service()
        .tasks()
        .patch(tasklist=tasklist_id, task=task_id, body=body)
        .execute()
    )
    return json.dumps(_slim_task(task), indent=2, ensure_ascii=False)


@mcp.tool()
def complete_task(task_id: str, tasklist_id: str = "@default") -> str:
    """Mark a task as completed.

    Args:
        task_id: Task id from list_tasks.
        tasklist_id: Task list id, or "@default".
    """
    task = (
        _get_service()
        .tasks()
        .patch(tasklist=tasklist_id, task=task_id, body={"status": "completed"})
        .execute()
    )
    return json.dumps(_slim_task(task), indent=2, ensure_ascii=False)


@mcp.tool()
def delete_task(task_id: str, tasklist_id: str = "@default") -> str:
    """Delete a task permanently.

    Args:
        task_id: Task id from list_tasks.
        tasklist_id: Task list id, or "@default".
    """
    _get_service().tasks().delete(tasklist=tasklist_id, task=task_id).execute()
    return json.dumps({"deleted": task_id})


if __name__ == "__main__":
    mcp.run()
