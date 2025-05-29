from pydantic import BaseModel, Field
from enum import Enum
from app.folders.schemas import FolderMember
from typing import Optional
from app.users.schemas import UserOut


class FileType(str, Enum):
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    TEXT = "TEXT"
    DOCUMENT = "DOCUMENT"
    VIDEO = "VIDEO"
    OTHER = "OTHER"


class AbstractFile(BaseModel):
    folder_id: int
    name: str = Field(..., min_length=2, max_length=128)
    type: FileType
    format: str
    encrypted_key: str
    encrypted_iv: str


class FileMetadata(AbstractFile):
    folder: FolderMember
    size: float
    shared: Optional[list[int]]


class FileMetadataShortened(BaseModel):
    file_id: int
    owner_id: int
    name: str
    type: FileType
    format: str
    encrypted_key: str
    encrypted_iv: str
    size: float



class FileResponse(BaseModel):
    file_id: int


class FileRename(BaseModel):
    new_name: str = Field(..., min_length=2, max_length=128)


class SharingDetails(BaseModel):
    enc_key: str
    enc_iv: str

    class Config:
        from_attributes = True


class SharingDetailOut(BaseModel):
    id: int
    name: str
    type: FileType
    format: str
    details: list[UserOut]

    class Config:
        from_attributes = True

