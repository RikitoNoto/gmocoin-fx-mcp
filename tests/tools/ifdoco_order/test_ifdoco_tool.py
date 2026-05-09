from dataclasses import dataclass
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP
from gmo_fx.api.ifo_order import IFDOCOOrderApi

from tools.ifdoco_order import register_ifdoco_order_tools
import tools.ifdoco_order.tool as ifdoco_tool
import utils.client_order_id as client_order_id_tool


@dataclass
class FakeIFDOCOOrder:
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
    symbol_limits: set[IFDOCOOrderApi.Symbol] | None = None,
    client_order_id_prefix: str | None = None,
):
    mcp = FastMCP("test")
    register_ifdoco_order_tools(
        mcp,
        api_key="test-key",
        secret_key="test-secret",
        size_limit=size_limit,
        symbol_limits=symbol_limits,
        client_order_id_prefix=client_order_id_prefix,
    )
    return mcp


class FakeIFDOCOOrderApi:
    init_calls: list[dict] = []
    api_calls: list[dict] = []
    return_orders: list[FakeIFDOCOOrder] = []
    Symbol = IFDOCOOrderApi.Symbol
    Side = IFDOCOOrderApi.Side
    ExecutionType = IFDOCOOrderApi.ExecutionType

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self, **kwargs):
        self.api_calls.append(kwargs)
        return SimpleNamespace(ifo_orders=self.return_orders)


class FakeChangeIfoOrderApi:
    init_calls: list[dict] = []
    api_calls: list[dict] = []
    return_orders: list[FakeIFDOCOOrder] = []

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self, **kwargs):
        self.api_calls.append(kwargs)
        return SimpleNamespace(orders=self.return_orders)


def reset_fake_change_ifo_api(orders: list[FakeIFDOCOOrder] | None = None):
    FakeChangeIfoOrderApi.init_calls = []
    FakeChangeIfoOrderApi.api_calls = []
    FakeChangeIfoOrderApi.return_orders = orders or [
        FakeIFDOCOOrder(
            root_order_id=987654321,
            client_order_id="ifo123",
            order_id=987654321,
            symbol=IFDOCOOrderApi.Symbol.USD_JPY,
            side=IFDOCOOrderApi.Side.BUY,
            order_type=SimpleNamespace(value="IFDOCO"),
            execution_type=SimpleNamespace(value="LIMIT"),
            settle_type=SimpleNamespace(value="OPEN"),
            size=10000,
            price=136.0,
            status=SimpleNamespace(value="WAITING"),
            expiry=date(2026, 6, 1),
            timestamp=datetime(2026, 5, 7, 11, 30, tzinfo=timezone.utc),
        ),
        FakeIFDOCOOrder(
            root_order_id=987654321,
            client_order_id="ifo123",
            order_id=987654322,
            symbol=IFDOCOOrderApi.Symbol.USD_JPY,
            side=IFDOCOOrderApi.Side.SELL,
            order_type=SimpleNamespace(value="IFDOCO"),
            execution_type=SimpleNamespace(value="LIMIT"),
            settle_type=SimpleNamespace(value="CLOSE"),
            size=10000,
            price=141.0,
            status=SimpleNamespace(value="WAITING"),
            expiry=date(2026, 6, 1),
            timestamp=datetime(2026, 5, 7, 11, 30, tzinfo=timezone.utc),
        ),
        FakeIFDOCOOrder(
            root_order_id=987654321,
            client_order_id="ifo123",
            order_id=987654323,
            symbol=IFDOCOOrderApi.Symbol.USD_JPY,
            side=IFDOCOOrderApi.Side.SELL,
            order_type=SimpleNamespace(value="IFDOCO"),
            execution_type=SimpleNamespace(value="STOP"),
            settle_type=SimpleNamespace(value="CLOSE"),
            size=10000,
            price=133.0,
            status=SimpleNamespace(value="WAITING"),
            expiry=date(2026, 6, 1),
            timestamp=datetime(2026, 5, 7, 11, 30, tzinfo=timezone.utc),
        ),
    ]


