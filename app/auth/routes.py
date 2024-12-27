from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.schemas import *
from app.auth.services import create_user, try_login, generate_challenge, accept_challenge
from app.database import get_db
from app.auth.errors import *

auth_router = APIRouter()


@auth_router.post("/login/challenge/{public_key}")
async def challenge_login(public_key: str, challenge: ChallengeAnswer, db: Session = Depends(get_db)):
    try:
        result = accept_challenge(public_key, challenge, db)
        return result
    except (NonExistentChallenge, NonExistentPublicKey) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InvalidSignature as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unexpected error")
    

@auth_router.get("/login/challenge/{public_key}")
def get_challenge(public_key: str, db: Session = Depends(get_db)):
    try:
        challenge_str = generate_challenge(public_key, db)
        return {"challenge": challenge_str}
    except NonExistentPublicKey as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unexpected error")


@auth_router.post("/register", response_model=UserOut)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        return create_user(db=db, user=user)
    except CredentialsAlreadyTaken as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unexpected error")


@auth_router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    try:
        return try_login(db=db, provided=user)
    except InvalidCredentials as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Unexpected error")