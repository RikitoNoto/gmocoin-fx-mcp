from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP

from tools.ifdoco_order import register_ifdoco_order_tools
import tools.ifdoco_order.tool as ifdoco_tool


def create_test_server():
    mcp = FastMCP("test")
    register_ifdoco_order_tools(mcp, api_key="test-key", secret_key="test-secret")
    return mcp


@pytest.mark.anyio
async def test_registers_change_oco_order_api_tool_without_credentials_in_schema():
    mcp = create_test_server()
    tool = await mcp.get_tool("change_oco_order_api")

    assert tool is not None
    assert tool.name == "change_oco_order_api"
    assert "required" not in tool.parameters or tool.parameters["required"] == []
    assert "api_key" not in tool.parameters["properties"]
    assert "secret_key" not in tool.parameters["properties"]


@pytest.mark.anyio
async def test_change_oco_order_api_uses_registered_credentials_and_maps_response(monkeypatch):
    init_calls = []
    api_calls = []

    class FakeChangeOcoOrderApi:
        def __init__(self, *, api_key, secret_key):
            init_calls.append({"api_key": api_key, "secret_key": secret_key})

        def __call__(self, **kwargs):
            api_calls.append(kwargs)
            return SimpleNamespace(root_order_id=123456)

    monkeypatch.setattr(ifdoco_tool, "ChangeOcoOrderApi", FakeChangeOcoOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "change_oco_order_api",
            {
                "root_order_id": 123456,
                "limit_price": 151.25,
                "stop_price": 149.75,
            },
        )

    assert init_calls == [{"api_key": "test-key", "secret_key": "test-secret"}]
    assert api_calls == [
        {
            "root_order_id": 123456,
            "client_order_id": None,
            "limit_price": 151.25,
            "stop_price": 149.75,
        }
    ]
    assert result.data == {"root_order_id": "123456"}
