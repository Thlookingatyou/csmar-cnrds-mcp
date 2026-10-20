# Local connector setup for Codex

Read this when `campus_*` tools are missing or the user requests installation. The skill
and runtime are separate installations. Reuse an existing working installation instead
of cloning another copy or replacing an unrelated MCP configuration.

## Install or locate the runtime

Repository: https://github.com/Thlookingatyou/csmar-cnrds-mcp

Requirements: Python 3.11+, Git and a desktop capable of running Chromium. The browser
must run on the user's institution-authorized computer/network. Follow the environment's
normal installation and configuration permissions; this skill does not grant additional ones.

In a user-appropriate application directory, the macOS/Linux setup is:

```sh
git clone https://github.com/Thlookingatyou/csmar-cnrds-mcp.git
cd csmar-cnrds-mcp
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m playwright install chromium
.venv/bin/python -m campus_data_mcp.cli doctor
```

Use the actual directory and Python executable, including an existing virtual environment
when appropriate. On Windows, use `python -m venv .venv` and
`.venv\Scripts\python.exe` for the following Python commands. On Linux, install browser
system dependencies only if needed and permitted; Playwright supports
`python -m playwright install --with-deps chromium`.

`doctor` verifies browser installation, not institutional entitlement. If an existing
runtime is broken, diagnose that specific failure before reinstalling it.

## Connect Codex

Check whether the connector is already configured and its tools are available. When the
Codex CLI is installed, inspect `codex mcp add --help` and `codex mcp list` as needed.
For a new connection, replace both example paths with actual **absolute paths**:

```sh
codex mcp add campus-data \
  --env CAMPUS_DATA_HOME=/ABSOLUTE/PRIVATE/PATH/campus-data-state \
  --env CAMPUS_DATA_HEADLESS=1 \
  -- /ABSOLUTE/PATH/csmar-cnrds-mcp/.venv/bin/python -m campus_data_mcp.cli serve
```

Quote paths containing spaces. Keep the state directory outside the source checkout;
profiles contain session secrets. A pre-existing state directory may preserve useful
sessions. The default is `~/.local/share/campus-data-mcp`.

If the CLI is unavailable, use the client's MCP settings or add the equivalent local
stdio entry to its supported configuration. For Codex, the TOML shape is:

```toml
[mcp_servers.campus-data]
command = "/ABSOLUTE/PATH/csmar-cnrds-mcp/.venv/bin/python"
args = ["-m", "campus_data_mcp.cli", "serve"]

[mcp_servers.campus-data.env]
CAMPUS_DATA_HOME = "/ABSOLUTE/PRIVATE/PATH/campus-data-state"
CAMPUS_DATA_HEADLESS = "1"
```

Merge only this server entry; preserve other client settings and existing server entries.
Use forward slashes or properly escaped Windows paths in TOML. The generic `mcpServers`
JSON example used by some other MCP clients is not a Codex TOML configuration.

After configuration, verify the server can initialize and exposes `campus_open`,
`campus_inspect`, `campus_school_login`, `campus_search`, `campus_act`, `campus_scroll`,
`campus_export`, `campus_downloads` and `campus_close`. A configuration listing alone does
not prove that tools loaded. If the current chat cannot reload MCP tools, explain the
remaining reload/restart step and resume the user's data task when the tools are available.
Do not report setup complete before the connection has been checked.

## Background mode and interactive login

The connector runs without a browser window by default. Keep `CAMPUS_DATA_HEADLESS=1`
for background work. Set it to `0` and restart the connector only when the user wants
visible operation or needs interactive troubleshooting. The snapshot's `headless` field
reports the current mode. The standalone `login` command always opens a visible browser.
Do not change to visible mode just to click ordinary tutorial or download controls.

For an initial interactive check, use the configured environment's Python:

```sh
python -m campus_data_mcp.cli login csmar
python -m campus_data_mcp.cli login cnrds
```

Use the same `CAMPUS_DATA_HOME` as the MCP server. Finish active downloads and close
the provider's MCP session before running `login`; close the standalone login browser
before reopening it through MCP. CNRDS may require clicking school
login again in a new session. Any SSO, SMS or CAPTCHA belongs with the user in the browser.
The project offers no password argument and no access bypass. Diagnose an unrecognized
campus IP or unavailable subscription from the provider's visible response.

Basic-table exports have been verified on one campus network using only the connector's
MCP tools. Both CSMAR's first-use tutorial and CNRDS's final download icon are now exposed
as current refs. `context` supplies the download row or nearby visible text, `dialog`
supplies its heading, and `icon_hint` helps identify unlabeled controls. Update an older
runtime with `git pull --ff-only`, reinstall with its Python and restart its MCP process
before expecting the new metadata. Authentication challenges still belong with the user.

Project setup guide: https://github.com/Thlookingatyou/csmar-cnrds-mcp/blob/main/docs/setup.md

Codex configuration reference: https://learn.chatgpt.com/docs/extend/mcp?surface=cli
