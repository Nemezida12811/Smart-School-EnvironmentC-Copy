import asyncio
import re
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Header

from .config import settings
from .errors import ApiError

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def validate_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email))


def validate_password(password: str) -> bool:
    return bool(password) and len(password) >= 6


def _pw(password: str) -> bytes:
    # bcrypt takes maximum 72 bytes (Node-version silently truncated, bcrypt>=5 in Python throws error)
    return password.encode()[:72]


async def hash_password(password: str) -> str:
    hashed = await asyncio.to_thread(bcrypt.hashpw, _pw(password), bcrypt.gensalt(10))
    return hashed.decode()


async def verify_password(password: str, hashed: str) -> bool:
    try:
        return await asyncio.to_thread(bcrypt.checkpw, _pw(password), hashed.encode())
    except ValueError:
        return False


def generate_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"userId": user_id, "iat": now, "exp": now + timedelta(days=7)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


async def current_user_id(authorization: str | None = Header(default=None)) -> str:
    """FastAPI-dependency (analog of verifyTokenMiddleware): returns user id from JWT."""
    if not authorization or not authorization.startswith("Bearer "):
        raise ApiError(401, "No token provided")
    try:
        decoded = jwt.decode(authorization[7:], settings.jwt_secret, algorithms=["HS256"])
        return str(decoded["userId"])
    except Exception:
        raise ApiError(401, "Invalid or expired token")
