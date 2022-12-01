from sqlalchemy.orm import Session
from uuid import uuid4

from ..models import expenditureModel
from ..schemas import expenditureSchemas

#expenditures
def get_expenditures(db: Session, skip: int = 0, limit: int = 100):
    return db.query(expenditureModel.ExpenditureModel).offset(skip).limit(limit).all()

def get_expenditures_filter_by_owner_id(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(expenditureModel.ExpenditureModel).filter(expenditureModel.ExpenditureModel.owner_id== user_id).offset(skip).limit(limit).all()

# dodać zwracane typy
def get_expenditure(db: Session, uuid: str, user_id: int):# -> expenditureModel.ExpenditureModel:
    return db.query(expenditureModel.ExpenditureModel).filter(expenditureModel.ExpenditureModel.uuid == uuid).first()

def put_expenditure(db: Session, expenditureDb: expenditureModel.ExpenditureModel, expenditure: expenditureSchemas.ExpenditureCreate) -> bool:
    db.query(expenditureModel.ExpenditureModel).filter(expenditureModel.ExpenditureModel.id == expenditureDb.id).update(expenditure.dict())
    db.commit()
    db.refresh(expenditureDb)

    return expenditureDb

def post_expenditure(db: Session, expenditure: expenditureSchemas.ExpenditureCreate, user_id: int):
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