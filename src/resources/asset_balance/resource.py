from fastmcp import FastMCP
from gmo_fx.api.assets import AssetsApi


def _map_asset(asset) -> dict[str, int | float]:
    return {
        "equity": asset.equity,
        "available_amount": asset.available_amount,
        "balance": asset.balance,
        "estimated_trade_fee": asset.estimated_trade_fee,
        "margin": asset.margin,
        "margin_ratio": asset.margin_ratio,
        "position_loss_gain": asset.position_loss_gain,
        "total_swap": asset.total_swap,
        "transferable_amount": asset.transferable_amount,
    }


def register_asset_balance_resources(
    mcp: FastMCP,
    api_key: str,
    secret_key: str,
) -> None:
    @mcp.resource(
        "gmocoin-fx://account/assets",
        name="asset_balance",
        description="GMO Coin FXの資産残高を取得します。",
        mime_type="application/json",
    )
    def asset_balance_resource() -> list[dict[str, int | float]]:
        """GMO Coin FXの資産残高を取得します。"""
        api = AssetsApi(api_key=api_key, secret_key=secret_key)

        response = api()
        return [_map_asset(asset) for asset in response.assets]
