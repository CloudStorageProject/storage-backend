from pydantic import BaseModel


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
    folders: list["FolderMember"] = []
    files: list["FileOut"] = []

    class Config:
        from_attributes = True


class FileOut(BaseModel):
    id: int
    name: str
    type: str
    format: str

    class Config:
        from_attributes = True
