import datetime
import polars as pl
import pytest
from polars.exceptions import ColumnNotFoundError

from ziplime.assets.entities.asset_symbol import AssetSymbol
from ziplime.utils.calendar_utils import get_calendar
from ziplime.utils.data_utils import (
    _backfill_symbol_data,
    _process_data,
    backfill_sid_data,
)


class _Asset:
    def __init__(self, sid: int, symbol: str | None = None):
        self.sid = sid
        self.symbol = symbol


class _Assets:
    async def get_assets_by_ids(self, ids):
        return [_Asset(sid) for sid in ids]

    async def get_exchange_equities_by_symbols(self, symbols):
        return [_Asset(index + 1, symbol.symbol) for index, symbol in enumerate(symbols)]


@pytest.mark.asyncio
async def test_backfill_symbol_data_adds_missing_dates_without_filling_values():
    data = pl.DataFrame(
        {
            "sid": [7, 7],
            "date": [
                datetime.datetime(2024, 1, 2),
                datetime.datetime(2024, 1, 4),
            ],
            "value": [10.0, 12.0],
        }
    )
    required = pl.DataFrame(
        {
            "date": [
                datetime.datetime(2024, 1, 2),
                datetime.datetime(2024, 1, 3),
                datetime.datetime(2024, 1, 4),
            ]
        }
    )

    result = await _backfill_symbol_data(data, _Assets(), required)

    assert result["date"].to_list() == required["date"].to_list()
    assert result["sid"].to_list() == [7, 7, 7]
    assert result.filter(pl.col("date") == datetime.datetime(2024, 1, 3))["value"].item() is None


@pytest.mark.asyncio
async def test_backfill_symbol_data_handles_series_required_sessions():
    data = pl.DataFrame(
        {
            "sid": [5],
            "date": [datetime.datetime(2024, 1, 2)],
            "value": [10.0],
        }
    )
    required = pl.Series("date", [datetime.datetime(2024, 1, 2), datetime.datetime(2024, 1, 3)])
    result = await _backfill_symbol_data(data, _Assets(), required)
    assert len(result) == 2
    assert result.filter(pl.col("date") == datetime.datetime(2024, 1, 3))["value"].item() is None


@pytest.mark.asyncio
async def test_backfill_symbol_data_returns_early_when_no_sids():
    data = pl.DataFrame({"sid": pl.Series([], dtype=pl.Int64), "date": pl.Series([], dtype=pl.Datetime)})
    required = pl.DataFrame({"date": [datetime.datetime(2024, 1, 2)]})
    result = await _backfill_symbol_data(data, _Assets(), required)
    assert result.is_empty()


@pytest.mark.asyncio
async def test_backfill_symbol_data_skips_when_no_missing_dates():
    data = pl.DataFrame(
        {
            "sid": [1, 1],
            "date": [datetime.datetime(2024, 1, 2), datetime.datetime(2024, 1, 3)],
            "price": [100.0, 101.0],
        }
    )
    required = pl.DataFrame({"date": [datetime.datetime(2024, 1, 2), datetime.datetime(2024, 1, 3)]})
    result = await _backfill_symbol_data(data, _Assets(), required)
    assert len(result) == 2
    assert result["price"].to_list() == [100.0, 101.0]


@pytest.mark.asyncio
async def test_backfill_symbol_data_rejects_unknown_sid():
    class NoAssets(_Assets):
        async def get_assets_by_ids(self, ids):
            return []

    data = pl.DataFrame({"sid": [99], "date": [datetime.datetime(2024, 1, 2)]})

    with pytest.raises(ValueError, match="SIDs are missing"):
        await _backfill_symbol_data(data, NoAssets(), data.select("date"))


