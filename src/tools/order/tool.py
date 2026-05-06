import re
from datetime import UTC, datetime
from typing import Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from gmo_fx.api.order import OrderApi

_CLIENT_ORDER_ID_MAX_LENGTH = 36
_CLIENT_ORDER_ID_DATETIME_FORMAT = "%Y%m%d%H%M%S"
_CLIENT_ORDER_ID_DATETIME_LENGTH = 14
# GMO Coin FX limits client_order_id to 36 characters. Reserve the final
# 14 characters for the yyyyMMddHHmmss timestamp suffix used for uniqueness.
_CLIENT_ORDER_ID_PREFIX_MAX_LENGTH = (
    _CLIENT_ORDER_ID_MAX_LENGTH - _CLIENT_ORDER_ID_DATETIME_LENGTH
)
_CLIENT_ORDER_ID_PREFIX_PATTERN = re.compile(r"^[A-Za-z0-9]+$")


class _ClientOrderIdGenerator:
    def __init__(self, prefix: str):
        self._validate_prefix(prefix)
        self.prefix = prefix

    @staticmethod
    def _validate_prefix(prefix: str) -> None:
        if len(prefix) > _CLIENT_ORDER_ID_PREFIX_MAX_LENGTH:
            raise ValueError(
                "client_order_id_prefix must be less than or equal to "
                f"{_CLIENT_ORDER_ID_PREFIX_MAX_LENGTH} characters"
            )
        if not _CLIENT_ORDER_ID_PREFIX_PATTERN.fullmatch(prefix):
            raise ValueError(
                "client_order_id_prefix must contain only ASCII letters and numbers"
            )

    def generate(self) -> str:
        now = datetime.now(UTC)

        return f"{self.prefix}{now.strftime(_CLIENT_ORDER_ID_DATETIME_FORMAT)}"


def register_order_tools(
    mcp: FastMCP,
    api_key: str,
    secret_key: str,
    size_limit: int | None = None,
    symbol_limits: set[OrderApi.Symbol] | None = None,
    client_order_id_prefix: str | None = None,
) -> None:
    client_order_id_generator = (
        _ClientOrderIdGenerator(client_order_id_prefix)
        if client_order_id_prefix is not None
        else None
    )

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

        if symbol_limits is not None and symbol not in symbol_limits:
            allow_symbols = ", ".join(sorted(s.value for s in symbol_limits))
            raise ToolError(f"symbol must be one of: {allow_symbols}")

        if size_limit is not None and size > size_limit:
            raise ToolError(f"size must be less than or equal to {size_limit}")

        if client_order_id_generator is not None:
            client_order_id = client_order_id_generator.generate()

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
