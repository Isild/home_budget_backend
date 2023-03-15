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
# expenditures
## add tests for search and date filters
def test_post_expenditure(test_db):
    user = testUserAdmin

    response = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user.uuid
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    )

    data = response.json()

    assert response.status_code == 201
    assert data["name"] == "name"
    assert data["cost"] == 1.2
    assert data["date"] == "2008-09-15"
    assert data["place"] == "place"
    assert "uuid" in data
    assert not "id" in data

def test_get_expenditure(test_db):
    user = testUserAdmin

    expenditure = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user.uuid
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    ).json()

    response = client.get(
        version + "/expenditures/"+ expenditure['uuid'],
        headers=authHeadersAdmin
    )

    data = response.json()
    assert response.status_code == 200
    assert expenditure['uuid'] == data['uuid']
    assert expenditure['name'] == data['name']
    assert expenditure['cost'] == data['cost']
    assert expenditure['date'] == data['date']
    assert expenditure['place'] == data['place']
    assert not "id" in data

def test_get_expenditure_not_found(test_db):
    user = testUserAdmin
    expenditure = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user.uuid
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    ).json()

    response = client.get(
        version + "/expenditures/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        headers=authHeadersAdmin
    )

    data = response.json()
    assert response.status_code == 404

def test_get_expenditures(test_db):
    user = testUserAdmin

    expenditure1 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user.uuid
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    )
    expenditure2 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user.uuid
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    )

    response = client.get(
        version + "/expenditures/",
        headers=authHeadersAdmin
    )
    expenditure1Dict = expenditure1.json()
    expenditure2Dict = expenditure2.json()

    assert response.status_code == 200
    assert response.json() == {
        'data': [
            expenditure1Dict,
            expenditure2Dict
        ],
        'page': 1,
        'last_page': 1,
        'limit': 100
    }

def test_get_expenditures_filter_by_user(test_db):
    user = testUserAdmin

    expenditure1 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user.uuid
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    )
    expenditure2 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user.uuid
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    )

    response = client.get(
        version + "/users/" + user.uuid + "/expenditures/",
        headers=authHeadersAdmin
    )

    expenditure1Dict = expenditure1.json()
    expenditure2Dict = expenditure2.json()

    assert response.status_code == 200
    assert response.json() == {
        'data': [
            expenditure1Dict,
            expenditure2Dict
        ],
        'page': 1,
        'last_page': 1,
        'limit': 100
    }

def test_get_expenditures_filter_by_user_not_found(test_db):
    user = testUserAdmin

    expenditure1 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user.uuid
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    )
    expenditure2 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user.uuid
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    )

    response = client.get(
        version + "/users/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb/expenditures/",
        headers=authHeadersAdmin
    )

    assert response.status_code == 404

def test_put_expenditure(test_db):
    user = testUserAdmin

    expenditureBeforeUpdate = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user.uuid
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    ).json()
    response = client.put(
        version + "/expenditures/" + expenditureBeforeUpdate['uuid'],
        json={
            "name":"name1",
            "cost":1.21,
            "date":"2008-09-16",
            "place":"place1",
            "type":"normal",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    )
    assert response.status_code == 204

    response = client.get(
        version + "/expenditures/"+ expenditureBeforeUpdate['uuid'],
        headers=authHeadersAdmin
    )

    expenditureAfterUpdate = response.json()
    assert expenditureBeforeUpdate['uuid'] == expenditureAfterUpdate['uuid']
    assert not expenditureBeforeUpdate['name'] == expenditureAfterUpdate['name']
    assert not expenditureBeforeUpdate['cost'] == expenditureAfterUpdate['cost']
    assert not expenditureBeforeUpdate['date'] == expenditureAfterUpdate['date']
    assert not expenditureBeforeUpdate['place'] == expenditureAfterUpdate['place']

def test_put_expenditure_not_found(test_db):
    user = testUserAdmin

    expenditureBeforeUpdate = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user.uuid
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    ).json()
    response = client.put(
        version + "/expenditures/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        json={
            "name":"name1",
            "cost":1.21,
            "date":"2008-09-16",
            "place":"place1",
            "type":"normal",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    )
    assert response.status_code == 404

def test_delete_expenditure(test_db):
    user = testUserAdmin

    expenditure = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user.uuid
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    ).json()

    response = client.delete(
        version + "/expenditures/"+ expenditure['uuid'],
        headers=authHeadersAdmin
    )
    assert response.status_code == 204
    
    response = client.get(
        version + "/expenditures/"+ expenditure['uuid'],
        headers=authHeadersAdmin
    )
    assert response.status_code == 404

def test_delete_expenditure_not_found(test_db):
    user = testUserAdmin

    expenditure = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user.uuid
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    ).json()

    response = client.delete(
        version + "/expenditures/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        headers=authHeadersAdmin
    )
    assert response.status_code == 404
