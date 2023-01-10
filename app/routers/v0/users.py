from fastapi import Depends, status, APIRouter
from sqlalchemy.orm import Session
from uuid import UUID 
import math

from ...services import userService, authService
from ...schemas import userSchemas

from ...dependencies import get_db, oauth2_scheme
from ...exceptions import httpExceptions

router = APIRouter(
    prefix="/users",
    responses={
        403: {"description": "Permissions denied"},
        404: {"description": "Resource not found"},
        500: {"description": "Server error"},
    },
)

# users
@router.post("/", response_model=userSchemas.User, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user(user: userSchemas.UserCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = authService.decode_token(db=db, token=token)

    if loggedUser.is_admin:
        db_user = userService.get_user_by_email(db, email=user.email)

        if db_user:
            raise httpExceptions.used_email_error
        return userService.create_user(db=db, user=user)
    else:
        raise httpExceptions.permission_denied_error


@router.get("/", response_model=userSchemas.Pagination, status_code=status.HTTP_200_OK, tags=["users"])
def index_users(token: str = Depends(oauth2_scheme), page: int = 1, limit: int = 100, search:str = None, db: Session = Depends(get_db)):
    loggedUser = authService.decode_token(db=db, token=token)

    if loggedUser.is_admin:
        users = userService.get_users(db, page=page, limit=limit, search=search)
    else:
        raise httpExceptions.permission_denied_error
        
    amount = userService.get_users_amount(db)
    last_page = math.ceil(amount/limit)

    return userSchemas.Pagination(data=users, page=page, last_page=last_page, limit=limit)


@router.get("/{user_uuid}", response_model=userSchemas.User, status_code=status.HTTP_200_OK, tags=["users"])
def show_user(user_uuid: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_user = userService.get_user(db, uuid=str(user_uuid))

    if db_user is None:
        raise httpExceptions.user_not_found_error

    return db_user

@router.delete("/{user_uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["users"])
def delete_user(user_uuid: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = authService.decode_token(db=db, token=token)

    if loggedUser.is_admin:
        db_user = userService.get_user(db, uuid=str(user_uuid))

        if db_user is None:
            raise httpExceptions.user_not_found_error

        userService.delete_user(db, uuid=db_user.uuid)

        return None
    else:
        raise httpExceptions.permission_denied_error