"""A listing is judged by its own venue's hours, and a mixed run is clocked wide enough for all.

The bug these cover: a simulation ran on one calendar and every listing was judged by it, so an
American ETF on a Moscow clock was declared tradeable at 10:01 Moscow -- 03:01 in New York -- and
the order died in `_calculate_order_value_amount` with a message about delisting. Daily runs hid
it, because a daily bar sits at the Moscow close, which is the middle of the American session.

The strategies this was fixed for are cross-market spreads, where most bars have one leg shut.

ziplime ships no Moscow venue: zipfinam registers MISX and RTSX through the extension point. These
tests register them the same way, RTSX on a stand-in for zipfinam's FORTS calendar, so what they
cover is the mechanism; the real FORTS calendar is tested in zipfinam.
"""

import datetime
import os
import types
import unittest
from unittest import mock
from zoneinfo import ZoneInfo

import exchange_calendars as xcals
import pandas as pd
from exchange_calendars.exchange_calendar_xmos import XMOSExchangeCalendar

from ziplime.assets.entities.currency import Currency
from ziplime.assets.entities.equity import Equity
from ziplime.assets.entities.exchange_asset import ExchangeAsset
from ziplime.assets.entities.exchange_info import ExchangeInfo
from ziplime.domain.bar_data import BarData
from ziplime.finance.asset_restrictions import NoRestrictions
from ziplime.utils.calendar_utils import get_calendar
from ziplime.utils import venue_calendars
from ziplime.utils.venue_calendars import (
    CONTINUOUS_CLOCK,
    ENTRY_POINT_GROUP,
    MIXED_VENUE_CLOCK,
    VENUE_CALENDARS_ENV,
    calendar_for_mic,
    calendar_name_for_mic,
    clock_calendar_name,
    covers,
    register_venue_calendars,
    trades_every_day,
    unregister_venue_calendars,
)

FAR_PAST = datetime.date(1990, 1, 1)
FAR_FUTURE = datetime.date(2099, 1, 1)

#: A Wednesday both markets trade, chosen so no holiday of either is involved.
SESSION = datetime.date(2025, 9, 24)


def listing(symbol: str, mic: str, sid: int = 1) -> ExchangeAsset:
    exchange = ExchangeInfo(mic=mic, name=mic, canonical_name=mic, country_code="US")
    equity = Equity(id=sid + 10_000, isin=None, asset_name=symbol, start_date=FAR_PAST,
                    end_date=FAR_FUTURE, first_traded=FAR_PAST, auto_close_date=FAR_FUTURE)
    usd = Currency(id=2, isin=None, asset_name="USD", start_date=FAR_PAST, end_date=FAR_FUTURE,
                   first_traded=FAR_PAST, auto_close_date=FAR_FUTURE)
    return ExchangeAsset(sid=sid, symbol=symbol, start_date=FAR_PAST, end_date=FAR_FUTURE,
                         first_traded=FAR_PAST, auto_close_date=FAR_FUTURE, external_id="",
                         exchange=exchange, asset=equity, quote=usd)


def moscow(hour: int, minute: int = 0) -> datetime.datetime:
    return pd.Timestamp(datetime.datetime(SESSION.year, SESSION.month, SESSION.day, hour, minute),
                        tz="Europe/Moscow").to_pydatetime()


class EveningMoscowCalendar(XMOSExchangeCalendar):
    """A stand-in for zipfinam's FORTS: XMOS's holidays, 09:00-23:50 Moscow with a clearing break."""

    name = "TEST_EVENING_MOSCOW"
    tz = ZoneInfo("Europe/Moscow")
    open_times = ((None, datetime.time(9)),)
    break_start_times = ((None, datetime.time(18, 50)),)
    break_end_times = ((None, datetime.time(19, 5)),)
    close_times = ((None, datetime.time(23, 50)),)


try:
    xcals.register_calendar_type(EveningMoscowCalendar.name, EveningMoscowCalendar)
except ValueError:
    pass

