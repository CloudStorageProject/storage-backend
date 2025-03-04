from sqlalchemy.orm import Session, joinedload
from app.models import Folder
from app.folders.schemas import FolderMember, FolderOut, FileOut
from app.folders.errors import FolderNotFound
from app.files.utils import bulk_remove_from_storage
from loguru import logger

def delete_folder_task(folder: Folder, db: Session) -> None:
    try:
        with db.begin():
            logger.debug(f"Working with folder {folder.name}, id = {folder.id}")

            delete_files_in_folder(folder, db)
            delete_subfolders_and_files(folder, db)

            logger.debug(f"Trying to delete the main folder {folder.name}, id = {folder.id}")
            db.delete(folder)
            db.commit()
    except Exception as e:
        db.rollback()
        raise e


def delete_subfolders_and_files(folder: Folder, db: Session) -> None:
    folder_full = db.query(Folder).options(joinedload(Folder.subfolders)).filter(Folder.id == folder.id).first()

    for subfolder in folder_full.subfolders:
        try:
            delete_files_in_folder(subfolder, db)
            delete_subfolders_and_files(subfolder, db)
            logger.debug(f"Trying to delete subfolder, id = {subfolder.id}")
            db.delete(subfolder)
        except Exception as e:
            db.rollback()
            raise e

def delete_files_in_folder(folder: Folder, db: Session) -> None:
    folder_full = db.query(Folder).options(joinedload(Folder.files)).filter(Folder.id == folder.id).first()
    file_names = [file.name_in_storage for file in folder_full.files]

    logger.debug(f"File names for folder {folder.name} with id = {folder.id}: {file_names}")

    if file_names:
        bulk_remove_from_storage(file_names)

    for file in folder_full.files:
        try:
            db.delete(file)
        except Exception as e:
            db.rollback()
            raise e
    db.flush()


def get_root(user_id: int, db: Session) -> Folder:
    return db.query(Folder).filter(Folder.parent_id == None, Folder.user_id == user_id).first()


def get_folder(user_id: int, folder_id: int, db: Session) -> Folder:
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()

    if not folder:
        raise FolderNotFound("This folder does not exist.")
    
    return folder


def folder_exists_in_parent(user_id: int, folder_name: str, folder_id: int, db: Session) -> bool:
    exists = db.query(Folder).filter(
        Folder.name == folder_name, 
        Folder.parent_id == folder_id, 
        Folder.user_id == user_id).first()
    
    return True if exists else False


def construct_model(folder) -> FolderOut:
    return FolderOut(
        id=folder.id,
        name=folder.name,
        folders=[FolderMember(id=f.id, name=f.name) for f in folder.subfolders],
        files=[FileOut(id=f.id, name=f.name, type=f.type, format=f.format) for f in folder.files]
    )
