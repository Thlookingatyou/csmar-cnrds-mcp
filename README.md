# Campus Data MCP

**A local browser bridge that lets AI agents use your existing CSMAR and CNRDS access,
without giving the agent a database password.**

Status: **experimental MVP**. The browser workflow is integration-tested against synthetic
sites. Public-site smoke tests and institutional download verification are separate; see
[validation](docs/validation.md). This is not an official CSMAR or CNRDS integration.

## Is password-free access possible?

Yes, where the institution's subscription enables campus-IP / school login. The browser
runs **on your computer**, so requests use your campus network or approved VPN. A cloud
agent connects to this local MCP server; running the browser on GitHub Actions or a
public server generally loses your campus IP.

| Service | Institutional route | Important boundary |
| --- | --- | --- |
| CSMAR | The website can recognize subscribing institutional IPs and log in automatically. | A visible table is not necessarily subscribed. The official personal-account API is a separate access route. |
| CNRDS | Use the website's visible **学校登录 / School Login** button, when available. | Basic databases may be available in full; specialty databases can still require personal registration. |

CNRDS is sometimes misspelled “CRNDS.” This project means **中国研究数据服务平台** at
`cnrds.com`. It cannot create subscriptions, extend an institution's licensed scope, or
make specialty data available when the website only grants samples.

Read the [feasibility assessment and sources](docs/feasibility.md).

## Install

Python 3.11+ and a desktop capable of running Chromium are required.

```sh
git clone https://github.com/Thlookingatyou/campus-data-mcp.git
cd campus-data-mcp
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m playwright install chromium
campus-data doctor
```

On Windows activate with `.venv\Scripts\Activate.ps1` and use `python` in place of
`python3`. Browser tests on Linux require `python -m playwright install --with-deps chromium`.

Connect to campus Wi-Fi, campus Ethernet, or your institution's authorized VPN. For a
first check, open one of the dedicated browsers:

```sh
campus-data login csmar
campus-data login cnrds
```

Use automatic/school login if your institution supports it. If the website requires
SSO, SMS, CAPTCHA, or personal registration, complete that yourself in the browser.
The connector has no password argument and will not fill authentication fields.
The dedicated profile stays on your computer and can be reused by the server.

## Connect an agent

Configure an MCP client to start this process locally. Replace both absolute paths:

```json
{
  "mcpServers": {
    "campus-data": {
      "command": "/ABSOLUTE/PATH/campus-data-mcp/.venv/bin/python",
      "args": ["-m", "campus_data_mcp.cli", "serve"],
      "env": {
        "CAMPUS_DATA_HOME": "/ABSOLUTE/PRIVATE/PATH/campus-data-state"
      }
    }
  }
}
```

If you installed the project into a different virtual environment, use that environment's
Python. On Windows, its executable is `.venv\Scripts\python.exe`. The server uses
**stdio only**; it does not expose an HTTP port or a shared public endpoint.

Example request to your agent:

> Open CNRDS and try school login. Search for the database containing corporate patent
> data. Inspect whether the selected table offers full data or samples. Select the fields
> and years I request, review the query on screen, and save the available CSV export locally.
> Report the file location and any access or coverage limitations.

See [the agent workflow](docs/agent-workflow.md) for a precise tool sequence.

## Tools

| Tool | Purpose |
| --- | --- |
| `campus_open` | Open a provider homepage or a provider URL in its dedicated browser. |
| `campus_school_login` | Click a unique visible school-login button. |
| `campus_inspect` | Read visible text and controls in all provider tabs and frames. |
| `campus_search` | Search the current website catalogue; accept explicit control references when needed. |
| `campus_act` | Click, fill, select, check, or press a restricted key on a current control. |
| `campus_scroll` | Bring a control into view. |
| `campus_export` | Click an export control and record the intended query. |
| `campus_downloads` | Check local download status and receipts. |
| `campus_close` | Close a provider session, keeping its profile for reuse. |

Every inspection or action returns fresh references and expires older ones. Search results
and export jobs can load asynchronously: inspect again, rather than resubmitting the query.
Browser-generated downloads are captured even if the provider produces them later or in
a new tab. When packaging finishes with a link, the agent must inspect and click that link.

## Local storage and privacy

Default root: `~/.local/share/campus-data-mcp`. Override it with `CAMPUS_DATA_HOME`.

```text
profiles/csmar/    private dedicated Chromium profile
profiles/cnrds/    separate CNRDS profile
incoming/         browser temporary downloads
downloads/csmar/  exports and *.manifest.json receipts
downloads/cnrds/  exports and *.manifest.json receipts
```

Profiles contain session secrets. Do not upload them, put the state directory inside a
public repository, or share it with other users. Directories are owner-only and saved
exports/manifests are owner-readable on systems with POSIX permissions. Windows users
should use a private user directory with suitable ACLs. These files are **not encrypted
by this project**. Close the server before deleting a profile to forget its session.

The tools do not return cookies, local storage, hidden fields, HTML source, input values,
or full signed URLs. Page text and labels can still include personal or licensed content;
token redaction is best-effort, not a general data-loss-prevention system. Any text returned
to a hosted AI model leaves your computer. Export tools return paths and receipts, not file
contents. Check your institution's license and model arrangements before exposing restricted
page content or asking another tool to read an export. A local model is an option.

Provider HTTPS domains and their subdomains are allowed. CNRDS's exact export host
`cnrds-file.oss-cn-shanghai.aliyuncs.com` is also allowed for CNRDS; other Aliyun buckets
are excluded. Other requests, redirects and
WebSockets are blocked. A required institution SSO or export CDN can be enabled **by the
local user** with comma-separated exact hostnames in `CAMPUS_DATA_EXTRA_HOSTS`; this
widens the trust boundary for both provider sessions. VPN portals that rewrite domains
need explicit configuration and may not work. Never disable TLS verification.

`CAMPUS_DATA_HEADLESS=1` is available for automated testing after access is established;
the default visible browser makes human verification possible. There is no automatic
CAPTCHA solving, fingerprint spoofing, quota splitting, account rotation, or bulk crawler.
Actions are serialized and spaced at least one second apart. This interval does not
replace provider limits: stop if the service displays a restriction.

The retained-file limit is 512 MiB **after transfer**; it is not a bandwidth cap. ZIP and 7z
exports receive file-signature checks. Archives
are retained without extraction. Files are not executed or automatically parsed. A checksum
proves file integrity, not correct coverage, full-data entitlement, or freedom from malware.

## Development

```sh
python -m pip install -e '.[dev]'
ruff check .
pytest -q
```

Tests use real Chromium with synthetic provider responses and synthetic data. They do
not need a school network or commercial data. CI runs the same suite. See
[validation](docs/validation.md) for what has and has not been verified.

## License

MIT for this project's original code. Database products, service documentation, and
downloaded data retain their owners' rights. This repository grants no rights to them.
