from dataclasses import dataclass
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP
from gmo_fx.api.active_orders import ActiveOrdersApi
from gmo_fx.api.order import OrderApi

from tools.active_orders import register_active_orders_tools
import tools.active_orders.tool as active_orders_tool


@dataclass
class FakeActiveOrder:
    root_order_id: int
    client_order_id: str | None
    order_id: int
    symbol: object
    side: object
    order_type: object
    execution_type: object
    settle_type: object
    size: int
    price: float
    status: object
    expiry: date
    timestamp: datetime


def construct_mcp(client_order_id_prefix: str | None = None):
    mcp = FastMCP("test")
    register_active_orders_tools(
        mcp,
        api_key="test-key",
        secret_key="test-secret",
        client_order_id_prefix=client_order_id_prefix,
    )
    return mcp


@pytest.fixture
def mcp():
    return construct_mcp()


class FakeActiveOrdersApi:
    return_active_orders: list[FakeActiveOrder] = []
    init_calls: list[dict] = []
    api_calls: list[dict] = []
    Symbol = ActiveOrdersApi.Symbol

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self, **kwargs):
        self.api_calls.append(kwargs)
        return SimpleNamespace(active_orders=self.return_active_orders)


def construct_fake_active_orders_api(
    active_orders: list[FakeActiveOrder] | None = None,
):
    if active_orders is None:
        active_orders = [
            FakeActiveOrder(
                root_order_id=1,
                client_order_id="c1",
                order_id=10,
                symbol=ActiveOrdersApi.Symbol.USD_JPY,
                side=OrderApi.Side.BUY,
                order_type=SimpleNamespace(value="NORMAL"),
                execution_type=OrderApi.ExecutionType.LIMIT,
                settle_type=SimpleNamespace(value="OPEN"),
                size=1,
                price=150.25,
                status=SimpleNamespace(value="ORDERED"),
                expiry=date(2026, 5, 31),
                timestamp=datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
            )
        ]
    FakeActiveOrdersApi.return_active_orders = active_orders
    return FakeActiveOrdersApi


class TestActiveOrdersTool:

    @pytest.fixture(autouse=True)
    def set_up_tear_down(self):
        yield
        FakeActiveOrdersApi.init_calls = []
        FakeActiveOrdersApi.api_calls = []
        FakeActiveOrdersApi.return_active_orders = []

    @pytest.mark.anyio
    async def test_registers_active_orders_api_tool_without_credentials_in_schema(
        self, mcp: FastMCP
    ):
        tool = await mcp.get_tool("active_orders_api")

        assert tool is not None
        assert tool.name == "active_orders_api"
        assert set(tool.parameters.get("required", [])) == set()
        assert "api_key" not in tool.parameters["properties"]
        assert "secret_key" not in tool.parameters["properties"]

    @pytest.mark.anyio
    async def test_active_orders_api_uses_registered_credentials_and_maps_response(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_active_orders_api()
        monkeypatch.setattr(active_orders_tool, "ActiveOrdersApi", FakeActiveOrdersApi)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "active_orders_api",
                {
                    "symbol": "USD_JPY",
                    "prev_id": 100,
                    "count": 20,
                },
            )

        assert FakeActiveOrdersApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert FakeActiveOrdersApi.api_calls == [
            {
                "symbol": ActiveOrdersApi.Symbol.USD_JPY,
                "prev_id": 100,
                "count": 20,
            }
        ]
        assert result.data == [
            {
                "root_order_id": 1,
                "client_order_id": "c1",
                "order_id": 10,
                "symbol": "USD_JPY",
                "side": "BUY",
                "order_type": "NORMAL",
                "execution_type": "LIMIT",
                "settle_type": "OPEN",
                "size": 1,
                "price": 150.25,
                "status": "ORDERED",
                "expiry": "2026-05-31",
                "timestamp": "2026-05-05T10:30:00+00:00",
            }
        ]

    @pytest.mark.anyio
    async def test_active_orders_api_filters_by_configured_client_order_id_prefix(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        construct_fake_active_orders_api(
            [
                FakeActiveOrder(
                    root_order_id=1,
                    client_order_id="GMOFX20260506010203",
                    order_id=10,
                    symbol=ActiveOrdersApi.Symbol.USD_JPY,
                    side=OrderApi.Side.BUY,
                    order_type=SimpleNamespace(value="NORMAL"),
                    execution_type=OrderApi.ExecutionType.LIMIT,
                    settle_type=SimpleNamespace(value="OPEN"),
                    size=1,
                    price=150.25,
                    status=SimpleNamespace(value="ORDERED"),
                    expiry=date(2026, 5, 31),
                    timestamp=datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
                ),
                FakeActiveOrder(
                    root_order_id=2,
                    client_order_id="OTHER20260506010203",
                    order_id=20,
                    symbol=ActiveOrdersApi.Symbol.EUR_JPY,
                    side=OrderApi.Side.SELL,
                    order_type=SimpleNamespace(value="NORMAL"),
                    execution_type=OrderApi.ExecutionType.STOP,
                    settle_type=SimpleNamespace(value="OPEN"),
                    size=2,
                    price=160.25,
                    status=SimpleNamespace(value="WAITING"),
                    expiry=date(2026, 6, 30),
                    timestamp=datetime(2026, 5, 5, 11, 30, tzinfo=timezone.utc),
                ),
                FakeActiveOrder(
                    root_order_id=3,
                    client_order_id=None,
                    order_id=30,
                    symbol=ActiveOrdersApi.Symbol.USD_JPY,
                    side=OrderApi.Side.BUY,
                    order_type=SimpleNamespace(value="NORMAL"),
                    execution_type=OrderApi.ExecutionType.LIMIT,
                    settle_type=SimpleNamespace(value="OPEN"),
                    size=3,
                    price=149.25,
                    status=SimpleNamespace(value="ORDERED"),
                    expiry=date(2026, 5, 31),
                    timestamp=datetime(2026, 5, 5, 12, 30, tzinfo=timezone.utc),
                ),
            ]
        )
        monkeypatch.setattr(active_orders_tool, "ActiveOrdersApi", FakeActiveOrdersApi)
        mcp_instance = construct_mcp(client_order_id_prefix="GMOFX")

        async with Client(mcp_instance) as client:
            result = await client.call_tool("active_orders_api", {})

        assert [order["client_order_id"] for order in result.data] == [
            "GMOFX20260506010203"
        ]
