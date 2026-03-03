from ziplime.assets.entities.equity import Equity
from ziplime.finance.commission.commission_model import CommissionModel
from ziplime.finance.shared import AllowedAssetMarker


class EquityCommissionModel(CommissionModel, metaclass=AllowedAssetMarker):
    """
    Base class for commission models which only support equities.
    """

    allowed_asset_types = (Equity,)
