from sqlalchemy.orm import Session
from app.models import User


def get_total_user_count(db: Session) -> int:
    return db.query(User).count()


def get_requested_page(db: Session, page: int, page_size: int) -> list[User]:
    offset = (page - 1) * page_size
    users = db.query(User).offset(offset).limit(page_size).all()
    return users
