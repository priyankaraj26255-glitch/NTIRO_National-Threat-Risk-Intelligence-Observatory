
import os

import jwt

from datetime import datetime, timedelta, timezone


def get_jwt_settings() -> tuple[str, str]:
    """Load JWT configuration from environment variables."""

    secret_key = os.getenv("JWT_SECRET_KEY")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")

    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured.")

    return secret_key, algorithm


def create_access_token(
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a signed JWT access token."""

    secret_key, algorithm = get_jwt_settings()

    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(minutes=30)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + expires_delta,
        "type": "access",
    }

    encoded_token = jwt.encode(
        payload,
        secret_key,
        algorithm=algorithm,
    )

    return encoded_token


def decode_access_token(token: str) -> dict:
    """Validate and decode a JWT access token."""

    secret_key, algorithm = get_jwt_settings()

    payload = jwt.decode(
        token,
        secret_key,
        algorithms=[algorithm],
        options={
            "require": ["sub", "iat", "exp", "type"],
        },
    )

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type.")

    return payload
