from dataclasses import dataclass
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP
from gmo_fx.api.ifd_order import IFDOrderApi

from tools.ifd_order import register_ifd_order_tools
import tools.ifd_order.tool as ifd_tool
import utils.client_order_id as client_order_id_tool


@dataclass
class FakeIFDOrder:
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
    expiry: date | None
    timestamp: datetime


def create_test_server(
    size_limit: int | None = None,
    symbol_limits: set[IFDOrderApi.Symbol] | None = None,
    client_order_id_prefix: str | None = None,
):
    mcp = FastMCP("test")
    register_ifd_order_tools(
        mcp,
        api_key="test-key",
        secret_key="test-secret",
        size_limit=size_limit,
        symbol_limits=symbol_limits,
        client_order_id_prefix=client_order_id_prefix,
    )
    return mcp


class FakeIFDOrderApi:
    init_calls: list[dict] = []
    api_calls: list[dict] = []
    return_orders: list[FakeIFDOrder] = []
    Symbol = IFDOrderApi.Symbol
    Side = IFDOrderApi.Side
    ExecutionType = IFDOrderApi.ExecutionType

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self, **kwargs):
        self.api_calls.append(kwargs)
        return SimpleNamespace(ifd_orders=self.return_orders)


def reset_fake_ifd_api(orders: list[FakeIFDOrder] | None = None):
    FakeIFDOrderApi.init_calls = []
    FakeIFDOrderApi.api_calls = []
    FakeIFDOrderApi.return_orders = orders or [
        FakeIFDOrder(
            root_order_id=123456789,
            client_order_id="abc123",
            order_id=123456789,
            symbol=IFDOrderApi.Symbol.USD_JPY,
            side=IFDOrderApi.Side.BUY,
            order_type=SimpleNamespace(value="IFD"),
            execution_type=IFDOrderApi.ExecutionType.LIMIT,
            settle_type=SimpleNamespace(value="OPEN"),
            size=10000,
            price=135.0,
            status=SimpleNamespace(value="WAITING"),
            expiry=date(2026, 5, 31),
            timestamp=datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
        ),
        FakeIFDOrder(
            root_order_id=123456789,
            client_order_id="abc123",
            order_id=123456790,
            symbol=IFDOrderApi.Symbol.USD_JPY,
            side=IFDOrderApi.Side.SELL,
            order_type=SimpleNamespace(value="IFD"),
            execution_type=IFDOrderApi.ExecutionType.STOP,
            settle_type=SimpleNamespace(value="CLOSE"),
            size=10000,
            price=132.0,
            status=SimpleNamespace(value="WAITING"),
            expiry=date(2026, 5, 31),
            timestamp=datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
        ),
    ]


@pytest.mark.anyio
async def test_registers_ifd_order_api_tool_schema_without_credentials():
    mcp = create_test_server()
    tool = await mcp.get_tool("ifd_order_api")

    assert tool is not None
    assert tool.name == "ifd_order_api"
    assert set(tool.parameters["properties"]) == {
        "symbol",
        "client_order_id",
        "first_side",
        "first_execution_type",
        "first_size",
        "first_price",
        "second_execution_type",
        "second_size",
        "second_price",
    }
    assert "api_key" not in tool.parameters["properties"]
    assert "secret_key" not in tool.parameters["properties"]


@pytest.mark.anyio
async def test_ifd_order_api_uses_registered_credentials_and_maps_response(monkeypatch):
    reset_fake_ifd_api()
    monkeypatch.setattr(ifd_tool, "IFDOrderApi", FakeIFDOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "ifd_order_api",
            {
                "symbol": "USD_JPY",
                "client_order_id": "abc123",
                "first_side": "BUY",
                "first_execution_type": "LIMIT",
                "first_size": 10000,
                "first_price": 135,
                "second_execution_type": "STOP",
                "second_size": 10000,
                "second_price": 132,
            },
        )

    assert FakeIFDOrderApi.init_calls == [
        {"api_key": "test-key", "secret_key": "test-secret"}
    ]
    assert FakeIFDOrderApi.api_calls == [
        {
            "symbol": IFDOrderApi.Symbol.USD_JPY,
            "client_order_id": "abc123",
            "first_side": IFDOrderApi.Side.BUY,
            "first_execution_type": IFDOrderApi.ExecutionType.LIMIT,
            "first_size": 10000,
            "first_price": 135.0,
            "second_execution_type": IFDOrderApi.ExecutionType.STOP,
            "second_size": 10000,
            "second_price": 132.0,
        }
    ]
    assert result.data == [
        {
            "root_order_id": 123456789,
            "client_order_id": "abc123",
            "order_id": 123456789,
            "symbol": "USD_JPY",
            "side": "BUY",
            "order_type": "IFD",
            "execution_type": "LIMIT",
            "settle_type": "OPEN",
            "size": 10000,
            "price": 135.0,
            "status": "WAITING",
            "expiry": "2026-05-31",
            "timestamp": "2026-05-05T10:30:00+00:00",
        },
        {
            "root_order_id": 123456789,
            "client_order_id": "abc123",
            "order_id": 123456790,
            "symbol": "USD_JPY",
            "side": "SELL",
            "order_type": "IFD",
            "execution_type": "STOP",
            "settle_type": "CLOSE",
            "size": 10000,
            "price": 132.0,
            "status": "WAITING",
            "expiry": "2026-05-31",
            "timestamp": "2026-05-05T10:30:00+00:00",
        },
    ]


