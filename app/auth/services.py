from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.auth.schemas import UserCreate, UserLogin, ChallengeAnswer
from app.auth.utils import hash_password, verify_signature, generate_challenge_string
from app.models import User, Challenge
from app.auth.utils import verify_password, create_access_token
from app.auth.errors import *


def accept_challenge(public_key: str, challenge: ChallengeAnswer, db: Session):
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

    return {"token": access_token}

def generate_challenge(public_key: str, db: Session):
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

    return challenge_str


def try_login(db: Session, provided: UserLogin):
    user = get_user_by_username(db, provided.username)

    if not user or (user and not verify_password(provided.password, user.hashed_password)):
        raise InvalidCredentials("Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username, "access_type": "limited"})

    return {"token": access_token}


def create_user(db: Session, user: UserCreate):
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
    db.commit()
    db.refresh(db_user)

    return db_user


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()
