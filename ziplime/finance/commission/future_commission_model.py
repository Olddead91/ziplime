from ziplime.assets.entities.futures_contract import FuturesContract
from ziplime.finance.commission.commission_model import CommissionModel
from ziplime.finance.shared import AllowedAssetMarker


class FutureCommissionModel(CommissionModel, metaclass=AllowedAssetMarker):
    """
    Base class for commission models which only support futures.
    """

    allowed_asset_types = (FuturesContract,)
