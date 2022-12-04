from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, Float
from sqlalchemy.orm import relationship

from ..database import Base

class ExpendituresDayStat(Base):
    __tablename__ = "expenditures_day_stats"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True)
    total_cost = Column(Float)
    date = Column(Date)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("UserModel", back_populates="expenditures_day_stats")