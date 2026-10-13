import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import polars as pl
import pytest
from exchange_calendars import get_calendar
from lime_trader.models.market import Period

from ziplime.assets.entities.asset import Asset
from ziplime.assets.entities.exchange_asset import ExchangeAsset
from ziplime.assets.entities.exchange_info import ExchangeInfo
from ziplime.data.services.lime_trader_sdk_data_source import LimeTraderSdkDataSource


class DummyQuote:
    def __init__(self, open=100.0, high=105.0, low=95.0, close=102.0, volume=1000.0, timestamp=None, symbol="AAPL"):
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.timestamp = timestamp or datetime.datetime(2024, 1, 3, 16, 0, tzinfo=datetime.timezone.utc)
        self.date = self.timestamp
        self.symbol = symbol


@pytest.fixture
def dummy_exchange_asset():
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
    return ExchangeAsset(
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


def test_frequency_to_period():
    calendar = get_calendar("XNYS")
    with patch("lime_trader.AsyncLimeClient.from_env"), patch("lime_trader.LimeClient.from_env"):
        source = LimeTraderSdkDataSource(lime_sdk_credentials_file=None, trading_calendar=calendar)
        assert source._frequency_to_period(datetime.timedelta(minutes=1)) == Period.MINUTE
        assert source._frequency_to_period(datetime.timedelta(minutes=5)) == Period.MINUTE_5
        assert source._frequency_to_period(datetime.timedelta(hours=1)) == Period.HOUR
        assert source._frequency_to_period(datetime.timedelta(days=1)) == Period.DAY

        with pytest.raises(ValueError, match="Unknown frequency"):
            source._frequency_to_period(datetime.timedelta(seconds=42))


@pytest.mark.asyncio
async def test_get_data(dummy_exchange_asset):
    calendar = get_calendar("XNYS")
    tz = calendar.tz

    with patch("lime_trader.AsyncLimeClient.from_env") as mock_async_client, \
         patch("lime_trader.LimeClient.from_env"):
        client_inst = MagicMock()
        mock_async_client.return_value = client_inst

        quote = DummyQuote(timestamp=datetime.datetime(2024, 1, 3, 16, 0, tzinfo=tz))
        client_inst.market.get_quotes_history = AsyncMock(return_value=[quote])

        source = LimeTraderSdkDataSource(lime_sdk_credentials_file=None, trading_calendar=calendar)

        date_from = datetime.datetime(2024, 1, 2, tzinfo=tz)
        date_to = datetime.datetime(2024, 1, 4, tzinfo=tz)
        df = await source.get_data(
            symbols=["AAPL"],
            frequency=datetime.timedelta(days=1),
            date_from=date_from,
            date_to=date_to,
        )
        assert len(df) == 1
        assert df["symbol"][0] == "AAPL"
        assert df["close"][0] == 102.0
