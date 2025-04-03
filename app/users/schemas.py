from pydantic import BaseModel

class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class UserDetailOut(UserOut):
    pub_key: str
    
class UserPageOut(BaseModel):
    page_size: int
    current_page: int
    pages_left: int
    users: list[UserOut]