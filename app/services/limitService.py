from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import uuid4
from datetime import date
from sqlalchemy import func

from ..models import limitsModel
from ..schemas import limitSchemas

#expenditures
def get_limits(db: Session, page: int = 1, limit: int = 100, search: str = None, year: int = None, user_id: int = None):
    query = db.query(limitsModel.LimitModel)

    query = query.order_by(limitsModel.LimitModel.year).order_by(limitsModel.LimitModel.month)

    if year:
        query = query.filter(limitsModel.LimitModel.year == year)

    if user_id:
        query = query.filter(limitsModel.LimitModel.owner_id == user_id)

    return query.offset((page - 1) * limit).limit(limit).all()

# dodać zwracane typy
def get_limit_by_uuid(db: Session, uuid: str, user_id: int):# -> limitsModel.LimitModel:
    return db.query(limitsModel.LimitModel).filter(limitsModel.LimitModel.uuid == uuid).filter(limitsModel.LimitModel.owner_id == user_id).first()

def get_limit_by_id(db: Session, id: int, user_id: int):# -> limitsModel.LimitModel:
    return db.query(limitsModel.LimitModel).filter(limitsModel.LimitModel.id == id).filter(limitsModel.LimitModel.owner_id == user_id).first() 

def get_limit_by_month_and_year(db: Session, user_id: int, year: int, month: int):# -> limitsModel.LimitModel:
    return db.query(limitsModel.LimitModel).filter(limitsModel.LimitModel.year == year).filter(limitsModel.LimitModel.month == month).first() 

def update_limit(db: Session, limitDb: limitsModel.LimitModel, limit: limitSchemas.LimitCreate) -> bool:
    db.query(limitsModel.LimitModel).filter(limitsModel.LimitModel.id == limitDb.id).update(limit.dict())
    db.commit()
    db.refresh(limitDb)

    return limitDb

def create_limit(db: Session, limit: limitSchemas.LimitCreate, user_id: int):
    uuid = str(uuid4())

    db_limit = limitsModel.LimitModel(**limit.dict(), owner_id=user_id, uuid=uuid)

    db.add(db_limit)
    db.commit()
    db.refresh(db_limit)

    return db_limit

def delete_limit(db: Session, uuid: str) -> bool:
    limit = db.query(limitsModel.LimitModel).filter(limitsModel.LimitModel.uuid == uuid).first()

    if limit == None:
        return None

    db.delete(limit)
    db.commit()

    return uuid

def get_limits_amount(db: Session, user_id: int = None) -> int:
    query = db.query(limitsModel.LimitModel)

    if user_id is not None:
        query = query.filter(limitsModel.LimitModel.owner_id == user_id) 

    return query.with_entities(func.count()).scalar()