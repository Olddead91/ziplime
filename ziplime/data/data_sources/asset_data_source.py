import polars as pl

from ziplime.assets.entities.asset import Asset
from ziplime.assets.entities.symbol_universe import SymbolsUniverse
from ziplime.assets.models.exchange_info import ExchangeInfo
from ziplime.assets.services.asset_service import AssetService


class AssetDataSource:

    def __init__(self):
        pass

    async def get_assets(self, **kwargs) -> list[Asset]:
        pass

    async def get_exchanges(self, **kwargs) -> list[ExchangeInfo]: ...

    async def get_symbol_universe(self, asset_service: AssetService, symbol_universe_name: str) -> SymbolsUniverse: ...

    async def search_assets(self, query: str, **kwargs) -> pl.DataFrame: ...
