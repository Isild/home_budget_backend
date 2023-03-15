from fastapi import Depends, status, APIRouter
from sqlalchemy.orm import Session
from uuid import UUID 
import math

from ...services import auth_service, user_service
from ...schemas import user_schemas

from ...dependencies import get_db, oauth2_scheme
from ...exceptions import http_exceptions

router = APIRouter(
    prefix="/users",
    responses={
        403: {"description": "Permissions denied"},
        404: {"description": "Resource not found"},
        500: {"description": "Server error"},
    },
)

# users
@router.post("/", response_model=user_schemas.User, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user(user: user_schemas.UserCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)

    if loggedUser.is_admin:
        db_user = user_service.get_user_by_email(db, email=user.email)

        if db_user:
            raise http_exceptions.used_email_error
        return user_service.create_user(db=db, user=user)
    else:
        raise http_exceptions.permission_denied_error


@router.get("/", response_model=user_schemas.Pagination, status_code=status.HTTP_200_OK, tags=["users"])
def index_users(token: str = Depends(oauth2_scheme), page: int = 1, limit: int = 100, search:str = None, db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)

    if loggedUser.is_admin:
        users = user_service.get_users(db, page=page, limit=limit, search=search)
    else:
        raise http_exceptions.permission_denied_error
        
    amount = user_service.get_users_amount(db)
    last_page = math.ceil(amount/limit)

    return user_schemas.Pagination(data=users, page=page, last_page=last_page, limit=limit)


@router.get("/{user_uuid}", response_model=user_schemas.User, status_code=status.HTTP_200_OK, tags=["users"])
def show_user(user_uuid: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_user = user_service.get_user(db, uuid=str(user_uuid))

    if db_user is None:
        raise http_exceptions.user_not_found_error

    return db_user

@router.delete("/{user_uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["users"])
def delete_user(user_uuid: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)

    if loggedUser.is_admin:
        db_user = user_service.get_user(db, uuid=str(user_uuid))

        if db_user is None:
            raise http_exceptions.user_not_found_error

        user_service.delete_user(db, uuid=db_user.uuid)

        return None
    else:
        raise http_exceptions.permission_denied_error