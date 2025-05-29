from sqlalchemy.orm import Session
from app.models import User
from app.users.errors import UserNotFound
from app.users.schemas import UserDetailOut, UserPageOut
from app.users.utils import get_matching_users
from app.users.errors import InvalidPageSize


def get_page(db: Session, username: str, size: int) -> UserPageOut:
    if size < 1 or size > 200:
        raise InvalidPageSize("Page size must be between 1 and 200.")
    
    return get_matching_users(db, username, size)


def get_pub_key(db: Session, id: int) -> UserDetailOut:
    user = db.query(User).filter(User.id == id).first()

    if user is None:
        raise UserNotFound("This user does not exist.")
    
    return UserDetailOut(
        id=user.id,
        username=user.username,
        pub_key=user.public_key
    )


    

