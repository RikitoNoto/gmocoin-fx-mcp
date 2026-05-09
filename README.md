# gmocoin-mcp

## Environment variables

| Name | Required | Description |
| --- | --- | --- |
| `GMO_API_KEY` | Yes | GMO Coin FX API key. |
| `GMO_SECRET_KEY` | Yes | GMO Coin FX secret key. |
| `ORDER_SIZE_LIMIT` | No | Maximum order size accepted by the `order_api`, `close_order_api`, `ifd_order_api`, and `ifdoco_order_api` tools. |
| `ORDER_SYMBOL_LIMITS` | No | Comma-separated list of symbols accepted by the `order_api`, `close_order_api`, `ifd_order_api`, and `ifdoco_order_api` tools. |
| `ORDER_CLIENT_ORDER_ID_PREFIX` | No | ASCII alphanumeric prefix used to auto-generate `client_order_id` for `order_api`, `close_order_api`, `ifd_order_api`, and `ifdoco_order_api` calls and to filter `active_orders_api`, `latest_executions_api`, and `open_positions_api` results. Must be 22 characters or fewer. The server appends a 14-digit timestamp suffix (`yyyyMMddHHmmss`) so the resulting ID stays within GMO Coin FX's 36-character limit. |
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

When running with Docker Compose, the compose file loads `.env` but does not force a transport. Leave `MCP_TRANSPORT` unset to use `stdio`, or set `MCP_TRANSPORT=http` in `.env` to use the published port `8000`.

## Tools

| Name | Description |
| --- | --- |
| `order_api` | Places a new GMO Coin FX order. |
| `close_order_api` | Places a GMO Coin FX close order. Supports optional `size` or `settle_position` parameters. |
| `ifd_order_api` | Places a GMO Coin FX IFD order using `symbol`, `client_order_id`, `first_side`, `first_execution_type`, `first_size`, `first_price`, `second_execution_type`, `second_size`, and `second_price`. |
| `ifdoco_order_api` | Places a GMO Coin FX IFDOCO order using `symbol`, `client_order_id`, `first_side`, `first_execution_type`, `first_size`, `first_price`, `second_size`, `second_limit_price`, and `second_stop_price`. |
| `change_ifdoco_order_api` | Changes prices for an existing GMO Coin FX IFDOCO order. Specify exactly one of `root_order_id` or `client_order_id`, plus at least one of `first_price`, `second_limit_price`, or `second_stop_price`. |
| `change_oco_order_api` | Changes limit/stop prices for an existing GMO Coin FX OCO order. |
| `change_order_api` | Changes the price of a GMO Coin FX normal order. Specify exactly one of `order_id` or `client_order_id`, plus `price`. |
| `cancel_orders_api` | Cancels up to 10 GMO Coin FX orders at once. Specify exactly one of `root_order_ids` or `client_order_ids`. |
| `active_orders_api` | Retrieves active GMO Coin FX orders. Supports optional `symbol`, `prev_id`, and `count` parameters. When `ORDER_CLIENT_ORDER_ID_PREFIX` is configured, only active orders whose `client_order_id` starts with that prefix are returned. |
| `latest_executions_api` | Retrieves the latest GMO Coin FX executions for a required `symbol` and optional `count`. When `ORDER_CLIENT_ORDER_ID_PREFIX` is configured, only executions whose `client_order_id` starts with that prefix are returned. |
| `open_positions_api` | Retrieves all GMO Coin FX open positions. Supports an optional `symbol` parameter. When `ORDER_CLIENT_ORDER_ID_PREFIX` is configured, latest executions are used to return only positions whose opening `client_order_id` starts with that prefix. |


## Resources

| URI | Description |
| --- | --- |
| `gmocoin-fx://account/assets` | Retrieves GMO Coin FX account asset balances as JSON. Asset balances are exposed as an MCP resource because they are read-only account state with a stable URI and no invocation parameters. |
