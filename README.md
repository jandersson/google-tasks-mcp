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
3. Configure the consent screen (**Google Auth Platform**, or **OAuth consent
   screen** in the sidebar): audience **External**, fill the required fields.
   The app name must not contain "Google" — Google rejects it.
4. On the **Audience** page, add your own Google account under **Test users**
   (it may already be there).
5. **Clients → Create client**, application type **Desktop app**.
6. Open the created client and **Download JSON** (in the Client secrets
   section), then save it as:

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

Clone the repo anywhere you like:

```
git clone https://github.com/jandersson/google-tasks-mcp.git
```

Then register the server, substituting the absolute path to your clone:

```
claude mcp add google-tasks -- uv run --script "/path/to/google-tasks-mcp/server.py"
```

(e.g. `C:\Users\you\google-tasks-mcp\server.py` on Windows,
`/Users/you/google-tasks-mcp/server.py` on macOS)

Restart Claude Code afterwards — newly added MCP servers only load in a new
session.

## First run

The first tool call opens a browser for Google authorization. Approve it (the
"unverified app" warning is expected for a personal test-user client) and the
token is cached; later calls run without a browser.

## Troubleshooting

- **Auth stops working after ~a week**: while the OAuth app's publishing
  status is "Testing", Google expires refresh tokens after 7 days. Fix it
  permanently on the **Audience** page → **Publish app** (no verification
  needed for personal use — the consent screen just keeps its "unverified"
  warning). Then delete `token.json` and authorize once more.
- **Tools don't appear after registering**: MCP servers load at session
  start, and resuming an existing conversation keeps its old tool set —
  start a *new* session.
- **Re-authorizing**: delete `token.json` from the config directory and the
  next tool call opens the browser again.
- **`create_recurring_tasks` is not idempotent** — running it twice creates
  two full series of tasks.
