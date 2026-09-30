from fastapi import APIRouter, Depends, Query

from app.api.procurement import require_procurement_user
from app.models.activity import (
    ActivityEntityType,
    ActivityType,
)
from app.models.user import User
from app.schemas.activity import ActivityResponse
from app.services.activity import get_activities


router = APIRouter(
    prefix="/activities",
    tags=["Activities"],
)


def activity_response(activity) -> ActivityResponse:
    return ActivityResponse(
        id=str(activity.id),
        entityType=activity.entityType,
        entityId=activity.entityId,
        activityType=activity.activityType,
        referenceNumber=activity.referenceNumber,
        description=activity.description,
        actorId=activity.actorId,
        createdAt=activity.createdAt,
    )


@router.get(
    "",
    response_model=list[ActivityResponse],
)
async def list_activities(
    entity_type: ActivityEntityType | None = Query(
        default=None,
        alias="entityType",
    ),
    activity_type: ActivityType | None = Query(
        default=None,
        alias="activityType",
    ),
    user: User = Depends(require_procurement_user),
):
    activities = await get_activities(
        entity_type=entity_type,
        activity_type=activity_type,
    )

    return [
        activity_response(activity)
        for activity in activities
    ]