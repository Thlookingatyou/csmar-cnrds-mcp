from types import SimpleNamespace

import pytest

from campus_data_mcp import cli
from campus_data_mcp.config import Settings


@pytest.mark.parametrize("provider", ["cnrds", "resset"])
async def test_interactive_login_opens_visible_browser_despite_background_default(
    monkeypatch, provider
):
    launches = []

    class LoginBrowser:
        def __init__(self, settings):
            launches.append(settings)

        async def open(self, target):
            assert target == provider
            return {}

        async def shutdown(self):
            pass

    monkeypatch.setattr(cli, "BrowserBridge", LoginBrowser)
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    await cli._browser_command(SimpleNamespace(command="login", provider=provider), Settings())
    assert len(launches) == 1
    assert launches[0].headless is False
