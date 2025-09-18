import asyncio
import logging
import pathlib

from ziplime.core.ingest_data import ingest_default_assets, get_asset_service, ingest_market_data, \
    ingest_symbol_universes
from ziplime.data.data_sources.limex_hub_asset_data_source import LimexHubAssetDataSource
from ziplime.utils.logging_utils import configure_logging


async def ingest_assets_data_limex_hub():
    asset_data_source = LimexHubAssetDataSource.from_env()
    asset_service = get_asset_service(
        clear_asset_db=True,
        db_path=str(pathlib.Path(__file__).parent.parent.resolve().joinpath("data", "assets.sqlite"))
    )
    await ingest_default_assets(asset_service=asset_service, asset_data_source=asset_data_source)
    await ingest_symbol_universes(asset_service=asset_service, asset_data_source=asset_data_source)


if __name__ == "__main__":
    configure_logging(level=logging.ERROR, file_name="mylog.log")
    asyncio.run(ingest_assets_data_limex_hub())
