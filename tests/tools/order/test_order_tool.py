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


def construct_mcp(
    size_limit: int | None = None,
    symbol_limits: set[OrderApi.Symbol] | None = None,
    client_order_id_prefix: str | None = None,
):
    mcp = FastMCP("test")
    register_order_tools(
        mcp,
        api_key="test-key",
        secret_key="test-secret",
        size_limit=size_limit,
        symbol_limits=symbol_limits,
        client_order_id_prefix=client_order_id_prefix,
    )
    return mcp


@pytest.fixture
def mcp():
    return construct_mcp()


class FakeOrderApi:
    return_orders: list[FakeOrder] = []
    init_calls: list[dict] = []
    api_calls: list[dict] = []
    Symbol = OrderApi.Symbol
    Side = OrderApi.Side
    ExecutionType = OrderApi.ExecutionType

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self, **kwargs):
        self.api_calls.append(kwargs)
        return SimpleNamespace(orders=self.return_orders)


def construct_fake_order_api(orders: list[FakeOrder] | None = None):
    if orders is None:
        orders = [
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
    FakeOrderApi.return_orders = orders
    return FakeOrderApi


class TestOrderTool:

    @pytest.fixture(autouse=True)
    def set_up_tear_down(self):
        self.set_up()
        yield
        self.tear_down()

    def set_up(self):
        pass

    def tear_down(self):
        FakeOrderApi.init_calls = []
        FakeOrderApi.api_calls = []
        FakeOrderApi.return_orders = []

    @pytest.mark.anyio
    async def test_registers_order_api_tool_without_credentials_in_schema(
        self, mcp: FastMCP
    ):
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
    async def test_order_api_uses_registered_credentials_and_maps_response(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_order_api()
        monkeypatch.setattr(order_tool, "OrderApi", FakeOrderApi)

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

        assert FakeOrderApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert FakeOrderApi.api_calls == [
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

    @pytest.mark.anyio
    async def test_order_api_generates_client_order_id_with_configured_prefix(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        class FixedDateTime:
            @classmethod
            def now(cls, tz):
                return datetime(2026, 5, 6, 1, 2, 3, tzinfo=tz)

        construct_fake_order_api()
        monkeypatch.setattr(order_tool, "OrderApi", FakeOrderApi)
        monkeypatch.setattr(order_tool, "datetime", FixedDateTime)
        mcp_instance = construct_mcp(client_order_id_prefix="GMOFX")

        async with Client(mcp_instance) as client:
            await client.call_tool(
                "order_api",
                {
                    "symbol": "USD_JPY",
                    "side": "BUY",
                    "size": 1,
                    "execution_type": "LIMIT",
                    "limit_price": 150.25,
                },
            )

        assert FakeOrderApi.api_calls[0]["client_order_id"] == "GMOFX20260506010203"

    @pytest.mark.anyio
    async def test_order_api_accepts_22_character_client_order_id_prefix(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        class FixedDateTime:
            @classmethod
            def now(cls, tz):
                return datetime(2026, 5, 6, 1, 2, 3, tzinfo=tz)

        construct_fake_order_api()
        monkeypatch.setattr(order_tool, "OrderApi", FakeOrderApi)
        monkeypatch.setattr(order_tool, "datetime", FixedDateTime)
        mcp_instance = construct_mcp(client_order_id_prefix="A" * 22)

        async with Client(mcp_instance) as client:
            await client.call_tool(
                "order_api",
                {
                    "symbol": "USD_JPY",
                    "side": "BUY",
                    "size": 1,
                    "execution_type": "LIMIT",
                    "limit_price": 150.25,
                },
            )

        assert (
            FakeOrderApi.api_calls[0]["client_order_id"]
            == "AAAAAAAAAAAAAAAAAAAAAA20260506010203"
        )
        assert len(FakeOrderApi.api_calls[0]["client_order_id"]) == 36

    @pytest.mark.parametrize(
        "prefix, expected_message",
        [
            (
                "A" * 23,
                "client_order_id_prefix must be less than or equal to 22 characters",
            ),
            (
                "ABC_123",
                "client_order_id_prefix must contain only ASCII letters and numbers",
            ),
            (
                "発注",
                "client_order_id_prefix must contain only ASCII letters and numbers",
            ),
        ],
    )
    def test_register_order_api_rejects_invalid_client_order_id_prefix(
        self, prefix: str, expected_message: str
    ):
        with pytest.raises(ValueError, match=expected_message):
            construct_mcp(client_order_id_prefix=prefix)

    @pytest.mark.anyio
    async def test_should_fail_order_when_size_limit_env(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        mcp_instance = construct_mcp(size_limit=10)
        monkeypatch.setattr(order_tool, "OrderApi", FakeOrderApi)

        async with Client(mcp_instance) as client:
            result = await client.call_tool(
                "order_api",
                {
                    "symbol": "USD_JPY",
                    "side": "BUY",
                    "size": 11,
                    "execution_type": "LIMIT",
                    "client_order_id": "c1",
                    "limit_price": 150.25,
                },
                raise_on_error=False,
            )

        assert FakeOrderApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert result.is_error == True
        assert result.content[0].text == "size must be less than or equal to 10"
        assert FakeOrderApi.api_calls == []

    @pytest.mark.anyio
    async def test_should_success_order_when_size_equals_limit_env(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        mcp_instance = construct_mcp(size_limit=10)
        monkeypatch.setattr(order_tool, "OrderApi", FakeOrderApi)

        async with Client(mcp_instance) as client:
            result = await client.call_tool(
                "order_api",
                {
                    "symbol": "USD_JPY",
                    "side": "BUY",
                    "size": 10,
                    "execution_type": "LIMIT",
                    "client_order_id": "c1",
                    "limit_price": 150.25,
                },
                raise_on_error=False,
            )

        assert FakeOrderApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert result.is_error == False
        assert FakeOrderApi.api_calls != []

    @pytest.mark.anyio
    async def test_should_fail_order_when_symbol_not_in_limits(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        mcp_instance = construct_mcp(symbol_limits={OrderApi.Symbol.USD_JPY})
        monkeypatch.setattr(order_tool, "OrderApi", FakeOrderApi)

        async with Client(mcp_instance) as client:
            result = await client.call_tool(
                "order_api",
                {
                    "symbol": "EUR_JPY",
                    "side": "BUY",
                    "size": 1,
                    "execution_type": "LIMIT",
                },
                raise_on_error=False,
            )

        assert result.is_error == True
        assert result.content[0].text == "symbol must be one of: USD_JPY"
        assert FakeOrderApi.api_calls == []
