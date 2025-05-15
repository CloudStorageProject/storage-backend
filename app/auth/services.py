from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.auth.schemas import (
    UserCreate, UserLogin, ChallengeAnswer, 
    CurrentUser, LoginResponse, ChallengeString, 
    UserInfo
)
from app.auth.utils import hash_password, verify_signature, generate_challenge_string
from app.models import User, Challenge, Folder
from app.auth.utils import (
    verify_password, create_access_token, decode_access_token, 
    get_user_by_username
)
from app.auth.errors import (
    InvalidCredentials, CredentialsAlreadyTaken, NonExistentPublicKey, 
    NonExistentChallenge, InvalidSignature, InvalidToken, 
    ExpiredToken, NonExistentUser
)
from app.database import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.main import settings
from loguru import logger


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_user_with_permissions(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db), full_access: bool = False) -> CurrentUser:
    try:
        user = get_user_by_token(token, db)
        logger.debug(user)
    except (ExpiredToken, InvalidToken) as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except NonExistentUser as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    if full_access and user.privileged == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Full access is required.")
    
    return user


def get_basic_auth(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> CurrentUser:
    return get_user_with_permissions(token=token, db=db, full_access=False)


def get_full_auth(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> CurrentUser:
    if settings.DEBUG_MODE:
        return get_basic_auth(token=token, db=db)
    else:
        return get_user_with_permissions(token=token, db=db, full_access=True)


def get_user_by_token(token: str, db: Session) -> CurrentUser:
    payload = decode_access_token(token)
    username = payload.get("sub")

    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise NonExistentUser("This user does not exist.")
    
    subscription_start_date = None
    subscription_end_date = None

    if user.subscription:
        subscription_start_date = user.subscription.subscription_start_date
        subscription_end_date = user.subscription.subscription_end_date

    return CurrentUser(
        username=user.username,
        email=user.email,
        public_key=user.public_key,
        id=user.id,
        privileged=(payload.get("access_type") == "full"),
        space_taken=user.space_taken,
        subscription_name=user.subscription_type.name,
        subscription_space=user.subscription_type.space,
        subscription_start_date=subscription_start_date,
        subscription_end_date=subscription_end_date,
        customer_id=user.stripe_customer_id
    )
    

def accept_challenge(public_key: str, challenge: ChallengeAnswer, db: Session) -> LoginResponse:
    user = db.query(User).filter(User.public_key == public_key).first()
    
    if not user:
        raise NonExistentPublicKey("No user found with this public key.")
    
    challenge_entry = db.query(Challenge).filter(
        Challenge.user_id == user.id,
        Challenge.random_chars == challenge.random_part,
        Challenge.is_used == False
    ).first()

    if not challenge_entry:
        raise NonExistentChallenge("This challenge does not exist or has already been used.")
    
    if not verify_signature(challenge.challenge, challenge.sign, public_key):
        raise InvalidSignature("Invalid signature.")
    
    access_token = create_access_token(data={"sub": challenge_entry.user.username, "access_type": "full"})

    challenge_entry.is_used = True
    db.commit()

    return LoginResponse(token=access_token, user=user)


def generate_challenge(public_key: str, db: Session) -> ChallengeString:
    user = db.query(User).filter(User.public_key == public_key).first()
    if not user:
        raise NonExistentPublicKey("There is no user with this public key.")
    
    challenge_str = generate_challenge_string()
    
    challenge = Challenge(
        user_id=user.id,
        random_chars=challenge_str.split(":")[1],
        is_used=False
    )

    db.add(challenge)
    db.commit()

    return ChallengeString(challenge=challenge_str)


def try_login(db: Session, provided: UserLogin) -> LoginResponse:
    user = get_user_by_username(db, provided.username)

    if not user or (user and not verify_password(provided.password, user.hashed_password)):
        raise InvalidCredentials("Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username, "access_type": "limited"})

    return LoginResponse(token=access_token, user=user)


def create_user(db: Session, user: UserCreate) -> UserInfo:
    try:
        db.begin()

        existing_user = db.query(User).filter(
            or_(
                User.username == user.username,
                User.email == user.email,
                User.public_key == user.public_key
            )
        ).first()

        if existing_user:
            if existing_user.username == user.username:
                raise CredentialsAlreadyTaken(f"Username '{user.username}' is already in use.")
            if existing_user.email == user.email:
                raise CredentialsAlreadyTaken(f"Email '{user.email}' is already in use.")
            if existing_user.public_key == user.public_key:
                raise CredentialsAlreadyTaken(f"Public key '{user.public_key}' is already in use.")

        db_user = User(
            username=user.username,
            hashed_password=hash_password(user.password),
            email=user.email,
            public_key=user.public_key
        )

        db.add(db_user)
        db.flush()

        root_folder = Folder(
            name="root",
            user_id=db_user.id,
            parent_id=None
        )

        db.add(root_folder)
        db.commit()

        return UserInfo(
            username=db_user.username,
            email=db_user.email,
            public_key=db_user.public_key
        )
    
    except Exception as e:
        db.rollback()
        raise e