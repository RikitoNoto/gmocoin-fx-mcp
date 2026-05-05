from fastmcp import FastMCP

mcp = FastMCP("GMO Coin MCP Server")

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)
