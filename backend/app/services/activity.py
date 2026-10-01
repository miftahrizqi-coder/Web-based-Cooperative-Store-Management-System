from datetime import datetime, timezone

from app.models.activity import (
    Activity,
    ActivityEntityType,
    ActivityType,
)
from app.models.audit_log import AuditAction, AuditModule
from app.services.audit import log_audit


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


_ACTION_MAP = {
    ActivityType.CREATED: AuditAction.CREATE,
    ActivityType.UPDATED: AuditAction.UPDATE,
    ActivityType.SUBMITTED: AuditAction.UPDATE,
    ActivityType.APPROVED: AuditAction.APPROVE,
    ActivityType.ORDERED: AuditAction.UPDATE,
    ActivityType.RECEIVED: AuditAction.PURCHASE,
    ActivityType.COMPLETED: AuditAction.UPDATE,
    ActivityType.CANCELLED: AuditAction.CANCEL,
    ActivityType.PAID: AuditAction.PAYMENT,
}

_MODULE_MAP = {
    ActivityEntityType.PURCHASE_ORDER: AuditModule.PURCHASE_ORDER,
    ActivityEntityType.GOODS_RECEIPT: AuditModule.GOODS_RECEIPT,
    ActivityEntityType.PURCHASE: AuditModule.PURCHASE,
    ActivityEntityType.SUPPLIER_INVOICE: AuditModule.SUPPLIER_INVOICE,
    ActivityEntityType.SUPPLIER_PAYMENT: AuditModule.SUPPLIER_PAYMENT,
}


async def create_activity(
    *,
    entity_type: ActivityEntityType,
    entity_id: str,
    activity_type: ActivityType,
    actor_id: str,
    description: str,
    reference_number: str | None = None,
    session=None,
) -> Activity:
    """Timeline procurement + audit log (keduanya ikut transaksi bila ada)."""
    activity = Activity(
        entityType=entity_type,
        entityId=entity_id,
        activityType=activity_type,
        referenceNumber=reference_number,
        description=description,
        actorId=actor_id,
        createdAt=utc_now(),
    )

    await activity.insert(session=session)

    await log_audit(
        action=_ACTION_MAP.get(activity_type, AuditAction.UPDATE),
        module=_MODULE_MAP[entity_type],
        description=description,
        user_id=actor_id,
        reference_id=entity_id,
        metadata={"referenceNumber": reference_number} if reference_number else None,
        session=session,
    )

    return activity


async def get_activities(
    *,
    entity_type: ActivityEntityType | None = None,
    activity_type: ActivityType | None = None,
    entity_id: str | None = None,
):
    """Mengembalikan query (belum dieksekusi) agar bisa dipaginasi."""
    filters: dict = {}

    if entity_type is not None:
        filters["entityType"] = entity_type.value

    if activity_type is not None:
        filters["activityType"] = activity_type.value

    if entity_id:
        filters["entityId"] = entity_id

    return Activity.find(filters).sort("-createdAt")
