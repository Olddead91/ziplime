import datetime
import pandas as pd
import pytest

from ziplime.utils.date_utils import (
    compute_date_range_chunks,
    make_utc_aware,
    normalize_datetime,
    period_to_timedelta,
    strip_time_and_timezone_info,
)


def test_compute_date_range_chunks_success():
    sessions = pd.date_range("2024-01-01", "2024-01-10", freq="D")
    start = pd.Timestamp("2024-01-02")
    end = pd.Timestamp("2024-01-08")

    # chunksize is None -> single chunk
    single = list(compute_date_range_chunks(sessions, start, end, chunksize=None))
    assert single == [(start, end)]

    # chunksize = 3
    chunks = list(compute_date_range_chunks(sessions, start, end, chunksize=3))
    assert len(chunks) == 3
    assert chunks[0] == (pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-04"))
    assert chunks[1] == (pd.Timestamp("2024-01-05"), pd.Timestamp("2024-01-07"))
    assert chunks[2] == (pd.Timestamp("2024-01-08"), pd.Timestamp("2024-01-08"))


def test_compute_date_range_chunks_validations():
    sessions = pd.date_range("2024-01-02", "2024-01-05", freq="D")

    with pytest.raises(KeyError, match="Start date 2024-01-01 is not found"):
        list(compute_date_range_chunks(sessions, pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-03"), 2))

    with pytest.raises(KeyError, match="End date 2024-01-10 is not found"):
        list(compute_date_range_chunks(sessions, pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-10"), 2))

    with pytest.raises(ValueError, match="cannot precede start date"):
        list(compute_date_range_chunks(sessions, pd.Timestamp("2024-01-04"), pd.Timestamp("2024-01-02"), 2))


def test_make_utc_aware():
    naive = pd.date_range("2024-01-01", periods=2, freq="D")
    aware = make_utc_aware(naive)
    assert aware.tz is not None
    assert str(aware.tz) == "UTC"

    eastern = naive.tz_localize("US/Eastern")
    converted = make_utc_aware(eastern)
    assert str(converted.tz) == "UTC"


def test_strip_time_and_timezone_info():
    dt = datetime.datetime(2024, 5, 10, 14, 30, 45, 123456, tzinfo=datetime.timezone.utc)
    stripped = strip_time_and_timezone_info(dt)
    assert stripped.hour == 0
    assert stripped.minute == 0
    assert stripped.second == 0
    assert stripped.microsecond == 0
    assert stripped.tzinfo == datetime.timezone.utc


def test_normalize_datetime():
    tz_ny = datetime.timezone(datetime.timedelta(hours=-5))
    tz_utc = datetime.timezone.utc

    naive_dt = datetime.datetime(2024, 1, 1, 10, 0)
    normalized_naive = normalize_datetime(naive_dt, tz_ny)
    assert normalized_naive.tzinfo == tz_ny
    assert normalized_naive.hour == 10

    aware_dt = datetime.datetime(2024, 1, 1, 15, 0, tzinfo=tz_utc)
    normalized_aware = normalize_datetime(aware_dt, tz_ny)
    assert normalized_aware.tzinfo == tz_ny
    assert normalized_aware.hour == 10


def test_period_to_timedelta():
    td = datetime.timedelta(days=2)
    assert period_to_timedelta(td) == td

    assert period_to_timedelta("1us") == datetime.timedelta(microseconds=1)
    assert period_to_timedelta("1ms") == datetime.timedelta(milliseconds=1)
    assert period_to_timedelta("1s") == datetime.timedelta(seconds=1)
    assert period_to_timedelta("1m") == datetime.timedelta(minutes=1)
    assert period_to_timedelta("1h") == datetime.timedelta(hours=1)
    assert period_to_timedelta("1d") == datetime.timedelta(days=1)
    assert period_to_timedelta("1w") == datetime.timedelta(days=7)
    assert period_to_timedelta("1mo") == datetime.timedelta(days=30)
    assert period_to_timedelta("1q") == datetime.timedelta(days=90)
    assert period_to_timedelta("1y") == datetime.timedelta(days=365)

    with pytest.raises(ValueError, match="Invalid period: invalid"):
        period_to_timedelta("invalid")
