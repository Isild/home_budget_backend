from typing import List
from pydantic import BaseModel, Field

from .expenditureSchemas import Expenditure

class UserBase(BaseModel):
    email: str

class UserRegister(UserBase):
    password:str

class UserResetPassword(UserRegister):
    new_password:str

class UserCreate(UserRegister):
    is_admin: bool
    is_active: bool

class UserPublic(UserBase):
    uuid: str
    is_active: bool
    is_active: bool
    disabled: bool

    class Config:
        orm_mode = True

class UserPublicWithExpenditures(UserPublic):
    expenditures: List[Expenditure] = []

class User(UserPublic):
    token: str
    is_admin: bool

class Pagination(BaseModel):
    data: List[UserPublic] = Field(
        title="The users data",
        description="The users data.",
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