"""
Authentication: password + TOTP (Section 1.3 / 3.4 MFA requirement).

This is intentionally simplified for a student project - it covers the
real mechanics (password hash check, TOTP verification, signed session
token) without a full user-registration system. You will wire this to
your actual `patients`/`staff` tables once those exist; for now it
demonstrates the pattern end to end.
"""
from datetime import datetime, timedelta, timezone

import pyotp
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import PyJWTError as JWTError
from passlib.context import CryptContext

from app.core.config import settings
from app.core.database import get_db_connection

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def verify_totp(totp_secret: str, code: str) -> bool:
    """Checks the 6-digit code against the user's TOTP secret (30s rotation)."""
    totp = pyotp.TOTP(totp_secret)
    return totp.verify(code, valid_window=1)  # allows 1 step of clock drift


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception


credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate session token",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependency for ANY protected route. Decodes the JWT issued at login
    and returns the user's UUID. Routes use this, then pass the result
    into get_authenticated_db() to get an RLS-aware connection.
    """
    return decode_access_token(token)


async def get_authenticated_db(user_id: str = Depends(get_current_user_id)):
    """
    This is the dependency real routes should use. It chains:
      1. verify the JWT -> get user_id
      2. open a db connection with app.current_user_id already SET

    Use this in routes instead of get_db_connection directly, unless
    the route is intentionally public (e.g. /login itself).
    """
    async for conn in get_db_connection(current_user_id=user_id):
        yield conn
