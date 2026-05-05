from typing import Optional

from fastmcp import FastMCP
from gmo_fx.api.change_oco_order import ChangeOcoOrderApi


def register_ifdoco_order_tools(mcp: FastMCP, api_key: str, secret_key: str) -> None:
    @mcp.tool()
    def change_oco_order_api(
        root_order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> dict[str, str]:
        """GMO Coin FXのOCO注文変更を実行します。"""
        api = ChangeOcoOrderApi(api_key=api_key, secret_key=secret_key)

        response = api(
            root_order_id=root_order_id,
            client_order_id=client_order_id,
            limit_price=limit_price,
            stop_price=stop_price,
        )

        return {
            "root_order_id": str(response.root_order_id),
        }
