from dataclasses import dataclass
import datetime

from ziplime.assets.entities.asset import Asset


@dataclass(frozen=True)
class FuturesContract(Asset):
    root_symbol: str
    # mapping exchange code -> symbol
    # symbol_mapping: dict[str, str]
    notice_date: datetime.date
    expiration_date: datetime.date
    multiplier: float
    tick_size: float

    # def get_symbol_by_exchange(self, exchange_name: str) -> str | None:
    #     return self.symbol_mapping.get(exchange_name, None)
