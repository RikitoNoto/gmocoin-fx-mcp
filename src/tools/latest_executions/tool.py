from typing import Optional

from fastmcp import FastMCP
from gmo_fx.api.latest_executions import LatestExecutionsApi


def _map_execution(execution) -> dict[str, str | int | float | None]:
    return {
        "amount": execution.amount,
        "execution_id": execution.execution_id,
        "client_order_id": execution.client_order_id,
        "order_id": execution.order_id,
        "position_id": execution.position_id,
        "symbol": execution.symbol.value,
        "side": execution.side.value,
        "settle_type": execution.settle_type.value,
        "size": execution.size,
        "price": execution.price,
        "loss_gain": execution.loss_gain,
        "fee": execution.fee,
        "settled_swap": execution.settled_swap,
        "timestamp": execution.timestamp.isoformat(),
    }


def register_latest_executions_tools(
    mcp: FastMCP,
    api_key: str,
    secret_key: str,
    client_order_id_prefix: str | None = None,
) -> None:
    @mcp.tool()
    def latest_executions_api(
        symbol: LatestExecutionsApi.Symbol,
        count: Optional[int] = None,
    ) -> list[dict[str, str | int | float | None]]:
        """GMO Coin FXの最新約定一覧を取得します。"""
        api = LatestExecutionsApi(api_key=api_key, secret_key=secret_key)

        response = api(symbol=symbol, **({"count": count} if count is not None else {}))
        executions = response.executions

        if client_order_id_prefix is not None:
            executions = [
                execution
                for execution in executions
                if execution.client_order_id is not None
                and execution.client_order_id.startswith(client_order_id_prefix)
            ]

        return [_map_execution(execution) for execution in executions]
