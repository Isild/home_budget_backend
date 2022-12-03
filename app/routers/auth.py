from typing import List
from fastapi import Depends, HTTPException, status, APIRouter, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from ..services import userService
from ..schemas import userSchemas, userTokenSchemas, successSchemas
from ..dependencies import get_db, oauth2_scheme
from ..services import authService
from ..exceptions import httpExceptions

router = APIRouter(
    prefix="/auth",
    responses={
        401: {"description": "Incorrect username or password"},
        404: {"description": "Resource not found"},
        500: {"description": "Something went wrong, please contact administration"},
    },
)


@router.post("/login", response_model=userTokenSchemas.TokenData, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(),  db: Session = Depends(get_db)):
    # in request form username will be a email
    userDB = userService.get_user_by_email(db, email=form_data.username)

    if not userDB:
        raise httpExceptions.unauth_error
        
    if not authService.authenticate_user(db=db, user=userDB, password=form_data.password):
        raise httpExceptions.unauth_error

    token = authService.generate_user_token(db, user=userDB)

    return {
        "access_token": token, 
        "token_type": "bearer"
    }

@router.post("/logout", status_code=200, tags=["auth"])
def logout(user = Depends(authService.get_current_active_user), db: Session = Depends(get_db)):
    authService.delete_token(db=db, user=user)

    return "Successfully logged out."

@router.post("/register", response_model=successSchemas.SuccessResponseSchema, status_code=status.HTTP_201_CREATED, tags=["auth"])
def register(user_data: userSchemas.UserRegister, db: Session = Depends(get_db)):
    db_user = userService.get_user_by_email(db, email=user_data.email)

    if db_user:
        raise httpExceptions.used_email_error

    userService.create_user(db=db, user=user_data)

    if userService.send_verification_email(user_data.email):
        return {
            "message": "Account has been successfully created, please check your email and confirm your registration."
        }
    else :
        raise httpExceptions.server_error

@router.post("/reset-password", response_model=successSchemas.SuccessResponseSchema, status_code=200, tags=["auth"])
def change_password(email: str, db: Session = Depends(get_db)):
    if userService.send_password_reset_email(email):
        return {
            "message": "Email with link to resed password was send, please check your email."
        }
    else :
        raise httpExceptions.server_error

@router.post("/change-password", response_model=successSchemas.SuccessResponseSchema, status_code=200, tags=["auth"])
def change_password(user: userSchemas.UserResetPassword, db: Session = Depends(get_db)):
    userDB = userService.get_user_by_email(db, email=user.email)

    if not userDB:
        raise httpExceptions.unauth_error

    if not authService.authenticate_user(db=db, user=userDB, password=user.password):
        raise httpExceptions.unauth_error

    if userService.change_user_password(db=db, user=userDB, new_password=user.new_password):
        return {
            "message": "Password has been successfully changed."
        }
    else :
        raise httpExceptions.server_error

@router.get("/users/me", response_model=userSchemas.UserPublic, tags=["auth"])
def red_user_me(current_user: userSchemas.User = Depends(authService.get_current_active_user)):
    return current_user