from sqlalchemy.orm import Session
from app.auth.schemas import UserCreate, UserLogin
from app.auth.utils import hash_password
from app.models import User
from app.auth.utils import verify_password, create_access_token
from app.auth.errors import CredentialsAlreadyTaken, InvalidCredentials

def try_login(db: Session, provided: UserLogin):
    user = get_user_by_username(db, provided.username)

    if not user or (user and not verify_password(provided.password, user.hashed_password)):
        raise InvalidCredentials("Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username, "privileged": False})

    return {"token": access_token}


def create_user(db: Session, user: UserCreate):
    db_user_by_username = get_user_by_username(db, user.username)
    db_user_by_email = db.query(User).filter(User.email == user.email).first()
    
    if db_user_by_username:
        raise CredentialsAlreadyTaken(f"Username '{user.username}' is already taken.")
    if db_user_by_email:
        raise CredentialsAlreadyTaken(f"Email '{user.email}' is already in use.")

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
