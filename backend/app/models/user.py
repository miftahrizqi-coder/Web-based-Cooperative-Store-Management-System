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

    class Settings:
        name = "users"
        indexes = [
            "username",
            "email",
            "role",
        ]