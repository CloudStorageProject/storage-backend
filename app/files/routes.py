from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.files.errors import *
from app.auth.services import get_basic_auth, get_full_auth
from app.files.schemas import *
from sqlalchemy.orm import Session
from app.folders.errors import *
from app.files.services import *
from io import BytesIO
from fastapi.responses import StreamingResponse


file_router = APIRouter()


# SHOULD BE CHANGED TO GET_FULL_AUTH IN PRODUCTION (?)
@file_router.post("/upload")
def upload_file(file: FileData, current_user: dict = Depends(get_basic_auth), db: Session = Depends(get_db)) -> FileResponse:
    try:
        return {"file_id": try_upload_file(current_user, file, db)}
    except FolderNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileUploadError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except FileAlreadyExistsInThisFolder as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# SHOULD BE CHANGED TO GET_FULL_AUTH IN PRODUCTION (?)
@file_router.get("/get/{file_id}")
def get_file_contents(file_id: int, current_user: dict = Depends(get_basic_auth), db: Session = Depends(get_db)):
    try:
        bytes = get_file(current_user, file_id, db)
        transformed = BytesIO(bytes)
        return StreamingResponse(transformed, media_type="application/octet-stream")
    except FileDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileRetrieveError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# SHOULD BE CHANGED TO GET_FULL_AUTH IN PRODUCTION (?)
# getting metadata (cryptographic parameters, type, format, etc)
@file_router.get("/getParams/{file_id}")
def get_file_parameters(file_id: int, current_user: dict = Depends(get_basic_auth), db: Session = Depends(get_db)):
    try:
        return get_metadata(current_user, file_id, db)
    except FileDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    

# SHOULD BE CHANGED TO GET_FULL_AUTH IN PRODUCTION (?)
@file_router.patch("/rename/{file_id}")
def rename_file(
    new_name: FileRename, 
    file_id: int, 
    current_user: dict = Depends(get_basic_auth), 
    db: Session = Depends(get_db)):
    try:
        return try_rename_file(current_user, file_id, new_name.new_name, db)
    except FileDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileAlreadyExistsInThisFolder as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    

# SHOULD BE CHANGED TO GET_FULL_AUTH IN PRODUCTION (?)
@file_router.delete("/delete/{file_id}")
def delete_file(file_id: int, current_user: dict = Depends(get_basic_auth), db: Session = Depends(get_db)):
    try:
        return try_delete_file(current_user, file_id, db)
    except FileDoesNotExist as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except FileDeletionError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
