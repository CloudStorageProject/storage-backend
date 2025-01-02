from pydantic import BaseModel, Field, EmailStr

class ChallengeAnswer(BaseModel):
    challenge: str
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

class UserOut(BaseModel):
    username: str

class Token(BaseModel):
    token: str