@pytest.mark.asyncio
async def test_backfill_sid_data_adds_sid_and_missing_dates_for_each_symbol():
    data = pl.DataFrame(
        {
            "symbol": ["AAA", "AAA", "BBB"],
            "date": [
                datetime.datetime(2024, 1, 2),
                datetime.datetime(2024, 1, 4),
                datetime.datetime(2024, 1, 3),
            ],
            "value": [10.0, 12.0, 20.0],
        }
    )
    required = pl.DataFrame(
        {
            "date": [
                datetime.datetime(2024, 1, 2),
                datetime.datetime(2024, 1, 3),
                datetime.datetime(2024, 1, 4),
            ]
        }
    )

    result = await backfill_sid_data(data, _Assets(), required)

    assert result.columns == ["symbol", "date", "value", "sid"]
    assert result.select("sid").unique().sort("sid")["sid"].to_list() == [1, 2]
    assert result.filter(
        (pl.col("symbol") == "AAA") & (pl.col("date") == datetime.datetime(2024, 1, 3))
    )["value"].item() is None
    assert result.filter(
        (pl.col("symbol") == "BBB") & (pl.col("date") == datetime.datetime(2024, 1, 2))
    )["value"].item() is None
    assert result.filter(
        (pl.col("symbol") == "AAA") & (pl.col("date") == datetime.datetime(2024, 1, 2))
    )["value"].item() == 10.0


@pytest.mark.asyncio
async def test_backfill_sid_data_rejects_unknown_symbol():
    class NoSymbols(_Assets):
        async def get_exchange_equities_by_symbols(self, symbols):
            return []

    data = pl.DataFrame(
        {
            "symbol": ["UNKNOWN"],
            "date": [datetime.datetime(2024, 1, 2)],
            "value": [1.0],
        }
    )

    with pytest.raises(ValueError, match="Symbols are missing"):
        await backfill_sid_data(data, NoSymbols(), data.select("date"))


@pytest.mark.asyncio
async def test_backfill_functions_require_their_identifier_and_date_columns():
    required = pl.DataFrame({"date": [datetime.datetime(2024, 1, 2)]})

    with pytest.raises(ValueError, match="sid.*date"):
        await _backfill_symbol_data(
            pl.DataFrame({"symbol": ["AAA"], "date": required["date"]}),
            _Assets(),
            required,
        )

    with pytest.raises((ColumnNotFoundError, KeyError, TypeError)):
        await backfill_sid_data(
            pl.DataFrame({"sid": [1], "date": required["date"]}),
            _Assets(),
            required,
        )


@pytest.mark.asyncio
async def test_process_data_rejects_start_date_before_first_session():
    calendar = get_calendar("XNYS")
    early_date = datetime.datetime(1800, 1, 1, tzinfo=calendar.tz)
    data = pl.DataFrame({"symbol": ["AAPL"], "date": [early_date]})

    with pytest.raises(ValueError, match="Date start must be after first session"):
        await _process_data(
            data=data,
            date_start=early_date,
            date_end=datetime.datetime(2024, 1, 2, tzinfo=calendar.tz),
            data_frequency_use_window_end=False,
            asset_service=_Assets(),
            name="bundle",
            symbols=["AAPL"],
            trading_calendar=calendar,
            frequency=datetime.timedelta(minutes=1),
        )


@pytest.mark.asyncio
async def test_process_data_rejects_end_date_after_last_session():
    calendar = get_calendar("XNYS")
    late_date = datetime.datetime(2100, 1, 1, tzinfo=calendar.tz)
    data = pl.DataFrame({"symbol": ["AAPL"], "date": [late_date]})

    with pytest.raises(ValueError, match="Date end must be before last session"):
        await _process_data(
            data=data,
            date_start=datetime.datetime(2024, 1, 2, tzinfo=calendar.tz),
            date_end=late_date,
            data_frequency_use_window_end=False,
            asset_service=_Assets(),
            name="bundle",
            symbols=["AAPL"],
            trading_calendar=calendar,
            frequency=datetime.timedelta(minutes=1),
        )


