from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import replace

from playwright.sync_api import sync_playwright

from .browser import BrowserBridge
from .config import PROVIDERS, CampusError, Settings


async def _browser_command(args, settings):
    bridge = BrowserBridge(
        replace(settings, headless=False) if args.command == "login" else settings
    )
    try:
        result = await bridge.open(args.provider)
        if args.command == "login":
            print("Use the opened browser to complete school login or manual verification.")
            await asyncio.to_thread(input, "Press Enter here when you have finished: ")
            print("Session saved locally. You can now start the MCP server.")
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        await bridge.shutdown()


def main():
    parser = argparse.ArgumentParser(description="Local CSMAR/CNRDS institutional browser bridge")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("serve", help="Run the MCP server over local stdio")
    sub.add_parser("doctor", help="Check browser installation and local configuration")
    for command in ("login", "inspect"):
        item = sub.add_parser(command)
        item.add_argument("provider", choices=tuple(PROVIDERS))
    args = parser.parse_args()
    try:
        settings = Settings.from_env()
        if args.command == "serve":
            from .server import build_server

            build_server(BrowserBridge(settings)).run(transport="stdio")
        elif args.command == "doctor":
            from pathlib import Path

            with sync_playwright() as pw:
                installed = Path(pw.chromium.executable_path).exists()
            print(
                json.dumps(
                    {
                        "browser_installed": installed,
                        "providers": list(PROVIDERS),
                        "data_home": str(settings.home),
                        "headless": settings.headless,
                        "extra_hosts": list(settings.extra_hosts),
                        "timeouts": {
                            "timeout_ms": settings.timeout_ms,
                            "operation_timeout_s": settings.operation_timeout_s,
                            "lock_timeout_s": settings.lock_timeout_s,
                            "inspection_timeout_s": settings.inspection_timeout_s,
                            "frame_timeout_s": settings.frame_timeout_s,
                        },
                        "transport": "local stdio",
                        "institutional_access": "not tested; open a provider on campus",
                    },
                    indent=2,
                )
            )
            if not installed:
                sys.exit(1)
        else:
            asyncio.run(_browser_command(args, settings))
    except CampusError as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
