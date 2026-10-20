from types import SimpleNamespace

from campus_data_mcp import cli
from campus_data_mcp.config import Settings


async def test_interactive_login_opens_visible_browser_despite_background_default(monkeypatch):
    launches = []

    class LoginBrowser:
        def __init__(self, settings):
            launches.append(settings)

        async def open(self, provider):
            assert provider == "cnrds"
            return {}

        async def shutdown(self):
            pass

    monkeypatch.setattr(cli, "BrowserBridge", LoginBrowser)
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    await cli._browser_command(SimpleNamespace(command="login", provider="cnrds"), Settings())
    assert len(launches) == 1
    assert launches[0].headless is False
