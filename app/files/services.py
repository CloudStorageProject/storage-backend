from app.files.schemas import FileData
from sqlalchemy.orm import Session
from app.folders.utils import get_folder
from app.files.utils import *
from app.models import File


def try_upload_file(current_user: dict, file: FileData, db: Session):
    # checking if the user owns this folder
    get_folder(current_user['id'], file.folder_id, db)
    # checking for duplicates in naming
    check_duplicate_file(file.folder_id, file.name, db)
    # trying to save in bucket
    filename = save_to_storage(current_user['username'], file, file.name)
    # (all exceptions are thrown internally)

    file_wrapper = File(
        **{key: value for key, value in vars(file).items() if key != 'content'},
        name_in_storage = filename
    )

    db.add(file_wrapper)
    db.commit()
    db.refresh(file_wrapper)

    return file_wrapper.id


def get_file(current_user: dict, file_id: int, db: Session):
    print(f"current_user = {current_user}, file_id = {file_id}")
    file_name = retrieve_file_from_id(current_user['id'], file_id, db).name_in_storage
    return retrieve_from_storage(current_user['username'], file_name)


def try_rename_file(current_user: dict, file_id: int, new_name: str, db: Session):
    file = retrieve_file_from_id(current_user['id'], file_id, db)
    check_duplicate_file(file.folder_id, new_name, db)

    file.name = new_name
    db.commit()

    return {"detail": "File renamed successfully."}


def try_delete_file(current_user: dict, file_id: int, db: Session):
    try:
        file = retrieve_file_from_id(current_user['id'], file_id, db)

        remove_from_storage(current_user['username'], file.name_in_storage)

        db.delete(file)
        db.commit()

        return {"detail": "File deleted successfully."}
    except Exception as e:
        db.rollback()
        raise e


def get_metadata(current_user: dict, file_id: int, db: Session):
    return retrieve_file_from_id(current_user['id'], file_id, db)

