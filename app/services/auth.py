# Authentication service functions
from datetime import datetime, timedelta
import jwt
from typing import Dict
from settings.config import settings  

def create_access_token(*, data: Dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if 'role' in to_encode:
        to_encode['role'] = to_encode['role'].upper()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> Dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None

# TODO: User authentication 