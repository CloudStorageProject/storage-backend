from sqlalchemy.orm import Session
from app.models import User
from app.users.schemas import UserPageOut


def get_matching_users(db: Session, username: str, size: int) -> UserPageOut:
    users = db.query(User).filter(User.username.ilike(f"{username}%")).limit(size).all()
    
    return UserPageOut(
        page_size=len(users),
        users=users
    )