from typing import List
from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from uuid import UUID  

from ...services import exposureService, userService
from ...schemas import expenditureSchemas

from ...dependencies import get_db, UserAuthMock, get_settings
from ...exceptions import httpExceptions

router = APIRouter(
    responses={
        403: {"description": "Permissions denied"},
        404: {"description": "Resource not found"},
        500: {"description": "Server error"}
    },
)

# expenditures
@router.post("/expenditures/", response_model=expenditureSchemas.Expenditure, status_code=status.HTTP_201_CREATED, tags=["expenditures"])
def store_expenditure(
    user_uuid: UUID, expenditure: expenditureSchemas.ExpenditureCreate, db: Session = Depends(get_db)
):
    db_user = userService.get_user(db=db, uuid=str(user_uuid))

    if db_user is None:
        raise httpExceptions.user_not_found_error

    return exposureService.post_expenditure(db=db, expenditure=expenditure, user_id=db_user.id)

@router.get("/expenditures/", response_model=List[expenditureSchemas.Expenditure], status_code=status.HTTP_200_OK, tags=["expenditures"])
def index_expenditures(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    if loggedUser.is_admin:
        expendiures = exposureService.get_expenditures(db, skip=skip, limit=limit)
    else:
        raise httpExceptions.permission_denied_error

    return expendiures

@router.get("/users/{user_uuid}/expenditures/", response_model=List[expenditureSchemas.Expenditure], status_code=status.HTTP_200_OK, tags=["expenditures"])
def index_expenditures(user_uuid: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()
    userPath = userService.get_user(db, uuid=str(user_uuid))

    if userPath is None:
        raise httpExceptions.user_not_found_error
    if not loggedUser.id == userPath.id:
        raise httpExceptions.permission_denied_error

    if loggedUser.is_admin:
        expendiures = exposureService.get_expenditures_filter_by_owner_id(db, user_id=userPath.id, skip=skip, limit=limit)

    return expendiures

@router.get("/expenditures/{uuid}", response_model=expenditureSchemas.Expenditure, status_code=status.HTTP_200_OK, tags=["expenditures"])
def show_expenditure(uuid: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    expenditure = exposureService.get_expenditure(db, uuid=str(uuid), user_id=loggedUser.id)

    if expenditure is None:
        raise httpExceptions.expenditure_not_found
    if expenditure.owner_id is not loggedUser.id:
        raise httpExceptions.permission_denied_error

    return expenditure

@router.put("/expenditures/{uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["expenditures"])
def put_expenditure(uuid: UUID, expenditure: expenditureSchemas.ExpenditureCreate, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    expenditureDB = exposureService.get_expenditure(db, uuid=str(uuid), user_id=loggedUser.id)
    if expenditureDB is None:
        raise httpExceptions.expenditure_not_found
    if expenditureDB.owner_id is not loggedUser.id:
        raise httpExceptions.permission_denied_error

    expenditure = exposureService.put_expenditure(db, expenditureDb=expenditureDB, expenditure=expenditure)

    return None

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