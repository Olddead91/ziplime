from ziplime.assets.entities.exchange_asset import ExchangeAsset
from ziplime.finance.commission.commission_model import CommissionModel


class NoCommission(CommissionModel):
    """Model commissions as free.

    Notes
    -----
    This is primarily used for testing.
    """

    def calculate(self, order, transaction) -> float:
        return 0.0

    def calculate_for_asset(self, asset: ExchangeAsset, quantity: int, transaction_amount: float) -> float:
        return 0.0
