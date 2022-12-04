from typing import List
from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from uuid import UUID  
from datetime import date, datetime


from ...services import exposureService, userService, expendituresDayStatService
from ...schemas import expendituresDayStatSchemas

from ...dependencies import get_db, UserAuthMock, get_settings
from ...exceptions import httpExceptions

router = APIRouter(
    responses={
        403: {"description": "Permissions denied"},
        404: {"description": "Resource not found"},
        500: {"description": "Server error"}
    },
)

@router.get("/users/{user_uuid}/expenditures-day-stats/", response_model=List[expendituresDayStatSchemas.ExpendituresDayStat], status_code=status.HTTP_200_OK, tags=["expenditures-day-stats"])
def index_expenditures_day_stats(user_uuid: UUID, skip: int = 0, limit: int = 100, search: str = None, date_from: date = None, date_to: date = None, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()
    userPath = userService.get_user(db, uuid=str(user_uuid))

    if userPath is None:
        raise httpExceptions.user_not_found_error
    if not loggedUser.id == userPath.id:
        raise httpExceptions.permission_denied_error

    expendiures_day_stats = expendituresDayStatService.get_expenditures_day_stats(db=db, user_id=userPath.id, skip=skip, limit=limit, search=search, date_from=date_from, date_to=date_to)

    return expendiures_day_stats

@router.get("/expenditures-day-stats/{uuid}", response_model=expendituresDayStatSchemas.ExpendituresDayStat, status_code=status.HTTP_200_OK, tags=["expenditures-day-stats"])
def show_expenditure_day_stat(uuid: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    expenditure = expendituresDayStatService.get_expenditure_day_stat(db, uuid=str(uuid))

    if expenditure is None:
        raise httpExceptions.expenditure_not_found
    if expenditure.owner_id is not loggedUser.id:
        raise httpExceptions.permission_denied_error

    return expenditure


def __get_auth_user():
    mockUser = UserAuthMock()

    return mockUser