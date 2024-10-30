from fastapi import FastAPI
from app.database import engine, Base
from app.auth.routes import auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
