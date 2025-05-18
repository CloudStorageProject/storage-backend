from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.schemas import (
    CurrentUser, ChallengeAnswer, UserLogin, 
    UserCreate, UserInfo, LoginResponse, 
    ChallengeString, UsernameCheck, EmailCheck, CheckResult
)
from app.auth.services import (
    get_basic_auth, accept_challenge, generate_challenge, 
    try_login, create_user, check_email, check_username
)
from app.database import get_db
from app.auth.errors import (
    InvalidCredentials, CredentialsAlreadyTaken, NonExistentPublicKey, 
    NonExistentChallenge, InvalidSignature
)


auth_router = APIRouter()


@auth_router.post("/checkUsername")
def check_existing_username(data: UsernameCheck, db: Session = Depends(get_db)) -> CheckResult:
    return check_username(data, db)


@auth_router.post("/checkEmail")
def check_existing_email(data: EmailCheck, db: Session = Depends(get_db)) -> CheckResult:
    return check_email(data, db)


@auth_router.get("/me")
def get_me(current_user: CurrentUser = Depends(get_basic_auth)) -> CurrentUser:
    return current_user
    

@auth_router.post("/login/challenge/{public_key}")
def challenge_login(public_key: str, challenge: ChallengeAnswer, db: Session = Depends(get_db)) -> LoginResponse:
    try:
        result = accept_challenge(public_key, challenge, db)
        return result
    except (NonExistentChallenge, NonExistentPublicKey) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvalidSignature as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    

@auth_router.get("/login/challenge/{public_key}")
def get_challenge(public_key: str, db: Session = Depends(get_db)) -> ChallengeString:
    try:
        return generate_challenge(public_key, db)
    except NonExistentPublicKey as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@auth_router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)) -> UserInfo:
    try:
        return create_user(db=db, user=user)
    except CredentialsAlreadyTaken as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@auth_router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)) -> LoginResponse:
    try:
        return try_login(db=db, provided=user)
    except InvalidCredentials as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))