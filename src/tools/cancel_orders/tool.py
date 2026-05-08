from typing import Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from gmo_fx.api.cancel_orders import CancelOrdersApi

MAX_CANCEL_ORDER_IDS = 10


def _map_cancel_order(order) -> dict[str, str | int | None]:
    return {
        "root_order_id": order.root_order_id,
        "client_order_id": order.client_order_id,
    }


def _validate_cancel_order_ids(
    root_order_ids: list[int] | None,
    client_order_ids: list[str] | None,
) -> None:
    if root_order_ids is None and client_order_ids is None:
        raise ToolError("Specify either root_order_ids or client_order_ids.")

    if root_order_ids is not None and client_order_ids is not None:
        raise ToolError(
            "Specify only one of root_order_ids or client_order_ids, not both."
        )

    ids = root_order_ids if root_order_ids is not None else client_order_ids
    name = "root_order_ids" if root_order_ids is not None else "client_order_ids"

    if ids is None or len(ids) == 0:
        raise ToolError(f"{name} must contain at least 1 ID.")

    if len(ids) > MAX_CANCEL_ORDER_IDS:
        raise ToolError(f"{name} must contain at most {MAX_CANCEL_ORDER_IDS} IDs.")


def register_cancel_orders_tools(
    mcp: FastMCP,
    api_key: str,
    secret_key: str,
) -> None:
    @mcp.tool()
    def cancel_orders_api(
        root_order_ids: Optional[list[int]] = None,
        client_order_ids: Optional[list[str]] = None,
    ) -> dict[str, list[dict[str, str | int | None]]]:
        """GMO Coin FXの注文を最大10件までまとめてキャンセルします。"""
        api = CancelOrdersApi(api_key=api_key, secret_key=secret_key)

        _validate_cancel_order_ids(
            root_order_ids=root_order_ids,
            client_order_ids=client_order_ids,
        )

        response = api(
            root_order_ids=root_order_ids,
            client_order_ids=client_order_ids,
        )

        return {
            "success": [_map_cancel_order(order) for order in response.cancel_orders]
        }
