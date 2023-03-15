from typing import List

from pydantic import BaseModel, Field

class LimitBase(BaseModel):
    year: int = Field(
        title="The year of the limit", 
        description="The year of the limit", 
        eq=0,
        example=1,
    )
    month: int = Field(
        title="The month of the limit", 
        description="The month of the limit", 
        eq=0,
        example=1,
    )
    limit: float = Field(
        title="The limit of the expenditures", 
        description="The limit of the expenditures in given month", 
        eq=0,
        example=21.37,
    )


class LimitCreate(LimitBase):
    pass

class Limit(LimitBase):
    uuid: str

    class Config:
        orm_mode = True

class Pagination(BaseModel):
    data: List[Limit] = Field(
        title="The limits data",
        description="The limits data.",
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