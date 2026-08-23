from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.user import UserRole


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Full name of user")
    email: EmailStr = Field(..., description="Valid work/institutional email address")
    password: str = Field(..., min_length=6, max_length=128, description="Account password (min 6 chars)")
    role: Optional[UserRole] = Field(default=UserRole.INSPECTOR, description="User RBAC role")


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