def reset_fake_ifdoco_api(orders: list[FakeIFDOCOOrder] | None = None):
    FakeIFDOCOOrderApi.init_calls = []
    FakeIFDOCOOrderApi.api_calls = []
    FakeIFDOCOOrderApi.return_orders = orders or [
        FakeIFDOCOOrder(
            root_order_id=123456789,
            client_order_id="abc123",
            order_id=123456789,
            symbol=IFDOCOOrderApi.Symbol.USD_JPY,
            side=IFDOCOOrderApi.Side.BUY,
            order_type=SimpleNamespace(value="IFDOCO"),
            execution_type=SimpleNamespace(value="LIMIT"),
            settle_type=SimpleNamespace(value="OPEN"),
            size=10000,
            price=135.0,
            status=SimpleNamespace(value="WAITING"),
            expiry=date(2026, 5, 31),
            timestamp=datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
        ),
        FakeIFDOCOOrder(
            root_order_id=123456789,
            client_order_id="abc123",
            order_id=123456790,
            symbol=IFDOCOOrderApi.Symbol.USD_JPY,
            side=IFDOCOOrderApi.Side.SELL,
            order_type=SimpleNamespace(value="IFDOCO"),
            execution_type=SimpleNamespace(value="LIMIT"),
            settle_type=SimpleNamespace(value="CLOSE"),
            size=10000,
            price=140.0,
            status=SimpleNamespace(value="WAITING"),
            expiry=date(2026, 5, 31),
            timestamp=datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
        ),
        FakeIFDOCOOrder(
            root_order_id=123456789,
            client_order_id="abc123",
            order_id=123456791,
            symbol=IFDOCOOrderApi.Symbol.USD_JPY,
            side=IFDOCOOrderApi.Side.SELL,
            order_type=SimpleNamespace(value="IFDOCO"),
            execution_type=SimpleNamespace(value="STOP"),
            settle_type=SimpleNamespace(value="CLOSE"),
            size=10000,
            price=132.0,
            status=SimpleNamespace(value="WAITING"),
            expiry=date(2026, 5, 31),
            timestamp=datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
        ),
    ]


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
async def test_registers_change_ifdoco_order_api_tool_without_credentials_in_schema():
    mcp = create_test_server()
    tool = await mcp.get_tool("change_ifdoco_order_api")

    assert tool is not None
    assert tool.name == "change_ifdoco_order_api"
    assert set(tool.parameters["properties"]) == {
        "root_order_id",
        "client_order_id",
        "first_price",
        "second_limit_price",
        "second_stop_price",
    }
    assert "required" not in tool.parameters or tool.parameters["required"] == []
    assert "api_key" not in tool.parameters["properties"]
    assert "secret_key" not in tool.parameters["properties"]


@pytest.mark.anyio
async def test_registers_ifdoco_order_api_tool_schema_without_credentials():
    mcp = create_test_server()
    tool = await mcp.get_tool("ifdoco_order_api")

    assert tool is not None
    assert tool.name == "ifdoco_order_api"
    assert set(tool.parameters["properties"]) == {
        "symbol",
        "first_side",
        "first_execution_type",
        "first_size",
        "first_price",
        "second_size",
        "second_limit_price",
        "second_stop_price",
        "client_order_id",
    }
    assert "api_key" not in tool.parameters["properties"]
    assert "secret_key" not in tool.parameters["properties"]


