import datetime
import uuid
from enum import Enum
from typing import TypedDict, Union, Optional


class JudgmentStatusEnum(str, Enum):
    """Nature of court judgment of a company
    French wording is kept to avoid miscomprehension of Bodacc publications
    """

    REDRESSEMENT = "REDRESSEMENT"
    LIQUIDATION = "LIQUIDATION"
    NOT_RISKY = "NOT_RISKY"


Identifier = Union[str, int, uuid.UUID]
Siren = str
SirenIndex = dict[Siren, Identifier]


class CompanyJudgment(TypedDict):
    identifier: Optional[Identifier]
    siren: Siren
    record_id: str
    record_date: datetime.date
    judgment_date: datetime.date
    raw_data: str
    judgment_status: JudgmentStatusEnum
