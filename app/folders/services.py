from sqlalchemy.orm import Session
from app.models import Folder
from app.folders.errors import FolderNameAlreadyTakenInParent, CannotModifyRootFolder
from app.folders.schemas import FolderOut
from app.folders.utils import (
    delete_folder_task, get_root, get_folder, 
    folder_exists_in_parent, construct_model
)
from app.auth.schemas import CurrentUser
from fastapi import BackgroundTasks


def get_root_folder(current_user: CurrentUser, db: Session) -> FolderOut:
    root_folder = get_root(current_user.id, db)
    return construct_model(root_folder)


def get_specific_folder(current_user: CurrentUser, folder_id: int, db: Session) -> FolderOut:
    folder = get_folder(current_user.id, folder_id, db)
    return construct_model(folder)


def create_in_root(current_user: CurrentUser, folder_name: str, db: Session) -> FolderOut:
    root_folder = get_root_folder(current_user, db)
    return create_in_folder(current_user, root_folder.id, folder_name, db)


def create_in_folder(current_user: CurrentUser, folder_id: int, folder_name: str, db: Session) -> FolderOut:
    # checking if parent exists
    get_folder(current_user.id, folder_id, db)

    if folder_exists_in_parent(current_user.id, folder_name, folder_id, db):
        raise FolderNameAlreadyTakenInParent("There is already a folder with the same name in this folder.")
    
    new_folder = Folder(
        name=folder_name, 
        user_id=current_user.id,
        parent_id=folder_id
    )

    db.add(new_folder)
    db.commit()
    db.refresh(new_folder)

    return new_folder


def change_folder_name(current_user: CurrentUser, folder_id: int, folder_name: str, db: Session) -> None:
    target = get_folder(current_user.id, folder_id, db)

    if target.parent_id is None:
        raise CannotModifyRootFolder("Root folder can't be modified.")
    
    if folder_exists_in_parent(current_user.id, folder_name, target.parent_id, db):
        raise FolderNameAlreadyTakenInParent("There is already a folder with the same name in this folder.")
    
    target.name = folder_name

    db.commit()
    db.refresh(target)


def delete_folder(current_user: CurrentUser, folder_id: int, db: Session, background_tasks: BackgroundTasks) -> None:
    db.expire_on_commit = False
    target = get_folder(current_user.id, folder_id, db)

    if target.parent_id is None:
        raise CannotModifyRootFolder("Root folder can't be deleted.")
    
    background_tasks.add_task(delete_folder_task, target, db)