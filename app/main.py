from app.environment import Settings
settings = Settings()

from fastapi import FastAPI, Request, status
from app.database import engine, Base, get_db
from app.auth.routes import auth_router
from app.folders.routes import folder_router
from app.files.routes import file_router
from app.users.routes import user_router
from app.settings.routes import settings_router
from app.payments.routes import payment_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from contextlib import asynccontextmanager
from app.payments.utils import init_subscription_types, initiate_subscription_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    
    db_gen = get_db()
    db = next(db_gen)
    try:
        init_subscription_types(db)
        initiate_subscription_task()
    finally:
        db_gen.close()

    yield


app = FastAPI(lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.debug(str(exc))
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Unexpected error."})


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router, prefix="/auth")
app.include_router(folder_router, prefix="/folders")
app.include_router(file_router, prefix="/files")
app.include_router(user_router, prefix="/users")
app.include_router(settings_router, prefix="/settings")
app.include_router(payment_router, prefix="/payments")
