from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    name: str = Field(min_length=1, max_length=100)
    role: UserRole
    memberId: str | None = None


class UserUpdateRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    role: UserRole
    is_active: bool
    memberId: str | None = None


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=200)


class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    name: str
    role: str
    is_active: bool
    memberId: str | None = None
    lastLoginAt: datetime | None = None
    createdAt: datetime | None = None
    updatedAt: datetime | None = None