#: What an extension for Moscow registers -- zipfinam's mapping, with the stand-in for FORTS.
MOSCOW_VENUES = {"MISX": "XMOS", "RTSX": EveningMoscowCalendar.name}


class WithMoscow(unittest.TestCase):
    """Moscow registered for the duration of each test, as an extension would register it."""

    def setUp(self):
        register_venue_calendars(MOSCOW_VENUES)
        self.addCleanup(unregister_venue_calendars, MOSCOW_VENUES)


class VenueLookupTests(WithMoscow):

    def test_registered_moscow_venues_keep_different_hours(self):
        self.assertEqual(calendar_name_for_mic("MISX"), "XMOS")
        self.assertEqual(calendar_name_for_mic("RTSX"), EveningMoscowCalendar.name)

    def test_every_american_equity_venue_keeps_the_nyse_session(self):
        for mic in ("ARCX", "BATS", "XASE", "XNCM", "XNGS", "XNMS", "XNYS"):
            self.assertEqual(calendar_name_for_mic(mic), "XNYS", mic)

    def test_an_unknown_venue_has_no_opinion_rather_than_a_wrong_one(self):
        self.assertIsNone(calendar_name_for_mic("ZZZZ"))
        self.assertIsNone(calendar_for_mic("ZZZZ"))
        self.assertIsNone(calendar_name_for_mic(None))

    def test_a_listing_carries_its_venues_calendar(self):
        self.assertEqual(listing("SPY", "ARCX").trading_calendar.name, "XNYS")
        self.assertEqual(listing("SBER", "MISX").trading_calendar.name, "XMOS")
        self.assertIsNone(listing("X", "ZZZZ").trading_calendar)


class ClockSelectionTests(WithMoscow):
    """What a run is clocked on, given where its instruments list."""

    def test_one_market_keeps_its_own_calendar(self):
        self.assertEqual(clock_calendar_name(["MISX"]), "XMOS")
        self.assertEqual(clock_calendar_name(["ARCX", "XNGS", "XNMS"]), "XNYS")

    def test_venues_that_keep_different_hours_need_a_wider_clock(self):
        self.assertEqual(clock_calendar_name(["MISX", "ARCX"]), MIXED_VENUE_CLOCK)
        self.assertEqual(clock_calendar_name(["RTSX", "XNYM"]), MIXED_VENUE_CLOCK)

    def test_the_mixed_clock_covers_both_markets_whole_sessions(self):
        """Because it keeps every hour of every weekday, which neither market's calendar does."""
        clock = get_calendar(MIXED_VENUE_CLOCK)
        for minute in (moscow(9, 30), moscow(12), moscow(17), moscow(21), moscow(23, 30)):
            self.assertTrue(clock.is_open_on_minute(minute), minute)

    def test_nothing_known_leaves_the_choice_to_the_caller(self):
        self.assertIsNone(clock_calendar_name([]))
        self.assertIsNone(clock_calendar_name(["ZZZZ"]))


