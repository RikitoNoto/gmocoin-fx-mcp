from dataclasses import dataclass
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP
from gmo_fx.api.close_order import CloseOrderApi

from tools.close_order import register_close_order_tools
import tools.close_order.tool as close_order_tool
import utils.client_order_id as client_order_id_tool


@dataclass
class FakeCloseOrder:
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
    symbol_limits: set[CloseOrderApi.Symbol] | None = None,
    client_order_id_prefix: str | None = None,
):
    mcp = FastMCP("test")
    register_close_order_tools(
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


class FakeCloseOrderApi:
    return_close_orders: list[FakeCloseOrder] = []
    init_calls: list[dict] = []
    api_calls: list[dict] = []
    Symbol = CloseOrderApi.Symbol
    Side = CloseOrderApi.Side
    ExecutionType = CloseOrderApi.ExecutionType
    SettlePosition = CloseOrderApi.SettlePosition

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self, **kwargs):
        self.api_calls.append(kwargs)
        return SimpleNamespace(close_orders=self.return_close_orders)


def construct_fake_close_order_api(close_orders: list[FakeCloseOrder] | None = None):
    if close_orders is None:
        close_orders = [
            FakeCloseOrder(
                root_order_id="r1",
                client_order_id="c1",
                order_id="o1",
                symbol=CloseOrderApi.Symbol.USD_JPY,
                side=CloseOrderApi.Side.SELL,
                order_type=SimpleNamespace(value="NORMAL"),
                execution_type=CloseOrderApi.ExecutionType.LIMIT,
                settle_type=SimpleNamespace(value="CLOSE"),
                size=1,
                price=150.25,
                status=SimpleNamespace(value="ORDERED"),
                cancel_type=None,
                expiry=date(2026, 5, 31),
                timestamp=datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
            )
        ]
    FakeCloseOrderApi.return_close_orders = close_orders
    return FakeCloseOrderApi


class TestCloseOrderTool:
    @pytest.fixture(autouse=True)
    def set_up_tear_down(self):
        yield
        FakeCloseOrderApi.init_calls = []
        FakeCloseOrderApi.api_calls = []
        FakeCloseOrderApi.return_close_orders = []

    @pytest.mark.anyio
    async def test_registers_close_order_api_tool_without_credentials_in_schema(
        self, mcp: FastMCP
    ):
        tool = await mcp.get_tool("close_order_api")

        assert tool is not None
        assert tool.name == "close_order_api"
        assert set(tool.parameters["required"]) == {
            "symbol",
            "side",
            "execution_type",
        }
        assert "api_key" not in tool.parameters["properties"]
        assert "secret_key" not in tool.parameters["properties"]

    @pytest.mark.anyio
    async def test_close_order_api_uses_registered_credentials_and_maps_response(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_close_order_api()
        monkeypatch.setattr(close_order_tool, "CloseOrderApi", FakeCloseOrderApi)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "close_order_api",
                {
                    "symbol": "USD_JPY",
                    "side": "SELL",
                    "execution_type": "LIMIT",
                    "client_order_id": "c1",
                    "size": 1,
                    "limit_price": 150.25,
                    "settle_position": [{"position_id": 123, "size": 1}],
                },
            )

        assert FakeCloseOrderApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert FakeCloseOrderApi.api_calls == [
            {
                "symbol": CloseOrderApi.Symbol.USD_JPY,
                "side": CloseOrderApi.Side.SELL,
                "execution_type": CloseOrderApi.ExecutionType.LIMIT,
                "client_order_id": "c1",
                "size": 1,
                "limit_price": 150.25,
                "stop_price": None,
                "lower_bound": None,
                "upper_bound": None,
                "settle_position": [CloseOrderApi.SettlePosition(123, 1)],
            }
        ]
        assert result.data == [
            {
                "root_order_id": "r1",
                "client_order_id": "c1",
                "order_id": "o1",
                "symbol": "USD_JPY",
                "side": "SELL",
                "order_type": "NORMAL",
                "execution_type": "LIMIT",
                "settle_type": "CLOSE",
                "size": 1,
                "price": 150.25,
                "status": "ORDERED",
                "cancel_type": None,
                "expiry": "2026-05-31",
                "timestamp": "2026-05-05T10:30:00+00:00",
            }
        ]

    @pytest.mark.anyio
    async def test_close_order_api_generates_client_order_id_with_configured_prefix(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        class FixedDateTime:
            @classmethod
            def now(cls, tz):
                return datetime(2026, 5, 6, 1, 2, 3, tzinfo=tz)

        construct_fake_close_order_api()
        monkeypatch.setattr(close_order_tool, "CloseOrderApi", FakeCloseOrderApi)
        monkeypatch.setattr(client_order_id_tool, "datetime", FixedDateTime)
        mcp_instance = construct_mcp(client_order_id_prefix="GMOFX")

        async with Client(mcp_instance) as client:
            await client.call_tool(
                "close_order_api",
                {
                    "symbol": "USD_JPY",
                    "side": "SELL",
                    "execution_type": "LIMIT",
                    "size": 1,
                    "limit_price": 150.25,
                },
            )

        assert FakeCloseOrderApi.api_calls[0]["client_order_id"] == (
            "GMOFX20260506010203"
        )

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
        ],
    )
    def test_register_close_order_api_rejects_invalid_client_order_id_prefix(
        self, prefix: str, expected_message: str
    ):
        with pytest.raises(ValueError, match=expected_message):
            construct_mcp(client_order_id_prefix=prefix)

    @pytest.mark.anyio
    async def test_should_fail_close_order_when_size_limit_env(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        mcp_instance = construct_mcp(size_limit=10)
        monkeypatch.setattr(close_order_tool, "CloseOrderApi", FakeCloseOrderApi)

        async with Client(mcp_instance) as client:
            result = await client.call_tool(
                "close_order_api",
                {
                    "symbol": "USD_JPY",
                    "side": "SELL",
                    "execution_type": "LIMIT",
                    "size": 11,
                    "limit_price": 150.25,
                },
                raise_on_error=False,
            )

        assert FakeCloseOrderApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert result.is_error is True
        assert result.content[0].text == "size must be less than or equal to 10"
        assert FakeCloseOrderApi.api_calls == []

    @pytest.mark.anyio
    async def test_should_fail_close_order_when_symbol_not_in_limits(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        mcp_instance = construct_mcp(symbol_limits={CloseOrderApi.Symbol.USD_JPY})
        monkeypatch.setattr(close_order_tool, "CloseOrderApi", FakeCloseOrderApi)

        async with Client(mcp_instance) as client:
            result = await client.call_tool(
                "close_order_api",
                {
                    "symbol": "EUR_JPY",
                    "side": "SELL",
                    "execution_type": "LIMIT",
                    "size": 1,
                },
                raise_on_error=False,
            )

        assert result.is_error is True
        assert result.content[0].text == "symbol must be one of: USD_JPY"
        assert FakeCloseOrderApi.api_calls == []
