from sqlalchemy.orm import Session
from uuid import uuid4
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy import func, desc

from ..models import user_model
from ..schemas import user_schemas
from ..dependencies import get_settings

from . import auth_service

def get_user(db: Session, uuid: str):
    return db.query(user_model.UserModel).filter(user_model.UserModel.uuid == uuid).first()
    
def get_user_by_name(db: Session, name: str):
    return db.query(user_model.UserModel).filter(user_model.UserModel.name == name).first()

def get_user_by_email(db: Session, email: str):
    return db.query(user_model.UserModel).filter(user_model.UserModel.email == email).first()

def get_user_by_token(db: Session, token: str):
    return db.query(user_model.UserModel).filter(user_model.UserModel.token == token).first()


def get_users(db: Session, page: int = 1, limit: int = 100, search: str = None):
    query = db.query(user_model.UserModel)

    query = query.order_by(desc(user_model.UserModel.email))

    if search:
        query = query.filter(user_model.UserModel.email.contains(search))

    return query.offset((page - 1) * limit).limit(limit).all()

def create_user(db: Session, user: user_schemas.User):
    hashed_password = auth_service.get_hashed_password(user.password)
    user_uuid = str(uuid4())
    
    db_user = user_model.UserModel(email=user.email, password=hashed_password, uuid=user_uuid)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    db.query(user_model.UserModel).filter(user_model.UserModel.id == db_user.id).update({"token": auth_service.generate_user_token(db=db, user=db_user)})

    db.commit()
    db.refresh(db_user)

    return db_user

def change_user_password(db:Session, user: user_schemas.User, new_password: str):
    hashed_password = auth_service.get_hashed_password(new_password)
    db.query(user_model.UserModel).filter(user_model.UserModel.id == user.id).update({"password": hashed_password})

    db.commit()
    db.refresh(user)

    return user

def remove_user_token(db:Session, user: user_schemas.User):
    db.query(user_model.UserModel).filter(user_model.UserModel.id == user.id).update({"token": None})

    db.commit()

    return user

def delete_user(db: Session, uuid: str):
    user = db.query(user_model.UserModel).filter(user_model.UserModel.uuid == uuid).first()

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
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[get_settings().algorithm])
    except:
        raise token_exception

    try:
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception
    except:
        raise credentials_exception

    user = auth_service.decode_token(db=db, token=token)

    if user:
        user = auth_service.check_is_user_active(user=user)

        if not user:
            raise HTTPException(status_code=400, detail="Inactive user")        
    else:
        raise credentials_exception

    return user

def send_verification_email(email: str):
    print("Email sent")

    return True

def send_password_reset_email(email: str):
    print("Email sent")

    return True

def get_users_amount(db: Session) -> int:
    query = db.query(user_model.UserModel)

    return query.with_entities(func.count()).scalar()