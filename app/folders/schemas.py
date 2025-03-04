from pydantic import BaseModel
from typing import List, Optional


class FolderMember(BaseModel):
    name: str
    id: int


class FolderBase(BaseModel):
    name: str


class FolderCreate(FolderBase):
    pass


class FolderPatch(FolderBase):
    pass


class FolderOut(FolderBase):
    id: int
    folders: List["FolderMember"] = []
    files: List["FileOut"] = []

    class Config:
        from_attributes = True


class FileOut(BaseModel):
    id: int
    name: str
    type: str
    format: str

    class Config:
        from_attributes = True
