from fastapi import Depends, status, APIRouter, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID  
from datetime import date
import math

from ...services import limitService, userService, authService
from ...schemas import limitSchemas
from ...dependencies import get_db, get_settings, oauth2_scheme
from ...exceptions import httpExceptions
from ...models import limitsModel

router = APIRouter(
    responses={
        403: {"description": "Permissions denied"},
        404: {"description": "Resource not found"},
        500: {"description": "Server error"}
    },
)

# limits
@router.post("/limits/", response_model=limitSchemas.Limit, status_code=status.HTTP_201_CREATED, tags=["limits"])
async def store_limit(limit: limitSchemas.LimitCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    db_user = authService.decode_token(db=db, token=token)

    if db_user is None:
        raise httpExceptions.user_not_found_error

    limitDB = limitService.get_limit_by_month_and_year(db=db, month=limit.month, year=limit.year, user_id=db_user.id)
    if limitDB:
        createdLimit = limitService.update_limit(db, limitDb=limitDB, limit=limit)
    else:
        createdLimit = limitService.create_limit(db=db, limit=limit, user_id=db_user.id)

    return createdLimit

@router.put("/limits/{uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["limits"])
def put_limit(uuid: UUID, limit: limitSchemas.LimitCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = authService.decode_token(db=db, token=token)

    limitDB = limitService.get_limit_by_uuid(db, uuid=str(uuid), user_id=loggedUser.id)
    if limitDB is None:
        raise httpExceptions.limit_not_found
    if limitDB.owner_id is not loggedUser.id:
        raise httpExceptions.permission_denied_error

    limitDB2 = limitService.get_limit_by_month_and_year(db=db, month=limit.month, year=limit.year, user_id=loggedUser.id)

    if limitDB2 is not None:
        if limitDB2.year == limitDB.year and limitDB2.month == limitDB.month and limitDB2.owner_id == limitDB.owner_id:
            limit = limitService.update_limit(db, limitDb=limitDB, limit=limit)
        else:
            raise httpExceptions.cannot_update_limit_unique_month
    else:
        limit = limitService.update_limit(db, limitDb=limitDB, limit=limit)

    return None

@router.get("/limits/", response_model=limitSchemas.Pagination, status_code=status.HTTP_200_OK, tags=["limits"])
def index_limit(token: str = Depends(oauth2_scheme), page: int = 1, limit: int = 100, search: str = None, year: date = None, db: Session = Depends(get_db)):
    loggedUser = authService.decode_token(db=db, token=token)

    if loggedUser.is_admin:
        limits = limitService.get_limits(db, page=page, limit=limit, search=search, year=year)
    else:
        raise httpExceptions.permission_denied_error

    amount = limitService.get_limits_amount(db,user_id=None)
    last_page = math.ceil(amount/limit)

    return limitSchemas.Pagination(data=limits, page=page, last_page=last_page, limit=limit)

@router.get("/users/{user_uuid}/limits/", response_model=limitSchemas.Pagination, status_code=status.HTTP_200_OK, tags=["limits"])
def index_user_limits(user_uuid: UUID, token: str = Depends(oauth2_scheme), page: int = 1, limit: int = 100, search: str = None, year: date = None, db: Session = Depends(get_db)):
    loggedUser = authService.decode_token(db=db, token=token)
    userPath = userService.get_user(db, uuid=str(user_uuid))
    
    if userPath is None:
            raise httpExceptions.user_not_found_error

    if loggedUser.is_admin:
        limits = limitService.get_limits(db, page=page, limit=limit, search=search, year=year, user_id=userPath.id)
        amount = limitService.get_limits_amount(db,user_id=userPath.id)
    else:
        if not loggedUser.id == userPath.id:
            raise httpExceptions.permission_denied_error

        limits = limitService.get_limits(db, page=page, limit=limit, search=search, year=year, user_id=loggedUser.id)
        amount = limitService.get_limits_amount(db,user_id=loggedUser.id)

    last_page = math.ceil(amount/limit)

    return limitSchemas.Pagination(data=limits, page=page, last_page=last_page, limit=limit)

@router.get("/limits/{uuid}", response_model=limitSchemas.Limit, status_code=status.HTTP_200_OK, tags=["limits"])
def show_limit(uuid: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = authService.decode_token(db=db, token=token)

    limit = limitService.get_limit_by_uuid(db, uuid=str(uuid), user_id=loggedUser.id)

    if limit is None:
        raise httpExceptions.expenditure_not_found
    if limit.owner_id is not loggedUser.id:
        raise httpExceptions.permission_denied_error

    return limit

@router.delete("/limits/{uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["limits"])
def delete_limit(uuid: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = authService.decode_token(db=db, token=token)

    limitDB = limitService.get_limit_by_uuid(db, uuid=str(uuid), user_id=loggedUser.id)

    if limitDB is None:
        raise httpExceptions.expenditure_not_found
    if limitDB.owner_id is not loggedUser.id:
        raise httpExceptions.permission_denied_error

    limitService.delete_limit(db, str(uuid))

    return None