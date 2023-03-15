from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pytest import fixture
from uuid import uuid4

from ..models import user_model
from ..database import Base
from ..main import app, get_db
from ..services import auth_service, user_service

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    preper_to_test(next(override_get_db()))

    yield
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        print("should close db")
        # db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

version :str = "/v0"

testUserAdmin = None
testUser = None

authHeadersAdmin = None
authHeaders = None

def preper_to_test(db):
    global testUser, testUserAdmin, authHeaders, authHeadersAdmin
    # admin user
    adminEmail = "emailAdmin@email.com"
    userAdmin = user_service.get_user_by_email(db=db, email=adminEmail)
    if userAdmin is None:
        userAdmin = user_model.UserModel(email=adminEmail, password="hashed_password", uuid=str(uuid4()), is_active=True, is_admin=True, disabled=False)
        db.add(userAdmin)

    # normal user
    userEmail = "email@email.com"
    user = user_service.get_user_by_email(db=db, email=userEmail)

    if user is None:
        user = user_model.UserModel(email=userEmail, password="hashed_password", uuid=str(uuid4()), is_active=True, is_admin=False, disabled=False)
        db.add(user)
        db.commit()
        db.refresh(user)

    
    db.refresh(user)
    db.refresh(userAdmin)

    auth_service.generate_user_token(db=db, user=user)
    auth_service.generate_user_token(db=db, user=userAdmin)

    testUser = user
    testUserAdmin = userAdmin

    authHeaders = {
        "Authorization": "Bearer " + user.token
    }
    
    authHeadersAdmin = {
        "Authorization": "Bearer " + testUserAdmin.token
    }


### Tests ###

def test_read_main(test_db):
    response = client.get("/")
    assert response.status_code == 200