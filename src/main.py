from fastmcp import FastMCP

from tools.kline import register_kline_tools

mcp = FastMCP("GMO Coin MCP Server")

register_kline_tools(mcp)

if __name__ == "__main__":
    mcp.run()
