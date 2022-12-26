from typing import List, Union

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date as date_type

from ..models.expendituresDayStatModel import ExpendituresDayStat

class ExpendituresDayStatBase(BaseModel):
    total_cost: float = Field(
        title="The total expenditures cost",
        description="The total expenditures cost per one day that user spend.",
        eq=0,
        example=1410
    )
    date: date_type = Field(
        title="The date of expenditures",
        description="The date of expenditures made in that day.",
        example="2022-11-06"
    )

class ExpendituresDayStat(ExpendituresDayStatBase):
    uuid: str

    class Config:
        orm_mode = True

    
class Pagination(BaseModel):
    data: List[ExpendituresDayStat] = Field(
        title="The expenditure stats data",
        description="The expenditure stats data.",
    )
    page: int = Field(
        title="The total pages amount",
        description="The total pages amount.",
    )
    last_page: int = Field(
        title="The last page number",
        description="The last page number of pagination.",
    )
    limit: int = Field(
        title="The limit of displaying data",
        description="The limit of displaying data.",
    )