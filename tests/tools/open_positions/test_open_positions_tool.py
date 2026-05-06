from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP
from gmo_fx.api.latest_executions import LatestExecutionsApi
from gmo_fx.api.open_positions import OpenPositionsApi
from gmo_fx.api.order import OrderApi

from tools.open_positions import register_open_positions_tools
import tools.open_positions.tool as open_positions_tool


@dataclass
class FakeOpenPosition:
    position_id: int
    symbol: object
    side: object
    size: int
    ordered_size: int
    price: float
    loss_gain: float
    total_swap: float
    timestamp: datetime


@dataclass
class FakeExecution:
    position_id: int
    symbol: object
    client_order_id: str | None


def construct_mcp(client_order_id_prefix: str | None = None):
    mcp = FastMCP("test")
    register_open_positions_tools(
        mcp,
        api_key="test-key",
        secret_key="test-secret",
        client_order_id_prefix=client_order_id_prefix,
    )
    return mcp


@pytest.fixture
def mcp():
    return construct_mcp()


class FakeOpenPositionsApi:
    return_pages: list[list[FakeOpenPosition]] = []
    init_calls: list[dict] = []
    api_calls: list[dict] = []
    Symbol = OpenPositionsApi.Symbol

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self, **kwargs):
        self.api_calls.append(kwargs)
        page_index = len(self.api_calls) - 1
        return SimpleNamespace(open_positions=self.return_pages[page_index])


class FakeLatestExecutionsApi:
    return_executions_by_symbol: dict[object, list[FakeExecution]] = {}
    init_calls: list[dict] = []
    api_calls: list[dict] = []
    Symbol = LatestExecutionsApi.Symbol

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self, **kwargs):
        self.api_calls.append(kwargs)
        return SimpleNamespace(
            executions=self.return_executions_by_symbol[kwargs["symbol"]]
        )


def make_position(
    *,
    position_id: int = 20,
    symbol=OpenPositionsApi.Symbol.USD_JPY,
    side=OrderApi.Side.BUY,
) -> FakeOpenPosition:
    return FakeOpenPosition(
        position_id=position_id,
        symbol=symbol,
        side=side,
        size=1,
        ordered_size=0,
        price=150.25,
        loss_gain=1250.0,
        total_swap=10.0,
        timestamp=datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
    )


