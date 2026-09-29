from datetime import datetime

from pydantic import BaseModel, Field

from app.models.member import MemberStatus


class MemberCreateRequest(BaseModel):
    memberNumber: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=1, max_length=30)
    email: str | None = Field(default=None, max_length=200)
    address: str | None = Field(default=None, max_length=500)
    joinedAt: datetime | None = None
    status: MemberStatus = MemberStatus.ACTIVE


class MemberUpdateRequest(BaseModel):
    memberNumber: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=1, max_length=30)
    email: str | None = Field(default=None, max_length=200)
    address: str | None = Field(default=None, max_length=500)
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