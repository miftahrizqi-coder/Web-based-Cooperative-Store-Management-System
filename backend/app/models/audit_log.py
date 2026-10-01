from datetime import datetime, timezone
from enum import Enum

from beanie import Document
from pydantic import Field


class AuditAction(str, Enum):
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SALE = "SALE"
    CANCEL = "CANCEL"
    PURCHASE = "PURCHASE"
    STOCK_ADJUSTMENT = "STOCK_ADJUSTMENT"
    STOCK_OPNAME = "STOCK_OPNAME"
    RETURN = "RETURN"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    PAYMENT = "PAYMENT"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PASSWORD_RESET = "PASSWORD_RESET"


class AuditModule(str, Enum):
    AUTH = "AUTH"
    USER = "USER"
    CATEGORY = "CATEGORY"
    PRODUCT = "PRODUCT"
    SUPPLIER = "SUPPLIER"
    SUPPLIER_PRODUCT = "SUPPLIER_PRODUCT"
    MEMBER = "MEMBER"
    PURCHASE_ORDER = "PURCHASE_ORDER"
    GOODS_RECEIPT = "GOODS_RECEIPT"
    PURCHASE = "PURCHASE"
    SUPPLIER_INVOICE = "SUPPLIER_INVOICE"
    SUPPLIER_PAYMENT = "SUPPLIER_PAYMENT"
    INVENTORY = "INVENTORY"
    SALE = "SALE"
    RETURN = "RETURN"
    EXPENSE = "EXPENSE"


class AuditLog(Document):
    userId: str | None = None
    userName: str | None = None
    action: AuditAction
    module: AuditModule
    referenceId: str | None = None
    description: str
    metadata: dict | None = None
    ipAddress: str | None = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "audit_logs"
        indexes = ["userId", "action", "module", "referenceId", "createdAt"]
