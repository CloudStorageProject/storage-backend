from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from app.database import get_db
from app.files.errors import (
    FileAlreadyExistsInThisFolder, FileUploadError, FileRetrieveError, 
    FileDoesNotExist, FileDeletionError, SpaceLimitExceeded,
    DestinationUserDoesNotExist, FileAlreadyShared, CannotShareWithYourself,
    FileIsNotShared
)
from app.auth.services import get_basic_auth, get_full_auth
from app.files.schemas import (
    FileData, FileMetadata, FileResponse, 
    FileRename, SharingDetails, SharingDetailOut,
    FileMetadataShortened
)
from sqlalchemy.orm import Session
from app.folders.errors import FolderNotFound
from app.files.services import (
    try_upload_file, get_file, try_rename_file, 
    try_delete_file, get_metadata, try_share_file,
    try_revoke_access, get_shared_data
)
from io import BytesIO
from fastapi.responses import StreamingResponse
from app.auth.schemas import CurrentUser
from typing import Union


file_router = APIRouter()


@file_router.get("/sharedByMe")
def get_shared_by_me( 
    db: Session = Depends(get_db), 
    current_user: CurrentUser = Depends(get_full_auth)) -> list[SharingDetailOut]:
    return get_shared_data(db, current_user)


@file_router.post("/")
def upload_file(
    file: str = Form(...),
    current_user: CurrentUser = Depends(get_full_auth),
    db: Session = Depends(get_db)
) -> FileResponse:
    try:
        file_data = FileData.parse_raw(file)
        file_id = try_upload_file(current_user, file_data, db)
        return FileResponse(file_id=file_id)
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors()
        )
    except FolderNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileUploadError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except (FileAlreadyExistsInThisFolder, SpaceLimitExceeded) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@file_router.get("/{file_id}")
def get_file_contents(
    file_id: int, 
    current_user: CurrentUser = Depends(get_full_auth), 
    db: Session = Depends(get_db)) -> StreamingResponse:
    try:
        bytes = get_file(current_user, file_id, db)
        transformed = BytesIO(bytes)
        return StreamingResponse(transformed, media_type="application/octet-stream")
    except FileDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileRetrieveError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

@file_router.get("/{file_id}/params")
def get_file_parameters(
    file_id: int, 
    current_user: CurrentUser = Depends(get_basic_auth), 
    db: Session = Depends(get_db)) -> Union[FileMetadata, FileMetadataShortened]:
    try:
        return get_metadata(current_user, file_id, db)
    except FileDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@file_router.patch("/{file_id}")
def rename_file(
    new_name: FileRename, 
    file_id: int, 
    current_user: CurrentUser = Depends(get_full_auth), 
    db: Session = Depends(get_db)) -> Response:
    try:
        try_rename_file(current_user, file_id, new_name.new_name, db)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except FileDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileAlreadyExistsInThisFolder as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    

@file_router.delete("/{file_id}")
def delete_file(
    file_id: int, 
    current_user: CurrentUser = Depends(get_full_auth), 
    db: Session = Depends(get_db)) -> Response:
    try:
        try_delete_file(current_user, file_id, db)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except FileDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileDeletionError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

@file_router.post("/{file_id}/share/{user_id}")
def share_file(
    sharing_details: SharingDetails,
    file_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_full_auth)) -> Response:
    try:
        try_share_file(sharing_details, current_user, user_id, file_id, db)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except (FileDoesNotExist, DestinationUserDoesNotExist) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (FileAlreadyShared, CannotShareWithYourself) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@file_router.delete("/{file_id}/share/{user_id}")
def revoke_access(
    file_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_full_auth)) -> Response:
    try:
        try_revoke_access(current_user, user_id, file_id, db)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except (FileDoesNotExist, DestinationUserDoesNotExist, FileIsNotShared) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
