from typing import List
from fastapi import Depends, HTTPException, status, APIRouter, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID  
from datetime import date, datetime
import asyncio
import math

from ...services import exposureService, userService, expendituresDayStatService
from ...schemas import expenditureSchemas, expendituresDayStatSchemas
from ...dependencies import get_db, UserAuthMock, get_settings
from ...exceptions import httpExceptions
from ...jobs import expenditureJobs
from ...models import expendituresDayStatModel, expenditureModel

router = APIRouter(
    responses={
        403: {"description": "Permissions denied"},
        404: {"description": "Resource not found"},
        500: {"description": "Server error"}
    },
)

# expenditures
@router.post("/expenditures/", response_model=expenditureSchemas.Expenditure, status_code=status.HTTP_201_CREATED, tags=["expenditures"])
async def store_expenditure(
     background_task: BackgroundTasks, user_uuid: UUID, expenditure: expenditureSchemas.ExpenditureCreate, db: Session = Depends(get_db)
):
    db_user = userService.get_user(db=db, uuid=str(user_uuid))

    if db_user is None:
        raise httpExceptions.user_not_found_error

    if expenditure.type not in expenditureModel.ExpenditureTypes._value2member_map_:
        raise httpExceptions.validation_error

    createdExpenditure = exposureService.post_expenditure(db=db, expenditure=expenditure, user_id=db_user.id)

    background_task.add_task(expenditureJobs.recalculateDayExpenditures, db=db, user_id=db_user.id, expenditure=createdExpenditure)

    return createdExpenditure

@router.put("/expenditures/{uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["expenditures"])
def put_expenditure(uuid: UUID, expenditure: expenditureSchemas.ExpenditureCreate, background_task: BackgroundTasks, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    expenditureDB = exposureService.get_expenditure(db, uuid=str(uuid), user_id=loggedUser.id)
    if expenditureDB is None:
        raise httpExceptions.expenditure_not_found
    if expenditureDB.owner_id is not loggedUser.id:
        raise httpExceptions.permission_denied_error
        
    if expenditure.type not in expenditureModel.ExpenditureTypes._value2member_map_:
        raise httpExceptions.validation_error

    expenditure = exposureService.put_expenditure(db, expenditureDb=expenditureDB, expenditure=expenditure)

    background_task.add_task(expenditureJobs.recalculateDayExpenditures, db=db, user_id=loggedUser.id, expenditure=expenditure)

    return None

@router.get("/expenditures/", response_model=expenditureSchemas.Pagination, status_code=status.HTTP_200_OK, tags=["expenditures"])
def index_expenditures(page: int = 1, limit: int = 100, search: str = None, date_from: date = None, date_to: date = None, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    if loggedUser.is_admin:
        expendiures = exposureService.get_expenditures(db, page=page, limit=limit, search=search, date_from=date_from, date_to=date_to)
    else:
        raise httpExceptions.permission_denied_error

    amount = exposureService.get_expenditure_amount(db,user_id=None)
    last_page = math.ceil(amount/limit)

    return expenditureSchemas.Pagination(data=expendiures, page=page, last_page=last_page, limit=limit)

@router.get("/users/{user_uuid}/expenditures/", response_model=expenditureSchemas.Pagination, status_code=status.HTTP_200_OK, tags=["expenditures"])
def index_expenditures(user_uuid: UUID, page: int = 1, limit: int = 100, search: str = None, date_from: date = None, date_to: date = None, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()
    userPath = userService.get_user(db, uuid=str(user_uuid))
    
    if userPath is None:
            raise httpExceptions.user_not_found_error

    if loggedUser.is_admin:
        expendiures = exposureService.get_expenditures(db, page=page, limit=limit, search=search, date_from=date_from, date_to=date_to, user_id=userPath.id)
        amount = exposureService.get_expenditure_amount(db,user_id=userPath.id)
    else:
        if not loggedUser.id == userPath.id:
            raise httpExceptions.permission_denied_error

        expendiures = exposureService.get_expenditures(db, page=page, limit=limit, search=search, date_from=date_from, date_to=date_to, user_id=loggedUser.id)
        amount = exposureService.get_expenditure_amount(db,user_id=loggedUser.id)

    last_page = math.ceil(amount/limit)

    return expenditureSchemas.Pagination(data=expendiures, page=page, last_page=last_page, limit=limit)

@router.get("/expenditures/{uuid}", response_model=expenditureSchemas.Expenditure, status_code=status.HTTP_200_OK, tags=["expenditures"])
def show_expenditure(uuid: UUID, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    expenditure = exposureService.get_expenditure(db, uuid=str(uuid), user_id=loggedUser.id)

    if expenditure is None:
        raise httpExceptions.expenditure_not_found
    if expenditure.owner_id is not loggedUser.id:
        raise httpExceptions.permission_denied_error

    return expenditure

@router.delete("/expenditures/{uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["expenditures"])
def delete_expenditure(uuid: UUID, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    expenditureDB = exposureService.get_expenditure(db, uuid=str(uuid), user_id=loggedUser.id)

    if expenditureDB is None:
        raise httpExceptions.expenditure_not_found
    if expenditureDB.owner_id is not loggedUser.id:
        raise httpExceptions.permission_denied_error

    exposureService.delete_expenditre(db, str(uuid))

    return None


def __get_auth_user():
    mockUser = UserAuthMock()

    return mockUser