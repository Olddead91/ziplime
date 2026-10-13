import datetime
import polars as pl
import pytest
from exchange_calendars import get_calendar

from ziplime.constants.data_type import DataType
from ziplime.data.services.data_source import DataSource
from ziplime.assets.entities.asset import Asset
from ziplime.assets.entities.exchange_asset import ExchangeAsset
from ziplime.assets.entities.exchange_info import ExchangeInfo


class DummyDataSource(DataSource):
    def __init__(self, data: pl.DataFrame, calendar):
        self.data = data
        start_date = data["date"].min()
        end_date = data["date"].max()
        super().__init__(
            name="dummy",
            start_date=start_date,
            end_date=end_date,
            frequency=datetime.timedelta(days=1),
            original_frequency=datetime.timedelta(days=1),
            data_type=DataType.MARKET_DATA,
            trading_calendar=calendar,
        )


def test_data_source_get_data_by_date():
    calendar = get_calendar("XNYS")
    tz = calendar.tz

    dates = [
        datetime.datetime(2024, 1, 2, 16, 0, tzinfo=tz),
        datetime.datetime(2024, 1, 3, 16, 0, tzinfo=tz),
        datetime.datetime(2024, 1, 4, 16, 0, tzinfo=tz),
        datetime.datetime(2024, 1, 5, 16, 0, tzinfo=tz),
    ]
    df = pl.DataFrame({
        "date": dates,
        "sid": [1, 1, 1, 1],
        "close": [100.0, 101.0, 102.0, 103.0],
    })

    source = DummyDataSource(data=df, calendar=calendar)
    assert source.last_available_bar() is None

    asset = Asset(
        id=1,
        isin="US0378331005",
        asset_name="Apple",
        start_date=datetime.date(2020, 1, 1),
        end_date=datetime.date(2030, 1, 1),
        first_traded=datetime.date(2020, 1, 1),
        auto_close_date=datetime.date(2030, 1, 1),
    )
    quote = Asset(
        id=2,
        isin=None,
        asset_name="USD",
        start_date=datetime.date(2020, 1, 1),
        end_date=datetime.date(2030, 1, 1),
        first_traded=datetime.date(2020, 1, 1),
        auto_close_date=datetime.date(2030, 1, 1),
    )
    exchange = ExchangeInfo(
        mic="XNGS",
        name="NASDAQ",
        canonical_name="NASDAQ",
        country_code="US",
    )
    exchange_asset = ExchangeAsset(
        sid=1,
        symbol="AAPL",
        start_date=datetime.date(2020, 1, 1),
        end_date=datetime.date(2030, 1, 1),
        first_traded=datetime.date(2020, 1, 1),
        auto_close_date=datetime.date(2030, 1, 1),
        external_id="AAPL-XNGS",
        exchange=exchange,
        asset=asset,
        quote=quote,
    )

    result_df = source.get_data_by_date(
        fields=frozenset(["close"]),
        from_date=dates[1],
        to_date=dates[2],
        frequency=datetime.timedelta(days=1),
        assets=frozenset([exchange_asset]),
        include_bounds=True,
    )
    assert len(result_df) == 1
    # Check that sid group contains the bounded dates
    assert result_df["sid"][0] == 1


@pytest.mark.asyncio
async def test_data_source_get_data_by_limit():
    calendar = get_calendar("XNYS")
    tz = calendar.tz

    dates = [
        datetime.datetime(2024, 1, 2, 16, 0, tzinfo=tz),
        datetime.datetime(2024, 1, 3, 16, 0, tzinfo=tz),
        datetime.datetime(2024, 1, 4, 16, 0, tzinfo=tz),
        datetime.datetime(2024, 1, 5, 16, 0, tzinfo=tz),
    ]
    df = pl.DataFrame({
        "date": dates,
        "sid": [1, 1, 1, 1],
        "close": [100.0, 101.0, 102.0, 103.0],
    })

    source = DummyDataSource(data=df, calendar=calendar)

    asset = Asset(
        id=1,
        isin="US0378331005",
        asset_name="Apple",
        start_date=datetime.date(2020, 1, 1),
        end_date=datetime.date(2030, 1, 1),
        first_traded=datetime.date(2020, 1, 1),
        auto_close_date=datetime.date(2030, 1, 1),
    )
    quote = Asset(
        id=2,
        isin=None,
        asset_name="USD",
        start_date=datetime.date(2020, 1, 1),
        end_date=datetime.date(2030, 1, 1),
        first_traded=datetime.date(2020, 1, 1),
        auto_close_date=datetime.date(2030, 1, 1),
    )
    exchange = ExchangeInfo(
        mic="XNGS",
        name="NASDAQ",
        canonical_name="NASDAQ",
        country_code="US",
    )
    exchange_asset = ExchangeAsset(
        sid=1,
        symbol="AAPL",
        start_date=datetime.date(2020, 1, 1),
        end_date=datetime.date(2030, 1, 1),
        first_traded=datetime.date(2020, 1, 1),
        auto_close_date=datetime.date(2030, 1, 1),
        external_id="AAPL-XNGS",
        exchange=exchange,
        asset=asset,
        quote=quote,
    )

    limit_df = await source.get_data_by_limit(
        fields=frozenset(["close"]),
        limit=2,
        end_date=dates[2],
        frequency=datetime.timedelta(days=1),
        assets=frozenset([exchange_asset]),
        include_end_date=True,
    )
    assert len(limit_df) == 2
