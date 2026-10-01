from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.member import MemberStatus


class MemberBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=1, max_length=30)
    email: EmailStr | None = None
    address: str | None = Field(default=None, max_length=500)

    @field_validator("email", mode="before")
    @classmethod
    def empty_email_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value


class MemberCreateRequest(MemberBase):
    # Kosong = dibuat otomatis (KOP-001, KOP-002, ...).
    memberNumber: str | None = Field(default=None, max_length=50)
    joinedAt: datetime | None = None
    status: MemberStatus = MemberStatus.ACTIVE


class MemberUpdateRequest(MemberBase):
    memberNumber: str = Field(min_length=1, max_length=50)
    joinedAt: datetime
    status: MemberStatus


class MemberResponse(BaseModel):
    id: str
    memberNumber: str
    name: str
    phone: str
    email: str | None
    address: str | None
    joinedAt: datetime
    status: MemberStatus
    createdAt: datetime
    updatedAt: datetime


class MemberStatsResponse(MemberResponse):
    transactionCount: int
    totalSpending: float
    lastTransactionAt: datetime | None
    hasUserAccount: bool = False
