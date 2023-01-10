from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, Float, Enum
from sqlalchemy.orm import relationship
from enum import Enum as py_enum

from ..database import Base
# from .userModel import 

class LimitModel(Base):
    __tablename__ = "limits"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True)
    year = Column(Integer)
    month = Column(Integer)
    limit = Column(Float)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("UserModel", back_populates="limits")