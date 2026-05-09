from typing import Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from gmo_fx.api.change_order import ChangeOrderApi


def _map_change_order(order) -> dict[str, str | int | float | None]:
    return {
        "root_order_id": order.root_order_id,
        "client_order_id": order.client_order_id,
        "order_id": order.order_id,
        "symbol": order.symbol.value,
        "side": order.side.value,
        "order_type": order.order_type.value,
        "execution_type": order.execution_type.value,
        "settle_type": order.settle_type.value,
        "size": order.size,
        "price": order.price,
        "status": order.status.value,
        "expiry": order.expiry.isoformat(),
        "timestamp": order.timestamp.isoformat(),
    }


def _validate_change_order_target(
    order_id: int | None,
    client_order_id: str | None,
) -> None:
    if (order_id is None) == (client_order_id is None):
        raise ToolError("Specify exactly one of order_id or client_order_id")

    if client_order_id == "":
        raise ToolError("client_order_id must not be empty")


def register_change_order_tools(
    mcp: FastMCP,
    api_key: str,
    secret_key: str,
) -> None:
    @mcp.tool()
    def change_order_api(
        price: float,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> list[dict[str, str | int | float | None]]:
        """GMO Coin FXの通常注文価格を変更します。"""
        _validate_change_order_target(
            order_id=order_id,
            client_order_id=client_order_id,
        )

        api = ChangeOrderApi(api_key=api_key, secret_key=secret_key)
        response = api(
            price=price,
            order_id=order_id,
            client_order_id=client_order_id,
        )

        return [_map_change_order(order) for order in response.orders]
