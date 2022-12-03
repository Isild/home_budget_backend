from sqlalchemy.orm import Session
from uuid import uuid4
from fastapi import HTTPException, status
from jose import jwt

from ..models import userModel
from ..schemas import userSchemas
from ..dependencies import get_settings

from . import authService

def get_user(db: Session, uuid: str):
    return db.query(userModel.UserModel).filter(userModel.UserModel.uuid == uuid).first()
    
def get_user_by_name(db: Session, name: str):
    return db.query(userModel.UserModel).filter(userModel.UserModel.name == name).first()

def get_user_by_email(db: Session, email: str):
    return db.query(userModel.UserModel).filter(userModel.UserModel.email == email).first()

def get_user_by_token(db: Session, token: str):
    return db.query(userModel.UserModel).filter(userModel.UserModel.token == token).first()


def get_users(db: Session, skip: int = 0, limit: int = 100, search: str = None):
    query = db.query(userModel.UserModel)

    if search:
        query = query.filter(userModel.UserModel.email.contains(search))

    return query.offset(skip).limit(limit).all()

def create_user(db: Session, user: userSchemas.User):
    hashed_password = authService.get_hashed_password(user.password)
    user_uuid = str(uuid4())
    
    db_user = userModel.UserModel(email=user.email, password=hashed_password, uuid=user_uuid)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    db.query(userModel.UserModel).filter(userModel.UserModel.id == db_user.id).update({"token": authService.generate_user_token(db=db, user=db_user)})

    db.commit()
    db.refresh(db_user)

    return db_user

def change_user_password(db:Session, user: userSchemas.User, new_password: str):
    hashed_password = authService.get_hashed_password(new_password)
    db.query(userModel.UserModel).filter(userModel.UserModel.id == user.id).update({"password": hashed_password})

    db.commit()
    db.refresh(user)

    return user

def remove_user_token(db:Session, user: userSchemas.User):
    db.query(userModel.UserModel).filter(userModel.UserModel.id == user.id).update({"token": None})

    db.commit()
    db.refresh(user)

    return user

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

    print(jwt.decode(token, get_settings().secret_key, algorithms=[get_settings().algorithm]))
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

    user = authService.decode_token(db=db, token=token)

    if user:
        user = authService.check_is_user_active(user=user)

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