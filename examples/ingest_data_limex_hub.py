import asyncio
import datetime
import pathlib
import logging

from ziplime.core.ingest_data import get_asset_service, ingest_market_data, ingest_custom_data
from ziplime.data.data_sources.limex_hub_fundamental_data_source import LimexHubFundamentalDataSource
from ziplime.data.services.limex_hub_data_source import LimexHubDataSource
from ziplime.utils.logging_utils import configure_logging



async def ingest_data_limex_hub():
    symbols = ["VOO", "META", "AAPL", "AMZN","AMGN", "NVDA", "AMD","NFLX", "GOOGL", "VXX"]
    start_date = datetime.datetime(year=2024, month=10, day=1, tzinfo=datetime.timezone.utc)
    end_date = datetime.datetime(year=2025, month=2, day=27, tzinfo=datetime.timezone.utc)

    market_data_bundle_source = LimexHubDataSource.from_env()
    asset_service = get_asset_service(
        clear_asset_db=False,
        db_path=str(pathlib.Path(__file__).parent.parent.resolve().joinpath("data", "assets.sqlite"))
    )
    await ingest_market_data(
        start_date=start_date,
        end_date=end_date,
        symbols=symbols,
        trading_calendar="NYSE",
        bundle_name="limex_us_minute_data",
        data_bundle_source=market_data_bundle_source,
        data_frequency=datetime.timedelta(minutes=1),
        asset_service=asset_service
    )

    # ingest fundamental data from limex hub
    data_bundle_source = LimexHubFundamentalDataSource.from_env()
    await ingest_custom_data(
        start_date=start_date - datetime.timedelta(days=3650),
        end_date=end_date,
        symbols=symbols,
        trading_calendar="NYSE",
        bundle_name="limex_us_fundamental_data",
        data_bundle_source=data_bundle_source,
        data_frequency="1mo",
        data_frequency_use_window_end=True,
        asset_service=asset_service
    )


if __name__ == "__main__":
    configure_logging(level=logging.ERROR, file_name="mylog.log")
    asyncio.run(ingest_data_limex_hub())
