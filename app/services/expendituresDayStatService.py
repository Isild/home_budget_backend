from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import date

from ..models import expendituresDayStatModel
from ..schemas import expendituresDayStatSchemas

def get_expenditures_day_stats(db: Session, user_id: int = None, skip: int = 0, limit: int = 100, search: str = None, date_from: date = None, date_to: date = None):
    query = db.query(expendituresDayStatModel.ExpendituresDayStat).filter(expendituresDayStatModel.ExpendituresDayStat.owner_id== user_id)

    if user_id:
        query = query.filter(expendituresDayStatModel.ExpendituresDayStat.owner_id == user_id)

    if search:
        query = query.filter(expendituresDayStatModel.ExpendituresDayStat.total_cost.match(search))

    if date_from:
        query = query.filter(expendituresDayStatModel.ExpendituresDayStat.date >= date_from)

    if date_to:
        query = query.filter(expendituresDayStatModel.ExpendituresDayStat.date <= date_to)

    return query.offset(skip).limit(limit).all()

def get_expenditure_day_stat(db: Session, uuid: str):
    return db.query(expendituresDayStatModel.ExpendituresDayStat).filter(expendituresDayStatModel.ExpendituresDayStat.uuid == uuid).first()

def update_expenditure_day_stat(db: Session, expenditureDayStatDb: expendituresDayStatModel.ExpendituresDayStat, expenditureDayStat: expendituresDayStatSchemas.ExpendituresDayStat) -> bool:
    db.query(expendituresDayStatModel.ExpendituresDayStat).filter(expendituresDayStatModel.ExpendituresDayStat.id == expenditureDayStatDb.id).update(expenditureDayStat.dict())
    db.commit()
    db.refresh(expenditureDayStatDb)

    return expenditureDayStatDb

def create_expenditure_day_stat(db: Session, expenditureDayStat: expendituresDayStatSchemas.ExpendituresDayStat, user_id: int):
    uuid = str(uuid4())

    db_expenditure = expendituresDayStatModel.ExpendituresDayStat(**expenditureDayStat.dict(), owner_id=user_id, uuid=uuid)

    db.add(db_expenditure)
    db.commit()
    db.refresh(db_expenditure)

    return db_expenditure

def remove_expenditure_day_stat(db: Session, uuid: str) -> bool:
    expenditure = db.query(expendituresDayStatModel.ExpendituresDayStat).filter(expendituresDayStatModel.ExpendituresDayStat.uuid == uuid).first()

    if expenditure == None:
        return None

    db.delete(expenditure)
    db.commit()

    return uuid