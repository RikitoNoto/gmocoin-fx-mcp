# gmocoin-mcp

## Environment variables

| Name | Required | Description |
| --- | --- | --- |
| `GMO_API_KEY` | Yes | GMO Coin FX API key. |
| `GMO_SECRET_KEY` | Yes | GMO Coin FX secret key. |
| `ORDER_SIZE_LIMIT` | No | Maximum order size accepted by the `order_api` tool. |
| `ORDER_SYMBOL_LIMITS` | No | Comma-separated list of symbols accepted by the `order_api` tool. |
| `ORDER_CLIENT_ORDER_ID_PREFIX` | No | ASCII alphanumeric prefix used to auto-generate `client_order_id` for `order_api` calls and to filter `active_orders_api` results. Must be 22 characters or fewer. The server appends a 14-digit timestamp suffix (`yyyyMMddHHmmss`) so the resulting ID stays within GMO Coin FX's 36-character limit. |


## Tools

| Name | Description |
| --- | --- |
| `order_api` | Places a new GMO Coin FX order. |
| `active_orders_api` | Retrieves active GMO Coin FX orders. Supports optional `symbol`, `prev_id`, and `count` parameters. When `ORDER_CLIENT_ORDER_ID_PREFIX` is configured, only active orders whose `client_order_id` starts with that prefix are returned. |
