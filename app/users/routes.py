from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.services import get_basic_auth
from app.users.errors import UserNotFound, InvalidPageSize
from app.users.services import get_pub_key, get_page
from app.users.schemas import UserDetailOut, UserPageOut
from app.auth.schemas import CurrentUser


user_router = APIRouter()


@user_router.get("/")
def get_users(
    username: str,
    size: int = Query(20), 
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_basic_auth),
) -> UserPageOut:
    
    try:
        return get_page(db, username, size)
    except InvalidPageSize as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@user_router.get("/publicKey/{id}")
def get_pub_key_by_id(
    id: int,
    current_user: CurrentUser = Depends(get_basic_auth),
    db: Session = Depends(get_db),
) -> UserDetailOut:
    try:
        return get_pub_key(db, id)
    except UserNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))