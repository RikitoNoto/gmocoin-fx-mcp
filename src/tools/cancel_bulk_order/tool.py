from typing import Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from gmo_fx.api.cancel_bulk_order import CancelBulkOrderApi


def _map_cancel_bulk_order(order) -> dict[str, str | int | None]:
    return {
        "root_order_id": order.root_order_id,
        "client_order_id": order.client_order_id,
    }


def _validate_symbols(
    symbols: list[CancelBulkOrderApi.Symbol],
    symbol_limits: set[CancelBulkOrderApi.Symbol] | None,
) -> None:
    if len(symbols) == 0:
        raise ToolError("symbols must contain at least 1 symbol.")

    if symbol_limits is None:
        return

    invalid_symbols = sorted(
        symbol.value for symbol in symbols if symbol not in symbol_limits
    )
    if invalid_symbols:
        allow_symbols = ", ".join(sorted(symbol.value for symbol in symbol_limits))
        raise ToolError(
            f"symbols must be one of: {allow_symbols}. "
            f"Invalid symbols: {', '.join(invalid_symbols)}"
        )


def register_cancel_bulk_order_tools(
    mcp: FastMCP,
    api_key: str,
    secret_key: str,
    symbol_limits: set[CancelBulkOrderApi.Symbol] | None = None,
) -> None:
    @mcp.tool()
    def cancel_bulk_order_api(
        symbols: list[CancelBulkOrderApi.Symbol],
        side: Optional[CancelBulkOrderApi.Side] = None,
        settle_type: Optional[CancelBulkOrderApi.SettleType] = None,
    ) -> dict[str, list[dict[str, str | int | None]]]:
        """GMO Coin FXの注文を銘柄などの条件で一括キャンセルします。"""
        _validate_symbols(symbols=symbols, symbol_limits=symbol_limits)

        api = CancelBulkOrderApi(api_key=api_key, secret_key=secret_key)
        response = api(
            symbols=symbols,
            side=side,
            settle_type=settle_type,
        )

        return {
            "success": [
                _map_cancel_bulk_order(order)
                for order in response.cancel_bulk_orders
            ]
        }
