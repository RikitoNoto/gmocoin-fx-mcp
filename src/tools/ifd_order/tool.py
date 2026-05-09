from typing import Optional, TypeVar

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from gmo_fx.api.ifd_order import IFDOrderApi
from utils.client_order_id import ClientOrderIdGenerator


T = TypeVar("T")


def _map_ifd_order(order) -> dict[str, str | int | float | None]:
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
        "expiry": order.expiry.isoformat() if order.expiry else None,
        "timestamp": order.timestamp.isoformat(),
    }


def _require_value(value: T | None, name: str) -> T:
    if value is None:
        raise ToolError(f"{name} is required for IFD order")
    return value


def _validate_positive_number(value: int | float, name: str) -> None:
    if value <= 0:
        raise ToolError(f"{name} must be greater than 0")


def register_ifd_order_tools(
    mcp: FastMCP,
    api_key: str,
    secret_key: str,
    size_limit: int | None = None,
    symbol_limits: set[IFDOrderApi.Symbol] | None = None,
    client_order_id_prefix: str | None = None,
) -> None:
    client_order_id_generator = (
        ClientOrderIdGenerator(client_order_id_prefix)
        if client_order_id_prefix is not None
        else None
    )

    @mcp.tool()
    def ifd_order_api(
        symbol: Optional[IFDOrderApi.Symbol] = None,
        client_order_id: Optional[str] = None,
        first_side: Optional[IFDOrderApi.Side] = None,
        first_execution_type: Optional[IFDOrderApi.ExecutionType] = None,
        first_size: Optional[int] = None,
        first_price: Optional[float] = None,
        second_execution_type: Optional[IFDOrderApi.ExecutionType] = None,
        second_size: Optional[int] = None,
        second_price: Optional[float] = None,
    ) -> list[dict[str, str | int | float | None]]:
        """GMO Coin FXのIFD注文を実行します。"""
        api = IFDOrderApi(api_key=api_key, secret_key=secret_key)

        symbol = _require_value(symbol, "symbol")
        first_side = _require_value(first_side, "first_side")
        first_execution_type = _require_value(
            first_execution_type, "first_execution_type"
        )
        first_size = _require_value(first_size, "first_size")
        first_price = _require_value(first_price, "first_price")
        second_execution_type = _require_value(
            second_execution_type, "second_execution_type"
        )
        second_size = _require_value(second_size, "second_size")
        second_price = _require_value(second_price, "second_price")

        if symbol_limits is not None and symbol not in symbol_limits:
            allow_symbols = ", ".join(sorted(s.value for s in symbol_limits))
            raise ToolError(f"symbol must be one of: {allow_symbols}")

        for name, value in {
            "first_size": first_size,
            "first_price": first_price,
            "second_size": second_size,
            "second_price": second_price,
        }.items():
            _validate_positive_number(value, name)

        if size_limit is not None:
            for name, value in {
                "first_size": first_size,
                "second_size": second_size,
            }.items():
                if value > size_limit:
                    raise ToolError(f"{name} must be less than or equal to {size_limit}")

        if client_order_id_generator is not None:
            client_order_id = client_order_id_generator.generate()

        response = api(
            symbol=symbol,
            client_order_id=client_order_id,
            first_side=first_side,
            first_execution_type=first_execution_type,
            first_size=first_size,
            first_price=first_price,
            second_execution_type=second_execution_type,
            second_size=second_size,
            second_price=second_price,
        )

        return [_map_ifd_order(order) for order in response.ifd_orders]
