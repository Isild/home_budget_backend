from typing import List
from pydantic import BaseModel

from .expenditureSchemas import Expenditure

class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str
    is_admin: bool
    is_active: bool

class UserPublic(UserBase):
    uuid: str
    is_active: bool
    expenditures: List[Expenditure] = []
    is_active: bool
    disabled: bool

    class Config:
        orm_mode = True

class User(UserPublic):
    token: str
    is_admin: bool