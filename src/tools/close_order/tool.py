from typing import Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from gmo_fx.api.close_order import CloseOrderApi
from tools.client_order_id import ClientOrderIdGenerator


def _map_close_order(order) -> dict[str, str | int | float | None]:
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
        "cancel_type": order.cancel_type.value if order.cancel_type else None,
        "expiry": order.expiry.isoformat() if order.expiry else None,
        "timestamp": order.timestamp.isoformat(),
    }


def register_close_order_tools(
    mcp: FastMCP,
    api_key: str,
    secret_key: str,
    size_limit: int | None = None,
    symbol_limits: set[CloseOrderApi.Symbol] | None = None,
    client_order_id_prefix: str | None = None,
) -> None:
    client_order_id_generator = (
        ClientOrderIdGenerator(client_order_id_prefix)
        if client_order_id_prefix is not None
        else None
    )

    @mcp.tool()
    def close_order_api(
        symbol: CloseOrderApi.Symbol,
        side: CloseOrderApi.Side,
        execution_type: CloseOrderApi.ExecutionType,
        client_order_id: Optional[str] = None,
        size: Optional[int] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        lower_bound: Optional[float] = None,
        upper_bound: Optional[float] = None,
        settle_position: Optional[list[CloseOrderApi.SettlePosition]] = None,
    ) -> list[dict[str, str | int | float | None]]:
        """GMO Coin FXの決済注文を実行します。"""
        api = CloseOrderApi(api_key=api_key, secret_key=secret_key)

        if symbol_limits is not None and symbol not in symbol_limits:
            allow_symbols = ", ".join(sorted(s.value for s in symbol_limits))
            raise ToolError(f"symbol must be one of: {allow_symbols}")

        if size_limit is not None and size is not None and size > size_limit:
            raise ToolError(f"size must be less than or equal to {size_limit}")

        if client_order_id_generator is not None:
            client_order_id = client_order_id_generator.generate()

        response = api(
            symbol=symbol,
            side=side,
            execution_type=execution_type,
            client_order_id=client_order_id,
            size=size,
            limit_price=limit_price,
            stop_price=stop_price,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            settle_position=settle_position,
        )

        return [_map_close_order(order) for order in response.close_orders]
