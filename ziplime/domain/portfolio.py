import datetime
from dataclasses import dataclass, field
from ziplime.assets.entities.exchange_asset import ExchangeAsset
from ziplime.domain.position import Position


@dataclass
class Portfolio:
    # capital_used: float
    cash_flow: float
    starting_cash: float
    portfolio_value: float
    pnl: float
    returns: float
    cash: float
    positions_value: float
    positions_exposure: float
    # exchange_portfolios: dict[str, Self]

    positions: dict[ExchangeAsset, Position] = field(default_factory=dict)

    start_date: datetime.datetime | None = None

    def get_asset_positions(self, asset: ExchangeAsset) -> list[Position]:
        positions = [position for exchange in self.positions.values() for trading_accounts in exchange.values()
                              for position in trading_accounts.values() if position.asset.sid == asset.sid]
        return positions