class CryptoVenueTests(WithMoscow):
    """Venues that never close, which a weekday clock cannot hold at all."""

    #: A Saturday, and a Sunday two days later.
    SATURDAY = pd.Timestamp("2025-09-27")
    SUNDAY = pd.Timestamp("2025-09-28")

    def test_the_crypto_venues_in_the_asset_databases_are_mapped(self):
        for mic in ("KRME", "_BNCC", "_BNCF"):
            self.assertEqual(calendar_name_for_mic(mic), CONTINUOUS_CLOCK, mic)

    def test_a_crypto_venue_trades_at_the_weekend(self):
        calendar = calendar_for_mic("_BNCC")
        self.assertTrue(calendar.is_session(self.SATURDAY))
        self.assertTrue(calendar.is_session(self.SUNDAY))

    def test_a_seven_day_week_is_read_off_the_calendar_rather_than_listed_here(self):
        """So a venue added through the environment is classified without this module knowing."""
        self.assertTrue(trades_every_day(CONTINUOUS_CLOCK))
        for name in (MIXED_VENUE_CLOCK, "XNYS", "XMOS", EveningMoscowCalendar.name):
            self.assertFalse(trades_every_day(name), name)

    def test_crypto_alone_keeps_the_continuous_clock(self):
        self.assertEqual(clock_calendar_name(["_BNCC"]), CONTINUOUS_CLOCK)
        self.assertEqual(clock_calendar_name(["_BNCC", "KRME"]), CONTINUOUS_CLOCK)

    def test_anything_mixed_with_crypto_needs_the_weekend_too(self):
        """A weekday clock would not mis-time the weekend bars, it would delete them."""
        for mics in (["_BNCC", "XNGS"], ["_BNCC", "MISX"], ["_BNCF", "RTSX", "XNYM"]):
            self.assertEqual(clock_calendar_name(mics), CONTINUOUS_CLOCK, mics)

    def test_a_mix_without_crypto_still_gets_the_cheaper_weekday_clock(self):
        self.assertEqual(clock_calendar_name(["MISX", "ARCX"]), MIXED_VENUE_CLOCK)

    def test_an_equity_is_shut_on_a_weekend_session_of_the_continuous_clock(self):
        saturday = pd.Timestamp(datetime.datetime(2025, 9, 27, 12),
                                tz="Europe/Moscow").to_pydatetime()
        self.assertFalse(CanTradeAcrossVenuesTests().can_trade(
            listing("GLD", "ARCX"), saturday, CONTINUOUS_CLOCK, datetime.timedelta(days=1)))

    def test_a_crypto_listing_is_open_on_that_same_session(self):
        saturday = pd.Timestamp(datetime.datetime(2025, 9, 27, 12),
                                tz="Europe/Moscow").to_pydatetime()
        for rate in (datetime.timedelta(days=1), datetime.timedelta(hours=1)):
            self.assertTrue(CanTradeAcrossVenuesTests().can_trade(
                listing("BTCUSDT", "_BNCC"), saturday, CONTINUOUS_CLOCK, rate), rate)

    def test_crypto_is_open_at_three_in_the_morning(self):
        night = pd.Timestamp(datetime.datetime(2025, 9, 24, 3),
                             tz="Europe/Moscow").to_pydatetime()
        self.assertTrue(CanTradeAcrossVenuesTests().can_trade(
            listing("BTCUSDT", "_BNCC"), night, CONTINUOUS_CLOCK, datetime.timedelta(hours=1)))


class VenueOverrideTests(WithMoscow):
    """A new venue can be added without rebuilding the core, which crypto makes routine."""

    def setUp(self):
        super().setUp()
        self.addCleanup(os.environ.pop, VENUE_CALENDARS_ENV, None)

    def set_override(self, value: str):
        os.environ[VENUE_CALENDARS_ENV] = value

    def test_a_venue_absent_from_the_table_can_be_named(self):
        self.assertIsNone(calendar_name_for_mic("MEXC"))
        self.set_override("MEXC=24/7")
        self.assertEqual(calendar_name_for_mic("MEXC"), CONTINUOUS_CLOCK)
        self.assertEqual(clock_calendar_name(["MEXC", "XNGS"]), CONTINUOUS_CLOCK)

    def test_several_entries_and_untidy_spacing_are_accepted(self):
        self.set_override(" mexc = 24/7 , XHKG=XHKG ")
        self.assertEqual(calendar_name_for_mic("MEXC"), CONTINUOUS_CLOCK)
        self.assertEqual(calendar_name_for_mic("XHKG"), "XHKG")

    def test_an_override_wins_over_the_shipped_table(self):
        self.set_override("ARCX=24/7")
        self.assertEqual(calendar_name_for_mic("ARCX"), CONTINUOUS_CLOCK)

    def test_an_override_wins_over_an_extension(self):
        self.set_override("MISX=24/7")
        self.assertEqual(calendar_name_for_mic("MISX"), CONTINUOUS_CLOCK)

    def test_the_table_comes_back_once_the_override_is_gone(self):
        self.set_override("MISX=24/7")
        self.assertEqual(calendar_name_for_mic("MISX"), CONTINUOUS_CLOCK)
        del os.environ[VENUE_CALENDARS_ENV]
        self.assertEqual(calendar_name_for_mic("MISX"), "XMOS")

    def test_rubbish_is_ignored_rather_than_fatal(self):
        """It is set on a deployment, and a typo there must not take every run down."""
        self.set_override("nonsense,,=,MEXC=24/7,XXXX=NoSuchCalendar")
        self.assertEqual(calendar_name_for_mic("MEXC"), CONTINUOUS_CLOCK)
        self.assertIsNone(calendar_for_mic("XXXX"), "an unresolvable name behaves as unknown")


