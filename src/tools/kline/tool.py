from datetime import datetime
from typing import Literal

from fastmcp import FastMCP
from gmo_fx.api.klines import KlinesApi


def register_kline_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def kline_api(
        symbol: KlinesApi.Symbol,
        price_type: Literal["BID", "ASK"],
        interval: KlinesApi.KlineInterval,
        date: str,
    ) -> list[dict[str, str | float]]:
        """GMO CoinのKline(ローソク足)を取得します。dateはYYYY-MM-DD形式で指定してください。"""
        api = KlinesApi()
        parsed_date = datetime.strptime(date, "%Y-%m-%d")

        response = api(
            symbol=symbol,
            price_type=price_type,
            interval=interval,
            date=parsed_date,
        )

        return [
            {
                "open_time": kline.open_time.isoformat(),
                "open": kline.open,
                "high": kline.high,
                "low": kline.low,
                "close": kline.close,
            }
            for kline in response.klines
        ]
