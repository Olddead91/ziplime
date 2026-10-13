import datetime
import tempfile
from pathlib import Path

import pytest

from ziplime.constants.data_type import DataType
from ziplime.data.domain.data_bundle import DataBundle
from ziplime.data.services.file_system_bundle_registry import FileSystemBundleRegistry
from ziplime.data.services.file_system_delta_lake_bundle_storage import (
    FileSystemDeltaLakeBundleStorage,
)
from ziplime.utils.calendar_utils import get_calendar


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.mark.asyncio
async def test_file_system_bundle_registry_lifecycle(temp_dir):
    registry = FileSystemBundleRegistry(base_data_path=str(temp_dir))
    storage = FileSystemDeltaLakeBundleStorage(base_data_path=str(temp_dir))
    calendar = get_calendar("XNYS")

    dt_now = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    bundle = DataBundle(
        name="test_bundle",
        version="v1",
        start_date=dt_now,
        end_date=dt_now + datetime.timedelta(days=5),
        trading_calendar=calendar,
        frequency=datetime.timedelta(days=1),
        original_frequency=datetime.timedelta(days=1),
        data_type=DataType.MARKET_DATA,
        timestamp=dt_now,
    )

    # 1. Register bundle
    await registry.register_bundle(data_bundle=bundle, bundle_storage=storage, merge=False)

    # 2. List bundles
    bundles = await registry.list_bundles()
    assert len(bundles) == 1
    assert bundles[0]["name"] == "test_bundle"
    assert bundles[0]["version"] == "v1"

    # 3. List bundles by name
    by_name = await registry.list_bundles_by_name("test_bundle")
    assert len(by_name) == 1
    assert by_name[0]["version"] == "v1"

    # 4. Load metadata
    meta = await registry.load_bundle_metadata("test_bundle", "v1")
    assert meta is not None
    assert meta["name"] == "test_bundle"
    assert meta["version"] == "v1"

    # 5. Load metadata with version=None (loads latest)
    meta_latest = await registry.load_bundle_metadata("test_bundle", None)
    assert meta_latest is not None
    assert meta_latest["version"] == "v1"

    # 6. Delete bundle
    deleted = await registry.delete_bundle("test_bundle", "v1")
    assert deleted is True

    # 7. Delete non-existent
    deleted_again = await registry.delete_bundle("test_bundle", "v1")
    assert deleted_again is False

    meta_after = await registry.load_bundle_metadata("test_bundle", "v1")
    assert meta_after is None
