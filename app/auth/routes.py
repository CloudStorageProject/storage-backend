# app/auth/routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.auth.schemas import UserCreate, UserOut, Token
from app.auth.services import create_user, get_user_by_username
from app.database import get_db
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.utils import verify_password

auth_router = APIRouter()

@auth_router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db=db, user=user)

@auth_router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = "dummy_access_token"  # Сюди додайте логіку для створення токена
    return {"access_token": access_token, "token_type": "bearer"}
