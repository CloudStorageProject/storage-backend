from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.models import Folder, File, SharedFile
from app.folders.schemas import FolderMember, FolderOut, FileOut
from app.folders.errors import FolderNotFound
from app.files.utils import bulk_remove_from_storage, decrement_user_space
from loguru import logger


def traverse_subfolders(db: Session, id: int) -> list[int]:
    folder_ids = db.execute(text("""
        WITH RECURSIVE folder_hierarchy AS (
            SELECT id, parent_id, name
            FROM folders
            WHERE id = :folder_id

            UNION ALL

            SELECT f.id, f.parent_id, f.name
            FROM folders f
            INNER JOIN folder_hierarchy fh ON f.parent_id = fh.id
        )
        SELECT id FROM folder_hierarchy
    """), {'folder_id': id}).fetchall()

    return [item[0] for item in folder_ids]


def get_files_for_folders(db: Session, folder_ids: list[int]) -> tuple[list[int], list[str], list[float]]:
    files = db.execute(text("""
        WITH RECURSIVE folder_hierarchy AS (
            SELECT id
            FROM folders
            WHERE id IN :folder_ids

            UNION ALL

            SELECT f.id
            FROM folders f
            INNER JOIN folder_hierarchy fh ON f.parent_id = fh.id
        )
        SELECT DISTINCT f.id, f.name_in_storage, f.size
        FROM files f
        INNER JOIN folder_hierarchy fh ON f.folder_id = fh.id;
    """), {"folder_ids": tuple(folder_ids)}).fetchall()

    file_ids = [item[0] for item in files]
    file_names = [item[1] for item in files]
    file_sizes = [item[2] for item in files]

    return file_ids, file_names, file_sizes


def delete_folder_task(folder: Folder, db: Session) -> None:
    try:
        with db.begin():
            logger.debug(f"Working with folder {folder.name}, id = {folder.id}")

            folder_ids = traverse_subfolders(db, folder.id)
            logger.debug(f"Traversing subfolders for folder {folder.id}: {folder_ids}")

            file_ids, file_names, file_sizes = get_files_for_folders(db, folder_ids)

            logger.debug(f"File ids: {file_ids}")
            logger.debug(f"File names: {file_names}")
            logger.debug(f"File sizes: {file_sizes}")

            if file_names:
                bulk_remove_from_storage(file_names)

            total_size_to_decrement = sum(file_sizes)
            logger.debug(f"Total size to decrement: {total_size_to_decrement}")

            decrement_user_space(folder.user_id, total_size_to_decrement, db)

            db.query(SharedFile).filter(SharedFile.file_id.in_(file_ids)).delete()

            db.query(File).filter(File.id.in_(file_ids)).delete()

            db.query(Folder).filter(Folder.id.in_(folder_ids)).delete()

            db.delete(folder)

            db.commit()

    except Exception as e:
        db.rollback()
        raise e


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
