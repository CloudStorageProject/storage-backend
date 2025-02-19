from minio import Minio, S3Error, InvalidResponseError
from datetime import datetime
from app.files.errors import FileUploadError
from app.files.schemas import FileData
from sqlalchemy.orm import Session
from app.models import File
from app.files.errors import *
import os
import io
import base64

# assuming the bucket is already created
bucket_name = os.getenv("BUCKET_NAME")
minio_client = Minio(
    os.getenv("MINIO_ENDPOINT"),
    access_key = os.getenv("MINIO_LOGIN"),
    secret_key = os.getenv("MINIO_PASSWORD"),
    secure = (True if os.getenv("MINIO_SECURE") == "true" else False)
)

def generate_filename(username: str, prefix: str):
    return username + prefix + str(datetime.utcnow().timestamp())


def save_to_storage(username: str, file: FileData, prefix: str):
    filename = generate_filename(username, prefix)
    file_content = base64.b64decode(file.content)

    try:
        minio_client.put_object(
            bucket_name,
            filename,
            data = io.BytesIO(file_content),
            length = len(file_content),
            content_type = "application/octet-stream"
        )
        return filename
    except S3Error as e:
        raise FileUploadError("An unexpected error occurred while uploading the file: " + str(e))


def remove_from_storage(file_name: str):
    try:
        minio_client.remove_object(bucket_name, file_name)
    except S3Error as e:
        raise FileDeletionError("An unexpected error occurred while deleting the file: " + str(e))


# ownership of the folder is already checked in get_folder
def check_duplicate_file(folder_id: int, file_name: str, db: Session):
    file = db.query(File).filter(File.folder_id == folder_id, File.name == file_name).first()
    if file:
        raise FileAlreadyExistsInThisFolder("A file with this name already exists in this folder.")


def retrieve_from_storage(filename: str):
    try:
        handle = minio_client.get_object(bucket_name, filename)
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



