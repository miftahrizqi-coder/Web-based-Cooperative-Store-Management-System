from datetime import datetime, timezone
from enum import Enum

from beanie import Document
from pydantic import EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    KASIR = "kasir"
    PENGURUS = "pengurus"
    ANGGOTA = "anggota"


class User(Document):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password_hash: str
    name: str = Field(min_length=1, max_length=100)
    role: UserRole
    is_active: bool = True

    # Akun role "anggota" ditautkan ke dokumen members agar anggota bisa
    # melihat profil & riwayat transaksinya sendiri (PRD §6.4).
    memberId: str | None = None

    # Dinaikkan saat password diubah/di-reset -> token lama tidak berlaku.
    tokenVersion: int = 0

    lastLoginAt: datetime | None = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        # username & email: index unik dibuat di core/database.py
        indexes = ["role", "memberId"]


class RevokedToken(Document):
    """Token yang di-logout sebelum kedaluwarsa (denylist berbasis jti)."""

    jti: str
    expiresAt: datetime

    class Settings:
        name = "revoked_tokens"
        indexes = ["jti"]
