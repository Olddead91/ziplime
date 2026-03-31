import datetime
from dataclasses import dataclass

from ziplime.assets.entities.asset import Asset


@dataclass
class Transaction:
    id: str
    asset: Asset
    amount: int
    dt: datetime.datetime
    price: float
    order_id: str
    exchange_name: str
    commission: float | None = None
    realized_pnl: float = 0.0

    def total_price(self) -> float:
        return self.price * self.amount
