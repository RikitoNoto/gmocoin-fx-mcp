from typing import Optional

from fastmcp import FastMCP
from gmo_fx.api.latest_executions import LatestExecutionsApi
from gmo_fx.api.open_positions import OpenPositionsApi

OPEN_POSITIONS_PAGE_SIZE = 100
LATEST_EXECUTIONS_COUNT = 100


def _map_open_position(position) -> dict[str, str | int | float]:
    return {
        "position_id": position.position_id,
        "symbol": position.symbol.value,
        "side": position.side.value,
        "size": position.size,
        "ordered_size": position.ordered_size,
        "price": position.price,
        "loss_gain": position.loss_gain,
        "total_swap": position.total_swap,
        "timestamp": position.timestamp.isoformat(),
    }


def _fetch_all_open_positions(
    api: OpenPositionsApi,
    symbol: OpenPositionsApi.Symbol | None,
) -> list:
    open_positions = []
    prev_id = None

    while True:
        kwargs = {"count": OPEN_POSITIONS_PAGE_SIZE}
        if symbol is not None:
            kwargs["symbol"] = symbol
        if prev_id is not None:
            kwargs["prev_id"] = prev_id

        response = api(**kwargs)
        page = response.open_positions
        open_positions.extend(page)

        if len(page) < OPEN_POSITIONS_PAGE_SIZE:
            break
        prev_id = page[-1].position_id

    return open_positions


def _filter_positions_by_client_order_id_prefix(
    positions: list,
    api: LatestExecutionsApi,
    client_order_id_prefix: str,
) -> list:
    position_symbols = sorted(
        {position.symbol for position in positions},
        key=lambda symbol: symbol.value,
    )
    matching_position_ids = set()

    for symbol in position_symbols:
        response = api(symbol=symbol, count=LATEST_EXECUTIONS_COUNT)
        matching_position_ids.update(
            execution.position_id
            for execution in response.executions
            if execution.client_order_id is not None
            and execution.client_order_id.startswith(client_order_id_prefix)
        )

    return [
        position
        for position in positions
        if position.position_id in matching_position_ids
    ]


def register_open_positions_tools(
    mcp: FastMCP,
    api_key: str,
    secret_key: str,
    client_order_id_prefix: str | None = None,
) -> None:
    @mcp.tool()
    def open_positions_api(
        symbol: Optional[OpenPositionsApi.Symbol] = None,
    ) -> list[dict[str, str | int | float]]:
        """GMO Coin FXの建玉一覧を取得します。"""
        open_positions_api = OpenPositionsApi(api_key=api_key, secret_key=secret_key)
        positions = _fetch_all_open_positions(open_positions_api, symbol)

        if client_order_id_prefix is not None:
            latest_executions_api = LatestExecutionsApi(
                api_key=api_key,
                secret_key=secret_key,
            )
            positions = _filter_positions_by_client_order_id_prefix(
                positions,
                latest_executions_api,
                client_order_id_prefix,
            )

        return [_map_open_position(position) for position in positions]
