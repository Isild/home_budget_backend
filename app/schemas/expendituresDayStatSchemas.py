from typing import List

from pydantic import BaseModel, Field
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

class ExpendituresLimitBase(BaseModel):
    total_cost: float = Field(
        title="The total expenditures cost in whole month",
        description="The total expenditures cost that user spent in whole month. It is sum of cost in all weeks.",
        eq=0,
        example=2137.00
    )
    year: int = Field(
        title="The year",
        description="The year.",
        example=2023,
        eq=0
    )
    total_limit: float = Field(
        title="The total limit",
        description="The total limit for year.",
        eq=0,
        example=20000.00
    )
    month_costs: list = Field(
        title="The month costs with limits",
        description="The month costs with limits.",
        eq=0,
        example=[{
            "1":456.00,
            "limit": 500.00
        }]
    )