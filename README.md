# google-tasks-mcp

A single-file Python MCP server for Google Tasks. Runs via `uv run --script`
(PEP 723 inline dependencies — no venv or install step).

## Tools

| Tool | Purpose |
| --- | --- |
| `list_tasklists` | List task lists (id + title) |
| `list_tasks` | List tasks in a list (optionally completed ones) |
| `create_task` | Create one task with optional notes and due date |
| `create_recurring_tasks` | Create N dated tasks spaced K days apart (the API can't set repeat rules, so a series of individual tasks stands in for one) |
| `update_task` | Change a task's title, notes, or due date |
| `complete_task` | Mark a task completed |
| `delete_task` | Delete a task permanently |

## Setup

### 1. OAuth client

1. Go to [console.cloud.google.com](https://console.cloud.google.com), pick or
   create a project.
2. **APIs & Services → Library** → enable **Google Tasks API**.
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID**,
   application type **Desktop app**.
   - If prompted to configure a consent screen first: User type **External**,
     fill the required fields, and add your own Google account as a test user.
4. Download the client JSON and save it as:

   ```
   %USERPROFILE%\.config\google-tasks-mcp\credentials.json   (Windows)
   ~/.config/google-tasks-mcp/credentials.json               (macOS / Linux)
   ```

`token.json` is written next to it after the first authorization. Neither file
belongs in git.

### 2. uv

Requires [uv](https://docs.astral.sh/uv/). On Windows:

```
winget install astral-sh.uv
```

On macOS:

```
brew install uv
```

(or the [standalone installer](https://docs.astral.sh/uv/getting-started/installation/):
`curl -LsSf https://astral.sh/uv/install.sh | sh`, which also covers Linux)

### 3. Register with Claude Code

Windows:

```
claude mcp add google-tasks -- uv run --script "%USERPROFILE%\dev\google-tasks-mcp\server.py"
```

macOS / Linux:

```
claude mcp add google-tasks -- uv run --script "$HOME/dev/google-tasks-mcp/server.py"
```

(adjust the path to wherever you cloned the repo)

Restart Claude Code afterwards — newly added MCP servers only load in a new
session.

## First run

The first tool call opens a browser for Google authorization. Approve it (the
"unverified app" warning is expected for a personal test-user client) and the
token is cached; later calls run without a browser.
