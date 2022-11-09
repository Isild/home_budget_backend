from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from enum import Enum

from ..database import Base
# from .userModel import 

class ExpenditureTypes(Enum):
    normal = "normal"
    cyclical = "cyclical"

class ExpenditureModel(Base):
    __tablename__ = "expenditures"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True)
    name = Column(String)
    cost = Column(Float)
    date = Column(DateTime)
    place = Column(String)
    # type = Column(Enum(ExpenditureTypes), default=ExpenditureTypes.normal)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("UserModel", back_populates="expenditures")