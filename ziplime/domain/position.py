import datetime
from dataclasses import dataclass

from ziplime.assets.entities.exchange_asset import ExchangeAsset


@dataclass
class Position:
    asset: ExchangeAsset
    amount: int
    cost_basis: float  # per share
    last_sale_price: float
    last_sale_date: datetime.datetime | None = None