class TestOpenPositionsTool:

    @pytest.fixture(autouse=True)
    def set_up_tear_down(self):
        yield
        FakeOpenPositionsApi.return_pages = []
        FakeOpenPositionsApi.init_calls = []
        FakeOpenPositionsApi.api_calls = []
        FakeLatestExecutionsApi.return_executions_by_symbol = {}
        FakeLatestExecutionsApi.init_calls = []
        FakeLatestExecutionsApi.api_calls = []

    @pytest.mark.anyio
    async def test_registers_open_positions_api_tool_without_credentials_in_schema(
        self, mcp: FastMCP
    ):
        tool = await mcp.get_tool("open_positions_api")

        assert tool is not None
        assert tool.name == "open_positions_api"
        assert set(tool.parameters.get("required", [])) == set()
        assert "api_key" not in tool.parameters["properties"]
        assert "secret_key" not in tool.parameters["properties"]

    @pytest.mark.anyio
    async def test_open_positions_api_uses_registered_credentials_and_maps_response(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        FakeOpenPositionsApi.return_pages = [[make_position()]]
        monkeypatch.setattr(open_positions_tool, "OpenPositionsApi", FakeOpenPositionsApi)
        monkeypatch.setattr(
            open_positions_tool, "LatestExecutionsApi", FakeLatestExecutionsApi
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "open_positions_api",
                {"symbol": "USD_JPY"},
            )

        assert FakeOpenPositionsApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert FakeOpenPositionsApi.api_calls == [
            {"count": 100, "symbol": OpenPositionsApi.Symbol.USD_JPY}
        ]
        assert FakeLatestExecutionsApi.init_calls == []
        assert result.data == [
            {
                "position_id": 20,
                "symbol": "USD_JPY",
                "side": "BUY",
                "size": 1,
                "ordered_size": 0,
                "price": 150.25,
                "loss_gain": 1250.0,
                "total_swap": 10.0,
                "timestamp": "2026-05-05T10:30:00+00:00",
            }
        ]

    @pytest.mark.anyio
    async def test_open_positions_api_fetches_all_pages(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        monkeypatch.setattr(open_positions_tool, "OPEN_POSITIONS_PAGE_SIZE", 2)
        FakeOpenPositionsApi.return_pages = [
            [
                make_position(position_id=30),
                make_position(position_id=20),
            ],
            [make_position(position_id=10)],
        ]
        monkeypatch.setattr(open_positions_tool, "OpenPositionsApi", FakeOpenPositionsApi)

        async with Client(mcp) as client:
            result = await client.call_tool("open_positions_api", {})

        assert FakeOpenPositionsApi.api_calls == [
            {"count": 2},
            {"count": 2, "prev_id": 20},
        ]
        assert [position["position_id"] for position in result.data] == [30, 20, 10]

    @pytest.mark.anyio
    async def test_open_positions_api_passes_symbol_to_open_positions_api(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        FakeOpenPositionsApi.return_pages = [
            [
                make_position(
                    position_id=20,
                    symbol=OpenPositionsApi.Symbol.USD_JPY,
                ),
                make_position(
                    position_id=30,
                    symbol=OpenPositionsApi.Symbol.EUR_JPY,
                ),
            ]
        ]
        monkeypatch.setattr(open_positions_tool, "OpenPositionsApi", FakeOpenPositionsApi)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "open_positions_api",
                {"symbol": "USD_JPY"},
            )

        assert FakeOpenPositionsApi.api_calls == [
            {"count": 100, "symbol": OpenPositionsApi.Symbol.USD_JPY}
        ]
        assert [position["symbol"] for position in result.data] == [
            "USD_JPY",
            "EUR_JPY",
        ]

    @pytest.mark.anyio
    async def test_open_positions_api_filters_by_latest_execution_client_order_id_prefix(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        usd_position = make_position(
            position_id=20,
            symbol=OpenPositionsApi.Symbol.USD_JPY,
        )
        eur_position = make_position(
            position_id=30,
            symbol=OpenPositionsApi.Symbol.EUR_JPY,
            side=OrderApi.Side.SELL,
        )
        FakeOpenPositionsApi.return_pages = [[usd_position, eur_position]]
        FakeLatestExecutionsApi.return_executions_by_symbol = {
            OpenPositionsApi.Symbol.USD_JPY: [
                FakeExecution(
                    position_id=20,
                    symbol=OpenPositionsApi.Symbol.USD_JPY,
                    client_order_id="GMOFX20260506010203",
                ),
            ],
            OpenPositionsApi.Symbol.EUR_JPY: [
                FakeExecution(
                    position_id=30,
                    symbol=OpenPositionsApi.Symbol.EUR_JPY,
                    client_order_id="OTHER20260506010203",
                ),
            ],
        }
        monkeypatch.setattr(open_positions_tool, "OpenPositionsApi", FakeOpenPositionsApi)
        monkeypatch.setattr(
            open_positions_tool, "LatestExecutionsApi", FakeLatestExecutionsApi
        )
        mcp_instance = construct_mcp(client_order_id_prefix="GMOFX")

        async with Client(mcp_instance) as client:
            result = await client.call_tool("open_positions_api", {})

        assert FakeLatestExecutionsApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert FakeLatestExecutionsApi.api_calls == [
            {"symbol": OpenPositionsApi.Symbol.EUR_JPY, "count": 100},
            {"symbol": OpenPositionsApi.Symbol.USD_JPY, "count": 100},
        ]
        assert [position["position_id"] for position in result.data] == [20]
