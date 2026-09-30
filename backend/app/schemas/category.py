from datetime import datetime

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)


class CategoryStatusUpdate(BaseModel):
    is_active: bool


class CategoryResponse(BaseModel):
    id: str
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime