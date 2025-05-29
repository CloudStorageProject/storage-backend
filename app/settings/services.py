from sqlalchemy.orm import Session
from app.models import User
from app.auth.utils import hash_password, verify_password
from app.auth.schemas import CurrentUser
from app.settings.schemas import UsernamePatch, PasswordPatch
from app.settings.errors import UsernameAlreadyExists, InvalidOldPassword


def try_patch_username(patch: UsernamePatch, current_user: CurrentUser, db: Session) -> None:
    existing_user = db.query(User).filter(User.username == patch.username).first()
    if existing_user:
        raise UsernameAlreadyExists(f"Username '{patch.username}' already exists.")
    
    user = db.query(User).filter(User.id == current_user.id).first()

    if not verify_password(patch.old_password, user.hashed_password):
        raise InvalidOldPassword("Invalid old password.")
    
    user.username = patch.username
    db.commit()


def try_patch_password(patch: PasswordPatch, current_user: CurrentUser, db: Session) -> None:
    user = db.query(User).filter(User.id == current_user.id).first()

    if not verify_password(patch.old_password, user.hashed_password):
        raise InvalidOldPassword("Invalid old password.")
    
    user.hashed_password = hash_password(patch.password)
    db.commit()