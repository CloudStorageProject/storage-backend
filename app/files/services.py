from app.files.schemas import FileData
from sqlalchemy import select, func, Integer
from sqlalchemy.orm import Session
from app.folders.utils import get_folder
from app.files.utils import (
    save_to_storage, remove_from_storage, check_duplicate_file, 
    retrieve_from_storage, retrieve_file_from_id, get_file_size_gb,
    increment_user_space, decrement_user_space, get_shared_state,
    get_shared_users_for_file
)
from app.models import (
    File, User, SharedFile
)
from app.auth.schemas import CurrentUser
from app.files.schemas import (
    FileMetadata, SharingDetails, SharingDetailOut,
    SharingDetailOut, FileMetadataShortened
)
from app.folders.schemas import FolderMember
from loguru import logger
from app.main import settings
from app.files.errors import (
    SpaceLimitExceeded, DestinationUserDoesNotExist, FileAlreadyShared,
    CannotShareWithYourself, FileIsNotShared, FileDoesNotExist
)
from typing import Union


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
    
    try:
        file_metadata = retrieve_file_from_id(current_user.id, file_id, db)

    except FileDoesNotExist as original_error:
        shared_file = get_shared_state(file_id, current_user.id, db)

        if not shared_file:
            raise FileDoesNotExist(str(original_error))
        
        return retrieve_from_storage(shared_file.file.name_in_storage)

    return retrieve_from_storage(file_metadata.name_in_storage)


def try_rename_file(current_user: CurrentUser, file_id: int, new_name: str, db: Session) -> None:
    file = retrieve_file_from_id(current_user.id, file_id, db)
    check_duplicate_file(file.folder_id, new_name, db)

    file.name = new_name
    db.commit()


def try_delete_file(current_user: CurrentUser, file_id: int, db: Session) -> None:
    try:
        file = retrieve_file_from_id(current_user.id, file_id, db)

        db.query(SharedFile).filter(SharedFile.file_id == file_id).delete()

        remove_from_storage(file.name_in_storage)

        decrement_user_space(current_user.id, file.size, db)

        db.delete(file)
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise e


def get_metadata(
    current_user: CurrentUser, 
    file_id: int, 
    db: Session) -> Union[FileMetadata, FileMetadataShortened]:
    try:
        file_metadata = retrieve_file_from_id(current_user.id, file_id, db)
    except FileDoesNotExist as e:
        shared_file = get_shared_state(file_id, current_user.id, db)

        if not shared_file:
            raise FileDoesNotExist(str(e))
        
        file_metadata = FileMetadataShortened(
            file_id=shared_file.file_id,
            owner_id=shared_file.initiator_user_id,
            name=shared_file.file.name,
            type=shared_file.file.type,
            format=shared_file.file.format,
            encrypted_key=shared_file.enc_key,
            encrypted_iv=shared_file.enc_iv,
            size=shared_file.file.size
        )

    return file_metadata



def try_share_file(details: SharingDetails, current_user: CurrentUser, dest_user_id: int, file_id: int, db: Session) -> None:
    if current_user.id == dest_user_id:
        raise CannotShareWithYourself("You can't share files with yourself.")

    # checking ownership
    retrieve_file_from_id(current_user.id, file_id, db)

    destination_user = db.query(User).filter(User.id == dest_user_id).first()
    if not destination_user:
        raise DestinationUserDoesNotExist("This user does not exist.")
    
    if get_shared_state(file_id, dest_user_id, db):
        raise FileAlreadyShared("This file is already shared.")
    
    shared_file = SharedFile(
        file_id=file_id,
        destination_user_id=dest_user_id,
        initiator_user_id=current_user.id,
        enc_iv=details.enc_iv,
        enc_key=details.enc_key,
    )

    db.add(shared_file)
    db.commit()


def try_revoke_access(current_user: CurrentUser, user_id: int, file_id: int, db: Session) -> None:
    # checking ownership
    retrieve_file_from_id(current_user.id, file_id, db)

    destination_user = db.query(User).filter(User.id == user_id).first()
    if not destination_user:
        raise DestinationUserDoesNotExist("This user does not exist.")
    
    shared_file = db.query(SharedFile).filter(
        SharedFile.file_id == file_id, SharedFile.destination_user_id == user_id
    ).first()
    
    if not shared_file:
        raise FileIsNotShared("This file is not shared with the specified user.")
    
    db.delete(shared_file)
    db.commit()


def get_shared_data(db: Session, current_user: CurrentUser) -> list[SharingDetailOut]:
    stmt = (
        select(
            File.id,
            File.name,
            File.type,
            File.format,
            func.jsonb_object_agg(
                func.cast(SharedFile.destination_user_id, Integer),  # Преобразование ключа в int
                func.jsonb_build_object(
                    'enc_iv', SharedFile.enc_iv,
                    'enc_key', SharedFile.enc_key
                )
            ).label("details")
        )
        .select_from(SharedFile)
        .join(File, File.id == SharedFile.file_id)
        .where(SharedFile.initiator_user_id == current_user.id)
        .group_by(File.id)
    )

    result = db.execute(stmt).all()

    return [SharingDetailOut.model_validate(row) for row in result]


def get_shared_data(db: Session, current_user: CurrentUser) -> list[SharingDetailOut]:
    stmt = (
        select(
            File.id,
            File.name,
            File.type,
            File.format,
            func.jsonb_agg(
                func.jsonb_build_object(
                    'id', SharedFile.destination_user_id,
                    'username', User.username
                )
            ).label("details")
        )
        .select_from(SharedFile)
        .join(File, File.id == SharedFile.file_id)
        .join(User, User.id == SharedFile.destination_user_id)
        .where(SharedFile.initiator_user_id == current_user.id)
        .group_by(File.id)
    )

    return db.execute(stmt).all()


