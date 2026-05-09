from dataclasses import dataclass
from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP
from gmo_fx.api.ifd_order import IFDOrderApi

from tools.change_ifd_order import register_change_ifd_order_tools
import tools.change_ifd_order.tool as change_ifd_order_tool


@dataclass
class FakeChangeIfdOrder:
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


def create_test_server():
    mcp = FastMCP("test")
    register_change_ifd_order_tools(
        mcp,
        api_key="test-key",
        secret_key="test-secret",
    )
    return mcp


class FakeChangeIfdOrderApi:
    init_calls: list[dict] = []
    api_calls: list[dict] = []
    return_orders: list[FakeChangeIfdOrder] = []

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self, **kwargs):
        self.api_calls.append(kwargs)
        return SimpleNamespace(orders=self.return_orders)


def reset_fake_change_ifd_api(orders: list[FakeChangeIfdOrder] | None = None):
    FakeChangeIfdOrderApi.init_calls = []
    FakeChangeIfdOrderApi.api_calls = []
    FakeChangeIfdOrderApi.return_orders = orders or [
        FakeChangeIfdOrder(
            root_order_id=987654321,
            client_order_id="ifd123",
            order_id=987654321,
            symbol=IFDOrderApi.Symbol.USD_JPY,
            side=IFDOrderApi.Side.BUY,
            order_type=SimpleNamespace(value="IFD"),
            execution_type=IFDOrderApi.ExecutionType.LIMIT,
            settle_type=SimpleNamespace(value="OPEN"),
            size=10000,
            price=136.0,
            status=SimpleNamespace(value="WAITING"),
            expiry=date(2026, 6, 1),
            timestamp=datetime(2026, 5, 7, 11, 30, tzinfo=timezone.utc),
        ),
        FakeChangeIfdOrder(
            root_order_id=987654321,
            client_order_id="ifd123",
            order_id=987654322,
            symbol=IFDOrderApi.Symbol.USD_JPY,
            side=IFDOrderApi.Side.SELL,
            order_type=SimpleNamespace(value="IFD"),
            execution_type=IFDOrderApi.ExecutionType.STOP,
            settle_type=SimpleNamespace(value="CLOSE"),
            size=10000,
            price=133.0,
            status=SimpleNamespace(value="WAITING"),
            expiry=date(2026, 6, 1),
            timestamp=datetime(2026, 5, 7, 11, 30, tzinfo=timezone.utc),
        ),
    ]


@pytest.mark.anyio
async def test_registers_change_ifd_order_api_tool_schema_without_credentials():
    mcp = create_test_server()
    tool = await mcp.get_tool("change_ifd_order_api")

    assert tool is not None
    assert tool.name == "change_ifd_order_api"
    assert set(tool.parameters["properties"]) == {
        "root_order_id",
        "client_order_id",
        "first_price",
        "second_price",
    }
    assert "api_key" not in tool.parameters["properties"]
    assert "secret_key" not in tool.parameters["properties"]


