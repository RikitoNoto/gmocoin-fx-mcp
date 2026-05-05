import os

from fastmcp import FastMCP

from tools.kline import register_kline_tools
from tools.order import register_order_tools

mcp = FastMCP("GMO Coin FX MCP Server")

register_kline_tools(mcp)
register_order_tools(
    mcp,
    api_key=os.environ["GMO_API_KEY"],
    secret_key=os.environ["GMO_SECRET_KEY"],
)

if __name__ == "__main__":
    mcp.run()
