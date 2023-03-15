from fastapi import FastAPI, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

import time

from .database import SessionLocal, engine
from .schemas import expenditure_schemas, user_schemas, user_token_schemas
from .models import expenditure_model, limits_model, user_model
from .routers import auth
from .routers.v0 import expenditure_day_stats, users, expenditures, limits
from .dependencies import get_db
from .services import auth_service
from .config import cors

user_model.Base.metadata.create_all(bind=engine)

app = FastAPI()

# middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors.origins,
    allow_credentials=True,
    allow_methods=cors.allow_methods,
    allow_headers=cors.allow_headers,
)

# app
@app.get("/", tags=["app"])
def read_root(request: Request):

    return {
        "version": "v0.2",
        "documentation": request.client.host + "/docs"
    }

app.include_router(
    auth.router,
)
app.include_router(
    expenditures.router,
    prefix="/v0",
)
app.include_router(
    expenditure_day_stats.router,
    prefix="/v0",
)
app.include_router(
    users.router,
    prefix="/v0",
)
app.include_router(
    limits.router,
    prefix="/v0",
)