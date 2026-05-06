# gmocoin-mcp

## Environment variables

| Name | Required | Description |
| --- | --- | --- |
| `GMO_API_KEY` | Yes | GMO Coin FX API key. |
| `GMO_SECRET_KEY` | Yes | GMO Coin FX secret key. |
| `ORDER_SIZE_LIMIT` | No | Maximum order size accepted by the `order_api` tool. |
| `ORDER_SYMBOL_LIMITS` | No | Comma-separated list of symbols accepted by the `order_api` tool. |
| `ORDER_CLIENT_ORDER_ID_PREFIX` | No | ASCII alphanumeric prefix used to auto-generate `client_order_id` for `order_api` calls and to filter `active_orders_api` results. Must be 22 characters or fewer. The server appends a 14-digit timestamp suffix (`yyyyMMddHHmmss`) so the resulting ID stays within GMO Coin FX's 36-character limit. |
| `MCP_TRANSPORT` | No | MCP transport to use. Defaults to `stdio`; set to `http` to listen over HTTP. `sse` and `streamable-http` are also accepted. |
| `MCP_HTTP_HOST` | No | Host/interface for HTTP transports. Defaults to `0.0.0.0`. |
| `MCP_HTTP_PORT` | No | Port for HTTP transports. Defaults to `8000`. |
| `MCP_HTTP_PATH` | No | Optional endpoint path for HTTP transports, such as `/mcp`. |

## Running over HTTP

The server still starts with the standard stdio MCP transport by default:

```bash
uv run src/main.py
```

To expose the MCP server over HTTP, set `MCP_TRANSPORT=http` before starting it:

```bash
MCP_TRANSPORT=http MCP_HTTP_HOST=0.0.0.0 MCP_HTTP_PORT=8000 uv run src/main.py
```

When running with Docker Compose, the compose file publishes port `8000`; set `MCP_TRANSPORT=http` in your environment or `.env` file to use that port.

## Tools

| Name | Description |
| --- | --- |
| `order_api` | Places a new GMO Coin FX order. |
| `active_orders_api` | Retrieves active GMO Coin FX orders. Supports optional `symbol`, `prev_id`, and `count` parameters. When `ORDER_CLIENT_ORDER_ID_PREFIX` is configured, only active orders whose `client_order_id` starts with that prefix are returned. |
