from fastapi import Depends, status, APIRouter
from sqlalchemy.orm import Session
from uuid import UUID  
from datetime import date
import math

from ...services import userService, expendituresDayStatService, authService
from ...schemas import expendituresDayStatSchemas

from ...dependencies import get_db, get_settings, oauth2_scheme
from ...exceptions import httpExceptions

router = APIRouter(
    responses={
        403: {"description": "Permissions denied"},
        404: {"description": "Resource not found"},
        500: {"description": "Server error"}
    },
)

@router.get("/users/{user_uuid}/expenditures-day-stats/", response_model=expendituresDayStatSchemas.Pagination, status_code=status.HTTP_200_OK, tags=["expenditures-day-stats"])
def index_expenditures_day_stats(user_uuid: UUID, token: str = Depends(oauth2_scheme), page: int = 1, limit: int = 100, date_from: date = None, date_to: date = None, group_by: str = None, db: Session = Depends(get_db)):
    loggedUser = authService.decode_token(db=db, token=token)
    userPath = userService.get_user(db, uuid=str(user_uuid))
    
    if userPath is None:
        raise httpExceptions.user_not_found_error
    if loggedUser is None:
        raise httpExceptions.user_not_found_error
    if not loggedUser.id == userPath.id:
        raise httpExceptions.permission_denied_error

    expendiures_day_stats = expendituresDayStatService.get_expenditures_day_stats(db=db, user_id=userPath.id, page=page, limit=limit, search=None, date_from=date_from, date_to=date_to, group_by=group_by)
    
    amount = expendituresDayStatService.get_expenditure_day_stats_amount(db,user_id=userPath.id)
    last_page = math.ceil(amount/limit)

    return expendituresDayStatSchemas.Pagination(data=expendiures_day_stats, page=page, last_page=last_page, limit=limit)

@router.get("/expenditures-day-stats/{uuid}", response_model=expendituresDayStatSchemas.ExpendituresDayStat, status_code=status.HTTP_200_OK, tags=["expenditures-day-stats"])
def show_expenditure_day_stat(uuid: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = authService.decode_token(db=db, token=token)

    expenditure = expendituresDayStatService.get_expenditure_day_stat(db, uuid=str(uuid))

    if expenditure is None:
        raise httpExceptions.expenditure_not_found
    if expenditure.owner_id is not loggedUser.id:
        raise httpExceptions.permission_denied_error

    return expenditure
