from dataclasses import dataclass
from types import SimpleNamespace
import json

import pytest
from fastmcp import Client, FastMCP

from resources.asset_balance import register_asset_balance_resources
import resources.asset_balance.resource as asset_balance_resource


@dataclass
class FakeAsset:
    equity: int
    available_amount: int
    balance: int
    estimated_trade_fee: float
    margin: int
    margin_ratio: float
    position_loss_gain: float
    total_swap: float
    transferable_amount: int


def construct_mcp():
    mcp = FastMCP("test")
    register_asset_balance_resources(
        mcp,
        api_key="test-key",
        secret_key="test-secret",
    )
    return mcp


@pytest.fixture
def mcp():
    return construct_mcp()


class FakeAssetsApi:
    return_assets: list[FakeAsset] = []
    init_calls: list[dict] = []
    api_calls: list[dict] = []

    def __init__(self, *, api_key, secret_key):
        self.init_calls.append({"api_key": api_key, "secret_key": secret_key})

    def __call__(self):
        self.api_calls.append({})
        return SimpleNamespace(assets=self.return_assets)


class TestAssetBalanceResource:
    @pytest.fixture(autouse=True)
    def set_up_tear_down(self):
        FakeAssetsApi.return_assets = []
        FakeAssetsApi.init_calls = []
        FakeAssetsApi.api_calls = []
        yield
        FakeAssetsApi.return_assets = []
        FakeAssetsApi.init_calls = []
        FakeAssetsApi.api_calls = []

    @pytest.mark.anyio
    async def test_registers_asset_balance_resource(self, mcp: FastMCP):
        resources = await mcp.list_resources()

        resource = next(
            (
                resource
                for resource in resources
                if str(resource.uri) == "gmocoin-fx://account/assets"
            ),
            None,
        )
        assert resource is not None
        assert resource.name == "asset_balance"
        assert resource.mime_type == "application/json"

    @pytest.mark.anyio
    async def test_asset_balance_resource_uses_registered_credentials_and_maps_response(
        self, monkeypatch: pytest.MonkeyPatch, mcp: FastMCP
    ):
        FakeAssetsApi.return_assets = [
            FakeAsset(
                equity=100000,
                available_amount=95000,
                balance=99000,
                estimated_trade_fee=10.5,
                margin=5000,
                margin_ratio=2500.5,
                position_loss_gain=-1000.25,
                total_swap=12.5,
                transferable_amount=94000,
            )
        ]
        monkeypatch.setattr(asset_balance_resource, "AssetsApi", FakeAssetsApi)

        async with Client(mcp) as client:
            result = await client.read_resource("gmocoin-fx://account/assets")

        assert FakeAssetsApi.init_calls == [
            {"api_key": "test-key", "secret_key": "test-secret"}
        ]
        assert FakeAssetsApi.api_calls == [{}]
        assert len(result) == 1
        assert result[0].mimeType == "application/json"
        assert json.loads(result[0].text) == [
            {
                "equity": 100000,
                "available_amount": 95000,
                "balance": 99000,
                "estimated_trade_fee": 10.5,
                "margin": 5000,
                "margin_ratio": 2500.5,
                "position_loss_gain": -1000.25,
                "total_swap": 12.5,
                "transferable_amount": 94000,
            }
        ]
