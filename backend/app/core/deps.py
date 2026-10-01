"""Dependency autentikasi & otorisasi berbasis role (PRD §6, §8)."""

from datetime import datetime, timezone

import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.models.user import RevokedToken, User, UserRole


bearer_scheme = HTTPBearer(auto_error=False)


# Kelompok role yang sering dipakai.
ADMIN = (UserRole.ADMIN,)
ADMIN_PENGURUS = (UserRole.ADMIN, UserRole.PENGURUS)
STAFF = (UserRole.ADMIN, UserRole.PENGURUS, UserRole.KASIR)
POS_OPERATORS = (UserRole.ADMIN, UserRole.KASIR)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Token autentikasi tidak ditemukan.")

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Sesi telah berakhir. Silakan login kembali.")
    except jwt.PyJWTError:
        raise _unauthorized("Token tidak valid.")

    if not payload.get("sub"):
        raise _unauthorized("Token tidak valid.")

    jti = payload.get("jti")
    if jti and await RevokedToken.find_one(RevokedToken.jti == jti):
        raise _unauthorized("Sesi telah logout. Silakan login kembali.")

    return payload


async def get_current_user(
    request: Request,
    payload: dict = Depends(get_token_payload),
) -> User:
    user_id = payload["sub"]

    if not ObjectId.is_valid(user_id):
        raise _unauthorized("Token tidak valid.")

    user = await User.get(ObjectId(user_id))

    if user is None:
        raise _unauthorized("Pengguna tidak ditemukan.")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun pengguna tidak aktif.",
        )

    if payload.get("ver", 0) != user.tokenVersion:
        raise _unauthorized("Sesi tidak berlaku lagi. Silakan login kembali.")

    request.state.user = user
    request.state.token_payload = payload
    return user


def require_role(*allowed_roles: UserRole):
    allowed = set(allowed_roles)

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki akses ke resource ini.",
            )
        return current_user

    return role_checker


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


def token_expiry(payload: dict) -> datetime:
    exp = payload.get("exp")
    if isinstance(exp, (int, float)):
        return datetime.fromtimestamp(exp, tz=timezone.utc)
    return datetime.now(timezone.utc)
