from typing import Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from gmo_fx.api.change_ifd_order import ChangeIfdOrderApi


def _map_change_ifd_order(order) -> dict[str, str | int | float | None]:
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


def _validate_positive_number(value: int | float, name: str) -> None:
    if value <= 0:
        raise ToolError(f"{name} must be greater than 0")


def _validate_exactly_one_order_id(
    root_order_id: int | None, client_order_id: str | None
) -> None:
    if (root_order_id is None) == (client_order_id is None):
        raise ToolError("Specify exactly one of root_order_id or client_order_id")

    if client_order_id == "":
        raise ToolError("client_order_id must not be empty")


def _validate_change_ifd_prices(
    first_price: float | None, second_price: float | None
) -> None:
    prices = {"first_price": first_price, "second_price": second_price}
    if all(value is None for value in prices.values()):
        raise ToolError("Specify at least one of first_price or second_price")

    for name, value in prices.items():
        if value is not None:
            _validate_positive_number(value, name)


def register_change_ifd_order_tools(
    mcp: FastMCP,
    api_key: str,
    secret_key: str,
) -> None:
    @mcp.tool()
    def change_ifd_order_api(
        root_order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
        first_price: Optional[float] = None,
        second_price: Optional[float] = None,
    ) -> list[dict[str, str | int | float | None]]:
        """GMO Coin FXのIFD注文を変更します。"""
        _validate_exactly_one_order_id(root_order_id, client_order_id)
        _validate_change_ifd_prices(first_price, second_price)

        api = ChangeIfdOrderApi(api_key=api_key, secret_key=secret_key)
        response = api(
            root_order_id=root_order_id,
            client_order_id=client_order_id,
            first_price=first_price,
            second_price=second_price,
        )

        return [_map_change_ifd_order(order) for order in response.orders]
