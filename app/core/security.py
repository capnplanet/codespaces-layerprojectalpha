import hashlib
import hmac
import os
from typing import Tuple
from jose import jwt
from datetime import datetime, timedelta
from app.core.config import get_settings

settings = get_settings()
ALGORITHM = "HS256"


def sign_hmac(message: str) -> str:
    key = settings.hmac_secret.encode()
    return hmac.new(key, message.encode(), hashlib.sha256).hexdigest()


def verify_hmac(message: str, signature: str) -> bool:
    expected = sign_hmac(message)
    return hmac.compare_digest(expected, signature)


def create_access_token(subject: str, role: str, expires_minutes: int = 60) -> str:
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> Tuple[str, str]:
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    return payload.get("sub"), payload.get("role")
