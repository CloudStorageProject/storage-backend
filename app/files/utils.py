from minio import Minio, S3Error, InvalidResponseError
from datetime import datetime
from app.files.errors import FileUploadError, BucketCreationError
from app.files.schemas import FileData
from sqlalchemy.orm import Session
from app.models import File
from app.files.errors import *
import os
import io
import base64


minio_client = Minio(
    os.getenv("MINIO_ENDPOINT"),
    access_key = os.getenv("MINIO_LOGIN"),
    secret_key = os.getenv("MINIO_PASSWORD"),
    secure = False
)
bucket = os.getenv("MINIO_BUCKET_NAME")


def create_bucket(username: str):
    try:
        minio_client.make_bucket(username)
    except Exception as e:
        raise BucketCreationError("An unexpected error occurred while creating the bucket: " + str(e))


def generate_filename(prefix: str):
    return prefix + str(datetime.utcnow().timestamp())


def save_to_storage(username: str, file: FileData, prefix: str):
    filename = generate_filename(prefix)
    # encoded = file.content.encode('utf-8')
    file_content = base64.b64decode(file.content)

    try:
        minio_client.put_object(
            username,
            filename,
            data = io.BytesIO(file_content),
            length = len(file_content),
            content_type = "application/octet-stream"
        )
        return filename
    except S3Error as e:
        raise FileUploadError("An unexpected error occurred while uploading the file: " + str(e))


def remove_from_storage(username: str, file_name: str):
    try:
        minio_client.remove_object(username, file_name)
    except S3Error as e:
        raise FileDeletionError("An unexpected error occurred while deleting the file: " + str(e))


# ownership of the folder is already checked in get_folder
def check_duplicate_file(folder_id: int, file_name: str, db: Session):
    file = db.query(File).filter(File.folder_id == folder_id, File.name == file_name).first()
    if file:
        raise FileAlreadyExistsInThisFolder("A file with this name already exists in this folder.")


def retrieve_from_storage(username: str, filename: str):
    try:
        handle = minio_client.get_object(username, filename)
        content = handle.read()
        handle.close()

        return content
    except (S3Error, InvalidResponseError) as e:
        raise FileRetrieveError("An unexpected error occurred while trying to retrieve the file: " + str(e))
    

def retrieve_file_from_id(user_id: int, file_id: int, db: Session):
    file = db.query(File).filter(File.id == file_id).first()

    if not file:
        raise FileDoesNotExist("This file does not exist.")
    
    folder = file.folder
    
    if folder.user_id != user_id:
        raise FileDoesNotExist("This file does not exist.")
    
    return file



