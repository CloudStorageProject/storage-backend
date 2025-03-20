from app.files.schemas import FileData
from sqlalchemy.orm import Session
from app.folders.utils import get_folder
from app.files.utils import (
    save_to_storage, remove_from_storage, check_duplicate_file, 
    retrieve_from_storage, retrieve_file_from_id, get_file_size_gb,
    increment_user_space, decrement_user_space
)
from app.models import File
from app.auth.schemas import CurrentUser
from app.files.schemas import FileMetadata
from loguru import logger
from app.main import settings
from app.files.errors import SpaceLimitExceeded


def try_upload_file(current_user: CurrentUser, file: FileData, db: Session) -> int:
    file_size = get_file_size_gb(file)

    if current_user.space_taken + file_size > settings.USER_SPACE_CAPACITY:
        raise SpaceLimitExceeded("Space limit exceeded.")

    # checking if the user owns this folder
    get_folder(current_user.id, file.folder_id, db)
    # checking for duplicates in naming
    check_duplicate_file(file.folder_id, file.name, db)
    # trying to save in bucket
    filename = save_to_storage(current_user.username, file, file.name)
    # (all exceptions are thrown internally)
    file_wrapper = File(
        **file.model_dump(exclude="content"),
        name_in_storage = filename,
        size = file_size
    )

    db.add(file_wrapper)

    increment_user_space(current_user.id, file_size, db)

    db.commit()
    db.refresh(file_wrapper)

    return file_wrapper.id


def get_file(current_user: CurrentUser, file_id: int, db: Session) -> bytes:
    logger.debug(f"current_user = {current_user}, file_id = {file_id}")
    file_wrapper = retrieve_file_from_id(current_user.id, file_id, db)
    return retrieve_from_storage(file_wrapper.name_in_storage)


def try_rename_file(current_user: CurrentUser, file_id: int, new_name: str, db: Session) -> None:
    file = retrieve_file_from_id(current_user.id, file_id, db)
    check_duplicate_file(file.folder_id, new_name, db)

    file.name = new_name
    db.commit()


def try_delete_file(current_user: CurrentUser, file_id: int, db: Session) -> None:
    try:
        file = retrieve_file_from_id(current_user.id, file_id, db)

        remove_from_storage(file.name_in_storage)

        decrement_user_space(current_user.id, file.size, db)

        db.delete(file)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise e


def get_metadata(current_user: CurrentUser, file_id: int, db: Session) -> FileMetadata:
    return retrieve_file_from_id(current_user.id, file_id, db)

