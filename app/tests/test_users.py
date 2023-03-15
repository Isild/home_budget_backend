from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pytest import fixture
from uuid import uuid4
from fastapi.encoders import jsonable_encoder

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
# user tests
def test_post_user(test_db):
    response = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        },
        headers=authHeadersAdmin
    )

    data = response.json()
    assert response.status_code == 201
    assert data["email"] == "email@w.x"
    assert data["is_active"] == True
    assert data["is_admin"] == False
    assert "uuid" in data
    assert not "password" in data
    assert not "id" in data

def test_post_user_duplicated_email(test_db):
    client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        },
        headers=authHeadersAdmin
    )
    response = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        },
        headers=authHeadersAdmin
    )

    assert response.status_code == 400

def test_get_users_access_denied(test_db):
    response = client.get(
        version + "/users/",
        headers=authHeaders
    )
    
    assert response.status_code == 403

def test_get_users(test_db):
    global testUser, testUserAdmin

    response = client.get(
        version + "/users/",
        headers=authHeadersAdmin
    )
    
    user1Dict = jsonable_encoder(testUserAdmin)
    user2Dict = jsonable_encoder(testUser)

    del user1Dict['token']
    del user1Dict['is_admin']
    del user1Dict['id']
    del user1Dict['password']
    del user2Dict['token']
    del user2Dict['is_admin']
    del user2Dict['id']
    del user2Dict['password']

    assert response.status_code == 200
    assert response.json() == {
        'data': [
            user1Dict,
            user2Dict
        ],
        'page': 1,
        'last_page': 1,
        'limit': 100
    }

def test_get_user(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        },
        headers=authHeadersAdmin
    ).json()

    response = client.get(
        version + "/users/"+ user['uuid'],
        headers=authHeadersAdmin
    )

    data = response.json()
    assert response.status_code == 200
    assert user['uuid'] == data['uuid']
    assert user['email'] == data['email']
    assert user['is_active'] == data['is_active']
    assert user['is_admin'] == data['is_admin']
    # assert user['expenditures'] == data['expenditures']
    assert not "id" in data
    assert not "password" in data

def test_get_user_not_found(test_db):
    response = client.get(
        version + "/users/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        headers=authHeadersAdmin
    )

    assert response.status_code == 404

def test_delete_user(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        },
        headers=authHeadersAdmin
    ).json()

    response = client.delete(
        version + "/users/"+ user['uuid'],
        headers=authHeadersAdmin
    )
    assert response.status_code == 204
    
    response = client.get(
        version + "/users/"+ user['uuid'],
        headers=authHeadersAdmin
    )
    assert response.status_code == 404

def test_delete_user_not_found(test_db):
    response = client.delete(
        version + "/users/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        headers=authHeadersAdmin
    )

    assert response.status_code == 404

def test_get_user_me(test_db):
    response = client.get(
        "auth/users/me",
        headers=authHeadersAdmin
    )
    
    assert response.status_code == 401