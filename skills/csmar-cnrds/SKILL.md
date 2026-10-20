---
name: csmar-cnrds
description: Search and download CSMAR (国泰安) and CNRDS (中国研究数据服务平台, sometimes written CRNDS) research data through existing institutional access. Use for catalogue discovery, table and field selection, campus login, filtered exports, or setup of this project's local MCP connector. Analysis of already downloaded files alone does not require this skill.
---

# CSMAR & CNRDS research data

Help the user obtain the requested data through their institution's existing access.
Respond in the user's language. The browser must run on their campus-connected computer
or institution-supported VPN; a remote cloud browser can have a different network identity.

## Connection

Use the installed CSMAR-CNRDS MCP connector's `campus_*` tools. Tool names may have a
client-added namespace. If the tools are missing, read [setup](references/setup.md),
install or reuse the local runtime, and configure the connection as supported by the client.
The connector runs hidden by default. Keep background mode for ordinary queries and
exports unless the user requests a visible browser. A skill supplies instructions; it
does not itself install Chromium or expose MCP tools.
Distinguish configuration saved from tools actually available in the current session.
For a setup-only request, verify the connection without creating a data-export job.

## Query and export

1. Establish the requested provider, table or research concept, dates, entities, fields,
   frequency and output format. Search for candidate tables before asking the user to
   supply unknown vendor table names. Clarify missing choices that materially change scope.
2. Open `csmar` or `cnrds` with `campus_open`. CSMAR may recognize the institution
   automatically. Use `campus_school_login` when a school-login control is visible.
   If personal login or CAPTCHA requires a person, finish active downloads, close that
   provider, and use `campus-data login <provider>` with the same `CAMPUS_DATA_HOME`.
   This opens a visible browser; close it before reopening the provider through MCP.
   Do not tell the user to interact with a hidden window.
3. Search with `campus_search`. If Enter does not submit, inspect and click the observed
   search button. Inspect table descriptions, available fields, units, date coverage and
   subscription/sample indicators before choosing the table.
4. Set the requested filters with `campus_act`, scrolling as needed. Use each SELECT
   option's observed `value`; `check` takes the string `"true"` or `"false"`.
   Preview and check the resulting coverage where available. CNRDS tables without a
   dedicated time control may support a year condition through **条件设置**.
5. Use `campus_export` for the requested export, with a query note recording the table,
   dates, entity filters, fields, units where known, format and full/sample indicators.
   An empty download result can mean the provider is preparing a job. Inspect the existing
   job and its status; when ready, click its download control. Do not submit a duplicate
   export merely because no file arrived immediately. Shared school accounts may show
   other users' jobs: download only the job matching this request and its creation time.
6. Check `campus_downloads`. Verify a saved file's actual format, row count, date/entity
   coverage and headers using available local file tools. State any check you could not
   perform. CNRDS can label a ZIP container `.7z`; inspect the signature rather than
   assuming its archive type. Preserve vendor attribution and copyright files.
7. Report the local file and receipt paths, query coverage and material limitations.
   Close the provider with `campus_close` after downloads finish unless the user needs
   the session left open. Files remain local; current-process download lists are not a
   complete history of earlier exports.

## Fragile interface behavior

- Every inspection or action returning a snapshot expires earlier control references.
  Use the fresh references; a SPA may require another inspection after loading settles.
- CSMAR can display a first-use notice/tutorial. The connector exposes CSS-only close
  controls and CNRDS download icons through current refs. Use `icon_hint`, `unlabeled`,
  `dialog` and `context` to identify them. Context includes a download's row and creation
  time; select only this request's job. The tested tutorial and final download steps work
  through MCP without manual browser interaction. For an unrepresented control, first
  check control pagination and inspect again; use available browser tools or ask for that
  specific human step only if it remains inaccessible. Report any fallback actually used.
- Do not fabricate field codes, hidden endpoints or subscription status. A visible catalogue,
  preview, institution label or saved export establishes only what was actually observed.
  Basic-table success does not establish access to specialty products or other institutions.
- Stop the affected operation on denied access or a displayed rate limit. Report the
  subscription/network restriction; do not retry through alternate accounts or hosts.
  Use the connector's existing host scope; extra SSO/CDN hosts require explicit local
  configuration rather than disabling its network checks.
- Keep profiles, exports and signed links outside public repositories. Do not ask for
  passwords, cookies or tokens in chat. Follow the user's data-sharing instructions and
  applicable institutional licence when reading data with other tools or sending it elsewhere.
