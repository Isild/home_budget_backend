from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import uuid4
from datetime import date
from sqlalchemy import func

from ..models import expenditureModel
from ..schemas import expenditureSchemas

#expenditures
def get_expenditures(db: Session, page: int = 1, limit: int = 100, search: str = None, date_from: date = None, date_to: date = None, user_id: int = None):
    query = db.query(expenditureModel.ExpenditureModel)

    query = query.order_by(expenditureModel.ExpenditureModel.date)

    if search:
        query = query.filter(or_(expenditureModel.ExpenditureModel.name.contains(search), expenditureModel.ExpenditureModel.place.contains(search)))

    if date_from:
        query = query.filter(expenditureModel.ExpenditureModel.date >= date_from)

    if date_to:
        query = query.filter(expenditureModel.ExpenditureModel.date <= date_to)

    if user_id:
        query = query.filter(expenditureModel.ExpenditureModel.owner_id == user_id)

    return query.offset((page - 1) * limit).limit(limit).all()

# do śmietnika
def get_expenditures_filter_by_owner_id(db: Session, user_id: int, skip: int = 0, limit: int = 100, search: str = None, date_from: date = None, date_to: date = None):
    query = db.query(expenditureModel.ExpenditureModel).filter(expenditureModel.ExpenditureModel.owner_id== user_id)

    if search:
        query = query.filter(or_(expenditureModel.ExpenditureModel.name.contains(search), expenditureModel.ExpenditureModel.place.contains(search)))

    if date_from:
        query = query.filter(expenditureModel.ExpenditureModel.date >= date_from)

    if date_to:
        query = query.filter(expenditureModel.ExpenditureModel.date <= date_to)

    return query.offset(skip).limit(limit).all()

# dodać zwracane typy
def get_expenditure(db: Session, uuid: str, user_id: int):# -> expenditureModel.ExpenditureModel:
    return db.query(expenditureModel.ExpenditureModel).filter(expenditureModel.ExpenditureModel.uuid == uuid).first()

def update_expenditure(db: Session, expenditureDb: expenditureModel.ExpenditureModel, expenditure: expenditureSchemas.ExpenditureCreate) -> bool:
    db.query(expenditureModel.ExpenditureModel).filter(expenditureModel.ExpenditureModel.id == expenditureDb.id).update(expenditure.dict())
    db.commit()
    db.refresh(expenditureDb)

    return expenditureDb

def create_expenditure(db: Session, expenditure: expenditureSchemas.ExpenditureCreate, user_id: int):
    uuid = str(uuid4())

    db_expenditure = expenditureModel.ExpenditureModel(**expenditure.dict(), owner_id=user_id, uuid=uuid)

    db.add(db_expenditure)
    db.commit()
    db.refresh(db_expenditure)

    return db_expenditure

def delete_expenditre(db: Session, uuid: str) -> bool:
    expenditure = db.query(expenditureModel.ExpenditureModel).filter(expenditureModel.ExpenditureModel.uuid == uuid).first()

    if expenditure == None:
        return None

    db.delete(expenditure)
    db.commit()

    return uuid

def get_expenditure_amount(db: Session, user_id: int = None) -> int:
    query = db.query(expenditureModel.ExpenditureModel)

    if user_id is not None:
        query = query.filter(expenditureModel.ExpenditureModel.owner_id == user_id) 

    return query.with_entities(func.count()).scalar()