from fastapi.security import OAuth2PasswordBearer
import os
from functools import lru_cache

from .database import SessionLocal
from .config import config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# helpers
class UserAuthMock:
    is_admin = True
    id = 1


# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@lru_cache()
def get_settings():
    return config.Settings()