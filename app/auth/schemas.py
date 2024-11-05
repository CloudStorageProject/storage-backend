from pydantic import BaseModel, Field, EmailStr

class UserCreate(BaseModel):
    username: str = Field(..., min_length=4, max_length=20, pattern=r'^[a-zA-Z0-9]+$')
    password: str = Field(..., min_length=8, max_length=128)
    email: EmailStr

    class Config:
        from_attributes = True
        str_strip_whitespace = True

class UserOut(BaseModel):
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str
