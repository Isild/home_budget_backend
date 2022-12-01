from fastapi import FastAPI, Request, Depends
import time

from .database import SessionLocal, engine
from .schemas import userSchemas, expenditureSchemas, userTokenSchemas
from .models import userModel, expenditureModel
from .routers import auth
from .routers.v0 import users, expenditures
from .dependencies import get_db
from .services import authService

userModel.Base.metadata.create_all(bind=engine)

app = FastAPI()

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
        "version": "v0.2",
        "documentation": request.client.host + "/docs"
    }


app.include_router(
    auth.router,
)
app.include_router(
    expenditures.router,
    prefix="/v0",
    # dependencies=[Depends(authService.get_current_active_user)]
)
app.include_router(
    users.router,
    prefix="/v0",
    # dependencies=[Depends(authService.get_current_active_user)]
)