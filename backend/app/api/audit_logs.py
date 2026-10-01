from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.deps import ADMIN, require_role
from app.core.utils import Pagination, PageParams, local_range_bounds, search_regex
from app.models.audit_log import AuditAction, AuditLog, AuditModule
from app.models.user import User


router = APIRouter(prefix="/api/audit-logs", tags=["Audit Log"])


class AuditLogResponse(BaseModel):
    id: str
    userId: str | None
    userName: str | None
    action: AuditAction
    module: AuditModule
    referenceId: str | None
    description: str
    metadata: dict | None
    ipAddress: str | None
    createdAt: datetime


@router.get("", response_model=list[AuditLogResponse])
async def list_audit_logs(
    module: AuditModule | None = Query(default=None),
    action: AuditAction | None = Query(default=None),
    user_id: str | None = Query(default=None, alias="userId"),
    search: str | None = Query(default=None),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    pagination: PageParams = Depends(Pagination(default_page_size=50)),
    current_user: User = Depends(require_role(*ADMIN)),
):
    query: dict = {}
    if module:
        query["module"] = module.value
    if action:
        query["action"] = action.value
    if user_id:
        query["userId"] = user_id
    if search and search.strip():
        query["description"] = search_regex(search)

    start, end = local_range_bounds(date_from, date_to)
    if start or end:
        query["createdAt"] = {}
        if start:
            query["createdAt"]["$gte"] = start
        if end:
            query["createdAt"]["$lt"] = end

    logs = await pagination.apply(AuditLog.find(query).sort("-createdAt"))

    # Lengkapi nama user untuk log lama yang belum menyimpan userName.
    missing = {log.userId for log in logs if log.userId and not log.userName}
    names: dict[str, str] = {}
    if missing:
        from bson import ObjectId

        ids = [ObjectId(uid) for uid in missing if ObjectId.is_valid(uid)]
        for user in await User.find({"_id": {"$in": ids}}).to_list():
            names[str(user.id)] = user.name

    return [
        AuditLogResponse(
            id=str(log.id),
            userId=log.userId,
            userName=log.userName or names.get(log.userId or ""),
            action=log.action,
            module=log.module,
            referenceId=log.referenceId,
            description=log.description,
            metadata=log.metadata,
            ipAddress=log.ipAddress,
            createdAt=log.createdAt,
        )
        for log in logs
    ]
