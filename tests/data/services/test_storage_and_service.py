import datetime
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import polars as pl
import pytest

from ziplime.constants.data_type import DataType
from ziplime.data.domain.data_bundle import DataBundle
from ziplime.data.services.file_system_bundle_registry import FileSystemBundleRegistry
from ziplime.data.services.file_system_delta_lake_bundle_storage import (
    FileSystemDeltaLakeBundleStorage,
)
from ziplime.data.services.bundle_service import BundleService
from ziplime.utils.calendar_utils import get_calendar


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_bundle_and_storage(temp_dir):
    calendar = get_calendar("XNYS")
    start = datetime.datetime(2024, 1, 3, 16, 0, tzinfo=calendar.tz)
    end = datetime.datetime(2024, 1, 5, 16, 0, tzinfo=calendar.tz)
    dates = [
        datetime.datetime(2024, 1, 3, 16, 0, tzinfo=calendar.tz),
        datetime.datetime(2024, 1, 4, 16, 0, tzinfo=calendar.tz),
        datetime.datetime(2024, 1, 5, 16, 0, tzinfo=calendar.tz),
    ]

    rows = []
    for d in dates:
        rows.append({
            "date": d,
            "sid": 1,
            "symbol": "AAPL",
            "mic": "XNGS",
            "open": 150.0,
            "high": 155.0,
            "low": 149.0,
            "close": 154.0,
            "price": 154.0,
            "volume": 1000.0,
        })
        rows.append({
            "date": d,
            "sid": 2,
            "symbol": "MSFT",
            "mic": "XNGS",
            "open": 300.0,
            "high": 305.0,
            "low": 299.0,
            "close": 304.0,
            "price": 304.0,
            "volume": 2000.0,
        })
    df = pl.DataFrame(rows).sort(["sid", "date"])

    bundle = DataBundle(
        name="daily_bundle",
        version="v1",
        start_date=start,
        end_date=end,
        trading_calendar=calendar,
        frequency=datetime.timedelta(days=1),
        original_frequency=datetime.timedelta(days=1),
        data_type=DataType.MARKET_DATA,
        timestamp=end,
        data=df,
    )
    storage = FileSystemDeltaLakeBundleStorage(base_data_path=str(temp_dir))
    registry = FileSystemBundleRegistry(base_data_path=str(temp_dir))
    return bundle, storage, registry


@pytest.mark.asyncio
async def test_delta_lake_storage_store_and_load(sample_bundle_and_storage):
    bundle, storage, registry = sample_bundle_and_storage

    # Store bundle
    await storage.store_bundle(bundle, merge=False)

    # To JSON and From JSON
    json_data = await storage.to_json(bundle)
    restored_storage = await FileSystemDeltaLakeBundleStorage.from_json(json_data)
    assert restored_storage.base_data_path == storage.base_data_path

    # Get SIDs
    sids = await storage.get_data_bundle_sids(bundle)
    assert sorted(sids) == [1, 2]

    # Load bundle data
    loaded_df = await storage.load_data_bundle(bundle)
    assert len(loaded_df) == 6

    # Load bundle before date
    before_df = await storage.load_data_bundle_before(
        bundle, sid=1, date=datetime.datetime(2024, 1, 4, tzinfo=bundle.trading_calendar.tz),
        columns=["date", "close"]
    )
    assert len(before_df) == 1
    assert before_df["close"][0] == 154.0

    # Initialize adjustment columns
    await storage.initialize_adjustment_columns(
        bundle,
        adjusted_columns={"close_adjusted": "close"},
        adjusted_flag_column="adjusted",
    )
    after_adj = await storage.load_data_bundle(bundle)
    assert "close_adjusted" in after_adj.columns
    assert "adjusted" in after_adj.columns


@pytest.mark.asyncio
async def test_bundle_service_load_and_clean(sample_bundle_and_storage):
    bundle, storage, registry = sample_bundle_and_storage
    service = BundleService(bundle_registry=registry)

    await service.register_bundle(bundle, storage, merge=False)
    await service.store_bundle(bundle, storage, merge=False)

    # Load definition
    loaded_bundle, loaded_storage = await service.load_bundle_definition("daily_bundle", "v1")
    assert loaded_bundle.name == "daily_bundle"
    assert loaded_bundle.version == "v1"

    # Batch iteration
    batches = []
    async for b in service.iter_bundle_batches(bundle, storage, batch_days=2, batch_assets=1):
        batches.append(b)
    assert len(batches) > 0

    # Clean bundle
    # Add a second version
    bundle2 = DataBundle(
        name="daily_bundle",
        version="v2",
        start_date=bundle.start_date,
        end_date=bundle.end_date,
        trading_calendar=bundle.trading_calendar,
        frequency=bundle.frequency,
        original_frequency=bundle.original_frequency,
        data_type=bundle.data_type,
        timestamp=bundle.end_date + datetime.timedelta(days=1),
        data=bundle.data,
    )
    await service.register_bundle(bundle2, storage, merge=False)
    await service.store_bundle(bundle2, storage, merge=False)

    # Keep last 1
    deleted = await service.clean(bundle_name="daily_bundle", keep_last=1)
    assert deleted == ["v1"]


@pytest.mark.asyncio
async def test_bundle_service_load_bundle(sample_bundle_and_storage):
    bundle, storage, registry = sample_bundle_and_storage
    service = BundleService(bundle_registry=registry)

    await service.register_bundle(bundle, storage, merge=False)
    await service.store_bundle(bundle, storage, merge=False)

    loaded_b, missing = await service.load_bundle("daily_bundle", "v1")
    assert loaded_b.data is not None
    assert len(loaded_b.data) == 6
    assert missing == {}


@pytest.mark.asyncio
async def test_bundle_service_ingest_custom(sample_bundle_and_storage):
    bundle, storage, registry = sample_bundle_and_storage
    service = BundleService(bundle_registry=registry)

    # Ingest custom data bundle
    source = MagicMock()
    custom_df = pl.DataFrame({
        "date": [
            datetime.datetime(2024, 1, 3, 16, 0, tzinfo=bundle.trading_calendar.tz),
            datetime.datetime(2024, 1, 4, 16, 0, tzinfo=bundle.trading_calendar.tz),
        ],
        "sid": [1, 1],
        "feature": [10.5, 20.5],
    })
    from unittest.mock import AsyncMock
    source.get_data = AsyncMock(return_value=custom_df)

    asset_service = MagicMock()
    # Mock backfill
    from unittest.mock import patch
    with patch("ziplime.data.services.bundle_service._backfill_symbol_data", new=AsyncMock(return_value=custom_df)):
        res_bundle = await service.ingest_custom_data_bundle(
            name="custom_bundle",
            bundle_version="v1",
            date_start=bundle.start_date,
            date_end=bundle.end_date,
            trading_calendar=bundle.trading_calendar,
            symbols=["AAPL"],
            data_bundle_source=source,
            frequency=datetime.timedelta(days=1),
            data_frequency_use_window_end=False,
            bundle_storage=storage,
            asset_service=asset_service,
            merge=False,
            merge_columns=["sid", "date"],
        )
        assert res_bundle.name == "custom_bundle"
        assert res_bundle.data_type == DataType.CUSTOM

