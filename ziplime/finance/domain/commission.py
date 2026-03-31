from dataclasses import dataclass

from ziplime.assets.entities.asset import Asset
from ziplime.finance.domain.order import Order


@dataclass
class Commission:
    asset: Asset
    order: Order
    amount: float
