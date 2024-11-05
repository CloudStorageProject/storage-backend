from sqlalchemy.orm import Session
from app.auth.schemas import UserCreate
from app.auth.utils import hash_password
from app.models import User  

def create_user(db: Session, user: UserCreate):
    db_user_by_username = db.query(User).filter(User.username == user.username).first()
    db_user_by_email = db.query(User).filter(User.email == user.email).first()
    
    if db_user_by_username:
        raise ValueError(f"Username '{user.username}' is already taken.")
    if db_user_by_email:
        raise ValueError(f"Email '{user.email}' is already in use.")

    db_user = User(
        username=user.username,
        hashed_password=hash_password(user.password),
        email=user.email
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()
