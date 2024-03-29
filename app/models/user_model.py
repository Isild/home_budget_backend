from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    token = Column(String, unique=True, default=None, nullable=True)
    disabled = Column(Boolean, default=False)

    expenditures = relationship("ExpenditureModel", back_populates="owner")
    expenditures_day_stats = relationship("ExpendituresDayStat", back_populates="owner")
    limits = relationship("LimitModel", back_populates="owner")
