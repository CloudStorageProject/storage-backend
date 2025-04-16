from sqlalchemy.orm import Session
from app.models import User
from app.auth.utils import hash_password
from app.settings.schemas import UsernamePatch, PasswordPatch
from app.settings.errors import UsernameAlreadyExists


def try_patch_username(patch: UsernamePatch, current_user: User, db: Session) -> None:
    existing_user = db.query(User).filter(User.username == patch.username).first()

    if existing_user:
        raise UsernameAlreadyExists(f"Username '{patch.username}' already exists.")
    
    user = db.query(User).filter(User.id == current_user.id).first()
    user.username = patch.username

    db.commit()
    db.refresh(user)


def try_patch_password(patch: PasswordPatch, current_user: User, db: Session) -> None:
    user = db.query(User).filter(User.id == current_user.id).first()
    user.hashed_password = hash_password(patch.password)

    db.commit()
    db.refresh(user)