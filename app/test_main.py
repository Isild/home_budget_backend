from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pytest import fixture

from .models import userModel, expenditureModel
from .database import Base
from .main import app, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

version :str = "/v0"

### Tests ###

def test_read_main(test_db):
    response = client.get("/")
    assert response.status_code == 200

# user tests
def test_post_user(test_db):
    response = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
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
        }
    )
    response = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    )

    data = response.json()
    assert response.status_code == 400

def test_get_users_empty(test_db):
    response = client.get(version + "/users/")
    
    assert response.status_code == 200
    assert response.json() == []

def test_get_users(test_db):
    user1 = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    )
    user2 = client.post(
        version + "/users/",
        json={
            "email":"email2@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    )
    response = client.get(version + "/users/")
    
    assert response.status_code == 200
    assert response.json() == [
        user1.json(),
        user2.json()
    ]

def test_get_user(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    ).json()

    response = client.get(version + "/users/"+ user['uuid'])

    data = response.json()
    assert response.status_code == 200
    assert user['uuid'] == data['uuid']
    assert user['email'] == data['email']
    assert user['is_active'] == data['is_active']
    assert user['is_admin'] == data['is_admin']
    assert user['expenditures'] == data['expenditures']
    assert not "id" in data
    assert not "password" in data

def test_get_user_not_found(test_db):
    response = client.get(version + "/users/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    assert response.status_code == 404

def test_delete_user(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    ).json()

    response = client.delete(version + "/users/"+ user['uuid'])
    assert response.status_code == 204
    
    response = client.get(version + "/users/"+ user['uuid'])
    assert response.status_code == 404

def test_delete_user_not_found(test_db):
    response = client.delete(version + "/users/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    assert response.status_code == 404

def test_get_user_me(test_db):
    response = client.get("auth/users/me")
    
    assert response.status_code == 401

# expenditures
def test_post_expenditure(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    ).json()

    response = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user['uuid']
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15T15:53:00+05:00",
            "place":"place"
        }
    )

    data = response.json()

    assert response.status_code == 201
    assert data["name"] == "name"
    assert data["cost"] == 1.2
    assert data["date"] == "2008-09-15T15:53:00"
    assert data["place"] == "place"
    assert "uuid" in data
    assert not "id" in data

def test_get_expenditure(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    ).json()
    expenditure = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user['uuid']
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15T15:53:00+05:00",
            "place":"place"
        }
    ).json()

    response = client.get(version + "/expenditures/"+ expenditure['uuid'])

    data = response.json()
    assert response.status_code == 200
    assert expenditure['uuid'] == data['uuid']
    assert expenditure['name'] == data['name']
    assert expenditure['cost'] == data['cost']
    assert expenditure['date'] == data['date']
    assert expenditure['place'] == data['place']
    assert not "id" in data

def test_get_expenditure_not_found(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    ).json()
    expenditure = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user['uuid']
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15T15:53:00+05:00",
            "place":"place"
        }
    ).json()

    response = client.get(version + "/expenditures/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    data = response.json()
    assert response.status_code == 404

def test_get_expenditures(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    ).json()
    expenditure1 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user['uuid']
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15T15:53:00+05:00",
            "place":"place"
        }
    )
    expenditure2 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user['uuid']
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15T15:53:00+05:00",
            "place":"place"
        }
    )

    response = client.get(version + "/expenditures/")

    assert response.status_code == 200
    assert response.json() == [
        expenditure1.json(),
        expenditure2.json()
    ]

def test_get_expenditures_filter_by_user(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    ).json()
    expenditure1 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user['uuid']
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15T15:53:00+05:00",
            "place":"place"
        }
    )
    expenditure2 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user['uuid']
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15T15:53:00+05:00",
            "place":"place"
        }
    )

    response = client.get(version + "/users/" + user['uuid'] + "/expenditures/")

    assert response.status_code == 200
    assert response.json() == [
        expenditure1.json(),
        expenditure2.json()
    ]


def test_get_expenditures_filter_by_user_not_found(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    ).json()
    expenditure1 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user['uuid']
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15T15:53:00+05:00",
            "place":"place"
        }
    )
    expenditure2 = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user['uuid']
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15T15:53:00+05:00",
            "place":"place"
        }
    )

    response = client.get(version + "/users/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb/expenditures/")

    assert response.status_code == 404

def test_put_expenditure(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    ).json()
    expenditureBeforeUpdate = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user['uuid']
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15T15:53:00+05:00",
            "place":"place"
        }
    ).json()
    response = client.put(
        version + "/expenditures/" + expenditureBeforeUpdate['uuid'],
        json={
            "name":"name1",
            "cost":1.21,
            "date":"2008-09-16T15:53:00+05:00",
            "place":"place1"
        }
    )
    assert response.status_code == 204

    response = client.get(version + "/expenditures/"+ expenditureBeforeUpdate['uuid'])

    expenditureAfterUpdate = response.json()
    assert expenditureBeforeUpdate['uuid'] == expenditureAfterUpdate['uuid']
    assert not expenditureBeforeUpdate['name'] == expenditureAfterUpdate['name']
    assert not expenditureBeforeUpdate['cost'] == expenditureAfterUpdate['cost']
    assert not expenditureBeforeUpdate['date'] == expenditureAfterUpdate['date']
    assert not expenditureBeforeUpdate['place'] == expenditureAfterUpdate['place']

def test_put_expenditure_not_found(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    ).json()
    expenditureBeforeUpdate = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user['uuid']
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15T15:53:00+05:00",
            "place":"place"
        }
    ).json()
    response = client.put(
        version + "/expenditures/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        json={
            "name":"name1",
            "cost":1.21,
            "date":"2008-09-16T15:53:00+05:00",
            "place":"place1"
        }
    )
    assert response.status_code == 404

def test_delete_expenditure(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    ).json()
    expenditure = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user['uuid']
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15T15:53:00+05:00",
            "place":"place"
        }
    ).json()

    response = client.delete(version + "/expenditures/"+ expenditure['uuid'])
    assert response.status_code == 204
    
    response = client.get(version + "/expenditures/"+ expenditure['uuid'])
    assert response.status_code == 404

def test_delete_expenditure_not_found(test_db):
    user = client.post(
        version + "/users/",
        json={
            "email":"email@w.x",
            "is_active":True,
            "is_admin":False,
            "password":"password"
        }
    ).json()
    expenditure = client.post(
        version + "/expenditures/",
        params={
            "user_uuid":user['uuid']
        },
        json={
            "name":"name",
            "cost":1.2,
            "date":"2008-09-15T15:53:00+05:00",
            "place":"place"
        }
    ).json()

    response = client.delete(version + "/expenditures/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    assert response.status_code == 404