from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.schemas import UserCreate, UserOut, UserLogin, Token
from app.auth.services import create_user, try_login
from app.database import get_db
from app.auth.errors import CredentialsAlreadyTaken, InvalidCredentials

auth_router = APIRouter()

@auth_router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return create_user(db=db, user=user)
    except CredentialsAlreadyTaken as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@auth_router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    try:
        return try_login(db=db, provided=user)
    except InvalidCredentials as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )