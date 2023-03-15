from fastapi import Depends, status, APIRouter, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID  
from datetime import date
import math

from ...services import auth_service, limit_service, user_service
from ...schemas import limit_schemas
from ...dependencies import get_db, get_settings, oauth2_scheme
from ...exceptions import http_exceptions
from ...models import limits_model

router = APIRouter(
    responses={
        403: {"description": "Permissions denied"},
        404: {"description": "Resource not found"},
        500: {"description": "Server error"}
    },
)

# limits
@router.post("/limits/", response_model=limit_schemas.Limit, status_code=status.HTTP_201_CREATED, tags=["limits"])
async def store_limit(limit: limit_schemas.LimitCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_user = auth_service.decode_token(db=db, token=token)

    if db_user is None:
        raise http_exceptions.user_not_found_error

    limitDB = limit_service.get_limit_by_month_and_year(db=db, month=limit.month, year=limit.year, user_id=db_user.id)
    if limitDB:
        createdLimit = limit_service.update_limit(db, limitDb=limitDB, limit=limit)
    else:
        createdLimit = limit_service.create_limit(db=db, limit=limit, user_id=db_user.id)

    return createdLimit

@router.put("/limits/{uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["limits"])
def put_limit(uuid: UUID, limit: limit_schemas.LimitCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)

    limitDB = limit_service.get_limit_by_uuid(db, uuid=str(uuid), user_id=loggedUser.id)
    if limitDB is None:
        raise http_exceptions.limit_not_found
    if limitDB.owner_id is not loggedUser.id:
        raise http_exceptions.permission_denied_error

    limitDB2 = limit_service.get_limit_by_month_and_year(db=db, month=limit.month, year=limit.year, user_id=loggedUser.id)

    if limitDB2 is not None:
        if limitDB2.year == limitDB.year and limitDB2.month == limitDB.month and limitDB2.owner_id == limitDB.owner_id:
            limit = limit_service.update_limit(db, limitDb=limitDB, limit=limit)
        else:
            raise http_exceptions.cannot_update_limit_unique_month
    else:
        limit = limit_service.update_limit(db, limitDb=limitDB, limit=limit)

    return None

@router.get("/limits/", response_model=limit_schemas.Pagination, status_code=status.HTTP_200_OK, tags=["limits"])
def index_limit(token: str = Depends(oauth2_scheme), page: int = 1, limit: int = 100, search: str = None, year: date = None, db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)

    if loggedUser.is_admin:
        limits = limit_service.get_limits(db, page=page, limit=limit, search=search, year=year)
    else:
        raise http_exceptions.permission_denied_error

    amount = limit_service.get_limits_amount(db,user_id=None)
    last_page = math.ceil(amount/limit)

    return limit_schemas.Pagination(data=limits, page=page, last_page=last_page, limit=limit)

@router.get("/users/{user_uuid}/limits/", response_model=limit_schemas.Pagination, status_code=status.HTTP_200_OK, tags=["limits"])
def index_user_limits(user_uuid: UUID, token: str = Depends(oauth2_scheme), page: int = 1, limit: int = 100, search: str = None, year: date = None, db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)
    userPath = user_service.get_user(db, uuid=str(user_uuid))
    
    if userPath is None:
            raise http_exceptions.user_not_found_error

    if loggedUser.is_admin:
        limits = limit_service.get_limits(db, page=page, limit=limit, search=search, year=year, user_id=userPath.id)
        amount = limit_service.get_limits_amount(db,user_id=userPath.id)
    else:
        if not loggedUser.id == userPath.id:
            raise http_exceptions.permission_denied_error

        limits = limit_service.get_limits(db, page=page, limit=limit, search=search, year=year, user_id=loggedUser.id)
        amount = limit_service.get_limits_amount(db,user_id=loggedUser.id)

    last_page = math.ceil(amount/limit)

    return limit_schemas.Pagination(data=limits, page=page, last_page=last_page, limit=limit)

@router.get("/limits/{uuid}", response_model=limit_schemas.Limit, status_code=status.HTTP_200_OK, tags=["limits"])
def show_limit(uuid: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)

    limit = limit_service.get_limit_by_uuid(db, uuid=str(uuid), user_id=loggedUser.id)

    if limit is None:
        raise http_exceptions.expenditure_not_found
    if limit.owner_id is not loggedUser.id:
        raise http_exceptions.permission_denied_error

    return limit

@router.delete("/limits/{uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["limits"])
def delete_limit(uuid: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)

    limitDB = limit_service.get_limit_by_uuid(db, uuid=str(uuid), user_id=loggedUser.id)

    if limitDB is None:
        raise http_exceptions.expenditure_not_found
    if limitDB.owner_id is not loggedUser.id:
        raise http_exceptions.permission_denied_error

    limit_service.delete_limit(db, str(uuid))

    return None