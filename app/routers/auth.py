from fastapi import Depends, status, APIRouter
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from ..services import user_service
from ..schemas import success_schemas, user_schemas, user_token_schemas
from ..dependencies import get_db, oauth2_scheme
from ..services import auth_service
from ..exceptions import http_exceptions

router = APIRouter(
    prefix="/auth",
    responses={
        401: {"description": "Incorrect username or password"},
        404: {"description": "Resource not found"},
        500: {"description": "Something went wrong, please contact administration"},
    },
)


@router.post("/login", response_model=user_token_schemas.TokenData, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(),  db: Session = Depends(get_db)):
    # in request form username will be a email
    userDB = user_service.get_user_by_email(db, email=form_data.username)

    if not userDB:
        raise http_exceptions.unauth_error
        
    if not auth_service.authenticate_user(db=db, user=userDB, password=form_data.password):
        raise http_exceptions.unauth_error

    token = auth_service.generate_user_token(db, user=userDB)

    return {
        "access_token": token, 
        "token_type": "bearer"
    }

@router.post("/logout", response_model=success_schemas.SuccessResponseSchema, status_code=200, tags=["auth"])
def logout(user = Depends(auth_service.get_current_active_user), db: Session = Depends(get_db)):
    auth_service.delete_token(db=db, user=user)

    return {
        "message": "Successfully logged out."
    }

@router.post("/register", response_model=success_schemas.SuccessResponseSchema, status_code=status.HTTP_201_CREATED, tags=["auth"])
def register(user_data: user_schemas.UserRegister, db: Session = Depends(get_db)):
    db_user = user_service.get_user_by_email(db, email=user_data.email)

    if db_user:
        raise http_exceptions.used_email_error

    user_data.is_active = False
    user_data.disabled = True
    user_service.create_user(db=db, user=user_data)

    if user_service.send_verification_email(user_data.email):
        return {
            "message": "Account has been successfully created, please check your email and confirm your registration."
        }
    else :
        raise http_exceptions.server_error

@router.post("/reset-password", response_model=success_schemas.SuccessResponseSchema, status_code=200, tags=["auth"])
def change_password(email: str, db: Session = Depends(get_db)):
    if user_service.send_password_reset_email(email):
        return {
            "message": "Email with link to resed password was send, please check your email."
        }
    else :
        raise http_exceptions.server_error

@router.post("/change-password", response_model=success_schemas.SuccessResponseSchema, status_code=200, tags=["auth"])
def change_password(user: user_schemas.UserResetPassword, db: Session = Depends(get_db)):
    userDB = user_service.get_user_by_email(db, email=user.email)

    if not userDB:
        raise http_exceptions.unauth_error

    if not auth_service.authenticate_user(db=db, user=userDB, password=user.password):
        raise http_exceptions.unauth_error

    if user_service.change_user_password(db=db, user=userDB, new_password=user.new_password):
        return {
            "message": "Password has been successfully changed."
        }
    else :
        raise http_exceptions.server_error

@router.get("/users/me", response_model=user_schemas.UserPublic, tags=["auth"])
def red_user_me(current_user: user_schemas.User = Depends(auth_service.get_current_active_user)):
    return current_user