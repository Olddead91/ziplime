from ziplime.finance.commission.equity_commission_model import EquityCommissionModel


class PerDollar(EquityCommissionModel):
    """
    Model commissions by applying a fixed cost per dollar transacted.

    Parameters
    ----------
    cost : float, optional
        The flat amount of commissions paid per dollar of equities
        traded. Default is a commission of $0.0015 per dollar transacted.
    """

    def __init__(self, cost: float):
        """
        Cost parameter is the cost of a trade per-dollar. 0.0015
        on $1 million means $1,500 commission (=1M * 0.0015)
        """
        self.cost_per_dollar = float(cost)

    def __repr__(self):
        return "{class_name}(cost_per_dollar={cost})".format(
            class_name=self.__class__.__name__, cost=self.cost_per_dollar
        )

    def calculate(self, order, transaction):
        """
        Pay commission based on dollar value of shares.
        """
        cost_per_share = transaction.price * self.cost_per_dollar
        return abs(transaction.amount) * cost_per_share
