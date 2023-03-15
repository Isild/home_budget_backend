from typing import List

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date as date_type

from ..models.expenditure_model import ExpenditureTypes

class ExpenditureBase(BaseModel):
    name: str = Field(
        title="The name of the expenditure", 
        description="The name of the expenditure", 
        min_length=3,
        max_length=300,
        example="Name",
    )
    type: ExpenditureTypes = Field(
        title="The type of the expenditure", 
        description="The type of the expenditure", 
        min_length=3, 
        max_length=300,
        example=ExpenditureTypes.cyclical,
    )
    cost: float = Field(
        title="The cost of the expenditure", 
        description="The cost of the expenditure", 
        eq=0,
        example=21.37,
    )
    date: date_type = Field(
        title="The date of the expenditure",
        description="The date of the expenditure",
        example="2022-11-06",
    )
    place: str = Field(
        title="The place of the expenditure", 
        description="The place of the expenditure in date format.", 
        min_length=3, 
        max_length=300,
        example="Rome",
    )


class ExpenditureCreate(ExpenditureBase):
    pass

class Expenditure(ExpenditureBase):
    uuid: str

    class Config:
        orm_mode = True

class Pagination(BaseModel):
    data: List[Expenditure] = Field(
        title="The expenditure data",
        description="The expenditure data.",
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