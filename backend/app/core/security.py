from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Union
import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.logging import logger
from app.database.connection import get_db
from app.models.user import User, UserRole

# Password hasher instance (uses Argon2 / Bcrypt)
password_hash_engine = PasswordHash.recommended()

# Bearer token extractor (auto_error=False to allow custom exception handling)
http_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash plain text password."""
    return password_hash_engine.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    try:
        return password_hash_engine.verify(plain_password, hashed_password)
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False


def create_access_token(
    subject: Union[str, int],
    role: str = "INSPECTOR",
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a signed JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Authentication token has expired")
    except jwt.PyJWTError as e:
        raise AuthenticationError(f"Invalid authentication token: {str(e)}")


async def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency to extract and authenticate the current user."""
    if not auth_credentials or not auth_credentials.credentials:
        raise AuthenticationError("Missing Bearer authentication token")

    token = auth_credentials.credentials
    payload = decode_access_token(token)
    user_id_str = payload.get("sub")

    if not user_id_str:
        raise AuthenticationError("Token payload missing subject identifier")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise AuthenticationError("Invalid subject format in token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("User associated with token no longer exists")

    if not user.is_active:
        raise AuthenticationError("User account has been deactivated")

    return user


def require_role(*allowed_roles: UserRole) -> Callable:
    """Dependency factory for enforcing Role-Based Access Control (RBAC)."""

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            role_names = [r.value for r in allowed_roles]
            raise AuthorizationError(
                f"Action restricted to roles: {', '.join(role_names)}. Current role: {current_user.role.value}"
            )
        return current_user

    return role_checker
