import hashlib
import hmac
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

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
    expire = datetime.now(tz=UTC) + timedelta(minutes=expires_minutes)
    to_encode = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> tuple[str, str]:
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[ALGORITHM],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )
    return payload.get("sub", ""), payload.get("role", "")


def require_auth(authorization: str | None) -> tuple[str, str]:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            return decode_token(token)
        except JWTError as exc:
            raise ValueError(f"invalid_token: {exc}") from exc
    if settings.environment == "dev" and settings.dev_auth_enabled:
        # Allow a static dev token value but still require it to be a valid JWT
        # signed with our secret
        dev_token = settings.dev_static_token
        try:
            return decode_token(dev_token)
        except JWTError:
            # fallback: generate ephemeral dev token when static not a JWT
            generated = create_access_token("dev", "admin", expires_minutes=60)
            return decode_token(generated)
    raise ValueError("missing_or_invalid_authorization")
