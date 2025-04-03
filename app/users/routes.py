from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.services import get_basic_auth
from app.users.errors import PageNotFound, UserNotFound
from app.users.services import get_page, get_basic_user_info, get_pub_key
from app.users.schemas import UserPageOut, UserOut, UserDetailOut
from app.auth.schemas import CurrentUser
from typing import Union

user_router = APIRouter()

@user_router.get("/")
def get_users_or_user_by_username(
    current_user: CurrentUser = Depends(get_basic_auth), 
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    username: str = Query(None)
) -> Union[UserPageOut, UserOut]:
    if username:
        try:
            return get_basic_user_info(db, username)
        except UserNotFound as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    else:
        try:
            return get_page(db, page, size)
        except PageNotFound as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


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