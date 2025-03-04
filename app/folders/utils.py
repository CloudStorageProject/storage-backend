from sqlalchemy.orm import Session
from app.models import Folder
from app.folders.schemas import *
from app.folders.errors import *


def get_root(user_id: int, db: Session):
    return db.query(Folder).filter(Folder.parent_id == None, Folder.user_id == user_id).first()


def get_folder(user_id: int, folder_id: int, db: Session):
    folder = db.query(Folder).filter(Folder.id == folder_id, Folder.user_id == user_id).first()

    if not folder:
        raise FolderNotFound("This folder does not exist.")
    
    return folder


def folder_exists_in_parent(user_id: int, folder_name: str, folder_id: int, db: Session):
    exists = db.query(Folder).filter(
        Folder.name == folder_name, 
        Folder.parent_id == folder_id, 
        Folder.user_id == user_id).first()
    
    return True if exists else False


def construct_model(folder):
    return FolderOut(
        id=folder.id,
        name=folder.name,
        folders=[FolderMember(id=f.id, name=f.name) for f in folder.subfolders],
        files=[FileOut(id=f.id, name=f.name, type=f.file_type, format=f.extension) for f in folder.files]
    )
