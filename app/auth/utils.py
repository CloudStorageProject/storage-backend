from passlib.context import CryptContext
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
from string import ascii_letters, digits
import jwt
import os
import base64
import random

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_signature(challenge: str, signature: str, public_key: str) -> bool:
    try:
        pub_key_bytes = base64.b64decode(public_key)
        pub_key = serialization.load_pem_public_key(pub_key_bytes)
        signature_bytes = base64.b64decode(signature)
        challenge_bytes = challenge.encode('utf-8')

        pub_key.verify(
            signature_bytes,
            challenge_bytes,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    
    except Exception as e:
        print(str(e))
        return False

def generate_challenge_string():
    return f"{int(datetime.utcnow().timestamp())}:{''.join(random.choices(ascii_letters + digits, k=20))}"
