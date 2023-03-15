from fastapi import Depends, status, APIRouter
from sqlalchemy.orm import Session
from uuid import UUID  
from datetime import date
import math

from ...services import auth_service, expenditures_day_stat_service, user_service
from ...schemas import expenditures_day_stat_schemas

from ...dependencies import get_db, get_settings, oauth2_scheme
from ...exceptions import http_exceptions

router = APIRouter(
    responses={
        403: {"description": "Permissions denied"},
        404: {"description": "Resource not found"},
        500: {"description": "Server error"}
    },
)

@router.get("/users/{user_uuid}/expenditures-day-stats/", response_model=expenditures_day_stat_schemas.Pagination, status_code=status.HTTP_200_OK, tags=["expenditures-day-stats"])
def index_expenditures_day_stats(user_uuid: UUID, token: str = Depends(oauth2_scheme), page: int = 1, limit: int = 100, date_from: date = None, date_to: date = None, group_by: str = None, db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)
    userPath = user_service.get_user(db, uuid=str(user_uuid))
    
    if userPath is None:
        raise http_exceptions.user_not_found_error
    if loggedUser is None:
        raise http_exceptions.user_not_found_error
    if not loggedUser.id == userPath.id:
        raise http_exceptions.permission_denied_error

    expendiures_day_stats = expenditures_day_stat_service.get_expenditures_day_stats(db=db, user_id=userPath.id, page=page, limit=limit, search=None, date_from=date_from, date_to=date_to, group_by=group_by)
    
    amount = expenditures_day_stat_service.get_expenditure_day_stats_amount(db,user_id=userPath.id)
    last_page = math.ceil(amount/limit)

    return expenditures_day_stat_schemas.Pagination(data=expendiures_day_stats, page=page, last_page=last_page, limit=limit)

@router.get("/expenditures-day-stats/{uuid}", response_model=expenditures_day_stat_schemas.ExpendituresDayStat, status_code=status.HTTP_200_OK, tags=["expenditures-day-stats"])
def show_expenditure_day_stat(uuid: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)

    if loggedUser is None:
        raise http_exceptions.unauth_error

    expenditure = expenditures_day_stat_service.get_expenditure_day_stat(db, uuid=str(uuid))

    if expenditure is None:
        raise http_exceptions.expenditure_not_found
    if expenditure.owner_id is not loggedUser.id:
        raise http_exceptions.permission_denied_error

    return expenditure

@router.get("/users/{user_uuid}/expenditures-day-stats/month-limit", response_model=expenditures_day_stat_schemas.ExpendituresLimitBase, status_code=status.HTTP_200_OK, tags=["expenditures-day-stats"])
def show_expenditures_month_limit(user_uuid: UUID, token: str = Depends(oauth2_scheme), year: int = None, db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)
    userPath = user_service.get_user(db, uuid=str(user_uuid))
    
    if userPath is None:
        raise http_exceptions.user_not_found_error
    if loggedUser is None:
        raise http_exceptions.user_not_found_error
    if not loggedUser.id == userPath.id:
        raise http_exceptions.permission_denied_error

    limit_data = expenditures_day_stat_service.get_month_limit_data(db=db, year=year, user_id=loggedUser.id)

    return limit_data