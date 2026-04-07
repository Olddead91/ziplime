import polars as pl
import structlog

from ziplime.assets.services.asset_service import AssetService
from ziplime.assets.entities.asset import  Asset
_logger = structlog.get_logger(__name__)


async def backfill_sid_data(data: pl.DataFrame, assetse: list[Asset], required_sessions: pl.Series):
    """Backfills missing symbol ID (sid) data in a DataFrame by performing lookups and handling missing
    data sessions. Used when symbols are provided in the input DataFrame but not sids.

    The method updates the input DataFrame by:
    1. Mapping symbols to their corresponding sid using the asset service.
    2. Backfilling missing data for required sessions.
    3. Logging warnings for missing data sessions.
    4. Raising an exception for any symbols absent from the asset database.

    Args:
        data (pl.DataFrame): A Polars DataFrame containing at least 'symbol' and 'date' columns.
        asset_service (AssetService): An instance of AssetService used to fetch equities by symbol.
        required_sessions (pl.Series): A Polars Series containing the required session dates.

    Returns:
        pl.DataFrame: Updated DataFrame with backfilled sid data.

    Raises:
        ValueError: If any symbols are missing in the asset database.
    """
    unique_symbols = list(data["symbol"].unique())
    symbol_to_sid = {a.get_symbol_by_exchange(exchange_name=None): a.sid for a in
                     await asset_service.get_equities_by_symbols(unique_symbols)}
    data = data.with_columns(
        pl.lit(0).alias("sid"),
    )

    for symbol in unique_symbols:
        symbol_data = data.filter(symbol=symbol).with_columns(pl.col("date"))
        missing_sessions = sorted(set(required_sessions["date"]) - set(symbol_data["date"]))

        if len(missing_sessions) > 0:
            self._logger.warning(
                f"Data for symbol {symbol} is missing on ticks ({len(missing_sessions)}): {[missing_session.isoformat() for missing_session in missing_sessions]}")
            new_rows_df = pl.DataFrame(
                {"date": missing_sessions, "symbol": symbol},
                schema_overrides={"date": data.schema["date"]}
            )
            # Concatenate with the original DataFrame
            data = pl.concat([data, new_rows_df], how="diagonal")
        missing_symbols = set(unique_symbols) - set(symbol_to_sid)
        if missing_symbols:
            raise ValueError(f"Symbols are missing in asset database: {missing_symbols}")

        data = data.with_columns(
            pl.col("symbol").replace(symbol_to_sid).cast(pl.Int64).alias("sid")
        ).sort(["sid", "date"])
    return data
