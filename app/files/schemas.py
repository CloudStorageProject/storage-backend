from pydantic import BaseModel, Field
from enum import Enum
from typing import Union
from app.folders.schemas import FolderMember


class FileType(str, Enum):
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    TEXT = "TEXT"
    DOCUMENT = "DOCUMENT"
    VIDEO = "VIDEO"


class AbstractFile(BaseModel):
    folder_id: int
    name: str = Field(..., min_length=2, max_length=128)
    type: FileType
    format: str
    encrypted_key: str
    encrypted_iv: str


class FileData(AbstractFile):
    content: str


class FileMetadata(AbstractFile):
    folder: FolderMember


class FileResponse(BaseModel):
    file_id: int


class FileRename(BaseModel):
    new_name: str = Field(..., min_length=2, max_length=128)