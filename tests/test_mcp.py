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
