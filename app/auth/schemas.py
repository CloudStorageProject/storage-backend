from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class EmailCheck(BaseModel):
    email: str


class UsernameCheck(BaseModel):
    username: str


class CheckResult(BaseModel):
    exists: bool


class CurrentUser(BaseModel):
    username: str
    email: str
    public_key: str
    id: int

    privileged: bool

    space_taken: float
    subscription_name: str
    subscription_space: float

    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None

    customer_id: str

    class Config:
        from_attributes = True


class ChallengeAnswer(BaseModel):
    challenge: str = Field(..., pattern=r'^\d+:[A-Za-z0-9+/=]+$')
    sign: str
    
    @property
    def random_part(self):
        return self.challenge.split(":")[1]


class UserLogin(BaseModel):
    username: str = Field(..., min_length=4, max_length=20, pattern=r'^[a-zA-Z0-9]+$')
    password: str = Field(..., min_length=8, max_length=128)

    class Config:
        from_attributes = True
        str_strip_whitespace = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=4, max_length=20, pattern=r'^[a-zA-Z0-9]+$')
    password: str = Field(..., min_length=8, max_length=128)
    public_key: str = Field(..., pattern=r'^[A-Za-z0-9+/=]+$')
    email: EmailStr

    class Config:
        from_attributes = True
        str_strip_whitespace = True


class UserInfo(BaseModel):
    username: str
    email: str
    public_key: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    token: str
    user: UserInfo

    
class ChallengeString(BaseModel):
    challenge: str
