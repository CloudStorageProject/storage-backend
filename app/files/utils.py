from minio import Minio, S3Error, InvalidResponseError
from minio.deleteobjects import DeleteObject
from datetime import datetime
from app.files.schemas import FileData
from sqlalchemy.orm import Session
from app.models import File, User
from app.files.errors import (
    FileAlreadyExistsInThisFolder, FileUploadError, FileRetrieveError, 
    FileDoesNotExist, FileDeletionError
)
from app.files.schemas import FileMetadata
from app.main import settings
from loguru import logger
import io

# assuming the bucket is already created
bucket_name = settings.BUCKET_NAME
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_LOGIN,
    secret_key=settings.MINIO_PASSWORD,
    secure=settings.MINIO_SECURE
)


def increment_user_space(user_id: int, space_in_mb: float, db: Session) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.space_taken += space_in_mb


def decrement_user_space(user_id: int, space_in_mb: float, db: Session) -> None:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.space_taken -= space_in_mb


def get_file_size_gb(file: FileData) -> float:
    return len(file.content) / (1024 ** 3)


def generate_filename(username: str, prefix: str) -> str:
    return f"{username}-{prefix}-{str(round(datetime.utcnow().timestamp()))}.senc"


def save_to_storage(username: str, file: FileData, prefix: str) -> str:
    filename = generate_filename(username, prefix)
    file.content = file.content.encode('utf-8')

    try:
        minio_client.put_object(
            bucket_name,
            filename,
            data = io.BytesIO(file.content),
            length = len(file.content),
            content_type = "text/plain"
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


def retrieve_from_storage(filename: str) -> bytes:
    try:
        handle = minio_client.get_object(bucket_name, filename)
        content = handle.read()
        handle.close()

        return content
    except (S3Error, InvalidResponseError) as e:
        raise FileRetrieveError("An unexpected error occurred while trying to retrieve the file: " + str(e))
    
# FileMetadata, since .folder is also loaded
def retrieve_file_from_id(user_id: int, file_id: int, db: Session) -> FileMetadata:
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise FileDoesNotExist("This file does not exist.")
    
    folder = file.folder
    
    if folder.user_id != user_id:
        raise FileDoesNotExist("This file does not exist.")
    
    return file



