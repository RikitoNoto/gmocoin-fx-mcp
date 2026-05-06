from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP
from gmo_fx.api.latest_executions import LatestExecutionsApi
from gmo_fx.api.order import OrderApi

from tools.latest_executions import register_latest_executions_tools
import tools.latest_executions.tool as latest_executions_tool


@dataclass
class FakeExecution:
    amount: float
    execution_id: int
    client_order_id: str | None
    order_id: int
    position_id: int
    symbol: object
    side: object
    settle_type: object
    size: int
    price: float
    loss_gain: float
    fee: float
    settled_swap: float
    timestamp: datetime


def construct_mcp(client_order_id_prefix: str | None = None):
    mcp = FastMCP("test")
    register_latest_executions_tools(
        mcp,
        api_key="test-key",
        secret_key="test-secret",
        client_order_id_prefix=client_order_id_prefix,
    )
    return mcp


@pytest.fixture
def mcp():
    return construct_mcp()


class FakeLatestExecutionsApi:
    return_executions: list[FakeExecution] = []
    init_calls: list[dict] = []
    api_calls: list[dict] = []
    Symbol = LatestExecutionsApi.Symbol

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self, **kwargs):
        self.api_calls.append(kwargs)
        return SimpleNamespace(executions=self.return_executions)


def make_execution(
    *,
    execution_id: int = 100,
    client_order_id: str | None = "c1",
    symbol=LatestExecutionsApi.Symbol.USD_JPY,
    side=OrderApi.Side.BUY,
) -> FakeExecution:
    return FakeExecution(
        amount=150.25,
        execution_id=execution_id,
        client_order_id=client_order_id,
        order_id=10,
        position_id=20,
        symbol=symbol,
        side=side,
        settle_type=SimpleNamespace(value="OPEN"),
        size=1,
        price=150.25,
        loss_gain=0.0,
        fee=0.0,
        settled_swap=0.0,
        timestamp=datetime(2026, 5, 5, 10, 30, tzinfo=timezone.utc),
    )


def construct_fake_latest_executions_api(
    executions: list[FakeExecution] | None = None,
):
    if executions is None:
        executions = [make_execution()]
    FakeLatestExecutionsApi.return_executions = executions
    return FakeLatestExecutionsApi


class TestLatestExecutionsTool:

    @pytest.fixture(autouse=True)
    def set_up_tear_down(self):
        yield
        FakeLatestExecutionsApi.init_calls = []
        FakeLatestExecutionsApi.api_calls = []
        FakeLatestExecutionsApi.return_executions = []

    @pytest.mark.anyio
    async def test_registers_latest_executions_api_tool_without_credentials_in_schema(
        self, mcp: FastMCP
    ):
        tool = await mcp.get_tool("latest_executions_api")

        assert tool is not None
        assert tool.name == "latest_executions_api"
        assert set(tool.parameters["required"]) == {"symbol"}
        assert "api_key" not in tool.parameters["properties"]
        assert "secret_key" not in tool.parameters["properties"]

    @pytest.mark.anyio
    async def test_latest_executions_api_uses_registered_credentials_and_maps_response(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_latest_executions_api()
        monkeypatch.setattr(
            latest_executions_tool, "LatestExecutionsApi", FakeLatestExecutionsApi
        )

        async with Client(mcp) as client:
            result = await client.call_tool(
                "latest_executions_api",
                {
                    "symbol": "USD_JPY",
                    "count": 20,
                },
            )

        assert FakeLatestExecutionsApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert FakeLatestExecutionsApi.api_calls == [
            {
                "symbol": LatestExecutionsApi.Symbol.USD_JPY,
                "count": 20,
            }
        ]
        assert result.data == [
            {
                "amount": 150.25,
                "execution_id": 100,
                "client_order_id": "c1",
                "order_id": 10,
                "position_id": 20,
                "symbol": "USD_JPY",
                "side": "BUY",
                "settle_type": "OPEN",
                "size": 1,
                "price": 150.25,
                "loss_gain": 0.0,
                "fee": 0.0,
                "settled_swap": 0.0,
                "timestamp": "2026-05-05T10:30:00+00:00",
            }
        ]

    @pytest.mark.anyio
    async def test_latest_executions_api_omits_count_when_not_requested(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_latest_executions_api()
        monkeypatch.setattr(
            latest_executions_tool, "LatestExecutionsApi", FakeLatestExecutionsApi
        )

        async with Client(mcp) as client:
            await client.call_tool(
                "latest_executions_api",
                {
                    "symbol": "USD_JPY",
                },
            )

        assert FakeLatestExecutionsApi.api_calls == [
            {"symbol": LatestExecutionsApi.Symbol.USD_JPY}
        ]

    @pytest.mark.anyio
    async def test_latest_executions_api_filters_by_configured_client_order_id_prefix(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        construct_fake_latest_executions_api(
            [
                make_execution(
                    execution_id=100,
                    client_order_id="GMOFX20260506010203",
                ),
                make_execution(
                    execution_id=200,
                    client_order_id="OTHER20260506010203",
                    side=OrderApi.Side.SELL,
                ),
                make_execution(
                    execution_id=300,
                    client_order_id=None,
                ),
            ]
        )
        monkeypatch.setattr(
            latest_executions_tool, "LatestExecutionsApi", FakeLatestExecutionsApi
        )
        mcp_instance = construct_mcp(client_order_id_prefix="GMOFX")

        async with Client(mcp_instance) as client:
            result = await client.call_tool(
                "latest_executions_api",
                {
                    "symbol": "USD_JPY",
                    "count": 100,
                },
            )

        assert result.data == [
            {
                "amount": 150.25,
                "execution_id": 100,
                "client_order_id": "GMOFX20260506010203",
                "order_id": 10,
                "position_id": 20,
                "symbol": "USD_JPY",
                "side": "BUY",
                "settle_type": "OPEN",
                "size": 1,
                "price": 150.25,
                "loss_gain": 0.0,
                "fee": 0.0,
                "settled_swap": 0.0,
                "timestamp": "2026-05-05T10:30:00+00:00",
            }
        ]
