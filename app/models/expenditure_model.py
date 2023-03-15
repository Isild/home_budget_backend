from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, Float, Enum
from sqlalchemy.orm import relationship
from enum import Enum as py_enum

from ..database import Base
# from .userModel import 

class ExpenditureTypes(str, py_enum):
    normal = "normal"
    cyclical = "cyclical"

class ExpenditureModel(Base):
    __tablename__ = "expenditures"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True)
    name = Column(String)
    cost = Column(Float)
    date = Column(Date)
    place = Column(String)
    type = Column(Enum(ExpenditureTypes), default=ExpenditureTypes.normal)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("UserModel", back_populates="expenditures")