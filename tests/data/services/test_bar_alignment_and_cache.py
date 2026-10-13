import datetime
import tempfile
from pathlib import Path

import polars as pl
import pytest
from exchange_calendars import get_calendar

from ziplime.data.services.bar_alignment import clock_minutes, align_to_clock
from ziplime.data.services.frame_cache import (
    cache_dir,
    cache_key,
    clear,
    load,
    store,
    FOREVER,
)


def test_clock_minutes_and_align_to_clock():
    calendar = get_calendar("XNYS")
    start = datetime.date(2024, 1, 3)
    end = datetime.date(2024, 1, 3)
    emission = datetime.timedelta(minutes=5)

    grid = clock_minutes(calendar, start, end, emission)
    assert len(grid) > 0
    # Sessions first minute is 09:30 or 09:31 depending on exchange calendar settings
    first_min = grid[0].time()
    assert first_min in (datetime.time(9, 30), datetime.time(9, 31))

    # Bars labelled with start time
    tz = calendar.tz
    bars = pl.DataFrame({
        "date": [
            datetime.datetime(2024, 1, 3, 9, 30, tzinfo=tz),
            datetime.datetime(2024, 1, 3, 9, 35, tzinfo=tz),
            # Final bar of session closing at 16:00 (15:55-16:00) should be dropped
            datetime.datetime(2024, 1, 3, 16, 1, tzinfo=tz),
        ],
        "close": [100.0, 101.0, 105.0],
    })

    aligned = align_to_clock(bars, grid, emission_rate=emission, column="date")
    assert len(aligned) == 2


def test_frame_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("ZIPLIME_CACHE_DIR", str(tmp_path))

    # Test cache key stability and normalization
    key1 = cache_key("yahoo", {"AAPL", "MSFT"}, [1, 2, 3], datetime.date(2024, 1, 1))
    key2 = cache_key("yahoo", {"MSFT", "AAPL"}, (1, 2, 3), datetime.date(2024, 1, 1))
    assert key1 == key2

    # Miss
    assert load(key1, max_age=datetime.timedelta(hours=1)) is None

    # Store and load
    df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    store(key1, df)

    cached_df = load(key1, max_age=datetime.timedelta(hours=1))
    assert cached_df is not None
    assert cached_df.equals(df)

    # Expired
    expired = load(key1, max_age=datetime.timedelta(seconds=-1))
    assert expired is None

    # Clear
    removed = clear()
    assert removed == 1
    assert load(key1, max_age=FOREVER) is None
