import os

from fastmcp import FastMCP
from dotenv import load_dotenv
from resources.asset_balance import register_asset_balance_resources
from tools.active_orders import register_active_orders_tools
from tools.ifdoco_order import register_ifdoco_order_tools
from tools.kline import register_kline_tools
from tools.order import register_order_tools
from gmo_fx.api.order import OrderApi

load_dotenv()

mcp = FastMCP("GMO Coin FX MCP Server")

register_kline_tools(mcp)
register_asset_balance_resources(
    mcp,
    api_key=os.environ["GMO_API_KEY"],
    secret_key=os.environ["GMO_SECRET_KEY"],
)
register_order_tools(
    mcp,
    api_key=os.environ["GMO_API_KEY"],
    secret_key=os.environ["GMO_SECRET_KEY"],
    size_limit=(
        int(os.environ["ORDER_SIZE_LIMIT"])
        if os.environ.get("ORDER_SIZE_LIMIT")
        else None
    ),
    symbol_limits=(
        {
            OrderApi.Symbol(symbol.strip())
            for symbol in os.environ["ORDER_SYMBOL_LIMITS"].split(",")
            if symbol.strip()
        }
        if os.environ.get("ORDER_SYMBOL_LIMITS")
        else None
    ),
    client_order_id_prefix=os.environ.get("ORDER_CLIENT_ORDER_ID_PREFIX") or None,
)
register_active_orders_tools(
    mcp,
    api_key=os.environ["GMO_API_KEY"],
    secret_key=os.environ["GMO_SECRET_KEY"],
    client_order_id_prefix=os.environ.get("ORDER_CLIENT_ORDER_ID_PREFIX") or None,
)
register_ifdoco_order_tools(
    mcp,
    api_key=os.environ["GMO_API_KEY"],
    secret_key=os.environ["GMO_SECRET_KEY"],
)

if __name__ == "__main__":
    mcp.run()
