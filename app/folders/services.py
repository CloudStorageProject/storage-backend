from sqlalchemy.orm import Session
from app.models import Folder, File, User
from app.folders.errors import *
from app.folders.schemas import *
from app.folders.utils import *
from fastapi import BackgroundTasks


def get_root_folder(user, db: Session):
    root_folder = get_root(user['id'], db)
    return construct_model(root_folder)


def get_specific_folder(user, folder_id: int, db: Session):
    folder = get_folder(user['id'], folder_id, db)
    return construct_model(folder)


def create_in_root(user, folder_name: str, db: Session):
    root_folder = get_root_folder(user, db)
    return create_in_folder(user, root_folder.id, folder_name, db)


def create_in_folder(user, folder_id: int, folder_name: str, db: Session):
    # checking if parent exists
    get_folder(user['id'], folder_id, db)

    if folder_exists_in_parent(user['id'], folder_name, folder_id, db):
        raise FolderNameAlreadyTakenInParent("There is already a folder with the same name in this folder.")
    
    new_folder = Folder(
        name=folder_name, 
        user_id=user['id'],
        parent_id=folder_id
    )

    db.add(new_folder)
    db.commit()
    db.refresh(new_folder)

    return new_folder


def change_folder_name(user, folder_id: int, folder_name: str, db: Session):
    target = get_folder(user['id'], folder_id, db)

    if target.parent_id is None:
        raise CannotModifyRootFolder("Root folder can't be modified.")
    
    if folder_exists_in_parent(user['id'], folder_name, target.parent_id, db):
        raise FolderNameAlreadyTakenInParent("There is already a folder with the same name in this folder.")
    
    target.name = folder_name

    db.commit()
    db.refresh(target)


def delete_folder(user, folder_id: int, db: Session, background_tasks: BackgroundTasks):
    db.expire_on_commit = False
    target = get_folder(user['id'], folder_id, db)

    if target.parent_id is None:
        raise CannotModifyRootFolder("Root folder can't be deleted.")
    
    background_tasks.add_task(delete_folder_task, target, db)