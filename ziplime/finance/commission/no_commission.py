from ziplime.finance.commission.commission_model import CommissionModel


class NoCommission(CommissionModel):
    """Model commissions as free.

    Notes
    -----
    This is primarily used for testing.
    """

    @staticmethod
    def calculate(order, transaction):
        return 0.0

