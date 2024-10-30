# app/models.py
from sqlalchemy import Column, Integer, String
from app.database import Base  # Імпорт бази даних

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
