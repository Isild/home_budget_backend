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
# expenditures day stat 
def test_index_expenditures_day_stats(test_db):
    expenditure1 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":testUserAdmin.uuid
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
    expenditure2 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":testUserAdmin.uuid
        },
        json={
            "name":"name",
            "cost":2.2,
            "date":"2009-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    ).json()
    expenditure3 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":testUserAdmin.uuid
        },
        json={
            "name":"name",
            "cost":3.2,
            "date":"2010-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    ).json()
    expenditure4 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":testUserAdmin.uuid
        },
        json={
            "name":"name",
            "cost":4.2,
            "date":"2010-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    ).json()

    response = client.get(
        version + "/users/" + testUserAdmin.uuid + "/expenditures-day-stats",
        headers=authHeadersAdmin
    )

    assert response.status_code == 200
    response = response.json()
    assert len(response['data']) == 3
    assert response['data'][0]['total_cost'] == expenditure1['cost']
    assert response['data'][0]['date'] == expenditure1['date']
    assert response['data'][1]['total_cost'] == expenditure2['cost']
    assert response['data'][1]['date'] == expenditure2['date']
    assert response['data'][2]['total_cost'] == expenditure3['cost'] + expenditure4['cost']
    assert response['data'][2]['date'] == expenditure3['date']
    assert response['data'][2]['date'] == expenditure4['date']

def test_show_expenditures_day_stats(test_db):
    expenditure1 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":testUserAdmin.uuid
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
    expenditure2 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":testUser.uuid
        },
        json={
            "name":"name",
            "cost":2.2,
            "date":"2009-09-15",
            "place":"place",
            "type":"cyclical"
        },
        headers=authHeadersAdmin
    ).json()

    response = client.get(
        version + "/users/" + testUserAdmin.uuid + "/expenditures-day-stats",
        headers=authHeadersAdmin
    )

    assert response.status_code == 200
    response = response.json()

    response = client.get(
        version + "/expenditures-day-stats/" + response['data'][0]['uuid'],
        headers=authHeadersAdmin
    )
    data = response.json()
    assert response.status_code == 200

    assert "uuid" in data
    assert "total_cost" in data
    assert "date" in data
    assert not "id" in data
