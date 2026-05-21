from sqlalchemy.orm import Mapped

from ziplime.core.db.annotated_types import StringPK
from ziplime.core.db.base_model import BaseModel


class ExchangeInfoModel(BaseModel):
    __tablename__ = "exchanges"
    mic: Mapped[StringPK]
    name: Mapped[str]
    canonical_name: Mapped[str]
    country_code: Mapped[str]
