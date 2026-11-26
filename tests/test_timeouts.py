import asyncio
from dataclasses import replace
from pathlib import Path

import pytest
from playwright.async_api import Frame

from campus_data_mcp.browser import BrowserBridge
from campus_data_mcp.config import CampusError, Settings
from campus_data_mcp.server import build_server
from campus_data_mcp.snapshot import SNAPSHOT_JS

from .conftest import CSV, controls, ref


async def test_busy_operation_fails_fast_but_receipts_remain_available(bridge):
    await bridge.open("cnrds")
    bridge.settings = replace(bridge.settings, lock_timeout_s=0.05)
    async with bridge.operation():
        with pytest.raises(CampusError) as result:
            await bridge.inspect("cnrds")
        assert result.value.code == "connector_busy"
        assert (await asyncio.wait_for(bridge.downloads("cnrds"), 0.5))["downloads"] == []
    assert controls(await bridge.inspect("cnrds"))


async def test_operation_deadline_and_cancellation_release_lock():
    bridge = BrowserBridge(Settings(operation_timeout_s=0.05, min_interval=0))
    with pytest.raises(CampusError) as result:
        async with bridge.operation():
            await asyncio.Event().wait()
    assert result.value.code == "operation_timeout"
    assert not bridge._lock.locked()

    entered = asyncio.Event()

    async def pending():
        async with bridge.operation():
            entered.set()
            await asyncio.Event().wait()

    task = asyncio.create_task(pending())
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert not bridge._lock.locked()


async def test_unresponsive_frame_returns_warning_and_next_inspection_recovers(bridge, monkeypatch):
    await bridge.open("cnrds")
    bridge.settings = replace(bridge.settings, frame_timeout_s=0.05)
    original = Frame.evaluate

    async def stuck(self, expression, arg=None):
        if expression == SNAPSHOT_JS:
            await asyncio.Event().wait()
        return await original(self, expression, arg)

    with monkeypatch.context() as patch:
        patch.setattr(Frame, "evaluate", stuck)
        snapshot = await asyncio.wait_for(bridge.inspect("cnrds"), 0.5)
    assert not snapshot["inspection_complete"]
    assert snapshot["warnings"]
    assert not bridge.sessions["cnrds"].refs
    assert controls(await bridge.inspect("cnrds"))


async def test_navigation_does_not_wait_for_stalled_image(bridge):
    pending = asyncio.Event()
    reached = asyncio.Event()

    async def delayed(route):
        reached.set()
        await pending.wait()
        await route.fulfill(body=b"", content_type="image/png")

    context = (await bridge._launch("cnrds")).context
    await context.route("**/slow-image", delayed)
    await context.route(
        "**/loading",
        lambda route: route.fulfill(
            body='<button>Ready before images</button><img src="/slow-image">',
            content_type="text/html",
        ),
    )
    try:
        snapshot = await asyncio.wait_for(bridge.open("cnrds", "https://www.cnrds.com/loading"), 2)
        await asyncio.wait_for(reached.wait(), 1)
        assert ref(snapshot, "Ready before images")
    finally:
        pending.set()


async def test_export_poll_deadline_does_not_duplicate_or_cancel_download(bridge, monkeypatch):
    await bridge.open("cnrds")
    snapshot = await bridge.search("cnrds", "daily")

    async def stuck(*args):
        await asyncio.Event().wait()

    bridge.settings = replace(bridge.settings, operation_timeout_s=0.3)
    with monkeypatch.context() as patch:
        patch.setattr(bridge, "_wait_downloads", stuck)
        with pytest.raises(CampusError) as error:
            await bridge.export("cnrds", ref(snapshot, "Export CSV"), "One requested export", 3)
    assert error.value.code == "operation_timeout"
    receipts = await bridge.downloads("cnrds", 3)
    assert len(receipts["downloads"]) == 1
    assert receipts["downloads"][0]["status"] == "saved"
    assert Path(receipts["downloads"][0]["path"]).read_bytes() == CSV
    assert not bridge._lock.locked()


