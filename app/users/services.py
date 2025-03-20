from sqlalchemy.orm import Session
from app.models import User
from app.users.errors import PageNotFound, UserNotFound
from app.users.schemas import UserPageOut, UserOut, UserDetailOut
from app.users.utils import get_total_user_count, get_requested_page
import math

def get_page(db: Session, page: int, page_size: int) -> UserPageOut:
    user_count = get_total_user_count(db)
    total_pages = math.ceil(user_count / page_size)

    if page > total_pages:
        raise PageNotFound("No users on this page.")
    
    return UserPageOut(
        current_page=page,
        pages_left=total_pages - page,
        users=get_requested_page(db, page, page_size)
    )

def get_basic_user_info(db: Session, username: str) -> UserOut:
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise UserNotFound("This user does not exist.")
    
    return UserOut(
        id=user.id,
        username=user.username
    )

def get_pub_key(db: Session, id: int) -> UserDetailOut:
    user = db.query(User).filter(User.id == id).first()

    if user is None:
        raise UserNotFound("This user does not exist.")
    
    return UserDetailOut(
        id=user.id,
        username=user.username,
        pub_key=user.public_key
    )


    

