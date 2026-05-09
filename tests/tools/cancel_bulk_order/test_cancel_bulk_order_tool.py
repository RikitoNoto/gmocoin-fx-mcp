from dataclasses import dataclass
from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP
from gmo_fx.api.cancel_bulk_order import CancelBulkOrderApi

from tools.cancel_bulk_order import register_cancel_bulk_order_tools
import tools.cancel_bulk_order.tool as cancel_bulk_order_tool


@dataclass
class FakeCancelBulkOrder:
    root_order_id: int
    client_order_id: str | None = None


def construct_mcp(
    symbol_limits: set[CancelBulkOrderApi.Symbol] | None = None,
):
    mcp = FastMCP("test")
    register_cancel_bulk_order_tools(
        mcp,
        api_key="test-key",
        secret_key="test-secret",
        symbol_limits=symbol_limits,
    )
    return mcp


@pytest.fixture
def mcp():
    return construct_mcp()


class FakeCancelBulkOrderApi:
    return_cancel_bulk_orders: list[FakeCancelBulkOrder] = []
    init_calls: list[dict] = []
    api_calls: list[dict] = []
    Symbol = CancelBulkOrderApi.Symbol
    Side = CancelBulkOrderApi.Side
    SettleType = CancelBulkOrderApi.SettleType

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self, **kwargs):
        self.api_calls.append(kwargs)
        return SimpleNamespace(cancel_bulk_orders=self.return_cancel_bulk_orders)


def construct_fake_cancel_bulk_order_api(
    cancel_bulk_orders: list[FakeCancelBulkOrder] | None = None,
):
    if cancel_bulk_orders is None:
        cancel_bulk_orders = [
            FakeCancelBulkOrder(root_order_id=1001, client_order_id="client-1"),
            FakeCancelBulkOrder(root_order_id=1002, client_order_id=None),
        ]
    FakeCancelBulkOrderApi.return_cancel_bulk_orders = cancel_bulk_orders
    return FakeCancelBulkOrderApi


class TestCancelBulkOrderTool:
    @pytest.fixture(autouse=True)
    def set_up_tear_down(self):
        yield
        FakeCancelBulkOrderApi.init_calls = []
        FakeCancelBulkOrderApi.api_calls = []
        FakeCancelBulkOrderApi.return_cancel_bulk_orders = []

    @pytest.mark.anyio
    async def test_registers_cancel_bulk_order_api_tool_without_credentials_in_schema(
        self, mcp: FastMCP
    ):
        tool = await mcp.get_tool("cancel_bulk_order_api")

        assert tool is not None
        assert tool.name == "cancel_bulk_order_api"
        assert set(tool.parameters["required"]) == {"symbols"}
        assert "symbols" in tool.parameters["properties"]
        assert "side" in tool.parameters["properties"]
        assert "settle_type" in tool.parameters["properties"]
        assert "api_key" not in tool.parameters["properties"]
        assert "secret_key" not in tool.parameters["properties"]

    @pytest.mark.anyio
    async def test_cancel_bulk_order_api_uses_conditions_and_maps_success_response(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_cancel_bulk_order_api()
        monkeypatch.setattr(
            cancel_bulk_order_tool, "CancelBulkOrderApi", FakeCancelBulkOrderApi
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "cancel_bulk_order_api",
                {
                    "symbols": ["USD_JPY", "EUR_JPY"],
                    "side": "BUY",
                    "settle_type": "OPEN",
                },
            )

        assert FakeCancelBulkOrderApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert FakeCancelBulkOrderApi.api_calls == [
            {
                "symbols": [
                    CancelBulkOrderApi.Symbol.USD_JPY,
                    CancelBulkOrderApi.Symbol.EUR_JPY,
                ],
                "side": CancelBulkOrderApi.Side.BUY,
                "settle_type": CancelBulkOrderApi.SettleType.OPEN,
            }
        ]
        assert result.data == {
            "success": [
                {"root_order_id": 1001, "client_order_id": "client-1"},
                {"root_order_id": 1002, "client_order_id": None},
            ]
        }

    @pytest.mark.anyio
    async def test_cancel_bulk_order_api_accepts_only_required_symbols(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_cancel_bulk_order_api(
            [FakeCancelBulkOrder(root_order_id=2001, client_order_id="client-1")]
        )
        monkeypatch.setattr(
            cancel_bulk_order_tool, "CancelBulkOrderApi", FakeCancelBulkOrderApi
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "cancel_bulk_order_api",
                {"symbols": ["USD_JPY"]},
            )

        assert FakeCancelBulkOrderApi.api_calls == [
            {
                "symbols": [CancelBulkOrderApi.Symbol.USD_JPY],
                "side": None,
                "settle_type": None,
            }
        ]
        assert result.data == {
            "success": [{"root_order_id": 2001, "client_order_id": "client-1"}]
        }

    @pytest.mark.anyio
    async def test_should_fail_cancel_bulk_order_when_symbols_empty(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_cancel_bulk_order_api()
        monkeypatch.setattr(
            cancel_bulk_order_tool, "CancelBulkOrderApi", FakeCancelBulkOrderApi
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "cancel_bulk_order_api",
                {"symbols": []},
                raise_on_error=False,
            )

        assert result.is_error is True
        assert result.content[0].text == "symbols must contain at least 1 symbol."
        assert FakeCancelBulkOrderApi.api_calls == []

    @pytest.mark.anyio
    async def test_should_fail_cancel_bulk_order_when_symbol_not_in_limits(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        mcp_instance = construct_mcp(symbol_limits={CancelBulkOrderApi.Symbol.USD_JPY})
        construct_fake_cancel_bulk_order_api()
        monkeypatch.setattr(
            cancel_bulk_order_tool, "CancelBulkOrderApi", FakeCancelBulkOrderApi
        )

        async with Client(mcp_instance) as client:
            result = await client.call_tool(
                "cancel_bulk_order_api",
                {"symbols": ["USD_JPY", "EUR_JPY"]},
                raise_on_error=False,
            )

        assert result.is_error is True
        assert (
            result.content[0].text
            == "symbols must be one of: USD_JPY. Invalid symbols: EUR_JPY"
        )
        assert FakeCancelBulkOrderApi.api_calls == []

    @pytest.mark.anyio
    async def test_should_success_cancel_bulk_order_when_symbols_are_in_limits(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        mcp_instance = construct_mcp(
            symbol_limits={
                CancelBulkOrderApi.Symbol.USD_JPY,
                CancelBulkOrderApi.Symbol.EUR_JPY,
            }
        )
        construct_fake_cancel_bulk_order_api()
        monkeypatch.setattr(
            cancel_bulk_order_tool, "CancelBulkOrderApi", FakeCancelBulkOrderApi
        )

        async with Client(mcp_instance) as client:
            result = await client.call_tool(
                "cancel_bulk_order_api",
                {"symbols": ["USD_JPY", "EUR_JPY"]},
                raise_on_error=False,
            )

        assert result.is_error is False
        assert FakeCancelBulkOrderApi.api_calls != []
