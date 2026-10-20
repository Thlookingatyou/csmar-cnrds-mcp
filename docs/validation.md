# Validation

This is an experimental browser connector. Do not equate synthetic integration tests with
an end-to-end institutional download.

## Results — 2026-10-18

- **51 tests passed** on macOS arm64, Python 3.13.5, MCP SDK 1.30.0, Playwright 1.64.0
  and Chromium 156. The suite includes real browser interaction and a real stdio MCP client.
- Static checks passed with Ruff 0.17.1. Editable package installation and the `doctor`
  command succeeded.
- Live public CSMAR smoke check: homepage and embedded application loaded; two allowed
  frames and 83 visible controls were observed. Institutional entitlement remained unverified.
- Live public CNRDS smoke check: login page loaded; 13 visible controls were observed.
  A verification/login hint was reported. One third-party font stylesheet was blocked;
  the provider page remained inspectable. No login attempt was made.
- No paid/subscribed dataset was downloaded in the live smoke checks. No institutional
  subscription, personal account, CAPTCHA completion or campus authorization was assumed.
- Tests use fictional rows. The synthetic suite covers school login, catalogue search,
  date/code/field/format controls, frame and popup handling, delayed export, checksums,
  duplicate filename isolation, rejected empty/executable/HTML exports, stale references,
  login-field isolation, cross-provider profile isolation, custom framework controls and pagination.

## Campus acceptance — 2026-10-18

An authorized user subsequently requested testing from a subscribed campus network.
Both providers supported password-free institutional access, catalogue search, preview
and receipt of a small data export:

| Provider | Query | Verified result |
| --- | --- | --- |
| CSMAR | Company Profile, listing dates 2024-01-01 through 2024-01-31; stock code, English acronym, listing date | ZIP received; embedded XLSX contains 14 data rows and three header rows, three columns |
| CNRDS | Basic MACRO / 综合 / 行政区划; explicit condition 年份 等于 2024; 年份, 字段名称, 数值 | Archive received; ZIP integrity verified; embedded XLSX contains 11 data rows, all 2024, three columns |

The real workflows exposed zero-size catalogue link wrappers and CNRDS's exact Aliyun
export host. These are covered by the updated scope and control tests. CNRDS may deliver
a ZIP container with a `.7z` filename; both archive signatures are accepted for that suffix.
The received CNRDS file was recovered from the browser's temporary download after the
initial strict 7z signature check rejected this packaging. The corrected check passes
the recovered file and regression tests. A follow-up live download, described below,
verified automatic saving with the corrected packaging check.

The initial acceptance needed native browser interaction to dismiss a CSMAR tutorial
overlay and click the CNRDS final download icon. The follow-up below fixes and verifies
those two limitations.
Institution identities, profiles, signed links, screenshots and licensed exports remain
outside this repository. Specialty products, other institutions, quota behavior and VPN
routing were not verified. Export coverage was checked against the preview and selected
filters, not an independently produced manual export.

## Follow-up: MCP-only browser workflow — 2026-10-18

The connector now exposes unlabeled CSS/SVG controls and custom icons inside dialogs.
Focus containers no longer suppress their inner controls. Each control can include its
icon classes, dialog heading, and visible table-row or nearby-text context. Context omits
input values, hidden content and common token strings, with regression coverage.

A new local stdio MCP client and fresh private profiles repeated both small queries.
Every website interaction used `campus_*` tools, with no native clicks, coordinate
operations or general browser-control fallback:

- **CSMAR:** searched the catalogue, opened Stock Trading / Company Profile, closed the
  first-use Notice and unlabeled tutorial icon through MCP refs, selected January 2024
  listing dates, previewed 14 records and downloaded the prepared ZIP. The ZIP passed
  CRC checks; its XLSX contained 14 data rows after three header rows, three columns,
  and all listing dates fell within 2024-01-01 through 2024-01-31.
- **CNRDS:** used school login, selected MACRO / 综合 / 行政区划, added the explicit
  年份 等于 2024 condition and previewed 11 rows. The new icon metadata exposed the final
  download in 下载列表. Its row identified the matching table and this query's creation
  time; only that job was downloaded. The browser automatically saved the vendor's
  `.7z`-named ZIP with its receipt. CRC passed and the XLSX contained 11 data rows,
  three columns, with every year equal to 2024.

The local regression suite now has **51 passing tests**, including CSS-only tutorial
closure, correct-row icon downloads for both providers, and SVG controls without duplicate
button descendants. Ruff passed. This verifies the two tested workflows on one campus;
other institutions, specialty products, future interface changes and authentication
challenges remain outside that evidence.

The GitHub Linux matrix tests Python 3.11 and 3.13. Its initial run passed on Python 3.11
and caught an asynchronous popup-readiness race in the Python 3.13 test. The popup test
now awaits the browser's page-opening event before inspecting the new tab. Check the
[latest CI results](https://github.com/Thlookingatyou/csmar-cnrds-mcp/actions) for remote status.
Local execution required permission to launch Chromium outside the agent's process sandbox.

## Background default — 2026-10-20

Version 0.1.2 runs the connector headless by default. `CAMPUS_DATA_HEADLESS=0` opts into
a visible connector session; the standalone `login` command always opens a visible window
for personal authentication. Snapshots report `headless` and provide mode-appropriate
verification instructions. Existing private profiles and download paths remain unchanged.

- **55 local tests passed**, with Ruff passing. Browser fixtures now use the default
  setting rather than an explicit headless override, covering search, filters, tutorial
  controls, prepared downloads and file saving. Tests also cover the environment override
  and the visible-login exception.
- A fresh headless browser loaded both real public homepages: CSMAR exposed two frames
  and 95 controls; CNRDS exposed one frame and 13 controls. No browser window was opened.
  This was a public-page check; no new institutional export was attempted. The earlier
  campus export results above remain separate evidence.

## Test layers

- Unit tests: URL scope, authentication-field classification, redaction and access hints.
- Browser integration: real Chromium against synthetic pages at provider-shaped URLs.
  Synthetic login/search/filter/export flows include frames and popups. All data is invented.
- MCP protocol integration: local stdio server initialization, tool discovery and validation.
- Public-site smoke checks: real public homepages where reachable, without credentials.
- Campus acceptance: both basic-table exports repeated using only MCP browser tools,
  with file and coverage checks as described above. Other products remain unverified.

## Campus acceptance checklist

- CSMAR auto login or CNRDS school login uses the correct institution.
- The selected basic table is subscribed; restricted specialty/sample tables remain restricted.
- Search, table choice, dates, code filters, fields, units and format match a manual query.
- A small export matches a manual export's rows, date range and identifiers.
- Packaging, new-tab downloads, expiry and provider rate limits are handled without repeated jobs.
- VPN routing preserves recognized institutional egress; proxy/SSO domains are explicitly scoped.
- Session profiles, data exports and receipts stay outside the Git repository.
- Institution/vendor rules permit the intended automation and model disclosure.
