# Release Notes

### Version 2.11.0

Each listing now keeps its own venue's trading hours, so one backtest can hold instruments from
markets that keep different hours. MOEX AlgoPack tables mount the same way Hugging Face datasets
do.

#### Upgrading from 2.10.3

- **AlgoPack is a pip extra:** `pip install "ziplime[algopack]"`. It also needs a subscription key
  in `ALGOPACK_API`, or call `ziplime.data.data_sources.algopack.api.set_token(...)`.
- **Single-market backtests are unchanged.** A run whose listings all trade on the simulation's
  own calendar gives the same results as on 2.10.3.

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
  - `calendar_for_mic` gives the calendar a venue keeps;
  - `clock_calendar_name` gives one calendar wide enough for every venue in a run, `24/5` when
    their hours differ;
  - `ZIPLIME_VENUE_CALENDARS` overrides the table, as `MIC=CALENDAR,...`.
- A `FORTS` calendar for the Moscow derivatives market: 09:00 to 23:50 Moscow, with the 18:50 to
  19:05 clearing break. It is built on XMOS, so the Russian holidays stay the same.
  `exchange_calendars` ships none, and XMOS is the equity session, which ends at 18:45.
- `ExchangeAsset.trading_calendar`: the listing's own venue calendar, or `None` for a venue not
  in the table. Callers then fall back to the simulation's calendar.
- MOEX AlgoPack datasets as `algopack://market/dataset[/granularity]`. Read one with
  `data.history(..., data_source="algopack://eq/tradestats")`, or mount one with
  `context.algopack_dataset("tradestats", granularity="5min")`. The tables are `tradestats`,
  `orderstats`, `obstats`, `hi2`, `alerts` and `futoi`, on the `eq`, `fo` and `fx` markets. Each
  row becomes visible only when the exchange published it. Finished months are cached to Parquet
  in `ALGOPACK_CACHE_DIR`, so a re-run does no network.
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
