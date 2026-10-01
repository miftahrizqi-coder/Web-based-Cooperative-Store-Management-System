from fastapi import APIRouter, Depends, Query

from app.core.deps import ADMIN_PENGURUS, require_role
from app.core.utils import Pagination, PageParams
from app.models.activity import ActivityEntityType, ActivityType
from app.models.user import User
from app.schemas.activity import ActivityResponse
from app.services.activity import get_activities


router = APIRouter(prefix="/activities", tags=["Activities"])


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


@router.get("", response_model=list[ActivityResponse])
async def list_activities(
    entity_type: ActivityEntityType | None = Query(default=None, alias="entityType"),
    activity_type: ActivityType | None = Query(default=None, alias="activityType"),
    entity_id: str | None = Query(default=None, alias="entityId"),
    pagination: PageParams = Depends(Pagination()),
    user: User = Depends(require_role(*ADMIN_PENGURUS)),
):
    query = await get_activities(
        entity_type=entity_type,
        activity_type=activity_type,
        entity_id=entity_id,
    )
    activities = await pagination.apply(query)
    return [activity_response(a) for a in activities]
