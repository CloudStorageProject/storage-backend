from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.services import get_full_auth
from app.auth.schemas import CurrentUser
from app.settings.schemas import UsernamePatch, PasswordPatch
from app.settings.services import try_patch_username, try_patch_password
from app.settings.errors import UsernameAlreadyExists


settings_router = APIRouter()


@settings_router.patch("/username")
def patch_username(
    data: UsernamePatch, 
    db: Session = Depends(get_db), 
    current_user: CurrentUser = Depends(get_full_auth)) -> Response:
    try:
        try_patch_username(data, current_user, db)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except UsernameAlreadyExists as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    

@settings_router.patch("/password")
def patch_password(
    data: PasswordPatch,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_full_auth)) -> Response:
    try_patch_password(data, current_user, db)
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

