from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List

from .models import userModel, expenditureModel

from .schemas import userSchemas, expenditureSchemas

#users 
def get_user(db: Session, uuid: str):
    return db.query(userModel.UserModel).filter(userModel.UserModel.uuid == uuid).first()


def get_user_by_email(db: Session, email: str):
    return db.query(userModel.UserModel).filter(userModel.UserModel.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(userModel.UserModel).offset(skip).limit(limit).all()

def create_user(db: Session, user: userSchemas.User):
    fake_hashed_password = user.password + "notreallyhashed"
    user_uuid = str(uuid4())
    
    db_user = userModel.UserModel(email=user.email, hashed_password=fake_hashed_password, uuid=user_uuid)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

def delete_user(db: Session, uuid: str):
    user = db.query(userModel.UserModel).filter(userModel.UserModel.uuid == uuid).first()

    if user == None:
        return None

    db.delete(user)
    db.commit()

    return None

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