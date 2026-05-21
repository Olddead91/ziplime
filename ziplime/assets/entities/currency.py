from dataclasses import dataclass

from ziplime.assets.entities.asset import Asset


@dataclass(frozen=True)
class Currency(Asset):
    pass
    # symbol_mapping: dict[str, CurrencySymbolMapping]

    # def get_symbol_by_exchange(self, exchange_name: str) -> str | None:
    #     return self.symbol_mapping.get(exchange_name, None)
