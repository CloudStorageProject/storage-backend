# app/auth/services.py
from sqlalchemy.orm import Session
from app.auth.schemas import UserCreate
from app.auth.utils import hash_password
from app.models import User  # Імпорт класу User з models.py

def create_user(db: Session, user: UserCreate):
    db_user = User(username=user.username, hashed_password=hash_password(user.password))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()
