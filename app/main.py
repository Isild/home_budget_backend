from typing import List
from fastapi import Depends, FastAPI, HTTPException, Request, status, Response
from sqlalchemy.orm import Session
from uuid import UUID  
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import time

from . import crud
from .database import SessionLocal, engine
from .schemas import userSchemas, expenditureSchemas, userTokenSchemas
from .models import userModel, expenditureModel

userModel.Base.metadata.create_all(bind=engine)

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# app
@app.get("/", tags=["app"])
def read_root(request: Request):
    return {
        "version": "v0.1",
        "documentation": request.client.host + "/docs"
    }

# auth 
async def get_current_active_user(token: str = Depends(oauth2_scheme)):
    db = next(get_db())
    return crud.get_current_user(db=db, token=token)
    
@app.post("/login", response_model=userTokenSchemas.TokenData, tags=["auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends(),  db: Session = Depends(get_db)):
    # in request form username will be a email
    userDB = crud.get_user_by_email(db, email=form_data.username)
    unauth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not userDB:
        raise unauth_error

    if not crud.authenticate_user(db=db, user=userDB, password=form_data.password):
        raise unauth_error

    token = crud.generate_user_token(db, user=userDB)

    return {
        "access_token": token, 
        "token_type": "bearer"
    }

@app.get("/users/me", response_model=userSchemas.UserPublic, tags=["auth"])
def red_user_me(current_user: userSchemas.UserPublic = Depends(get_current_active_user)):
    return current_user

# users
@app.post("/users/", response_model=userSchemas.User, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user(user: userSchemas.UserCreate, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    if loggedUser.is_admin:
        db_user = crud.get_user_by_email(db, email=user.email)

        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        return crud.create_user(db=db, user=user)
    else:
        raise HTTPException(status_code=403, detail="Permissions denied")


@app.get("/users/", response_model=List[userSchemas.User], status_code=status.HTTP_200_OK, tags=["users"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_uuid}", response_model=userSchemas.User, status_code=status.HTTP_200_OK, tags=["users"])
def read_user(user_uuid: UUID, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, uuid=str(user_uuid))

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user

@app.delete("/users/{user_uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["users"])
def read_user(user_uuid: UUID, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    if loggedUser.is_admin:
        db_user = crud.get_user(db, uuid=str(user_uuid))

        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        crud.delete_user(db, uuid=db_user.uuid)

        return None
    else:
        raise HTTPException(status_code=403, detail="Permissions denied")

# expenditures
@app.post("/expenditures/", response_model=expenditureSchemas.Expenditure, status_code=status.HTTP_201_CREATED, tags=["expenditures"])
def store_expenditure(
    user_uuid: UUID, expenditure: expenditureSchemas.ExpenditureCreate, db: Session = Depends(get_db)
):
    db_user = crud.get_user(db=db, uuid=str(user_uuid))

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return crud.post_expenditure(db=db, expenditure=expenditure, user_id=db_user.id)

@app.get("/expenditures/", response_model=List[expenditureSchemas.Expenditure], status_code=status.HTTP_200_OK, tags=["expenditures"])
def index_expenditures(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    if loggedUser.is_admin:
        expendiures = crud.get_expenditures(db, skip=skip, limit=limit)
    else:
        raise HTTPException(status_code=403, detail="Permissions denied")

    return expendiures

@app.get("/users/{user_uuid}/expenditures/", response_model=List[expenditureSchemas.Expenditure], status_code=status.HTTP_200_OK, tags=["expenditures"])
def index_expenditures(user_uuid: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()
    userPath = crud.get_user(db, uuid=str(user_uuid))

    if userPath is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not loggedUser.id == userPath.id:
        raise HTTPException(status_code=403, detail="Permissions denied")

    if loggedUser.is_admin:
        expendiures = crud.get_expenditures_filter_by_owner_id(db, user_id=userPath.id, skip=skip, limit=limit)

    return expendiures

@app.get("/expenditures/{uuid}", response_model=expenditureSchemas.Expenditure, status_code=status.HTTP_200_OK, tags=["expenditures"])
def show_expenditure(uuid: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    expenditure = crud.get_expenditure(db, uuid=str(uuid), user_id=loggedUser.id)

    if expenditure is None:
        raise HTTPException(status_code=404, detail="Expenditure not found")
    if expenditure.owner_id is not loggedUser.id:
        raise HTTPException(status_code=403, detail="Permissions denied")

    return expenditure

@app.put("/expenditures/{uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["expenditures"])
def put_expenditure(uuid: UUID, expenditure: expenditureSchemas.ExpenditureCreate, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    expenditureDB = crud.get_expenditure(db, uuid=str(uuid), user_id=loggedUser.id)
    if expenditureDB is None:
        raise HTTPException(status_code=404, detail="Expenditure not found")
    if expenditureDB.owner_id is not loggedUser.id:
        raise HTTPException(status_code=403, detail="Permissions denied")

    expenditure = crud.put_expenditure(db, expenditureDb=expenditureDB, expenditure=expenditure)

    return None

@app.delete("/expenditures/{uuid}", status_code=status.HTTP_204_NO_CONTENT, tags=["expenditures"])
def delete_expenditure(uuid: UUID, db: Session = Depends(get_db)):
    loggedUser = __get_auth_user()

    expenditureDB = crud.get_expenditure(db, uuid=str(uuid), user_id=loggedUser.id)

    if expenditureDB is None:
        raise HTTPException(status_code=404, detail="Expenditure not found")
    if expenditureDB.owner_id is not loggedUser.id:
        raise HTTPException(status_code=403, detail="Permissions denied")

    crud.delete_expenditre(db, str(uuid))

    return None

# helpers
class UserAuthMock:
    is_admin = True
    id = 1

def __get_auth_user():
    mockUser = UserAuthMock()

    return mockUser

    