from typing import Optional

from fastmcp import FastMCP
from gmo_fx.api.active_orders import ActiveOrdersApi


def _map_active_order(order) -> dict[str, str | int | float | None]:
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


def register_active_orders_tools(
    mcp: FastMCP,
    api_key: str,
    secret_key: str,
    client_order_id_prefix: str | None = None,
) -> None:
    @mcp.tool()
    def active_orders_api(
        symbol: Optional[ActiveOrdersApi.Symbol] = None,
        prev_id: Optional[int] = None,
        count: Optional[int] = None,
    ) -> list[dict[str, str | int | float | None]]:
        """GMO Coin FXの有効注文一覧を取得します。"""
        api = ActiveOrdersApi(api_key=api_key, secret_key=secret_key)

        response = api(symbol=symbol, prev_id=prev_id, count=count)
        active_orders = response.active_orders

        if client_order_id_prefix is not None:
            active_orders = [
                order
                for order in active_orders
                if order.client_order_id is not None
                and order.client_order_id.startswith(client_order_id_prefix)
            ]

        return [_map_active_order(order) for order in active_orders]
