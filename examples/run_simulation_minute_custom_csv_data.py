import asyncio
import datetime
import logging
import pathlib

import structlog

from ziplime.constants.data_type import DataType
from ziplime.utils.logging_utils import configure_logging

from pathlib import Path

import pytz

from ziplime.core.ingest_data import get_asset_service
from ziplime.core.run_simulation import run_simulation
from ziplime.data.services.bundle_service import BundleService
from ziplime.data.services.csv_data_source import CSVDataSource
from ziplime.data.services.file_system_bundle_registry import FileSystemBundleRegistry
from ziplime.utils.calendar_utils import get_calendar

logger = structlog.get_logger(__name__)


async def _run_simulation():
    bundle_storage_path = str(Path(Path.home(), ".ziplime", "data"))
    bundle_registry = FileSystemBundleRegistry(base_data_path=bundle_storage_path)
    bundle_service = BundleService(bundle_registry=bundle_registry)
    emission_rate = datetime.timedelta(minutes=1)
    asset_service = get_asset_service(
        clear_asset_db=False,
        db_path=str(pathlib.Path(__file__).parent.parent.resolve().joinpath("data", "assets.sqlite"))
    )
    start_date = datetime.datetime(year=2025, month=1, day=3, tzinfo=pytz.timezone("America/New_York"))
    end_date = datetime.datetime(year=2025, month=2, day=1, tzinfo=pytz.timezone("America/New_York"))
    market_data_bundle = await bundle_service.load_bundle(bundle_name="limex_us_minute_data",
                                                          bundle_version=None,
                                                          frequency=emission_rate,
                                                          start_date=start_date,
                                                          end_date=end_date,
                                                          symbols=["VOO", "META", "AAPL", "AMZN", "NFLX", "GOOGL", "VXX"],
                                                          )

    custom_data_sources = []
    custom_data_sources.append(
        await bundle_service.load_bundle(bundle_name="limex_us_fundamental_data", bundle_version=None))

    data_bundle_source = CSVDataSource(
        csv_file_name="/my_data.csv",
        column_mapping={
            "Time": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
            "EventSymbol": "symbol"
        },
        date_format="%Y%m%d-%H%M%S%z",
        name="custom_minute_bars",
        date_column_name="Time",
        frequency=datetime.timedelta(minutes=1),
        trading_calendar=get_calendar("NYSE"),
        asset_service=asset_service,
        data_frequency_use_window_end=False,
        symbols=["SPX"],
        data_type=DataType.CUSTOM
    )
    await data_bundle_source.load_data_in_memory()
    custom_data_sources.append(data_bundle_source)
    # run daily simulation
    res, errors = await run_simulation(
        start_date=start_date,
        end_date=end_date,
        trading_calendar="NYSE",
        algorithm_file=str(Path("algorithms/test_algo/test_algo.py").absolute()),
        total_cash=100000.0,
        market_data_source=market_data_bundle,
        custom_data_sources=custom_data_sources,
        config_file=str(Path("algorithms/test_algo/test_algo_config.json").absolute()),
        emission_rate=emission_rate,
        benchmark_asset_symbol="SPX",
        benchmark_returns=None,
        stop_on_error=False,
    )

    logger.error(errors)
    print(res.head(n=10).to_markdown())


if __name__ == "__main__":
    configure_logging(level=logging.ERROR, file_name="mylog.log")
    asyncio.run(
        _run_simulation()
    )
