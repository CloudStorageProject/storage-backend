from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    MINIO_ENDPOINT: str
    MINIO_LOGIN: str
    MINIO_PASSWORD: str
    BUCKET_NAME: str
    MINIO_SECURE: bool
    DEBUG_MODE: bool
    TRUSTED_ORIGIN: str
    USER_SPACE_CAPACITY: int

    class Config:
        env_file = ".env"