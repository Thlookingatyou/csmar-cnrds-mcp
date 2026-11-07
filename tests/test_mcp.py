import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_stdio_protocol_discovery_and_input_validation(tmp_path):
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "campus_data_mcp.cli", "serve"],
        env={"CAMPUS_DATA_HOME": str(tmp_path / "mcp-state")},
    )
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            response = await session.list_tools()
            names = {tool.name for tool in response.tools}
            assert len(names) == 9
            assert {"campus_search", "campus_export", "campus_school_login"} <= names
            result = await session.call_tool("campus_inspect", {"provider": "cnrds"})
            assert "Start this provider" in json.dumps(result.model_dump())
            invalid = await session.call_tool("campus_open", {"provider": "evil"})
            assert invalid.isError


async def test_stalled_operation_returns_diagnostic_over_stdio(tmp_path):
    runner = tmp_path / "stalled_server.py"
    runner.write_text("""
import asyncio
from campus_data_mcp.browser import BrowserBridge
from campus_data_mcp.config import Settings
from campus_data_mcp.server import build_server
class StalledBridge(BrowserBridge):
    async def open(self, provider, url=None):
        async with self.operation():
            await asyncio.Event().wait()
build_server(StalledBridge(Settings(operation_timeout_s=0.05, min_interval=0))).run()
""")
    params = StdioServerParameters(command=sys.executable, args=[str(runner)])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            result = await asyncio.wait_for(
                session.call_tool("campus_open", {"provider": "cnrds"}), 3
            )
            assert not result.isError
            data = result.structuredContent or json.loads(result.content[0].text)
            assert data["code"] == "operation_timeout"
            assert data["request_id"]
            assert data["elapsed_ms"] < 2000
            # A timed-out operation must leave the transport available for the next call.
            result = await session.call_tool("campus_downloads", {"provider": "cnrds"})
            data = result.structuredContent or json.loads(result.content[0].text)
            assert data["code"] == "connector_error"
