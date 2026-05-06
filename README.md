# gmocoin-mcp

## Environment variables

| Name | Required | Description |
| --- | --- | --- |
| `GMO_API_KEY` | Yes | GMO Coin FX API key. |
| `GMO_SECRET_KEY` | Yes | GMO Coin FX secret key. |
| `ORDER_SIZE_LIMIT` | No | Maximum order size accepted by the `order_api` tool. |
| `ORDER_SYMBOL_LIMITS` | No | Comma-separated list of symbols accepted by the `order_api` tool. |
| `ORDER_CLIENT_ORDER_ID_PREFIX` | No | ASCII alphanumeric prefix used to auto-generate `client_order_id` for `order_api` calls. Must be 22 characters or fewer. The server appends a 14-digit timestamp suffix (`yyyyMMddHHmmss`) so the resulting ID stays within GMO Coin FX's 36-character limit. |
