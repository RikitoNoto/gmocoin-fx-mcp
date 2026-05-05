import os

from fastmcp import FastMCP
from dotenv import load_dotenv
from tools.ifdoco_order import register_ifdoco_order_tools
from tools.kline import register_kline_tools
from tools.order import register_order_tools

load_dotenv()

mcp = FastMCP("GMO Coin FX MCP Server")

register_kline_tools(mcp)
register_order_tools(
    mcp,
    api_key=os.environ["GMO_API_KEY"],
    secret_key=os.environ["GMO_SECRET_KEY"],
)
register_ifdoco_order_tools(
    mcp,
    api_key=os.environ["GMO_API_KEY"],
    secret_key=os.environ["GMO_SECRET_KEY"],
)

if __name__ == "__main__":
    mcp.run()