@pytest.mark.anyio
async def test_ifd_order_api_generates_client_order_id_with_configured_prefix(
    monkeypatch: pytest.MonkeyPatch,
):
    class FixedDateTime:
        @classmethod
        def now(cls, tz):
            return datetime(2026, 5, 6, 1, 2, 3, tzinfo=tz)

    reset_fake_ifd_api()
    monkeypatch.setattr(ifd_tool, "IFDOrderApi", FakeIFDOrderApi)
    monkeypatch.setattr(client_order_id_tool, "datetime", FixedDateTime)
    mcp = create_test_server(client_order_id_prefix="GMOFX")

    async with Client(mcp) as client:
        await client.call_tool(
            "ifd_order_api",
            {
                "symbol": "USD_JPY",
                "first_side": "BUY",
                "first_execution_type": "LIMIT",
                "first_size": 10000,
                "first_price": 135,
                "second_execution_type": "STOP",
                "second_size": 10000,
                "second_price": 132,
            },
        )

    assert FakeIFDOrderApi.api_calls[0]["client_order_id"] == "GMOFX20260506010203"


@pytest.mark.anyio
async def test_ifd_order_api_validates_required_second_execution_type(monkeypatch):
    reset_fake_ifd_api()
    monkeypatch.setattr(ifd_tool, "IFDOrderApi", FakeIFDOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "ifd_order_api",
            {
                "symbol": "USD_JPY",
                "first_side": "BUY",
                "first_execution_type": "LIMIT",
                "first_size": 10000,
                "first_price": 135,
                "second_size": 10000,
                "second_price": 132,
            },
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == "second_execution_type is required for IFD order"
    assert FakeIFDOrderApi.api_calls == []


@pytest.mark.anyio
async def test_ifd_order_api_validates_positive_price(monkeypatch):
    reset_fake_ifd_api()
    monkeypatch.setattr(ifd_tool, "IFDOrderApi", FakeIFDOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "ifd_order_api",
            {
                "symbol": "USD_JPY",
                "first_side": "BUY",
                "first_execution_type": "LIMIT",
                "first_size": 10000,
                "first_price": 135,
                "second_execution_type": "STOP",
                "second_size": 10000,
                "second_price": 0,
            },
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == "second_price must be greater than 0"
    assert FakeIFDOrderApi.api_calls == []


@pytest.mark.anyio
async def test_ifd_order_api_applies_size_limit(monkeypatch):
    reset_fake_ifd_api()
    monkeypatch.setattr(ifd_tool, "IFDOrderApi", FakeIFDOrderApi)
    mcp = create_test_server(size_limit=10000)

    async with Client(mcp) as client:
        result = await client.call_tool(
            "ifd_order_api",
            {
                "symbol": "USD_JPY",
                "first_side": "BUY",
                "first_execution_type": "LIMIT",
                "first_size": 10001,
                "first_price": 135,
                "second_execution_type": "STOP",
                "second_size": 10000,
                "second_price": 132,
            },
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == "first_size must be less than or equal to 10000"
    assert FakeIFDOrderApi.api_calls == []


@pytest.mark.anyio
async def test_ifd_order_api_applies_symbol_limits(monkeypatch):
    reset_fake_ifd_api()
    monkeypatch.setattr(ifd_tool, "IFDOrderApi", FakeIFDOrderApi)
    mcp = create_test_server(symbol_limits={IFDOrderApi.Symbol.USD_JPY})

    async with Client(mcp) as client:
        result = await client.call_tool(
            "ifd_order_api",
            {
                "symbol": "EUR_JPY",
                "first_side": "BUY",
                "first_execution_type": "LIMIT",
                "first_size": 10000,
                "first_price": 135,
                "second_execution_type": "STOP",
                "second_size": 10000,
                "second_price": 132,
            },
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == "symbol must be one of: USD_JPY"
    assert FakeIFDOrderApi.api_calls == []
