from dataclasses import dataclass


@dataclass(frozen=True)
class ExchangeInfo:
    mic: str
    name: str
    canonical_name: str
    country_code: str