class CanTradeAcrossVenuesTests(WithMoscow):
    """`can_trade` asks the listing's venue, not the simulation's calendar."""

    @staticmethod
    def bar_data(dt: datetime.datetime, clock: str, emission_rate):
        source = types.SimpleNamespace(name="test", last_available_bar=lambda sid=None: None)
        return BarData(data_sources={"test": source}, simulation_dt_func=lambda: dt,
                       trading_calendar=get_calendar(clock), restrictions=NoRestrictions(),
                       emission_rate=emission_rate)

    def can_trade(self, asset, dt, clock, emission_rate):
        return bool(self.bar_data(dt, clock, emission_rate).can_trade(assets=[asset]).iloc[0])

    def test_an_american_listing_is_not_tradeable_at_the_moscow_open(self):
        """The bug: 10:01 Moscow is 03:01 in New York, and the order used to be attempted."""
        self.assertFalse(self.can_trade(listing("GLD", "ARCX"), moscow(10, 1), "XMOS",
                                        datetime.timedelta(hours=1)))

    def test_it_is_tradeable_once_new_york_opens(self):
        self.assertTrue(self.can_trade(listing("GLD", "ARCX"), moscow(17), "XMOS",
                                       datetime.timedelta(hours=1)))

    def test_a_daily_bar_asks_about_the_day_rather_than_the_minute(self):
        """A daily run puts its bar at the simulation calendar's close, which means nothing
        anywhere else -- and daily US-on-Moscow runs work today, so they must keep working."""
        self.assertTrue(self.can_trade(listing("GLD", "ARCX"), moscow(18, 45), "XMOS",
                                       datetime.timedelta(days=1)))

    def test_a_venues_own_holiday_closes_it_even_on_a_daily_run(self):
        thanksgiving = pd.Timestamp(datetime.datetime(2025, 11, 27, 18, 45),
                                    tz="Europe/Moscow").to_pydatetime()
        self.assertFalse(self.can_trade(listing("GLD", "ARCX"), thanksgiving, "XMOS",
                                        datetime.timedelta(days=1)))

    def test_a_moscow_listing_on_a_mixed_clock_follows_the_moscow_session(self):
        moscow_equity = listing("SBER", "MISX")
        hourly = datetime.timedelta(hours=1)
        self.assertTrue(self.can_trade(moscow_equity, moscow(12), MIXED_VENUE_CLOCK, hourly))
        self.assertFalse(self.can_trade(moscow_equity, moscow(21), MIXED_VENUE_CLOCK, hourly))

    def test_a_futures_listing_on_a_mixed_clock_trades_into_the_evening(self):
        """Which is the whole reason FORTS exists: XMOS would have said no at 21:00."""
        self.assertTrue(self.can_trade(listing("NGZ6", "RTSX"), moscow(21), MIXED_VENUE_CLOCK,
                                       datetime.timedelta(hours=1)))

    def test_an_unknown_venue_still_follows_the_simulation_calendar(self):
        """The behaviour that predates listings carrying their own hours."""
        self.assertTrue(self.can_trade(listing("X", "ZZZZ"), moscow(12), "XMOS",
                                       datetime.timedelta(hours=1)))


