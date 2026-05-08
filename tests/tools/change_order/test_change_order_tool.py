from dataclasses import dataclass
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP
from gmo_fx.api.change_order import Order
from gmo_fx.common import SettleType, Side, Symbol

from tools.change_order import register_change_order_tools
import tools.change_order.tool as change_order_tool


@dataclass
class FakeChangeOrder:
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


def construct_mcp():
    mcp = FastMCP("test")
    register_change_order_tools(
        mcp,
        api_key="test-key",
        secret_key="test-secret",
    )
    return mcp


@pytest.fixture
def mcp():
    return construct_mcp()


class FakeChangeOrderApi:
    return_orders: list[FakeChangeOrder] = []
    init_calls: list[dict] = []
    api_calls: list[dict] = []

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self, **kwargs):
        self.api_calls.append(kwargs)
        return SimpleNamespace(orders=self.return_orders)


def construct_fake_change_order_api(orders: list[FakeChangeOrder] | None = None):
    if orders is None:
        orders = [
            FakeChangeOrder(
                root_order_id=1,
                client_order_id="c1",
                order_id=10,
                symbol=Symbol.USD_JPY,
                side=Side.BUY,
                order_type=SimpleNamespace(value="NORMAL"),
                execution_type=Order.ExecutionType.LIMIT,
                settle_type=SettleType.OPEN,
                size=1,
                price=150.25,
                status=Order.Status.MODIFYING,
                expiry=date(2026, 5, 31),
                timestamp=datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
            )
        ]
    FakeChangeOrderApi.return_orders = orders
    return FakeChangeOrderApi


class TestChangeOrderTool:
    @pytest.fixture(autouse=True)
    def set_up_tear_down(self):
        yield
        FakeChangeOrderApi.init_calls = []
        FakeChangeOrderApi.api_calls = []
        FakeChangeOrderApi.return_orders = []

    @pytest.mark.anyio
    async def test_registers_change_order_api_tool_without_credentials_in_schema(
        self, mcp: FastMCP
    ):
        tool = await mcp.get_tool("change_order_api")

        assert tool is not None
        assert tool.name == "change_order_api"
        assert set(tool.parameters["required"]) == {"price"}
        assert "order_id" in tool.parameters["properties"]
        assert "client_order_id" in tool.parameters["properties"]
        assert "api_key" not in tool.parameters["properties"]
        assert "secret_key" not in tool.parameters["properties"]

    @pytest.mark.anyio
    async def test_change_order_api_uses_order_id_and_maps_response(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_change_order_api()
        monkeypatch.setattr(change_order_tool, "ChangeOrderApi", FakeChangeOrderApi)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "change_order_api",
                {
                    "order_id": 10,
                    "price": 150.25,
                },
            )

        assert FakeChangeOrderApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert FakeChangeOrderApi.api_calls == [
            {
                "price": 150.25,
                "order_id": 10,
                "client_order_id": None,
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
                "status": "MODIFYING",
                "expiry": "2026-05-31",
                "timestamp": "2026-05-05T10:30:00+00:00",
            }
        ]

    @pytest.mark.anyio
    async def test_change_order_api_uses_client_order_id(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_change_order_api()
        monkeypatch.setattr(change_order_tool, "ChangeOrderApi", FakeChangeOrderApi)

        async with Client(mcp) as client:
            await client.call_tool(
                "change_order_api",
                {
                    "client_order_id": "c1",
                    "price": 150.25,
                },
            )

        assert FakeChangeOrderApi.api_calls == [
            {
                "price": 150.25,
                "order_id": None,
                "client_order_id": "c1",
            }
        ]

    @pytest.mark.anyio
    async def test_should_fail_change_order_when_order_id_and_client_order_id_missing(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        monkeypatch.setattr(change_order_tool, "ChangeOrderApi", FakeChangeOrderApi)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "change_order_api",
                {"price": 150.25},
                raise_on_error=False,
            )

        assert FakeChangeOrderApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert result.is_error is True
        assert result.content[0].text == (
            "Specify exactly one of order_id or client_order_id"
        )
        assert FakeChangeOrderApi.api_calls == []

    @pytest.mark.anyio
    async def test_should_fail_change_order_when_order_id_and_client_order_id_both_set(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        monkeypatch.setattr(change_order_tool, "ChangeOrderApi", FakeChangeOrderApi)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "change_order_api",
                {
                    "order_id": 10,
                    "client_order_id": "c1",
                    "price": 150.25,
                },
                raise_on_error=False,
            )

        assert result.is_error is True
        assert result.content[0].text == (
            "Specify exactly one of order_id or client_order_id"
        )
        assert FakeChangeOrderApi.api_calls == []
