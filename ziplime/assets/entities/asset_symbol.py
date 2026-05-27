from dataclasses import dataclass


@dataclass(frozen=True)
class AssetSymbol:
    symbol: str
    mic: str | None
