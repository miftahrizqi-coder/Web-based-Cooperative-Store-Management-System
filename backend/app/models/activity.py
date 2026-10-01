from datetime import datetime, timezone
from enum import Enum

from beanie import Document
from pydantic import Field


class ActivityEntityType(str, Enum):
    PURCHASE_ORDER = "PURCHASE_ORDER"
    GOODS_RECEIPT = "GOODS_RECEIPT"
    PURCHASE = "PURCHASE"
    SUPPLIER_INVOICE = "SUPPLIER_INVOICE"
    SUPPLIER_PAYMENT = "SUPPLIER_PAYMENT"


class ActivityType(str, Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    ORDERED = "ORDERED"
    RECEIVED = "RECEIVED"
    COMPLETED = "COMPLETED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class Activity(Document):
    entityType: ActivityEntityType
    entityId: str

    activityType: ActivityType

    referenceNumber: str | None = None
    description: str

    actorId: str

    createdAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "activities"

        indexes = [
            "entityType",
            "entityId",
            "activityType",
            "actorId",
            "createdAt",
        ]