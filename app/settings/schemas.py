from pydantic import BaseModel, Field


class UsernamePatch(BaseModel):
    username: str = Field(..., min_length=4, max_length=20, pattern=r'^[a-zA-Z0-9]+$')


class PasswordPatch(BaseModel):
    password: str = Field(..., min_length=8, max_length=128)