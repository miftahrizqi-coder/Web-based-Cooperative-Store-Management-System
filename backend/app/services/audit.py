"""Audit trail aktivitas penting (PRD §29)."""

import logging

from app.models.audit_log import AuditAction, AuditLog, AuditModule
from app.models.user import User


logger = logging.getLogger("koperasi.audit")


async def log_audit(
    *,
    action: AuditAction,
    module: AuditModule,
    description: str,
    user: User | None = None,
    user_id: str | None = None,
    reference_id: str | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
    session=None,
) -> AuditLog | None:
    """
    Simpan audit log. Jika `session` diberikan, log ikut transaksi sehingga
    ikut ter-rollback bila operasi utama gagal.
    """
    entry = AuditLog(
        userId=str(user.id) if user else user_id,
        userName=user.name if user else None,
        action=action,
        module=module,
        referenceId=reference_id,
        description=description,
        metadata=metadata,
        ipAddress=ip_address,
    )

    try:
        await entry.insert(session=session)
    except Exception:
        if session is not None:
            raise
        # Audit tidak boleh menggagalkan operasi yang sudah selesai.
        logger.exception("Gagal menyimpan audit log: %s", description)
        return None

    return entry
