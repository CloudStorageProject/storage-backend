from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.schemas import *
from app.auth.services import *
from app.database import get_db
from app.auth.errors import *


auth_router = APIRouter()


@auth_router.get("/me")
def get_me(current_user: dict = Depends(get_basic_auth), db: Session = Depends(get_db)) -> UserInfo:
    return strip_unnecessary(current_user)
    

@auth_router.post("/login/challenge/{public_key}")
def challenge_login(public_key: str, challenge: ChallengeAnswer, db: Session = Depends(get_db)) -> Token:
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
        challenge_str = generate_challenge(public_key, db)
        return {"challenge": challenge_str}
    except NonExistentPublicKey as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@auth_router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    try:
        return create_user(db=db, user=user)
    except CredentialsAlreadyTaken as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@auth_router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)) -> Token:
    try:
        return try_login(db=db, provided=user)
    except InvalidCredentials as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))