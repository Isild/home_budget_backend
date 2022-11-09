from typing import List
from pydantic import BaseModel

from .expenditureSchemas import Expenditure

class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str
    is_admin: bool
    is_active: bool

class User(UserBase):
    uuid: str
    is_active: bool
    expenditures: List[Expenditure] = []
    is_admin: bool
    is_active: bool

    class Config:
        orm_mode = True