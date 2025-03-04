from app.settings import Settings
settings = Settings()

from fastapi import FastAPI, Request, status
from app.database import engine, Base
from app.auth.routes import auth_router
from app.folders.routes import folder_router
from app.files.routes import file_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.debug(str(exc))
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "Unexpected error."})


app.add_middleware(
    CORSMiddleware,
    allow_origins=(["*"] if settings.DEBUG_MODE else [settings.TRUSTED_ORIGIN]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(folder_router, prefix="/folders")
app.include_router(file_router, prefix="/files")
