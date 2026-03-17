import datetime
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import TypedDict, Union, Optional


class JudgmentEnum(Enum):
    """ Nature of court judgment of a company
        French wording is kept to avoid miscomprehension of Bodacc publications
    """
    REDRESSEMENT = 'REDRESSEMENT'
    LIQUIDATION = 'LIQUIDATION'
    ANNULEE = 'ANNULEE'

Identifier = Union[str, int, uuid.UUID]
SirenIndex = dict[str, Identifier]
Siren = str

class CompanyJudgment(TypedDict):
    identifier: Optional[Identifier]
    siren: Siren
    record_id: str
    date: datetime.date
    raw_data: str
    judgment: JudgmentEnum
    start_date: datetime.date
    expected_end_date: datetime.date


