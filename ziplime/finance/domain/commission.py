from dataclasses import dataclass

from ziplime.assets.entities.exchange_asset import ExchangeAsset
from ziplime.finance.domain.order import Order


@dataclass
class Commission:
    asset: ExchangeAsset
    order: Order
    amount: float
