from datetime import datetime, timezone
from enum import Enum

from beanie import Document
from pydantic import Field


class ExpenseCategory(str, Enum):
    ELECTRICITY = "ELECTRICITY"
    WATER = "WATER"
    INTERNET = "INTERNET"
    TRANSPORTATION = "TRANSPORTATION"
    OFFICE_SUPPLIES = "OFFICE_SUPPLIES"
    MAINTENANCE = "MAINTENANCE"
    OTHER = "OTHER"


class Expense(Document):
    expenseNumber: str
    category: ExpenseCategory
    description: str = Field(min_length=1, max_length=500)
    amount: float = Field(gt=0)
    date: datetime
    createdBy: str
    updatedBy: str | None = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "expenses"
        indexes = ["category", "date", "createdBy"]
