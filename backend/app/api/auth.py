from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.deps import (
    client_ip,
    get_current_user,
    get_token_payload,
    token_expiry,
)
from app.core.rate_limit import login_rate_limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.core.utils import utc_now
from app.models.audit_log import AuditAction, AuditModule
from app.models.user import RevokedToken, User
from app.services.audit import log_audit


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=200)


class CurrentUserResponse(BaseModel):
    id: str
    username: str
    email: str
    name: str
    role: str
    is_active: bool
    memberId: str | None = None


class LoginResponse(BaseModel):
    user: CurrentUserResponse
    token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=200)


class ChangePasswordResponse(BaseModel):
    message: str
    token: str


def current_user_response(user: User) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
        memberId=user.memberId,
    )


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request):
    ip = client_ip(request)
    username = payload.username.strip()
    limiter_key = f"{ip}:{username.lower()}"

    retry_after = login_rate_limiter.retry_after(limiter_key)
    if retry_after:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Terlalu banyak percobaan login gagal. "
                f"Coba lagi dalam {retry_after} detik."
            ),
            headers={"Retry-After": str(retry_after)},
        )

    user = await User.find_one(User.username == username)

    if user is None or not verify_password(payload.password, user.password_hash):
        login_rate_limiter.register_failure(limiter_key)
        await log_audit(
            action=AuditAction.LOGIN_FAILED,
            module=AuditModule.AUTH,
            description=f"Login gagal untuk username '{username}'",
            user_id=str(user.id) if user else None,
            ip_address=ip,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun pengguna tidak aktif. Hubungi admin.",
        )

    login_rate_limiter.reset(limiter_key)

    user.lastLoginAt = utc_now()
    await user.save()

    await log_audit(
        action=AuditAction.LOGIN,
        module=AuditModule.AUTH,
        description=f"{user.name} login",
        user=user,
        reference_id=str(user.id),
        ip_address=ip,
    )

    return LoginResponse(
        user=current_user_response(user),
        token=create_access_token(str(user.id), user.tokenVersion),
    )


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user_response(current_user)


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    payload: dict = Depends(get_token_payload),
):
    jti = payload.get("jti")
    if jti:
        await RevokedToken(jti=jti, expiresAt=token_expiry(payload)).insert()

    await log_audit(
        action=AuditAction.LOGOUT,
        module=AuditModule.AUTH,
        description=f"{current_user.name} logout",
        user=current_user,
        reference_id=str(current_user.id),
        ip_address=client_ip(request),
    )

    return {"message": "Logout berhasil."}


@router.put("/password", response_model=ChangePasswordResponse)
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password saat ini salah.",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password baru harus berbeda dari password saat ini.",
        )

    current_user.password_hash = hash_password(payload.new_password)
    # Semua token lama menjadi tidak berlaku.
    current_user.tokenVersion += 1
    current_user.updatedAt = utc_now()
    await current_user.save()

    await log_audit(
        action=AuditAction.PASSWORD_CHANGE,
        module=AuditModule.AUTH,
        description=f"{current_user.name} mengubah password",
        user=current_user,
        reference_id=str(current_user.id),
        ip_address=client_ip(request),
    )

    return ChangePasswordResponse(
        message="Password berhasil diubah.",
        token=create_access_token(str(current_user.id), current_user.tokenVersion),
    )