@pytest.mark.anyio
async def test_change_ifd_order_api_uses_root_order_id_and_maps_response(monkeypatch):
    reset_fake_change_ifd_api()
    monkeypatch.setattr(
        change_ifd_order_tool, "ChangeIfdOrderApi", FakeChangeIfdOrderApi
    )
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "change_ifd_order_api",
            {
                "root_order_id": 987654321,
                "first_price": 136,
                "second_price": 133,
            },
        )

    assert FakeChangeIfdOrderApi.init_calls == [
        {"api_key": "test-key", "secret_key": "test-secret"}
    ]
    assert FakeChangeIfdOrderApi.api_calls == [
        {
            "root_order_id": 987654321,
            "client_order_id": None,
            "first_price": 136.0,
            "second_price": 133.0,
        }
    ]
    assert result.data == [
        {
            "root_order_id": 987654321,
            "client_order_id": "ifd123",
            "order_id": 987654321,
            "symbol": "USD_JPY",
            "side": "BUY",
            "order_type": "IFD",
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
            "client_order_id": "ifd123",
            "order_id": 987654322,
            "symbol": "USD_JPY",
            "side": "SELL",
            "order_type": "IFD",
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
async def test_change_ifd_order_api_uses_client_order_id_and_partial_price(monkeypatch):
    reset_fake_change_ifd_api()
    monkeypatch.setattr(
        change_ifd_order_tool, "ChangeIfdOrderApi", FakeChangeIfdOrderApi
    )
    mcp = create_test_server()

    async with Client(mcp) as client:
        await client.call_tool(
            "change_ifd_order_api",
            {
                "client_order_id": "ifd123",
                "second_price": 133,
            },
        )

    assert FakeChangeIfdOrderApi.api_calls == [
        {
            "root_order_id": None,
            "client_order_id": "ifd123",
            "first_price": None,
            "second_price": 133.0,
        }
    ]


@pytest.mark.anyio
async def test_change_ifd_order_api_validates_required_order_identifier(monkeypatch):
    reset_fake_change_ifd_api()
    monkeypatch.setattr(
        change_ifd_order_tool, "ChangeIfdOrderApi", FakeChangeIfdOrderApi
    )
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "change_ifd_order_api",
            {"first_price": 136},
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == (
        "Specify exactly one of root_order_id or client_order_id"
    )
    assert FakeChangeIfdOrderApi.init_calls == []
    assert FakeChangeIfdOrderApi.api_calls == []


@pytest.mark.anyio
async def test_change_ifd_order_api_rejects_both_order_identifiers(monkeypatch):
    reset_fake_change_ifd_api()
    monkeypatch.setattr(
        change_ifd_order_tool, "ChangeIfdOrderApi", FakeChangeIfdOrderApi
    )
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "change_ifd_order_api",
            {
                "root_order_id": 987654321,
                "client_order_id": "ifd123",
                "first_price": 136,
            },
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == (
        "Specify exactly one of root_order_id or client_order_id"
    )
    assert FakeChangeIfdOrderApi.init_calls == []
    assert FakeChangeIfdOrderApi.api_calls == []


@pytest.mark.anyio
async def test_change_ifd_order_api_rejects_empty_client_order_id(monkeypatch):
    reset_fake_change_ifd_api()
    monkeypatch.setattr(
        change_ifd_order_tool, "ChangeIfdOrderApi", FakeChangeIfdOrderApi
    )
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "change_ifd_order_api",
            {
                "client_order_id": "",
                "first_price": 136,
            },
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == "client_order_id must not be empty"
    assert FakeChangeIfdOrderApi.init_calls == []
    assert FakeChangeIfdOrderApi.api_calls == []


@pytest.mark.anyio
async def test_change_ifd_order_api_validates_required_price(monkeypatch):
    reset_fake_change_ifd_api()
    monkeypatch.setattr(
        change_ifd_order_tool, "ChangeIfdOrderApi", FakeChangeIfdOrderApi
    )
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "change_ifd_order_api",
            {"root_order_id": 987654321},
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == "Specify at least one of first_price or second_price"
    assert FakeChangeIfdOrderApi.init_calls == []
    assert FakeChangeIfdOrderApi.api_calls == []


@pytest.mark.anyio
async def test_change_ifd_order_api_validates_positive_price(monkeypatch):
    reset_fake_change_ifd_api()
    monkeypatch.setattr(
        change_ifd_order_tool, "ChangeIfdOrderApi", FakeChangeIfdOrderApi
    )
    mcp = create_test_server()

    async with Client(mcp) as client:
        result = await client.call_tool(
            "change_ifd_order_api",
            {
                "root_order_id": 987654321,
                "second_price": 0,
            },
            raise_on_error=False,
        )

    assert result.is_error is True
    assert result.content[0].text == "second_price must be greater than 0"
    assert FakeChangeIfdOrderApi.init_calls == []
    assert FakeChangeIfdOrderApi.api_calls == []
