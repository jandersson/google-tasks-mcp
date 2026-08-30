# Privacy Policy — Tasks MCP

Tasks MCP is a self-hosted, single-user tool. You run it on your own machine
against your own Google account.

- **No data collection.** The developer operates no servers and receives no
  data. Nothing is logged, transmitted, or shared with anyone.
- **Local storage only.** Your OAuth credentials and access token are stored
  as files on your own computer (`~/.config/google-tasks-mcp/`). They are
  used solely to call the Google Tasks API on your behalf.
- **Scope of access.** The app requests the Google Tasks scope
  (`https://www.googleapis.com/auth/tasks`) to read and manage your task
  lists — at your explicit instruction, from your own machine.
- **Revocation.** Revoke access at any time at
  [myaccount.google.com/permissions](https://myaccount.google.com/permissions)
  and delete the local token file.

Questions: open an issue on the
[GitHub repository](https://github.com/jandersson/google-tasks-mcp).
