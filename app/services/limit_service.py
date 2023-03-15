from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import uuid4
from datetime import date
from sqlalchemy import func

from ..models import limits_model
from ..schemas import limit_schemas

#expenditures
def get_limits(db: Session, page: int = 1, limit: int = 100, search: str = None, year: int = None, user_id: int = None):
    query = db.query(limits_model.LimitModel)

    query = query.order_by(limits_model.LimitModel.year).order_by(limits_model.LimitModel.month)

    if year:
        query = query.filter(limits_model.LimitModel.year == year)

    if user_id:
        query = query.filter(limits_model.LimitModel.owner_id == user_id)

    return query.offset((page - 1) * limit).limit(limit).all()

# dodać zwracane typy
def get_limit_by_uuid(db: Session, uuid: str, user_id: int):# -> limitsModel.LimitModel:
    return db.query(limits_model.LimitModel).filter(limits_model.LimitModel.uuid == uuid).filter(limits_model.LimitModel.owner_id == user_id).first()

def get_limit_by_id(db: Session, id: int, user_id: int):# -> limitsModel.LimitModel:
    return db.query(limits_model.LimitModel).filter(limits_model.LimitModel.id == id).filter(limits_model.LimitModel.owner_id == user_id).first() 

def get_limit_by_month_and_year(db: Session, user_id: int, year: int, month: int):# -> limitsModel.LimitModel:
    return db.query(limits_model.LimitModel).filter(limits_model.LimitModel.year == year).filter(limits_model.LimitModel.month == month).first() 

def update_limit(db: Session, limitDb: limits_model.LimitModel, limit: limit_schemas.LimitCreate) -> bool:
    db.query(limits_model.LimitModel).filter(limits_model.LimitModel.id == limitDb.id).update(limit.dict())
    db.commit()
    db.refresh(limitDb)

    return limitDb

def create_limit(db: Session, limit: limit_schemas.LimitCreate, user_id: int):
    uuid = str(uuid4())

    db_limit = limits_model.LimitModel(**limit.dict(), owner_id=user_id, uuid=uuid)

    db.add(db_limit)
    db.commit()
    db.refresh(db_limit)

    return db_limit

def delete_limit(db: Session, uuid: str) -> bool:
    limit = db.query(limits_model.LimitModel).filter(limits_model.LimitModel.uuid == uuid).first()

    if limit == None:
        return None

    db.delete(limit)
    db.commit()

    return uuid

def get_limits_amount(db: Session, user_id: int = None) -> int:
    query = db.query(limits_model.LimitModel)

    if user_id is not None:
        query = query.filter(limits_model.LimitModel.owner_id == user_id) 

    return query.with_entities(func.count()).scalar()