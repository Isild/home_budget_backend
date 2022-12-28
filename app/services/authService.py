from sqlalchemy.orm import Session
from typing import Union
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi import Depends

from ..models import userModel
from . import userService
from ..dependencies import oauth2_scheme, get_db, get_settings

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

    encoded_jwt = jwt.encode(to_encode, get_settings().secret_key, algorithm=get_settings().algorithm)

    return encoded_jwt

def __verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)

def get_hashed_password(password: str):
    return __hash_password(password=password)

def decode_token(db: Session, token: str):
    user = userService.get_user_by_token(db=db,token=token)

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
    access_token_expires = timedelta(minutes=get_settings().access_token_expire_minutes)

    token = __create_access_token(
        data = {"sub": user.email}, expires_delta=access_token_expires
    )

    db.query(userModel.UserModel).filter(userModel.UserModel.id == user.id).update({"token": token})
    db.commit()
    db.refresh(user)

    return token

async def get_current_active_user(token: str = Depends(oauth2_scheme)):
# async def get_current_active_user(request: Request = Depends(Request), token: str = Depends(oauth2_scheme)):
    db = next(get_db())
    user = userService.get_current_user(db=db, token=token)
    
    return user

# def get_user_from_request(request: Request = Depends(Request)):
#     if request.user is not None:
#         return request.user
        
#     return get_current_active_user()

def delete_token(db: Session, user: userModel.UserModel):
    userService.remove_user_token(db=db, user=user)