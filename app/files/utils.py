from minio import Minio, S3Error, InvalidResponseError
from minio.deleteobjects import DeleteObject
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import File, User, SharedFile
from app.files.errors import (
    FileAlreadyExistsInThisFolder, FileUploadError, FileRetrieveError, 
    FileDoesNotExist, FileDeletionError
)
from app.files.schemas import FileMetadata
from app.main import settings
from loguru import logger
from typing import Optional
from fastapi import UploadFile
import io

# assuming the bucket is already created
bucket_name = settings.BUCKET_NAME
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_LOGIN,
    secret_key=settings.MINIO_PASSWORD,
    secure=settings.MINIO_SECURE
)


def increment_user_space(user_id: int, space_in_gb: float, db: Session) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.space_taken += space_in_gb


def decrement_user_space(user_id: int, space_in_gb: float, db: Session) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.space_taken -= space_in_gb


def get_file_size_gb(file: UploadFile) -> float:
    current_pos = file.file.tell()
    file.file.seek(0, 2)
    size_bytes = file.file.tell()
    file.file.seek(current_pos)

    return size_bytes / (1024 ** 3)


def generate_filename(username: str, prefix: str) -> str:
    return f"{username}-{prefix}-{str(round(datetime.utcnow().timestamp()))}.senc"


def save_to_storage(username: str, file: UploadFile, prefix: str) -> str:
    filename = generate_filename(username, prefix)

    try:
        minio_client.put_object(
            bucket_name,
            filename,
            data = file.file,
            length = -1,
            part_size = 10 * 1024 * 1024,
            content_type = "text/plain",
        )

        return filename
    except S3Error as e:
        raise FileUploadError("An unexpected error occurred while uploading the file: " + str(e))


def remove_from_storage(file_name: str) -> None:
    try:
        minio_client.remove_object(bucket_name, file_name)
    except S3Error as e:
        raise FileDeletionError("An unexpected error occurred while deleting the file: " + str(e))


def bulk_remove_from_storage(file_names: list[str]) -> None:
    try:
        logger.debug('Trying to delete multiple objects...')
        
        objects_to_delete = [DeleteObject(file_name) for file_name in file_names]
        deleted_objects = minio_client.remove_objects(bucket_name, objects_to_delete)
        
        for result in deleted_objects:
            if result.error:
                logger.debug(f"Failed to delete {result.object_name}: {result.error}")
            else:
                logger.debug(f"Successfully deleted {result.object_name}")
                
    except S3Error as e:
        logger.debug(f'Could not delete multiple objects: {str(e)}')
        raise FileDeletionError(f"An unexpected error occurred while deleting files: {str(e)}")


# ownership of the folder is already checked in get_folder
def check_duplicate_file(folder_id: int, file_name: str, db: Session) -> None:
    file = db.query(File).filter(File.folder_id == folder_id, File.name == file_name).first()
    if file:
        raise FileAlreadyExistsInThisFolder("A file with this name already exists in this folder.")


async def retrieve_stream_from_storage(filename: str):
    try:
        response = minio_client.get_object(bucket_name, filename)

        def iterate_file():
            for chunk in response.stream(1024 * 1024):
                yield chunk
        
        return iterate_file
    
    except (S3Error, InvalidResponseError) as e:
        raise FileRetrieveError("Error retrieving file: " + str(e))
    
    
# FileMetadata, since .folder is also loaded
def retrieve_file_from_id(user_id: int, file_id: int, db: Session) -> FileMetadata:
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise FileDoesNotExist("This file does not exist.")
    
    folder = file.folder
    
    if folder.user_id != user_id:
        raise FileDoesNotExist("This file does not exist.")
    
    file.shared = get_shared_users_for_file(db, file_id)
    
    return file


def get_shared_state(file_id: int, user_id: int, db: Session) -> Optional[SharedFile]:
    return db.query(SharedFile).filter(SharedFile.file_id == file_id, SharedFile.destination_user_id == user_id).first()


def get_shared_users_for_file(db: Session, file_id: int) -> list[int]:
    shared_file_entries = db.query(SharedFile).filter(SharedFile.file_id == file_id).all()
    return [shared_file.destination_user_id for shared_file in shared_file_entries]



