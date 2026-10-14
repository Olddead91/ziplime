# Release Notes

### Version 2.11.0

Each listing now keeps its own venue's trading hours, so one backtest can hold instruments from
markets that keep different hours. Extensions can now add venues, calendars and data-source
addresses without patching ziplime. `zipfinam` uses this for the Moscow Exchange: MISX, the FORTS
calendar and MOEX AlgoPack.

#### Upgrading from 2.10.3

- **Single-market backtests are unchanged.** A run whose listings all trade on the simulation's
  own calendar gives the same results as on 2.10.3.
- **Moscow venues need zipfinam.** ziplime ships no calendar for MISX or RTSX. Install `zipfinam`
  (1.26.10.1 or later) to have Moscow listings judged by their own hours; without it they are
  judged by the simulation's calendar, as before.

#### Backtest results that change

- **A listing is judged by its own venue's hours.** Before, every listing was judged by the
  simulation's calendar. On an hourly run clocked on Moscow, an American ETF counted as tradeable
  at 10:01 Moscow, which is 03:01 in New York. The order then failed with
  `CannotOrderDelistedAsset: no last price`. Now `data.can_trade` asks the listing's venue. On a
  daily run it asks whether the venue traded that day; on an intraday run it asks about the minute.
- **`context.rebalance` leaves a leg alone while its market is shut.** That leg is neither ordered
  to its target nor closed. Before, the run failed on the first bar where one leg's market was
  closed.

#### New

- `ziplime.utils.venue_calendars`:
  - `calendar_for_mic` gives the calendar a venue keeps, for the US equity venues, CME, NYMEX,
    ICE and the crypto venues;
  - `clock_calendar_name` gives one calendar wide enough for every venue in a run: `24/5` when
    their hours differ, `24/7` when one never closes;
  - `ZIPLIME_VENUE_CALENDARS` overrides the table, as `MIC=CALENDAR,...`.
- **Extension point for venues.** `register_venue_calendars({MIC: calendar})`, or the
  `ziplime.venue_calendars` entry point group, which is loaded on first lookup.
- **Extension point for data-source addresses.** `register_address_scheme(scheme, mount)`, or the
  `ziplime.address_schemes` entry point group. A strategy then reads
  `data.history(..., data_source="scheme://...")` with no registration of its own. `hf://` stays
  built in.
- `ExchangeAsset.trading_calendar`: the listing's own venue calendar, or `None` for a venue not
  in the table. Callers then fall back to the simulation's calendar.
- Ordering a listing whose market is closed now says so and names both calendars. Before, the
  error blamed delisting.

### Version 1.10.16
- Raise proper exception when data bundle is not found

### Version 1.9.18
- Add asset mic in database
- Add default assets database file
- Update examples
- Add cache of currencies query
- Allow calendar dates older than 2005

### Version 1.8.21
- Use scan_parquet to load bundle data partially
- Throw proper error in bundle when data is missing
- Add an option to configure the logging level and log to the file
- Add a start / end auction date to allow getting open/close prices at a specific time in the day when running daily simulation for a minute data bundle
- Allow custom aggregations when using aggregated low-frequency data bundle in simulation
- Symbols universe
- Support for ingesting market data from Yahoo Finance

### Version 1.7.14
- Custom data - Limex fundamental data ingestion
- Add all frequencies supported by polars
- Allow both string and timedelta as frequency
- Add option to use custom CSV data
- Use float for all decimal types

### Version 1.6.26
- Add the forward_fill_missing_ohlcv_data parameter to the BundleService ingest_data function

### Version v1.6.11
- Add an option to continue running algorith on error - stop_on_error

### Version v1.6.2
- Remove uvloop to improve compatibility with Windows OS

### Version v1.5.30
- Add additional ETF/stock symbols
- Log warning if the price is missing when updating the last sale price in positions dict

### Version v1.5.29
- Add ETF symbols to all symbols list

### Version v1.5.28
- Fix simulation error when data is missing during ingestion
