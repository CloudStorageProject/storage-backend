from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base  

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)
    public_key = Column(String, unique=True)
    space_taken = Column(Float, default=0.0)

    challenges = relationship("Challenge", back_populates="user")
    folders = relationship("Folder", back_populates="user")


class Challenge(Base):
    __tablename__ = "challenges"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=func.now())
    random_chars = Column(String(20))
    is_used = Column(Boolean, default=False)

    user = relationship("User", back_populates="challenges")


class Folder(Base):
    __tablename__ = 'folders'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('folders.id'), nullable=True)
    name = Column(String, nullable=False)

    
    user = relationship('User', back_populates='folders')
    parent = relationship('Folder', remote_side=[id])
    subfolders = relationship('Folder', back_populates='parent')
    files = relationship('File', back_populates='folder')


class File(Base):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    format = Column(String, nullable=False)
    type = Column(String, nullable=False)
    folder_id = Column(Integer, ForeignKey('folders.id'), nullable=False)
    encrypted_key = Column(String, nullable=False)
    encrypted_iv = Column(String, nullable=False)
    name_in_storage = Column(String, nullable=False)
    size = Column(Float, default=0.0)
    
    folder = relationship('Folder', back_populates='files')