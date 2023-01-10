from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pytest import fixture
from uuid import uuid4

from ..models import userModel
from ..database import Base
from ..main import app, get_db
from ..services import authService, userService

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
    userAdmin = userService.get_user_by_email(db=db, email=adminEmail)
    if userAdmin is None:
        userAdmin = userModel.UserModel(email=adminEmail, password="hashed_password", uuid=str(uuid4()), is_active=True, is_admin=True, disabled=False)
        db.add(userAdmin)
    
    # normal user
    userEmail = "email@email.com"
    user = userService.get_user_by_email(db=db, email=userEmail)

    if user is None:
        user = userModel.UserModel(email=userEmail, password="hashed_password", uuid=str(uuid4()), is_active=True, is_admin=False, disabled=False)
        db.add(user)
        db.commit()
        db.refresh(user)

    
    db.refresh(user)
    db.refresh(userAdmin)

    authService.generate_user_token(db=db, user=user)
    authService.generate_user_token(db=db, user=userAdmin)

    testUser = user
    testUserAdmin = userAdmin

    authHeaders = {
        "Authorization": "Bearer " + user.token
    }
    
    authHeadersAdmin = {
        "Authorization": "Bearer " + testUserAdmin.token
    }


### Tests ###
# limits
def test_post_limit(test_db):
    user = testUserAdmin

    response = client.post(
        version + "/limits/",
        params={
        },
        json={
            "year": 1,
            "month": 2023,
            "limit": 21.37
        },
        headers=authHeadersAdmin
    )

    data = response.json()

    assert response.status_code == 201
    assert data["year"] == 1
    assert data["month"] == 2023
    assert data["limit"] == 21.37
    assert "uuid" in data
    assert not "id" in data

def test_get_limit(test_db):
    user = testUserAdmin

    limit = client.post(
        version + "/limits/",
        params={
        },
        json={
            "year": 1,
            "month": 2023,
            "limit": 21.37
        },
        headers=authHeadersAdmin
    ).json()

    response = client.get(
        version + "/limits/"+ limit['uuid'],
        headers=authHeadersAdmin
    )

    data = response.json()
    assert response.status_code == 200
    assert limit['uuid'] == data['uuid']
    assert limit['year'] == data['year']
    assert limit['month'] == data['month']
    assert limit['limit'] == data['limit']
    assert not "id" in data

def test_get_limit_not_found(test_db):
    user = testUserAdmin
    expenditure = client.post(
        version + "/limits/",
        params={
        },
        json={
            "year": 1,
            "month": 2023,
            "limit": 21.37
        },
        headers=authHeadersAdmin
    ).json()

    response = client.get(
        version + "/limits/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        headers=authHeadersAdmin
    )

    data = response.json()
    assert response.status_code == 404

def test_get_limits(test_db):
    user = testUserAdmin

    limit1 = client.post(
        version + "/limits/",
        params={
        },
        json={
            "year": 1,
            "month": 2023,
            "limit": 21.37
        },
        headers=authHeadersAdmin
    )
    limit2 = client.post(
        version + "/limits/",
        params={
        },
        json={
            "year": 2,
            "month": 2023,
            "limit": 21.37
        },
        headers=authHeadersAdmin
    )

    response = client.get(
        version + "/limits/",
        headers=authHeadersAdmin
    )
    limit1Dict = limit1.json()
    limit2Dict = limit2.json()

    assert response.status_code == 200
    assert response.json() == {
        'data': [
            limit1Dict,
            limit2Dict
        ],
        'page': 1,
        'last_page': 1,
        'limit': 100
    }

def test_get_limits_filter_by_user(test_db):
    user = testUserAdmin

    limit1 = client.post(
        version + "/limits/",
        params={
        },
        json={
            "year": 2023,
            "month": 1,
            "limit": 21.37
        },
        headers=authHeadersAdmin
    )
    limit2 = client.post(
        version + "/limits/",
        params={
        },
        json={
            "year": 2023,
            "month": 2,
            "limit": 21.37
        },
        headers=authHeadersAdmin
    )
    limit3 = client.post(
        version + "/limits/",
        params={
        },
        json={
            "year": 2023,
            "month": 3,
            "limit": 21.37
        },
        headers=authHeaders
    )

    response = client.get(
        version + "/users/" + user.uuid + "/limits/",
        headers=authHeadersAdmin
    )

    limit1Dict = limit1.json()
    limit2Dict = limit2.json()

    assert response.status_code == 200
    assert response.json() == {
        'data': [
            limit1Dict,
            limit2Dict
        ],
        'page': 1,
        'last_page': 1,
        'limit': 100
    }

def test_get_limits_filter_by_user_not_found(test_db):
    user = testUserAdmin

    limit1 = client.post(
        version + "/limits/",
        params={
        },
        json={
            "year": 1,
            "month": 2023,
            "limit": 21.37
        },
        headers=authHeadersAdmin
    )
    limit2 = client.post(
        version + "/limits/",
        params={
        },
        json={
            "year": 1,
            "month": 2023,
            "limit": 21.37
        },
        headers=authHeadersAdmin
    )

    response = client.get(
        version + "/users/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb/limits/",
        headers=authHeadersAdmin
    )

    assert response.status_code == 404

def test_put_limit(test_db):
    user = testUserAdmin

    limitBeforeUpdate = client.post(
        version + "/limits/",
        params={
        },
        json={
            "year": 1,
            "month": 2023,
            "limit": 21.37
        },
        headers=authHeadersAdmin
    ).json()
    response = client.put(
        version + "/limits/" + limitBeforeUpdate['uuid'],
        json={
            "year": 2,
            "month": 3,
            "limit": 22.37
        },
        headers=authHeadersAdmin
    )
    assert response.status_code == 204

    response = client.get(
        version + "/limits/"+ limitBeforeUpdate['uuid'],
        headers=authHeadersAdmin
    )

    limitAfterUpdate = response.json()
    assert limitBeforeUpdate['uuid'] == limitAfterUpdate['uuid']
    assert not limitBeforeUpdate['year'] == limitAfterUpdate['year']
    assert not limitBeforeUpdate['month'] == limitAfterUpdate['month']
    assert not limitBeforeUpdate['limit'] == limitAfterUpdate['limit']

def test_put_limit_not_found(test_db):
    user = testUserAdmin

    limitBeforeUpdate = client.post(
        version + "/limits/",
        params={
        },
        json={
            "month": 1,
            "year": 2023,
            "limit": 21.37
        },
        headers=authHeadersAdmin
    ).json()
    response = client.put(
        version + "/limits/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        json={
            "month": 1,
            "year": 2024,
            "limit": 22.37
        },
        headers=authHeadersAdmin
    )
    assert response.status_code == 404

def test_delete_limit(test_db):
    user = testUserAdmin

    limit = client.post(
        version + "/limits/",
        params={
        },
        json={
            "month": 1,
            "year": 2023,
            "limit": 21.37
        },
        headers=authHeadersAdmin
    ).json()

    response = client.delete(
        version + "/limits/"+ limit['uuid'],
        headers=authHeadersAdmin
    )
    assert response.status_code == 204
    
    response = client.get(
        version + "/limits/"+ limit['uuid'],
        headers=authHeadersAdmin
    )
    assert response.status_code == 404

def test_delete_limit_not_found(test_db):
    user = testUserAdmin

    limit = client.post(
        version + "/limits/",
        params={
        },
        json={
            "month": 1,
            "year": 2023,
            "limit": 21.37
        },
        headers=authHeadersAdmin
    ).json()

    response = client.delete(
        version + "/limits/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        headers=authHeadersAdmin
    )
    assert response.status_code == 404
