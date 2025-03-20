from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str # посилання на базу данних
    SECRET_KEY: str # ключ до шифрування jwt-токенів
    ALGORITHM: str # алгоритм шифрування токенів
    ACCESS_TOKEN_EXPIRE_MINUTES: int # термін придатності токенів
    MINIO_ENDPOINT: str # шлях до minio
    MINIO_LOGIN: str # логін до minio
    MINIO_PASSWORD: str # пароль до minio
    BUCKET_NAME: str # назва бакета minio
    MINIO_SECURE: bool # чи використовуємо SSL в minio
    DEBUG_MODE: bool # якщо true, всі get_full_auth використовують get_basic_auth
    TRUSTED_ORIGIN: str # довірений ресурс для звернення
    USER_SPACE_CAPACITY: int # ємність сховища користувача в ГБ
    CORS_DEBUG_MODE: bool # якщо true, звернення дозволені зі всіх джерел

    class Config:
        env_file = ".env"