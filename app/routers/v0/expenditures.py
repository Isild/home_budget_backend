from fastapi import Depends, status, APIRouter, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID  
from datetime import date
import math

from ...services import auth_service, exposure_service, user_service
from ...schemas import expenditure_schemas
from ...dependencies import get_db, get_settings, oauth2_scheme
from ...exceptions import http_exceptions
from ...jobs import expenditure_jobs
from ...models import expenditure_model

router = APIRouter(
    responses={
        403: {"description": "Permissions denied"},
        404: {"description": "Resource not found"},
        500: {"description": "Server error"}
    },
)

# expenditures
@router.post("/expenditures/", response_model=expenditure_schemas.Expenditure, status_code=status.HTTP_201_CREATED, tags=["expenditures"])
async def store_expenditure(
     background_task: BackgroundTasks, expenditure: expenditure_schemas.ExpenditureCreate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    db_user = auth_service.decode_token(db=db, token=token)

    if db_user is None:
        raise http_exceptions.user_not_found_error

    if expenditure.type not in expenditure_model.ExpenditureTypes._value2member_map_:
        raise http_exceptions.validation_error

    createdExpenditure = exposure_service.create_expenditure(db=db, expenditure=expenditure, user_id=db_user.id)

    background_task.add_task(expenditure_jobs.recalculateDayExpenditures, db=db, user_id=db_user.id, expenditure=createdExpenditure)

    return createdExpenditure

@router.put("/expenditures/{uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["expenditures"])
def put_expenditure(uuid: UUID, expenditure: expenditure_schemas.ExpenditureCreate, background_task: BackgroundTasks, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)

    expenditureDB = exposure_service.get_expenditure(db, uuid=str(uuid), user_id=loggedUser.id)
    if expenditureDB is None:
        raise http_exceptions.expenditure_not_found
    if expenditureDB.owner_id is not loggedUser.id:
        raise http_exceptions.permission_denied_error
        
    if expenditure.type not in expenditure_model.ExpenditureTypes._value2member_map_:
        raise http_exceptions.validation_error

    expenditure = exposure_service.update_expenditure(db, expenditureDb=expenditureDB, expenditure=expenditure)

    background_task.add_task(expenditure_jobs.recalculateDayExpenditures, db=db, user_id=loggedUser.id, expenditure=expenditure)

    return None

@router.get("/expenditures/", response_model=expenditure_schemas.Pagination, status_code=status.HTTP_200_OK, tags=["expenditures"])
def index_expenditures(token: str = Depends(oauth2_scheme), page: int = 1, limit: int = 100, search: str = None, date_from: date = None, date_to: date = None, db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)

    if loggedUser.is_admin:
        expendiures = exposure_service.get_expenditures(db, page=page, limit=limit, search=search, date_from=date_from, date_to=date_to)
    else:
        raise http_exceptions.permission_denied_error

    amount = exposure_service.get_expenditure_amount(db,user_id=None)
    last_page = math.ceil(amount/limit)

    return expenditure_schemas.Pagination(data=expendiures, page=page, last_page=last_page, limit=limit)

@router.get("/users/{user_uuid}/expenditures/", response_model=expenditure_schemas.Pagination, status_code=status.HTTP_200_OK, tags=["expenditures"])
def index_user_expenditures(user_uuid: UUID, token: str = Depends(oauth2_scheme), page: int = 1, limit: int = 100, search: str = None, date_from: date = None, date_to: date = None, db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)
    userPath = user_service.get_user(db, uuid=str(user_uuid))
    
    if userPath is None:
            raise http_exceptions.user_not_found_error

    if loggedUser.is_admin:
        expendiures = exposure_service.get_expenditures(db, page=page, limit=limit, search=search, date_from=date_from, date_to=date_to, user_id=userPath.id)
        amount = exposure_service.get_expenditure_amount(db,user_id=userPath.id)
    else:
        if not loggedUser.id == userPath.id:
            raise http_exceptions.permission_denied_error

        expendiures = exposure_service.get_expenditures(db, page=page, limit=limit, search=search, date_from=date_from, date_to=date_to, user_id=loggedUser.id)
        amount = exposure_service.get_expenditure_amount(db,user_id=loggedUser.id)

    last_page = math.ceil(amount/limit)

    return expenditure_schemas.Pagination(data=expendiures, page=page, last_page=last_page, limit=limit)

@router.get("/expenditures/{uuid}", response_model=expenditure_schemas.Expenditure, status_code=status.HTTP_200_OK, tags=["expenditures"])
def show_expenditure(uuid: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)

    expenditure = exposure_service.get_expenditure(db, uuid=str(uuid), user_id=loggedUser.id)

    if expenditure is None:
        raise http_exceptions.expenditure_not_found
    if expenditure.owner_id is not loggedUser.id:
        raise http_exceptions.permission_denied_error

    return expenditure

@router.delete("/expenditures/{uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["expenditures"])
def delete_expenditure(uuid: UUID, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    loggedUser = auth_service.decode_token(db=db, token=token)

    expenditureDB = exposure_service.get_expenditure(db, uuid=str(uuid), user_id=loggedUser.id)

    if expenditureDB is None:
        raise http_exceptions.expenditure_not_found
    if expenditureDB.owner_id is not loggedUser.id:
        raise http_exceptions.permission_denied_error

    exposure_service.delete_expenditre(db, str(uuid))

    return None