# Validation

This is an experimental browser connector. Do not equate synthetic integration tests with
an end-to-end institutional download.

## Results — 2026-10-18

- **43 tests passed** on macOS arm64, Python 3.13.5, MCP SDK 1.30.0, Playwright 1.64.0
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

GitHub's Linux/Python-version matrix is configured but has not yet run remotely. Local
execution required permission to launch Chromium outside the agent's process sandbox.

## Test layers

- Unit tests: URL scope, authentication-field classification, redaction and access hints.
- Browser integration: real Chromium against synthetic pages at provider-shaped URLs.
  Synthetic login/search/filter/export flows include frames and popups. All data is invented.
- MCP protocol integration: local stdio server initialization, tool discovery and validation.
- Public-site smoke checks: real public homepages where reachable, without credentials.
- Campus acceptance: not yet performed; requires a subscribed institution's network and
  permission to access/download the selected products.

## Campus acceptance checklist

- CSMAR auto login or CNRDS school login uses the correct institution.
- The selected basic table is subscribed; restricted specialty/sample tables remain restricted.
- Search, table choice, dates, code filters, fields, units and format match a manual query.
- A small export matches a manual export's rows, date range and identifiers.
- Packaging, new-tab downloads, expiry and provider rate limits are handled without repeated jobs.
- VPN routing preserves recognized institutional egress; proxy/SSO domains are explicitly scoped.
- Session profiles, data exports and receipts stay outside the Git repository.
- Institution/vendor rules permit the intended automation and model disclosure.
