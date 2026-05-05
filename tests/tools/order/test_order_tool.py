from dataclasses import dataclass
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP
from gmo_fx.api.order import OrderApi

from tools.order import register_order_tools
import tools.order.tool as order_tool


@dataclass
class FakeOrder:
    root_order_id: str
    client_order_id: str | None
    order_id: str
    symbol: object
    side: object
    order_type: object
    execution_type: object
    settle_type: object
    size: int
    price: float | None
    status: object
    cancel_type: object | None
    expiry: date | None
    timestamp: datetime


def create_test_server():
    mcp = FastMCP("test")
    register_order_tools(mcp, api_key="test-key", secret_key="test-secret")
    return mcp


@pytest.mark.anyio
async def test_registers_order_api_tool_without_credentials_in_schema():
    mcp = create_test_server()
    tool = await mcp.get_tool("order_api")

    assert tool is not None
    assert tool.name == "order_api"
    assert set(tool.parameters["required"]) == {
        "symbol",
        "side",
        "size",
        "execution_type",
    }
    assert "api_key" not in tool.parameters["properties"]
    assert "secret_key" not in tool.parameters["properties"]


@pytest.mark.anyio
async def test_order_api_uses_registered_credentials_and_maps_response(monkeypatch):
    init_calls = []
    api_calls = []

    class FakeOrderApi:
        Symbol = OrderApi.Symbol
        Side = OrderApi.Side
        ExecutionType = OrderApi.ExecutionType

        def __init__(self, *, api_key, secret_key):
            init_calls.append({"api_key": api_key, "secret_key": secret_key})

        def __call__(self, **kwargs):
            api_calls.append(kwargs)
            return SimpleNamespace(
                orders=[
                    FakeOrder(
                        root_order_id="r1",
                        client_order_id="c1",
                        order_id="o1",
                        symbol=OrderApi.Symbol.USD_JPY,
                        side=OrderApi.Side.BUY,
                        order_type=SimpleNamespace(value="NORMAL"),
                        execution_type=OrderApi.ExecutionType.LIMIT,
                        settle_type=SimpleNamespace(value="OPEN"),
                        size=1,
                        price=150.25,
                        status=SimpleNamespace(value="ORDERED"),
                        cancel_type=None,
                        expiry=date(2026, 5, 31),
                        timestamp=datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
                    )
                ]
            )

    monkeypatch.setattr(order_tool, "OrderApi", FakeOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "order_api",
            {
                "symbol": "USD_JPY",
                "side": "BUY",
                "size": 1,
                "execution_type": "LIMIT",
                "client_order_id": "c1",
                "limit_price": 150.25,
            },
        )

    assert init_calls == [{"api_key": "test-key", "secret_key": "test-secret"}]
    assert api_calls == [
        {
            "symbol": OrderApi.Symbol.USD_JPY,
            "side": OrderApi.Side.BUY,
            "size": 1,
            "execution_type": OrderApi.ExecutionType.LIMIT,
            "client_order_id": "c1",
            "limit_price": 150.25,
            "stop_price": None,
            "lower_bound": None,
            "upper_bound": None,
        }
    ]
    assert result.data == [
        {
            "root_order_id": "r1",
            "client_order_id": "c1",
            "order_id": "o1",
            "symbol": "USD_JPY",
            "side": "BUY",
            "order_type": "NORMAL",
            "execution_type": "LIMIT",
            "settle_type": "OPEN",
            "size": 1,
            "price": 150.25,
            "status": "ORDERED",
            "cancel_type": None,
            "expiry": "2026-05-31",
            "timestamp": "2026-05-05T10:30:00+00:00",
        }
    ]
