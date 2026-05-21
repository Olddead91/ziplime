from dataclasses import dataclass

from ziplime.assets.entities.exchange_asset import ExchangeAsset


@dataclass(frozen=True)
class TradingPair:
    base_asset: ExchangeAsset
    quote_asset: ExchangeAsset
    exchange_name: str
