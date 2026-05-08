import os
from typing import Literal, TypedDict, cast

from dotenv import load_dotenv
from fastmcp import FastMCP
from gmo_fx.api.order import OrderApi
from resources.asset_balance import register_asset_balance_resources
from tools.active_orders import register_active_orders_tools
from tools.change_order import register_change_order_tools
from tools.close_order import register_close_order_tools
from tools.ifdoco_order import register_ifdoco_order_tools
from tools.kline import register_kline_tools
from tools.latest_executions import register_latest_executions_tools
from tools.open_positions import register_open_positions_tools
from tools.order import register_order_tools

load_dotenv()

Transport = Literal["stdio", "http", "sse", "streamable-http"]
HTTP_TRANSPORTS = {"http", "sse", "streamable-http"}


class RunConfig(TypedDict, total=False):
    transport: Transport
    host: str
    port: int
    path: str


def _optional_int_env(name: str) -> int | None:
    value = os.environ.get(name)
    if not value:
        return None
    return int(value)


def _symbol_limits_from_env() -> set[OrderApi.Symbol] | None:
    value = os.environ.get("ORDER_SYMBOL_LIMITS")
    if not value:
        return None
    return {
        OrderApi.Symbol(symbol.strip())
        for symbol in value.split(",")
        if symbol.strip()
    }


def create_mcp() -> FastMCP:
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
        size_limit=_optional_int_env("ORDER_SIZE_LIMIT"),
        symbol_limits=_symbol_limits_from_env(),
        client_order_id_prefix=os.environ.get("ORDER_CLIENT_ORDER_ID_PREFIX") or None,
    )
    register_change_order_tools(
        mcp,
        api_key=os.environ["GMO_API_KEY"],
        secret_key=os.environ["GMO_SECRET_KEY"],
    )
    register_close_order_tools(
        mcp,
        api_key=os.environ["GMO_API_KEY"],
        secret_key=os.environ["GMO_SECRET_KEY"],
        size_limit=_optional_int_env("ORDER_SIZE_LIMIT"),
        symbol_limits=_symbol_limits_from_env(),
        client_order_id_prefix=os.environ.get("ORDER_CLIENT_ORDER_ID_PREFIX") or None,
    )
    register_active_orders_tools(
        mcp,
        api_key=os.environ["GMO_API_KEY"],
        secret_key=os.environ["GMO_SECRET_KEY"],
        client_order_id_prefix=os.environ.get("ORDER_CLIENT_ORDER_ID_PREFIX") or None,
    )
    register_latest_executions_tools(
        mcp,
        api_key=os.environ["GMO_API_KEY"],
        secret_key=os.environ["GMO_SECRET_KEY"],
        client_order_id_prefix=os.environ.get("ORDER_CLIENT_ORDER_ID_PREFIX") or None,
    )
    register_open_positions_tools(
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
    return mcp


def get_run_config() -> RunConfig:
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    if transport not in {"stdio", "http", "sse", "streamable-http"}:
        raise ValueError(
            "MCP_TRANSPORT must be one of: stdio, http, sse, streamable-http"
        )

    run_config: RunConfig = {"transport": cast(Transport, transport)}
    if transport in HTTP_TRANSPORTS:
        run_config["host"] = os.environ.get("MCP_HTTP_HOST", "0.0.0.0")
        run_config["port"] = int(os.environ.get("MCP_HTTP_PORT", "8000"))
        if os.environ.get("MCP_HTTP_PATH"):
            run_config["path"] = os.environ["MCP_HTTP_PATH"]

    return run_config


def run_server(server: FastMCP) -> None:
    server.run(**get_run_config())


mcp = create_mcp()

if __name__ == "__main__":
    run_server(mcp)
