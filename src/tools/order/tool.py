from typing import Optional

from fastmcp import FastMCP
from gmo_fx.api.order import OrderApi


def register_order_tools(mcp: FastMCP, api_key: str, secret_key: str) -> None:
    @mcp.tool()
    def order_api(
        symbol: OrderApi.Symbol,
        side: OrderApi.Side,
        size: int,
        execution_type: OrderApi.ExecutionType,
        client_order_id: Optional[str] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        lower_bound: Optional[float] = None,
        upper_bound: Optional[float] = None,
    ) -> list[dict[str, str | int | float | None]]:
        """GMO Coin FXの新規注文を実行します。"""
        api = OrderApi(api_key=api_key, secret_key=secret_key)

        response = api(
            symbol=symbol,
            side=side,
            size=size,
            execution_type=execution_type,
            client_order_id=client_order_id,
            limit_price=limit_price,
            stop_price=stop_price,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )

        return [
            {
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
                "cancel_type": order.cancel_type.value if order.cancel_type else None,
                "expiry": order.expiry.isoformat() if order.expiry else None,
                "timestamp": order.timestamp.isoformat(),
            }
            for order in response.orders
        ]
