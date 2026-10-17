# Feasibility assessment

Assessment date: 2026-10-18. “CRNDS” is interpreted as CNRDS.

## Conclusion

A local agent connector is technically feasible **when the same local browser already
has institutional access**. Password-free institutional access and a password-based
personal SDK are different authentication channels. An agent can operate the former
through the normal website without learning a database or university password.

The correct boundary is the institution's existing entitlement. Neither campus IP nor
a successful school login guarantees that every table, year, field, or specialty product
is included. The provider remains the authority on permissions.

## Evidence

1. [CSMAR institutional access instructions, Hubei University of Economics](https://tsg.hbue.edu.cn/79/55/c1502a227669/page.htm)
   describe automatic institutional login within the school's IP range and a separate
   personal-registration route. This is evidence of an institutional browser route;
   institutional coverage varies. No account credentials from that page are included here.
2. [CNRDS access instructions, Shanghai University of International Business and Economics](https://lib.suibe.edu.cn/2023/0606/c109a11444/page.psp)
   distinguish campus-IP access, basic databases under school login, and personal accounts
   for specialty databases. Similar current instructions appear at
   [Dongguan Polytechnic](https://lib.dgpt.edu.cn/info/1048/2188.htm).
3. The vendor's [CNRDS login page](https://www.cnrds.com/Home/Login) contains a school-login
   control and client-side `schoolLogin()` handler in its public HTML. Availability is
   conditional: the school button is not necessarily visible on an unrecognized IP.
   It also exposes personal/SMS login and a data-use agreement. This project calls the
   visible UI, not that hidden handler or an invented authentication endpoint.
4. [CSMAR's live homepage](https://data.csmar.com/) embeds its application in an iframe.
   Inspecting only the top-level DOM would miss its search interface; this bridge reads
   allowed provider frames and popups as well.
5. [Playwright's browser-context API](https://playwright.dev/python/docs/api/class-browsercontext)
   supports isolated browser contexts, popups and persistent local profiles. Its
   [download API](https://playwright.dev/python/docs/downloads) supports retaining exports
   delivered by a normal browser download.

These observations establish technical feasibility, not institutional permission for
automated access or disclosure to a particular AI provider. CNRDS's current agreement
restricts data use and transfer; the user's actual institution/vendor agreement must
govern deployment. The project avoids assuming that an ordinary browsing subscription
automatically includes API use, unrestricted automation, or third-party model disclosure.

## Existing work

There is already a password-free CSMAR MCP implementation:
[xuan-wei/csmar-web-mcp](https://github.com/xuan-wei/csmar-web-mcp). It documents institutional-IP
web authentication and direct HTTP/WebSocket querying. Its existence is useful independent
evidence that the personal-account SDK is not the only technical route. Its support claims
were not independently verified on a subscribed IP here.

[advancehs/cnrds-data-downloader](https://github.com/advancehs/cnrds-data-downloader) documents
a CNRDS download workflow with account/password setup. That requirement in one implementation
does not imply all institutional access must use a personal password.

This project contains original implementation code; it does not vendor either repository,
copy their private endpoint implementations, or redistribute a vendor SDK or datasets.

## Why this implementation uses a browser

A persistent browser can use the site's own campus login, cookies, CSRF handling, export
packaging, and future verification screens. It avoids fabricating an undocumented CNRDS
API contract. Agents inspect the current controls rather than relying on table IDs or
selectors assumed from another university's session.

The tradeoff is UI sensitivity. Search boxes can be ambiguous, controls can change, export
jobs can take time, and custom widgets require several interactions. This MVP exposes
those intermediate states instead of claiming a universal one-call query API. It returns
ephemeral references, supports frames and popups, and records export provenance.

## Deployment choices

| Deployment | Expected behavior |
| --- | --- |
| Local laptop on a subscribed campus network | Best initial target; provider decides access. |
| Local laptop on institution-approved VPN | Can work if database requests actually use the campus egress IP. |
| University-managed workstation/server with permission | Can work; requires local browser and institution approval of automation. |
| GitHub-hosted runner or ordinary cloud server | Usually lacks campus IP; not an institutional-access solution. |
| Library proxy that rewrites URLs | May require exact trusted-host configuration and site-specific work. |
| Personal/SMS/SSO access | Human completes login in the dedicated browser; no password is passed to the agent. |

## Remaining acceptance work

On a subscribing campus, verify both providers' visible login route, one subscribed basic
table, one non-subscribed/specialty table, preview versus full export, asynchronous packaging,
and any provider-specific limits. Compare one small export with the same manual website
query, including row counts, date coverage, fields, units and file type. Confirm the library
permits the planned automation/model use before operating against production data.

Future typed query adapters should follow observed, authorized sessions or vendor-approved
APIs. They should not claim support based only on mocked responses or public catalogues.