@pytest.mark.asyncio
async def test_process_data_returns_none_on_empty_data():
    calendar = get_calendar("XNYS")
    start = datetime.datetime(2024, 1, 2, 9, 30, tzinfo=calendar.tz)
    end = datetime.datetime(2024, 1, 2, 16, 0, tzinfo=calendar.tz)
    data = pl.DataFrame({"symbol": pl.Series([], dtype=pl.String), "date": pl.Series([], dtype=pl.Datetime)})

    result = await _process_data(
        data=data,
        date_start=start,
        date_end=end,
        data_frequency_use_window_end=False,
        asset_service=_Assets(),
        name="empty_bundle",
        symbols=["AAPL"],
        trading_calendar=calendar,
        frequency=datetime.timedelta(minutes=1),
    )
    assert result is None


@pytest.mark.asyncio
async def test_process_data_rejects_missing_date_column():
    calendar = get_calendar("XNYS")
    start = datetime.datetime(2024, 1, 2, 9, 30, tzinfo=calendar.tz)
    end = datetime.datetime(2024, 1, 2, 16, 0, tzinfo=calendar.tz)
    data = pl.DataFrame({"symbol": ["AAPL"], "price": [150.0]})

    with pytest.raises(ValueError, match="missing required columns: \\['date'\\]"):
        await _process_data(
            data=data,
            date_start=start,
            date_end=end,
            data_frequency_use_window_end=False,
            asset_service=_Assets(),
            name="bad_bundle",
            symbols=["AAPL"],
            trading_calendar=calendar,
            frequency=datetime.timedelta(minutes=1),
        )


@pytest.mark.asyncio
async def test_process_data_rejects_missing_both_symbol_and_sid():
    calendar = get_calendar("XNYS")
    start = datetime.datetime(2024, 1, 2, 9, 30, tzinfo=calendar.tz)
    end = datetime.datetime(2024, 1, 2, 16, 0, tzinfo=calendar.tz)
    data = pl.DataFrame({"date": [start], "price": [150.0]})

    with pytest.raises(ValueError, match="must supply either a symbol or a sid column"):
        await _process_data(
            data=data,
            date_start=start,
            date_end=end,
            data_frequency_use_window_end=False,
            asset_service=_Assets(),
            name="bad_bundle",
            symbols=["AAPL"],
            trading_calendar=calendar,
            frequency=datetime.timedelta(minutes=1),
        )


@pytest.mark.asyncio
async def test_process_data_with_sid_column_and_window_end_daily():
    calendar = get_calendar("XNYS")
    start = datetime.datetime(2024, 1, 2, 9, 30, tzinfo=calendar.tz)
    end = datetime.datetime(2024, 1, 2, 16, 0, tzinfo=calendar.tz)
    data = pl.DataFrame({"sid": [1], "date": [start], "close": [100.0]})

    result = await _process_data(
        data=data,
        date_start=start,
        date_end=end,
        data_frequency_use_window_end=True,
        asset_service=_Assets(),
        name="sid_daily_bundle",
        symbols=["AAPL"],
        trading_calendar=calendar,
        frequency=datetime.timedelta(days=1),
    )
    assert "sid" in result.columns
    assert "date" in result.columns


@pytest.mark.asyncio
async def test_process_data_with_symbol_and_string_frequency_window_end():
    calendar = get_calendar("XNYS")
    start = datetime.datetime(2024, 1, 2, 9, 30, tzinfo=calendar.tz)
    end = datetime.datetime(2024, 1, 2, 16, 0, tzinfo=calendar.tz)
    data = pl.DataFrame({"symbol": ["AAPL"], "date": [start], "close": [100.0]})

    result = await _process_data(
        data=data,
        date_start=start,
        date_end=end,
        data_frequency_use_window_end=True,
        asset_service=_Assets(),
        name="symbol_1d_bundle",
        symbols=["AAPL"],
        trading_calendar=calendar,
        frequency="1d",
    )
    assert "sid" in result.columns
    assert "symbol" in result.columns
