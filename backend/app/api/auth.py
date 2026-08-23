from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.logging import logger
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database.connection import get_db
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse
from app.schemas.common import APIResponse

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Registers a new inspector, admin, or viewer and returns an authentication token.",
)
async def register(
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Register a new user account."""
    # Check if email is already in use
    existing = await db.execute(select(User).where(User.email == payload.email.lower()))
    if existing.scalar_one_or_none():
        raise ValidationError(f"Email address '{payload.email}' is already registered")

    # Hash password and create user
    user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        password_hash=hash_password(payload.password),
        role=payload.role or UserRole.INSPECTOR,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # Record audit log
    audit_log = AuditLog(
        user_id=user.id,
        action="USER_REGISTERED",
        entity_type="USER",
        entity_id=str(user.id),
        metadata_json={"email": user.email, "role": user.role.value},
    )
    db.add(audit_log)
    await db.commit()

    logger.info(f"New user registered: {user.email} with role {user.role.value}")

    # Generate JWT token
    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
    )
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in_seconds,
            user=UserResponse.model_validate(user),
        ),
        message="User account created successfully",
    )


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="Authenticate user and obtain JWT token",
    description="Authenticates user credentials and returns a Bearer access token.",
)
async def login(
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[TokenResponse]:
    """Authenticate user with email and password."""
    result = await db.execute(select(User).where(User.email == payload.email.lower().strip()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        logger.warning(f"Failed login attempt for email: {payload.email}")
        raise AuthenticationError("Invalid email or password")

    if not user.is_active:
        raise AuthenticationError("This user account has been disabled")

    # Record login audit log
    audit_log = AuditLog(
        user_id=user.id,
        action="USER_LOGGED_IN",
        entity_type="USER",
        entity_id=str(user.id),
        metadata_json={"email": user.email},
    )
    db.add(audit_log)
    await db.commit()

    logger.info(f"User logged in successfully: {user.email}")

    # Generate JWT token
    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
    )
    expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in_seconds,
            user=UserResponse.model_validate(user),
        ),
        message="Authentication successful",
    )


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    summary="Get current user profile",
    description="Returns the profile details of the currently authenticated user.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserResponse]:
    """Get authenticated user profile."""
    return APIResponse(
        success=True,
        data=UserResponse.model_validate(current_user),
        message="User profile retrieved successfully",
    )
