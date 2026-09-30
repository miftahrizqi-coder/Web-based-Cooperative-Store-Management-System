from datetime import datetime

from pydantic import BaseModel

from app.models.activity import (
    ActivityEntityType,
    ActivityType,
)


class ActivityResponse(BaseModel):
    id: str

    entityType: ActivityEntityType
    entityId: str

    activityType: ActivityType

    referenceNumber: str | None
    description: str

    actorId: str

    createdAt: datetime