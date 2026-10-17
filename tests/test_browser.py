import hashlib
import json
from pathlib import Path

import pytest

from campus_data_mcp.config import CampusError

from .conftest import CSV, controls, ref


@pytest.mark.parametrize("provider", ["csmar", "cnrds"])
async def test_school_login_search_filters_and_export(bridge, provider):
    snapshot = await bridge.open(provider)
    assert controls(snapshot)
    snapshot = await bridge.school_login(provider)
    assert "Synthetic University" in json.dumps(snapshot)
    snapshot = await bridge.search(provider, "daily trading")
    assert "Daily trading" in json.dumps(snapshot)
    snapshot = await bridge.act(provider, ref(snapshot, "Start date"), "fill", "2024-01-01")
    snapshot = await bridge.act(provider, ref(snapshot, "End date"), "fill", "2024-01-31")
    snapshot = await bridge.act(provider, ref(snapshot, "Stock code"), "fill", "000001")
    snapshot = await bridge.act(provider, ref(snapshot, "Closing price"), "check", "true")
    format_ref = next(c["ref"] for c in controls(snapshot) if c["tag"] == "select")
    snapshot = await bridge.act(provider, format_ref, "select", "csv")
    exported = await bridge.export(
        provider,
        ref(snapshot, "Export CSV"),
        "Synthetic daily table; 000001; January 2024; price; CSV",
        3,
    )
    receipt = exported["downloads"][0]
    assert receipt["status"] == "saved"
    path = Path(receipt["path"])
    assert path.read_bytes() == CSV
    assert path.parent == bridge.settings.home / "downloads" / provider
    assert receipt["sha256"] == hashlib.sha256(CSV).hexdigest()
    assert path.stat().st_mode & 0o777 == 0o600
    assert "fixture-signed-url" not in json.dumps(receipt)
    assert json.loads(Path(receipt["manifest_path"]).read_text())["query_note"]
    await bridge.close(provider)
    assert path.exists()


async def test_snapshots_omit_hidden_fields_scripts_and_input_values(bridge):
    snapshot = await bridge.open("cnrds")
    text = json.dumps(snapshot)
    for secret in (
        "fixture-user",
        "fixture-password",
        "fixture-hidden-token",
        "fixture-secret-notes",
        "fixture-script-token",
    ):
        assert secret not in text
    assert any(c["manual_only"] for c in controls(snapshot) if c["type"] == "password")


async def test_agent_cannot_fill_authentication_fields(bridge):
    snapshot = await bridge.open("cnrds")
    username = next(c["ref"] for c in controls(snapshot) if c["name"].strip() == "username")
    with pytest.raises(CampusError, match="manual-only"):
        await bridge.act("cnrds", username, "fill", "should-not-fill")


async def test_old_references_are_rejected(bridge):
    snapshot = await bridge.open("cnrds")
    old = ref(snapshot, "学校登录")
    await bridge.inspect("cnrds")
    with pytest.raises(CampusError, match="expired"):
        await bridge.act("cnrds", old, "click")


async def test_redirect_or_link_to_another_domain_is_blocked(bridge):
    snapshot = await bridge.open("cnrds")
    try:
        await bridge.act("cnrds", ref(snapshot, "External link"), "click")
    except Exception:
        pass  # Chromium may surface its network-error page for an aborted navigation.
    assert any("evil.invalid" in u for u in bridge.sessions["cnrds"].blocked)
    with pytest.raises(CampusError, match="HTTPS"):
        await bridge.open("cnrds", "https://evil.invalid/")


async def test_popup_download_is_captured(bridge):
    await bridge.open("cnrds")
    snapshot = await bridge.search("cnrds", "daily")
    await bridge.act("cnrds", ref(snapshot, "Open job page"), "click")
    session = bridge.sessions["cnrds"]
    popup = list(session.pages.values())[-1]
    await popup.wait_for_load_state("domcontentloaded")
    snapshot = await bridge.inspect("cnrds")
    assert len(snapshot["pages"]) == 2
    result = await bridge.export(
        "cnrds", ref(snapshot, "Download prepared export"), "Synthetic prepared export", 3
    )
    assert result["downloads"][0]["status"] == "saved"


@pytest.mark.parametrize(
    "label", ["Export executable", "Export empty", "Export expired-session HTML"]
)
async def test_rejected_downloads_leave_no_data_file(bridge, label):
    await bridge.open("cnrds")
    snapshot = await bridge.search("cnrds", "daily")
    result = await bridge.export("cnrds", ref(snapshot, label), "Synthetic bad export", 3)
    assert result["downloads"][0]["status"] == "failed"
    assert not list((bridge.settings.home / "downloads").glob("**/*.csv"))


async def test_session_profiles_are_separate_and_persist(bridge):
    await bridge.open("cnrds")
    await bridge.school_login("cnrds")
    await bridge.close("cnrds")
    await bridge.open("cnrds")
    cnrds_page = list(bridge.sessions["cnrds"].pages.values())[-1]
    assert await cnrds_page.evaluate("localStorage.getItem('fixture-session')")
    await bridge.open("csmar")
    csmar_page = list(bridge.sessions["csmar"].pages.values())[-1]
    assert await csmar_page.evaluate("localStorage.getItem('fixture-session')") is None


async def test_denied_ip_is_not_reported_as_authorized(bridge):
    snapshot = await bridge.open("cnrds", "https://www.cnrds.com/denied")
    access = snapshot["pages"][0]["frames"][0]["access"]
    assert access["hint"] == "ip_not_authorized"
    assert access["entitlement"] == "unverified"
    result = await bridge.school_login("cnrds")
    assert result["action"] == "not_clicked"


async def test_control_pagination_can_reach_large_field_lists(bridge):
    snapshot = await bridge.open("cnrds", "https://www.cnrds.com/many")
    frame = snapshot["pages"][0]["frames"][0]
    assert frame["controls_total"] == 300
    assert frame["controls_truncated"]
    snapshot = await bridge.inspect("cnrds", control_offset=250)
    assert len(controls(snapshot)) == 50
    assert ref(snapshot, "Item 299")


async def test_changed_control_cannot_become_a_password_field(bridge):
    snapshot = await bridge.open("cnrds")
    control = next(c for c in controls(snapshot) if "搜索" in c["label"])
    item = bridge.sessions["cnrds"].refs[control["ref"]]
    await item.locator.evaluate("el => el.type = 'password'")
    with pytest.raises(CampusError, match="manual-only"):
        await bridge.act("cnrds", control["ref"], "fill", "must-not-fill")


async def test_same_filenames_do_not_overwrite_previous_exports(bridge):
    await bridge.open("cnrds")
    snapshot = await bridge.search("cnrds", "daily")
    first = await bridge.export("cnrds", ref(snapshot, "Export CSV"), "First synthetic query", 3)
    second = await bridge.export(
        "cnrds", ref(first["snapshot"], "Export CSV"), "Second synthetic query", 3
    )
    assert first["downloads"][0]["path"] != second["downloads"][0]["path"]
    assert len(list((bridge.settings.home / "downloads" / "cnrds").glob("*.csv"))) == 2


async def test_custom_pointer_widget_with_framework_listener(bridge):
    snapshot = await bridge.open("cnrds")
    snapshot = await bridge.act("cnrds", ref(snapshot, "Custom catalogue tab"), "click")
    assert ref(snapshot, "Custom tab activated")
