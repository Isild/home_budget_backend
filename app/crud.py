from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import Union
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

from .models import userModel, expenditureModel
from .schemas import userSchemas, expenditureSchemas, userTokenSchemas

SECRET_KEY = "f666b14c51f01679796419bb6d43fcbc07e8036ad3b5e62b1824ca66c561821a"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# auth   
def __hash_password(password: str):
    return pwd_context.hash(password)

def __create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=10)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def __verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)
 
def decode_token(db: Session, token: str):
    user = get_user_by_token(db=db,token=token)

    if not user:
        return None
    
    return user

def check_is_user_active(user: userModel.UserModel):
    if user.is_active:
        return user
    else:
        return None

def check_user_password_hash(user: userModel.UserModel, password: str):
    if __hash_password(password=user.password) == __hash_password(password=password):
        return True
    else:
        return False

def authenticate_user(db: Session, user: userModel.UserModel, password: str):
    if not user:
        return False
    if not __verify_password(password=password, hashed_password=user.password):
        return False
    
    return user

def generate_user_token(db: Session, user: userModel.UserModel):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    token = __create_access_token(
        data = {"sub": user.email}, expires_delta=access_token_expires
    )

    db.query(userModel.UserModel).filter(userModel.UserModel.id == user.id).update({"token": token})
    db.commit()
    db.refresh(user)

    return token

#users 
def get_user(db: Session, uuid: str):
    return db.query(userModel.UserModel).filter(userModel.UserModel.uuid == uuid).first()
    
def get_user_by_name(db: Session, name: str):
    return db.query(userModel.UserModel).filter(userModel.UserModel.name == name).first()

def get_user_by_email(db: Session, email: str):
    return db.query(userModel.UserModel).filter(userModel.UserModel.email == email).first()

def get_user_by_token(db: Session, token: str):
    return db.query(userModel.UserModel).filter(userModel.UserModel.token == token).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(userModel.UserModel).offset(skip).limit(limit).all()

def create_user(db: Session, user: userSchemas.User):
    hashed_password = __hash_password(user.password)
    user_uuid = str(uuid4())
    
    db_user = userModel.UserModel(email=user.email, password=hashed_password, uuid=user_uuid)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    db.query(userModel.UserModel).filter(userModel.UserModel.id == db_user.id).update({"token": generate_user_token(db=db, user=db_user)})

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

def get_current_user(db: Session, token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        raise token_exception

    try:
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception
    except:
        raise credentials_exception

    user = decode_token(db=db, token=token)

    if user:
        user = check_is_user_active(user=user)

        if not user:
            raise HTTPException(status_code=400, detail="Inactive user")        
    else:
        raise credentials_exception

    return user

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