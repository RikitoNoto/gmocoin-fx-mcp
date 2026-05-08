from dataclasses import dataclass
from types import SimpleNamespace

import pytest
from fastmcp import Client, FastMCP

from tools.cancel_orders import register_cancel_orders_tools
import tools.cancel_orders.tool as cancel_orders_tool


@dataclass
class FakeCancelOrder:
    root_order_id: int
    client_order_id: str | None = None


def construct_mcp():
    mcp = FastMCP("test")
    register_cancel_orders_tools(
        mcp,
        api_key="test-key",
        secret_key="test-secret",
    )
    return mcp


@pytest.fixture
def mcp():
    return construct_mcp()


class FakeCancelOrdersApi:
    return_cancel_orders: list[FakeCancelOrder] = []
    init_calls: list[dict] = []
    api_calls: list[dict] = []

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self, **kwargs):
        self.api_calls.append(kwargs)
        return SimpleNamespace(cancel_orders=self.return_cancel_orders)


def construct_fake_cancel_orders_api(
    cancel_orders: list[FakeCancelOrder] | None = None,
):
    if cancel_orders is None:
        cancel_orders = [
            FakeCancelOrder(root_order_id=1001, client_order_id="client-1"),
            FakeCancelOrder(root_order_id=1002, client_order_id=None),
        ]
    FakeCancelOrdersApi.return_cancel_orders = cancel_orders
    return FakeCancelOrdersApi


class TestCancelOrdersTool:
    @pytest.fixture(autouse=True)
    def set_up_tear_down(self):
        yield
        FakeCancelOrdersApi.init_calls = []
        FakeCancelOrdersApi.api_calls = []
        FakeCancelOrdersApi.return_cancel_orders = []

    @pytest.mark.anyio
    async def test_registers_cancel_orders_api_tool_without_credentials_in_schema(
        self, mcp: FastMCP
    ):
        tool = await mcp.get_tool("cancel_orders_api")

        assert tool is not None
        assert tool.name == "cancel_orders_api"
        assert set(tool.parameters.get("required", [])) == set()
        assert "root_order_ids" in tool.parameters["properties"]
        assert "client_order_ids" in tool.parameters["properties"]
        assert "api_key" not in tool.parameters["properties"]
        assert "secret_key" not in tool.parameters["properties"]

    @pytest.mark.anyio
    async def test_cancel_orders_api_uses_root_order_ids_and_maps_success_response(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_cancel_orders_api()
        monkeypatch.setattr(cancel_orders_tool, "CancelOrdersApi", FakeCancelOrdersApi)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "cancel_orders_api",
                {"root_order_ids": [1001, 1002]},
            )

        assert FakeCancelOrdersApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert FakeCancelOrdersApi.api_calls == [
            {"root_order_ids": [1001, 1002], "client_order_ids": None}
        ]
        assert result.data == {
            "success": [
                {"root_order_id": 1001, "client_order_id": "client-1"},
                {"root_order_id": 1002, "client_order_id": None},
            ]
        }

    @pytest.mark.anyio
    async def test_cancel_orders_api_uses_client_order_ids(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_cancel_orders_api(
            [FakeCancelOrder(root_order_id=2001, client_order_id="client-1")]
        )
        monkeypatch.setattr(cancel_orders_tool, "CancelOrdersApi", FakeCancelOrdersApi)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "cancel_orders_api",
                {"client_order_ids": ["client-1"]},
            )

        assert FakeCancelOrdersApi.api_calls == [
            {"root_order_ids": None, "client_order_ids": ["client-1"]}
        ]
        assert result.data == {
            "success": [{"root_order_id": 2001, "client_order_id": "client-1"}]
        }

    @pytest.mark.anyio
    async def test_should_fail_cancel_orders_when_no_ids_specified(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_cancel_orders_api()
        monkeypatch.setattr(cancel_orders_tool, "CancelOrdersApi", FakeCancelOrdersApi)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "cancel_orders_api",
                {},
                raise_on_error=False,
            )

        assert result.is_error is True
        assert result.content[0].text == "Specify either root_order_ids or client_order_ids."
        assert FakeCancelOrdersApi.api_calls == []

    @pytest.mark.anyio
    async def test_should_fail_cancel_orders_when_both_id_types_specified(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        construct_fake_cancel_orders_api()
        monkeypatch.setattr(cancel_orders_tool, "CancelOrdersApi", FakeCancelOrdersApi)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "cancel_orders_api",
                {"root_order_ids": [1001], "client_order_ids": ["client-1"]},
                raise_on_error=False,
            )

        assert result.is_error is True
        assert (
            result.content[0].text
            == "Specify only one of root_order_ids or client_order_ids, not both."
        )
        assert FakeCancelOrdersApi.api_calls == []

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        ("arguments", "message"),
        [
            ({"root_order_ids": []}, "root_order_ids must contain at least 1 ID."),
            ({"client_order_ids": []}, "client_order_ids must contain at least 1 ID."),
            (
                {"root_order_ids": list(range(1, 12))},
                "root_order_ids must contain at most 10 IDs.",
            ),
            (
                {"client_order_ids": [f"client-{i}" for i in range(1, 12)]},
                "client_order_ids must contain at most 10 IDs.",
            ),
        ],
    )
    async def test_should_fail_cancel_orders_when_id_count_is_invalid(
        self,
        arguments: dict,
        message: str,
        monkeypatch: pytest.MonkeyPatch,
        mcp: FastMCP,
    ):
        construct_fake_cancel_orders_api()
        monkeypatch.setattr(cancel_orders_tool, "CancelOrdersApi", FakeCancelOrdersApi)

        async with Client(mcp) as client:
            result = await client.call_tool(
                "cancel_orders_api",
                arguments,
                raise_on_error=False,
            )

        assert result.is_error is True
        assert result.content[0].text == message
        assert FakeCancelOrdersApi.api_calls == []
