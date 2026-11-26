from pathlib import Path
from urllib.parse import urlsplit

import pytest_asyncio

from campus_data_mcp.browser import BrowserBridge
from campus_data_mcp.config import Settings, allowed_url

CATALOGUE = (Path(__file__).parent / "fixtures" / "catalogue.html").read_text()
WIDGETS = (Path(__file__).parent / "fixtures" / "widgets.html").read_text()
CSV = b"stock_code,date,closing_price\n000001,2024-01-02,10.0\n"


@pytest_asyncio.fixture
async def bridge(tmp_path):
    item = BrowserBridge(Settings(home=tmp_path / "state", min_interval=0, timeout_ms=3000))
    original_route = item._route

    async def fixture_route(provider, route):
        url = route.request.url
        if not allowed_url(provider, url):
            return await original_route(provider, route)
        path = urlsplit(url).path
        if path == "/export":
            await route.fulfill(
                body=CSV,
                headers={
                    "content-type": "text/csv",
                    "content-disposition": 'attachment; filename="../../data.csv"',
                },
            )
        elif path == "/bad-export":
            await route.fulfill(
                body=b"fake executable",
                headers={
                    "content-type": "application/octet-stream",
                    "content-disposition": 'attachment; filename="unsafe.exe"',
                },
            )
        elif path == "/empty-export":
            await route.fulfill(
                body=b"",
                headers={
                    "content-type": "text/csv",
                    "content-disposition": 'attachment; filename="empty.csv"',
                },
            )
        elif path == "/html-export":
            await route.fulfill(
                body=b"<!doctype html><html><body>Please log in</body></html>",
                headers={
                    "content-type": "text/html",
                    "content-disposition": 'attachment; filename="data.csv"',
                },
            )
        elif path == "/popup":
            await route.fulfill(
                body='<a href="/export">Download prepared export</a>', content_type="text/html"
            )
        elif path == "/denied":
            await route.fulfill(
                body="<p>IP超出限定范围</p>", content_type="text/html; charset=utf-8"
            )
        elif path == "/waf":
            await route.fulfill(
                status=418,
                body="<p>安全拦截 HWWAF</p>",
                content_type="text/html; charset=utf-8",
            )
        elif path == "/out-of-scope-frame":
            await route.fulfill(
                body=(
                    "<p>Main provider shell</p>"
                    '<iframe src="https://sso.university.edu/private-fixture-path?ticket=private-fixture-ticket"></iframe>'
                ),
                content_type="text/html",
            )
        elif path == "/dialog":
            await route.fulfill(
                body=(
                    "<script>function ask(){if(confirm('Verification code: 481239. "
                    "https://db.resset.com/export?ticket=private-fixture-ticket'))"
                    "document.body.textContent='Confirmation accepted'}</script>"
                    '<button onclick="ask()">Trigger confirm</button>'
                ),
                content_type="text/html",
            )
        elif path == "/carsi":
            await route.fulfill(
                body=(
                    '<button onclick="this.outerHTML=&quot;Institutional sign-in selected&quot;">'
                    "CARSI平台登录</button>"
                ),
                content_type="text/html; charset=utf-8",
            )
        elif path == "/rate-limit-search":
            await route.fulfill(
                body=(
                    '<form onsubmit="event.preventDefault(); '
                    'fetch(&quot;/rate-limit-response&quot;);">'
                    '<input placeholder="Search catalogue"><button>Search</button></form>'
                ),
                content_type="text/html",
            )
        elif path == "/rate-limit-response":
            await route.fulfill(status=429, body="private-response-body")
        elif path == "/widgets":
            await route.fulfill(body=WIDGETS, content_type="text/html")
        elif path == "/many":
            await route.fulfill(
                body="".join(f"<button>Item {i}</button>" for i in range(300)),
                content_type="text/html",
            )
        elif provider == "csmar" and path == "/":
            await route.fulfill(
                body='<iframe src="/app" style="width:100%;height:900px"></iframe>',
                content_type="text/html",
            )
        else:
            await route.fulfill(body=CATALOGUE, content_type="text/html")

    item._route = fixture_route
    try:
        yield item
    finally:
        await item.shutdown()


def controls(snapshot):
    return [
        control
        for page in snapshot["pages"]
        for frame in page["frames"]
        for control in frame["controls"]
    ]


def ref(snapshot, label):
    return next(c["ref"] for c in controls(snapshot) if c["label"] == label)
