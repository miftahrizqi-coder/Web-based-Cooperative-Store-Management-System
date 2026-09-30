from datetime import datetime, timezone

from app.models.activity import (
    Activity,
    ActivityEntityType,
    ActivityType,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def create_activity(
    *,
    entity_type: ActivityEntityType,
    entity_id: str,
    activity_type: ActivityType,
    actor_id: str,
    description: str,
    reference_number: str | None = None,
) -> Activity:
    activity = Activity(
        entityType=entity_type,
        entityId=entity_id,
        activityType=activity_type,
        referenceNumber=reference_number,
        description=description,
        actorId=actor_id,
        createdAt=utc_now(),
    )

    await activity.insert()

    return activity


async def get_activities(
    *,
    entity_type: ActivityEntityType | None = None,
    activity_type: ActivityType | None = None,
) -> list[Activity]:
    filters = []

    if entity_type is not None:
        filters.append(
            Activity.entityType == entity_type
        )

    if activity_type is not None:
        filters.append(
            Activity.activityType == activity_type
        )

    if filters:
        return await (
            Activity.find(*filters)
            .sort("-createdAt")
            .to_list()
        )

    return await (
        Activity.find_all()
        .sort("-createdAt")
        .to_list()
    )