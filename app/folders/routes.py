from fastapi import APIRouter, Depends, status, HTTPException, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.services import get_basic_auth, get_full_auth
from app.folders.errors import FolderNotFound, FolderNameAlreadyTakenInParent, CannotModifyRootFolder
from app.folders.services import (
    get_root_folder, get_specific_folder, create_in_root, 
    create_in_folder, change_folder_name, delete_folder,
    compute_space, get_shared_with_me
)
from app.folders.schemas import (
    FolderCreate, FolderPatch, FolderOut,
    TakenSpace
)
from app.files.schemas import FileMetadataShortened
from app.auth.schemas import CurrentUser


folder_router = APIRouter()


@folder_router.get("/shared")
def shared_with_me(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_basic_auth)) -> list[FileMetadataShortened]:
    return get_shared_with_me(db, current_user)


@folder_router.get("/space")
def get_space(current_user: CurrentUser = Depends(get_basic_auth)) -> TakenSpace:
    return compute_space(current_user)


@folder_router.get("/")
def get_root(current_user: CurrentUser = Depends(get_basic_auth), db: Session = Depends(get_db)) -> FolderOut:
    root_folder = get_root_folder(current_user, db)
    return root_folder


@folder_router.get("/{folder_id}")
def get_folder(folder_id: int, current_user: CurrentUser = Depends(get_basic_auth), db: Session = Depends(get_db)) -> FolderOut:
    try:
        folder = get_specific_folder(current_user, folder_id, db)
        return folder
    except FolderNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@folder_router.post("/")
def create_folder_in_root(
    folder: FolderCreate, 
    current_user: CurrentUser = Depends(get_full_auth), 
    db: Session = Depends(get_db)) -> FolderOut:
    try:
        created = create_in_root(current_user, folder.name, db)
        return created
    except FolderNameAlreadyTakenInParent as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@folder_router.post("/{folder_id}")
def create_folder_in_folder(
    folder_id: int, 
    folder: FolderCreate, 
    current_user: CurrentUser = Depends(get_full_auth), 
    db: Session = Depends(get_db)) -> FolderOut:
    try:
        created = create_in_folder(current_user, folder_id, folder.name, db)
        return created
    except FolderNameAlreadyTakenInParent as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except FolderNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@folder_router.patch("/{folder_id}")
def folder_patch(
    folder_id: int,
    folder: FolderPatch,
    current_user: CurrentUser = Depends(get_full_auth),
    db: Session = Depends(get_db)) -> Response:
    try:
        change_folder_name(current_user, folder_id, folder.name, db)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except (CannotModifyRootFolder, FolderNameAlreadyTakenInParent) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except FolderNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    

@folder_router.delete("/{folder_id}")
def folder_delete(
    folder_id: int,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_full_auth), 
    db: Session = Depends(get_db)) -> Response:
    try:
        delete_folder(current_user, folder_id, db, background_tasks)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except CannotModifyRootFolder as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except FolderNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

