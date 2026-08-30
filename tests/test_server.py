# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pytest>=8",
#     "mcp>=1.2.0,<2",
#     "google-api-python-client>=2.100.0",
#     "google-auth-oauthlib>=1.2.0",
# ]
# ///
"""Unit tests for server.py. Run with:  uv run --script tests/test_server.py

All Google API calls are captured by a fake service object — no credentials,
no network.
"""

import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server


class FakeRequest:
    def __init__(self, result):
        self._result = result

    def execute(self):
        return self._result


class FakeTasks:
    """Records calls; returns canned results."""

    def __init__(self):
        self.inserted = []
        self.patched = []
        self.deleted = []
        self.list_result = {"items": []}

    def insert(self, tasklist, body):
        self.inserted.append((tasklist, body))
        return FakeRequest({"id": f"task{len(self.inserted)}", **body})

    def patch(self, tasklist, task, body):
        self.patched.append((tasklist, task, body))
        return FakeRequest({"id": task, **body})

    def delete(self, tasklist, task):
        self.deleted.append((tasklist, task))
        return FakeRequest(None)

    def list(self, **kwargs):
        self.list_kwargs = kwargs
        return FakeRequest(self.list_result)


class FakeTasklists:
    def __init__(self):
        self.list_result = {"items": []}

    def list(self, **kwargs):
        return FakeRequest(self.list_result)


class FakeService:
    def __init__(self):
        self._tasks = FakeTasks()
        self._tasklists = FakeTasklists()

    def tasks(self):
        return self._tasks

    def tasklists(self):
        return self._tasklists


@pytest.fixture
def service(monkeypatch):
    fake = FakeService()
    monkeypatch.setattr(server, "_service", fake)
    return fake


def test_all_tools_registered():
    tools = asyncio.run(server.mcp.list_tools())
    assert sorted(t.name for t in tools) == [
        "complete_task",
        "create_recurring_tasks",
        "create_task",
        "delete_task",
        "list_tasklists",
        "list_tasks",
        "update_task",
    ]


def test_slim_task_drops_unknown_keys():
    task = {"id": "x", "title": "t", "etag": "junk", "selfLink": "junk",
            "status": "needsAction"}
    assert server._slim_task(task) == {
        "id": "x", "title": "t", "status": "needsAction"
    }


def test_list_tasklists(service):
    service._tasklists.list_result = {
        "items": [{"id": "a", "title": "My Tasks", "etag": "junk"}]
    }
    result = json.loads(server.list_tasklists())
    assert result == [{"id": "a", "title": "My Tasks"}]


def test_create_task_formats_due_date(service):
    server.create_task("Water", notes="gently", due_date="2026-09-05")
    tasklist, body = service._tasks.inserted[0]
    assert tasklist == "@default"
    assert body == {
        "title": "Water",
        "notes": "gently",
        "due": "2026-09-05T00:00:00.000Z",
    }


def test_create_task_omits_empty_fields(service):
    server.create_task("Bare")
    _, body = service._tasks.inserted[0]
    assert body == {"title": "Bare"}


def test_create_recurring_tasks_spacing(service):
    out = json.loads(
        server.create_recurring_tasks(
            "Water", start_date="2026-09-05", every_days=6, count=3, notes="n"
        )
    )
    dues = [body["due"] for _, body in service._tasks.inserted]
    assert dues == [
        "2026-09-05T00:00:00.000Z",
        "2026-09-11T00:00:00.000Z",
        "2026-09-17T00:00:00.000Z",
    ]
    assert all(body["title"] == "Water" and body["notes"] == "n"
               for _, body in service._tasks.inserted)
    assert out["created"] == 3
    assert [t["due"] for t in out["tasks"]] == [
        "2026-09-05", "2026-09-11", "2026-09-17"
    ]


def test_create_recurring_tasks_month_rollover(service):
    server.create_recurring_tasks(
        "Water", start_date="2026-01-30", every_days=6, count=2
    )
    assert service._tasks.inserted[1][1]["due"] == "2026-02-05T00:00:00.000Z"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"count": 0},
        {"count": 101},
        {"every_days": 0},
    ],
)
def test_create_recurring_tasks_validation(service, kwargs):
    args = {"count": 3, "every_days": 6, **kwargs}
    with pytest.raises(ValueError):
        server.create_recurring_tasks("Water", "2026-09-05", **args)
    assert service._tasks.inserted == []


def test_create_recurring_tasks_bad_date(service):
    with pytest.raises(ValueError):
        server.create_recurring_tasks("Water", "05/09/2026", 6, 3)
    assert service._tasks.inserted == []


def test_update_task_partial(service):
    server.update_task("t1", due_date="2026-10-01")
    tasklist, task, body = service._tasks.patched[0]
    assert (tasklist, task) == ("@default", "t1")
    assert body == {"due": "2026-10-01T00:00:00.000Z"}


def test_update_task_nothing_to_update(service):
    with pytest.raises(ValueError):
        server.update_task("t1")
    assert service._tasks.patched == []


def test_complete_task(service):
    server.complete_task("t1", tasklist_id="listA")
    assert service._tasks.patched == [("listA", "t1", {"status": "completed"})]


def test_delete_task(service):
    out = json.loads(server.delete_task("t1"))
    assert service._tasks.deleted == [("@default", "t1")]
    assert out == {"deleted": "t1"}


def test_list_tasks_flags(service):
    service._tasks.list_result = {"items": [{"id": "a", "title": "t",
                                             "etag": "junk"}]}
    result = json.loads(server.list_tasks(show_completed=True))
    assert result == [{"id": "a", "title": "t"}]
    assert service._tasks.list_kwargs["showCompleted"] is True
    assert service._tasks.list_kwargs["showHidden"] is True


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