class ContainedCalendarTests(WithMoscow):
    """A venue whose hours already hold the others' does not need a 24-hour clock."""

    def test_the_evening_session_contains_the_equity_one(self):
        self.assertTrue(covers(EveningMoscowCalendar.name, "XMOS"))
        self.assertFalse(covers("XMOS", EveningMoscowCalendar.name),
                         "the narrow one does not contain the wide one")

    def test_containment_needs_the_same_zone(self):
        """Otherwise 24/7 would swallow everything and the zones would not line up."""
        self.assertFalse(covers(CONTINUOUS_CLOCK, "XNYS"))
        self.assertFalse(covers(MIXED_VENUE_CLOCK, "XMOS"))

    def test_moscow_shares_beside_moscow_futures_are_clocked_on_the_wider_session(self):
        self.assertEqual(clock_calendar_name(["MISX", "RTSX"]), EveningMoscowCalendar.name)

    def test_venues_that_genuinely_miss_each_other_still_need_the_wide_clock(self):
        self.assertEqual(clock_calendar_name(["MISX", "ARCX"]), MIXED_VENUE_CLOCK)
        self.assertEqual(clock_calendar_name(["RTSX", "XNYM"]), MIXED_VENUE_CLOCK)


class ExtensionTests(unittest.TestCase):
    """How a market ziplime does not ship gets its venues in."""

    def tearDown(self):
        unregister_venue_calendars(["MISX", "RTSX", "ARCX", "XHKG"])

    def test_moscow_is_not_shipped_with_the_core(self):
        self.assertIsNone(calendar_name_for_mic("MISX"))
        self.assertIsNone(calendar_name_for_mic("RTSX"))

    def test_a_registered_venue_is_looked_up_and_can_be_taken_back(self):
        register_venue_calendars({"misx ": "XMOS"})
        self.assertEqual(calendar_for_mic("MISX").name, "XMOS")
        self.assertEqual(listing("SBER", "MISX").trading_calendar.name, "XMOS")
        unregister_venue_calendars(["MISX"])
        self.assertIsNone(calendar_for_mic("MISX"), "the cached answer must not survive")

    def test_an_extension_wins_over_the_shipped_table(self):
        register_venue_calendars({"ARCX": CONTINUOUS_CLOCK})
        self.assertEqual(calendar_name_for_mic("ARCX"), CONTINUOUS_CLOCK)
        unregister_venue_calendars(["ARCX"])
        self.assertEqual(calendar_name_for_mic("ARCX"), "XNYS")

    def test_an_unresolvable_calendar_behaves_as_an_unknown_venue(self):
        register_venue_calendars({"XHKG": "NoSuchCalendar"})
        self.assertEqual(calendar_name_for_mic("XHKG"), "NoSuchCalendar")
        self.assertIsNone(calendar_for_mic("XHKG"))

    def _with_entry_points(self, *advertised):
        """Pretend these entry points are installed, and make the module read them afresh."""
        patcher = mock.patch("importlib.metadata.entry_points",
                             lambda group: [ep for ep in advertised if group == ENTRY_POINT_GROUP])
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(setattr, venue_calendars, "_entry_points_loaded", True)
        venue_calendars._entry_points_loaded = False
        venue_calendars._clear_caches()

    @staticmethod
    def _entry_point(name, provided):
        return types.SimpleNamespace(name=name, load=lambda: provided)

    def test_an_installed_extension_is_picked_up_without_being_imported(self):
        """Installing zipfinam is all a deployment does; nothing in the service imports it."""
        self._with_entry_points(self._entry_point("moscow", lambda: MOSCOW_VENUES))
        self.assertEqual(calendar_name_for_mic("RTSX"), EveningMoscowCalendar.name)

    def test_an_extension_may_advertise_a_plain_mapping(self):
        self._with_entry_points(self._entry_point("moscow", {"MISX": "XMOS"}))
        self.assertEqual(calendar_name_for_mic("MISX"), "XMOS")

    def test_a_broken_extension_is_skipped_rather_than_fatal(self):
        def broken():
            raise RuntimeError("extension failed to import")

        self._with_entry_points(types.SimpleNamespace(name="broken", load=broken),
                                self._entry_point("moscow", {"MISX": "XMOS"}))
        self.assertEqual(calendar_name_for_mic("MISX"), "XMOS")
        self.assertEqual(calendar_name_for_mic("ARCX"), "XNYS")


if __name__ == "__main__":
    unittest.main()
