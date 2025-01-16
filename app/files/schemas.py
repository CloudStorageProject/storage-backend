from pydantic import BaseModel, Field
from enum import Enum


class FileType(str, Enum):
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    TEXT = "TEXT"
    DOCUMENT = "DOCUMENT"
    VIDEO = "VIDEO"


class FileData(BaseModel):
    folder_id: int
    name: str = Field(..., min_length=2, max_length=128)
    type: FileType
    format: str
    encrypted_key: str
    encrypted_iv: str
    content: str


class FileResponse(BaseModel):
    file_id: int


class FileRename(BaseModel):
    new_name: str = Field(..., min_length=2, max_length=128)


class FileMetadata(BaseModel):
    id: int
    name: str
    format: str
    type: str
    folder_id: int
    encrypted_key: str
    encrypted_iv: str
    name_in_storage: str