@pytest.mark.anyio
async def test_ifdoco_order_api_uses_registered_credentials_and_maps_response(monkeypatch):
    reset_fake_ifdoco_api()
    monkeypatch.setattr(ifdoco_tool, "IFDOCOOrderApi", FakeIFDOCOOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "ifdoco_order_api",
            {
                "symbol": "USD_JPY",
                "client_order_id": "abc123",
                "first_side": "BUY",
                "first_execution_type": "LIMIT",
                "first_size": 10000,
                "first_price": 135,
                "second_size": 10000,
                "second_limit_price": 140,
                "second_stop_price": 132,
            },
        )

    assert FakeIFDOCOOrderApi.init_calls == [
        {"api_key": "test-key", "secret_key": "test-secret"}
    ]
    assert FakeIFDOCOOrderApi.api_calls == [
        {
            "symbol": IFDOCOOrderApi.Symbol.USD_JPY,
            "client_order_id": "abc123",
            "first_side": IFDOCOOrderApi.Side.BUY,
            "first_execution_type": IFDOCOOrderApi.ExecutionType.LIMIT,
            "first_size": 10000,
            "first_price": 135.0,
            "second_size": 10000,
            "second_limit_price": 140.0,
            "second_stop_price": 132.0,
        }
    ]
    assert result.data == [
        {
            "root_order_id": 123456789,
            "client_order_id": "abc123",
            "order_id": 123456789,
            "symbol": "USD_JPY",
            "side": "BUY",
            "order_type": "IFDOCO",
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
            "order_type": "IFDOCO",
            "execution_type": "LIMIT",
            "settle_type": "CLOSE",
            "size": 10000,
            "price": 140.0,
            "status": "WAITING",
            "expiry": "2026-05-31",
            "timestamp": "2026-05-05T10:30:00+00:00",
        },
        {
            "root_order_id": 123456789,
            "client_order_id": "abc123",
            "order_id": 123456791,
            "symbol": "USD_JPY",
            "side": "SELL",
            "order_type": "IFDOCO",
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
async def test_ifdoco_order_api_generates_client_order_id_with_configured_prefix(
    monkeypatch: pytest.MonkeyPatch,
):
    class FixedDateTime:
        @classmethod
        def now(cls, tz):
            return datetime(2026, 5, 6, 1, 2, 3, tzinfo=tz)

    reset_fake_ifdoco_api()
    monkeypatch.setattr(ifdoco_tool, "IFDOCOOrderApi", FakeIFDOCOOrderApi)
    monkeypatch.setattr(client_order_id_tool, "datetime", FixedDateTime)
    mcp = create_test_server(client_order_id_prefix="GMOFX")

    async with Client(mcp) as client:
        await client.call_tool(
            "ifdoco_order_api",
            {
                "symbol": "USD_JPY",
                "first_side": "BUY",
                "first_execution_type": "LIMIT",
                "first_size": 10000,
                "first_price": 135,
                "second_size": 10000,
                "second_limit_price": 140,
                "second_stop_price": 132,
            },
        )

    assert FakeIFDOCOOrderApi.api_calls[0]["client_order_id"] == "GMOFX20260506010203"


@pytest.mark.anyio
async def test_ifdoco_order_api_validates_required_second_limit_price(monkeypatch):
    reset_fake_ifdoco_api()
    monkeypatch.setattr(ifdoco_tool, "IFDOCOOrderApi", FakeIFDOCOOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "ifdoco_order_api",
            {
                "symbol": "USD_JPY",
                "first_side": "BUY",
                "first_execution_type": "LIMIT",
                "first_size": 10000,
                "first_price": 135,
                "second_size": 10000,
                "second_stop_price": 132,
            },
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == "second_limit_price is required for IFDOCO order"
    assert FakeIFDOCOOrderApi.api_calls == []


@pytest.mark.anyio
async def test_ifdoco_order_api_validates_positive_price(monkeypatch):
    reset_fake_ifdoco_api()
    monkeypatch.setattr(ifdoco_tool, "IFDOCOOrderApi", FakeIFDOCOOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "ifdoco_order_api",
            {
                "symbol": "USD_JPY",
                "first_side": "BUY",
                "first_execution_type": "LIMIT",
                "first_size": 10000,
                "first_price": 135,
                "second_size": 10000,
                "second_limit_price": 140,
                "second_stop_price": 0,
            },
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == "second_stop_price must be greater than 0"
    assert FakeIFDOCOOrderApi.api_calls == []


@pytest.mark.anyio
async def test_ifdoco_order_api_applies_size_limit(monkeypatch):
    reset_fake_ifdoco_api()
    monkeypatch.setattr(ifdoco_tool, "IFDOCOOrderApi", FakeIFDOCOOrderApi)
    mcp = create_test_server(size_limit=10000)

    async with Client(mcp) as client:
        result = await client.call_tool(
            "ifdoco_order_api",
            {
                "symbol": "USD_JPY",
                "first_side": "BUY",
                "first_execution_type": "LIMIT",
                "first_size": 10000,
                "first_price": 135,
                "second_size": 10001,
                "second_limit_price": 140,
                "second_stop_price": 132,
            },
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == "second_size must be less than or equal to 10000"
    assert FakeIFDOCOOrderApi.api_calls == []


@pytest.mark.anyio
async def test_ifdoco_order_api_applies_symbol_limits(monkeypatch):
    reset_fake_ifdoco_api()
    monkeypatch.setattr(ifdoco_tool, "IFDOCOOrderApi", FakeIFDOCOOrderApi)
    mcp = create_test_server(symbol_limits={IFDOCOOrderApi.Symbol.USD_JPY})

    async with Client(mcp) as client:
        result = await client.call_tool(
            "ifdoco_order_api",
            {
                "symbol": "EUR_JPY",
                "first_side": "BUY",
                "first_execution_type": "LIMIT",
                "first_size": 10000,
                "first_price": 135,
                "second_size": 10000,
                "second_limit_price": 140,
                "second_stop_price": 132,
            },
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == "symbol must be one of: USD_JPY"
    assert FakeIFDOCOOrderApi.api_calls == []


@pytest.mark.anyio
async def test_change_ifdoco_order_api_uses_root_order_id_and_maps_response(monkeypatch):
    reset_fake_change_ifo_api()
    monkeypatch.setattr(ifdoco_tool, "ChangeIfoOrderApi", FakeChangeIfoOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "change_ifdoco_order_api",
            {
                "root_order_id": 987654321,
                "first_price": 136,
                "second_limit_price": 141,
                "second_stop_price": 133,
            },
        )

    assert FakeChangeIfoOrderApi.init_calls == [
        {"api_key": "test-key", "secret_key": "test-secret"}
    ]
    assert FakeChangeIfoOrderApi.api_calls == [
        {
            "root_order_id": 987654321,
            "client_order_id": None,
            "first_price": 136.0,
            "second_limit_price": 141.0,
            "second_stop_price": 133.0,
        }
    ]
    assert result.data == [
        {
            "root_order_id": 987654321,
            "client_order_id": "ifo123",
            "order_id": 987654321,
            "symbol": "USD_JPY",
            "side": "BUY",
            "order_type": "IFDOCO",
            "execution_type": "LIMIT",
            "settle_type": "OPEN",
            "size": 10000,
            "price": 136.0,
            "status": "WAITING",
            "expiry": "2026-06-01",
            "timestamp": "2026-05-07T11:30:00+00:00",
        },
        {
            "root_order_id": 987654321,
            "client_order_id": "ifo123",
            "order_id": 987654322,
            "symbol": "USD_JPY",
            "side": "SELL",
            "order_type": "IFDOCO",
            "execution_type": "LIMIT",
            "settle_type": "CLOSE",
            "size": 10000,
            "price": 141.0,
            "status": "WAITING",
            "expiry": "2026-06-01",
            "timestamp": "2026-05-07T11:30:00+00:00",
        },
        {
            "root_order_id": 987654321,
            "client_order_id": "ifo123",
            "order_id": 987654323,
            "symbol": "USD_JPY",
            "side": "SELL",
            "order_type": "IFDOCO",
            "execution_type": "STOP",
            "settle_type": "CLOSE",
            "size": 10000,
            "price": 133.0,
            "status": "WAITING",
            "expiry": "2026-06-01",
            "timestamp": "2026-05-07T11:30:00+00:00",
        },
    ]


@pytest.mark.anyio
async def test_change_ifdoco_order_api_uses_client_order_id_and_partial_price(monkeypatch):
    reset_fake_change_ifo_api()
    monkeypatch.setattr(ifdoco_tool, "ChangeIfoOrderApi", FakeChangeIfoOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        await client.call_tool(
            "change_ifdoco_order_api",
            {
                "client_order_id": "ifo123",
                "second_stop_price": 133,
            },
        )

    assert FakeChangeIfoOrderApi.api_calls == [
        {
            "root_order_id": None,
            "client_order_id": "ifo123",
            "first_price": None,
            "second_limit_price": None,
            "second_stop_price": 133.0,
        }
    ]


@pytest.mark.anyio
async def test_change_ifdoco_order_api_validates_required_order_identifier(monkeypatch):
    reset_fake_change_ifo_api()
    monkeypatch.setattr(ifdoco_tool, "ChangeIfoOrderApi", FakeChangeIfoOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "change_ifdoco_order_api",
            {"first_price": 136},
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == (
        "Specify exactly one of root_order_id or client_order_id"
    )
    assert FakeChangeIfoOrderApi.api_calls == []


@pytest.mark.anyio
async def test_change_ifdoco_order_api_rejects_both_order_identifiers(monkeypatch):
    reset_fake_change_ifo_api()
    monkeypatch.setattr(ifdoco_tool, "ChangeIfoOrderApi", FakeChangeIfoOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "change_ifdoco_order_api",
            {
                "root_order_id": 987654321,
                "client_order_id": "ifo123",
                "first_price": 136,
            },
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == (
        "Specify exactly one of root_order_id or client_order_id"
    )
    assert FakeChangeIfoOrderApi.api_calls == []


@pytest.mark.anyio
async def test_change_ifdoco_order_api_validates_required_price(monkeypatch):
    reset_fake_change_ifo_api()
    monkeypatch.setattr(ifdoco_tool, "ChangeIfoOrderApi", FakeChangeIfoOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "change_ifdoco_order_api",
            {"root_order_id": 987654321},
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == (
        "Specify at least one of first_price, "
        "second_limit_price, or second_stop_price"
    )
    assert FakeChangeIfoOrderApi.api_calls == []


@pytest.mark.anyio
async def test_change_ifdoco_order_api_validates_positive_price(monkeypatch):
    reset_fake_change_ifo_api()
    monkeypatch.setattr(ifdoco_tool, "ChangeIfoOrderApi", FakeChangeIfoOrderApi)
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "change_ifdoco_order_api",
            {
                "root_order_id": 987654321,
                "second_limit_price": 0,
            },
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == "second_limit_price must be greater than 0"
    assert FakeChangeIfoOrderApi.api_calls == []


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
