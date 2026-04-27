import datetime
from dataclasses import dataclass

from ziplime.assets.entities.asset import Asset


@dataclass
class Transaction:
    id: str
    amount: int
    dt: datetime.datetime
    price: float
    exchange_name: str
    trading_account_id: str


    order_id: str = None
    asset: Asset = None
    commission: float | None = None
    realized_pnl: float = 0.0

    def total_price(self) -> float:
        return self.price * self.amount