async def test_closed_browser_is_explicit_and_open_can_recover(bridge):
    await bridge.open("cnrds")
    await bridge.sessions["cnrds"].context.close()
    with pytest.raises(CampusError) as error:
        await bridge.inspect("cnrds")
    assert error.value.code == "browser_closed"
    assert controls(await bridge.open("cnrds"))


async def test_mcp_deadline_is_a_structured_reply_not_transport_failure(monkeypatch):
    bridge = BrowserBridge(Settings(operation_timeout_s=0.05, min_interval=0))

    async def stuck(*args, **kwargs):
        async with bridge.operation():
            await asyncio.Event().wait()

    monkeypatch.setattr(bridge, "open", stuck)
    server = build_server(bridge)
    result = await asyncio.wait_for(server.call_tool("campus_open", {"provider": "cnrds"}), 1)
    content = str(result)
    assert "operation_timeout" in content
    assert "request_id" in content
    assert "elapsed_ms" in content


async def test_large_pointer_catalogue_is_paginated_with_row_context(bridge):
    context = (await bridge._launch("cnrds")).context
    body = (
        "<table>"
        + "".join(
            f'<tr><td>Job {i}</td><td><i style="cursor:pointer">Download</i></td></tr>'
            for i in range(1500)
        )
        + "</table>"
    )
    await context.route(
        "**/large", lambda route: route.fulfill(body=body, content_type="text/html")
    )
    snapshot = await bridge.open("cnrds", "https://www.cnrds.com/large")
    assert snapshot["inspection_complete"], snapshot["warnings"]
    frame = snapshot["pages"][0]["frames"][0]
    assert frame["controls_total"] == 1500
    assert frame["controls_truncated"]
    snapshot = await bridge.inspect("cnrds", control_offset=1250)
    assert "Job 1499" in controls(snapshot)[-1]["context"]


async def test_unexpected_exception_returns_safe_diagnostic(monkeypatch):
    bridge = BrowserBridge()

    async def broken(*args, **kwargs):
        raise RuntimeError("token=private-error-content")

    monkeypatch.setattr(bridge, "open", broken)
    result = await build_server(bridge).call_tool("campus_open", {"provider": "csmar"})
    assert "internal_error" in str(result)
    assert "request_id" in str(result)
    assert "private-error-content" not in str(result)


async def test_open_waits_briefly_for_initial_spa_render(bridge):
    context = (await bridge._launch("cnrds")).context
    await context.route(
        "**/spa",
        lambda route: route.fulfill(
            body=(
                "<body><script>setTimeout(() => {document.body.innerHTML = "
                "'<button>Rendered</button>'}, 100)</script>"
            ),
            content_type="text/html",
        ),
    )
    snapshot = await bridge.open("cnrds", "https://www.cnrds.com/spa")
    assert snapshot["page_state"] == "content_available"
    assert ref(snapshot, "Rendered")


async def test_open_waits_past_spa_loading_placeholder(bridge):
    context = (await bridge._launch("cnrds")).context
    await context.route(
        "**/spa-loading",
        lambda route: route.fulfill(
            body=(
                "<body><p>加载中...</p><script>setTimeout(() => {document.body.innerHTML = "
                "'<button>Catalogue loaded</button>'}, 150)</script></body>"
            ),
            content_type="text/html; charset=utf-8",
        ),
    )
    snapshot = await bridge.open("cnrds", "https://www.cnrds.com/spa-loading")
    assert snapshot["page_state"] == "content_available"
    assert ref(snapshot, "Catalogue loaded")


async def test_navigation_failure_reports_safe_network_hint_and_blocked_hosts(bridge, monkeypatch):
    session = await bridge._launch("cnrds")
    session.blocked.append("https://idp.university.edu/sso")
    page = list(session.pages.values())[-1]

    async def fail_goto(*args, **kwargs):
        raise RuntimeError(
            "Page.goto: net::ERR_BLOCKED_BY_CLIENT at https://idp.university.edu/sso?token=secret"
        )

    monkeypatch.setattr(page, "goto", fail_goto)
    with pytest.raises(CampusError) as error:
        await bridge.open("cnrds")
    assert error.value.code == "navigation_failed"
    assert "net::ERR_BLOCKED_BY_CLIENT" in str(error.value)
    assert "idp.university.edu" in str(error.value)
    assert "secret" not in str(error.value)
