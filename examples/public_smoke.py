"""Read public pages only. No login attempts, credentials, searches or data exports."""

import asyncio
import json
import tempfile
from pathlib import Path

from campus_data_mcp.browser import BrowserBridge
from campus_data_mcp.config import CampusError, Settings


async def main():
    with tempfile.TemporaryDirectory(prefix="campus-data-public-smoke-") as folder:
        bridge = BrowserBridge(Settings(home=Path(folder), headless=True, timeout_ms=20000))
        try:
            for provider in ("csmar", "cnrds"):
                try:
                    snapshot = await bridge.open(provider)
                    # Public single-page applications need time to render after DOMContentLoaded.
                    for _ in range(5):
                        await asyncio.sleep(2)
                        snapshot = await bridge.inspect(provider)
                        frames = [f for p in snapshot["pages"] for f in p["frames"]]
                        if any(f["controls"] for f in frames):
                            break
                    frames = [f for p in snapshot["pages"] for f in p["frames"]]
                    print(
                        json.dumps(
                            {
                                "provider": provider,
                                "pages": len(snapshot["pages"]),
                                "frames": len(frames),
                                "visible_controls": sum(len(f["controls"]) for f in frames),
                                "access_hints": [f["access"]["hint"] for f in frames],
                                "blocked_urls": snapshot["blocked_urls"],
                                "institutional_export_verified": False,
                            },
                            ensure_ascii=False,
                        )
                    )
                except CampusError as error:
                    print(json.dumps({"provider": provider, "error": str(error)}))
        finally:
            await bridge.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
