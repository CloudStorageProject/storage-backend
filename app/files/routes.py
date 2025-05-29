from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
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
    FileMetadata, FileResponse, 
    FileRename, SharingDetails, SharingDetailOut,
    FileMetadataShortened, AbstractFile
)
from sqlalchemy.orm import Session
from app.folders.errors import FolderNotFound
from app.files.services import (
    try_upload_file, get_file_stream, try_rename_file, 
    try_delete_file, get_metadata, try_share_file,
    try_revoke_access, get_shared_data
)
from io import BytesIO
from fastapi.responses import StreamingResponse
from app.auth.schemas import CurrentUser
from typing import Union
from pydantic import ValidationError


file_router = APIRouter()


@file_router.get("/sharedByMe")
def get_shared_by_me( 
    db: Session = Depends(get_db), 
    current_user: CurrentUser = Depends(get_full_auth)) -> list[SharingDetailOut]:
    return get_shared_data(db, current_user)


@file_router.post("/")
def upload_file(
    metadata: str = Form(...),
    upload: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_full_auth),
    db: Session = Depends(get_db)
) -> FileResponse:
    """
    Handles file upload with associated metadata.

    This endpoint accepts a file and its metadata, validates the metadata,
    and uploads the file to the server for the authenticated user. It performs
    checks such as file duplication, folder existence, and space availability.

    Parameters:
        metadata (str): A JSON string containing the file's metadata. It is parsed
            into an `AbstractFile` object.
        upload (UploadFile): The file to be uploaded.
        current_user (CurrentUser): The currently authenticated user, resolved via dependency injection.
        db (Session): SQLAlchemy database session, resolved via dependency injection.

    Returns:
        FileResponse: An object representing a successful file upload, including the file's unique ID.

    Raises:
        HTTPException (422): If the metadata is invalid or fails validation.
        HTTPException (404): If the target folder for the upload does not exist.
        HTTPException (500): If an internal error occurs during file upload.
        HTTPException (403): If the file already exists in the folder or the user's storage quota is exceeded.
    """
    try:
        metadata_obj = AbstractFile.parse_raw(metadata)

        file_id = try_upload_file(current_user, metadata_obj, upload, db)
        return FileResponse(file_id=file_id)

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())
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
    db: Session = Depends(get_db)
) -> StreamingResponse:
    """
    Retrieve and stream the contents of a file by its ID.

    This endpoint allows an authenticated user to download a file they have access to.
    The file is streamed directly to the client with appropriate headers for download.

    Parameters:
        file_id (int): The unique identifier of the file to retrieve.
        current_user (CurrentUser): The currently authenticated user, resolved via dependency injection.
        db (Session): SQLAlchemy database session, resolved via dependency injection.

    Returns:
        StreamingResponse: A streamed response containing the file's binary content

    Raises:
        HTTPException (404): If the file does not exist or is not accessible to the user.
        HTTPException (500): If an error occurs while retrieving the file.
    """
    try:
        file_stream = get_file_stream(current_user, file_id, db)
        return StreamingResponse(file_stream, media_type="text/plain")
    
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
