from ziplime.assets.entities.asset import Asset
from ziplime.finance.commission.commission_model import CommissionModel


class NoCommission(CommissionModel):
    """Model commissions as free.

    Notes
    -----
    This is primarily used for testing.
    """

    def calculate(self, order, transaction) -> float:
        return 0.0

    def calculate_for_asset(self, asset: Asset, quantity: int) -> float:
        return 0.0
