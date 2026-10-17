# Validation

This is an experimental browser connector. Do not equate synthetic integration tests with
an end-to-end institutional download.

## Results — 2026-10-18

- **46 tests passed** on macOS arm64, Python 3.13.5, MCP SDK 1.30.0, Playwright 1.64.0
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
the recovered file and regression tests; the full live download was not repeated afterward.

Native browser interaction was needed to dismiss a CSMAR tutorial overlay and click the
CNRDS final download icon, which the current MCP snapshot did not expose. Thus these
results demonstrate campus feasibility, not a completely unattended MCP-only workflow.
Institution identities, profiles, signed links, screenshots and licensed exports remain
outside this repository. Specialty products, other institutions, quota behavior and VPN
routing were not verified. Export coverage was checked against the preview and selected
filters, not an independently produced manual export.

The GitHub Linux matrix tests Python 3.11 and 3.13. Its initial run passed on Python 3.11
and caught an asynchronous popup-readiness race in the Python 3.13 test. The popup test
now awaits the browser's page-opening event before inspecting the new tab. Check the
[latest CI results](https://github.com/Thlookingatyou/csmar-cnrds-mcp/actions) for remote status.
Local execution required permission to launch Chromium outside the agent's process sandbox.

## Test layers

- Unit tests: URL scope, authentication-field classification, redaction and access hints.
- Browser integration: real Chromium against synthetic pages at provider-shaped URLs.
  Synthetic login/search/filter/export flows include frames and popups. All data is invented.
- MCP protocol integration: local stdio server initialization, tool discovery and validation.
- Public-site smoke checks: real public homepages where reachable, without credentials.
- Campus acceptance: two basic-table exports verified as described above, with native
  interaction required for two controls. This does not establish access to other products.

## Campus acceptance checklist

- CSMAR auto login or CNRDS school login uses the correct institution.
- The selected basic table is subscribed; restricted specialty/sample tables remain restricted.
- Search, table choice, dates, code filters, fields, units and format match a manual query.
- A small export matches a manual export's rows, date range and identifiers.
- Packaging, new-tab downloads, expiry and provider rate limits are handled without repeated jobs.
- VPN routing preserves recognized institutional egress; proxy/SSO domains are explicitly scoped.
- Session profiles, data exports and receipts stay outside the Git repository.
- Institution/vendor rules permit the intended automation and model disclosure.
