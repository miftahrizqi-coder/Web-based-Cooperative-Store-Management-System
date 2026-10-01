from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.deps import ADMIN, client_ip, require_role
from app.core.security import hash_password
from app.core.utils import Pagination, PageParams, parse_object_id, search_regex, utc_now
from app.models.audit_log import AuditAction, AuditModule
from app.models.member import Member
from app.models.user import User, UserRole
from app.schemas.user import (
    ResetPasswordRequest,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.services.audit import log_audit


router = APIRouter(prefix="/api/users", tags=["Users"])

admin_only = require_role(*ADMIN)


def to_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
        memberId=user.memberId,
        lastLoginAt=user.lastLoginAt,
        createdAt=user.createdAt,
        updatedAt=user.updatedAt,
    )


async def get_user_or_404(user_id: str) -> User:
    user = await User.get(parse_object_id(user_id, "ID pengguna"))
    if user is None:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan.")
    return user


async def validate_member_link(
    role: UserRole,
    member_id: str | None,
    exclude_user_id=None,
) -> str | None:
    """Akun anggota wajib ditautkan ke satu data anggota (1:1)."""
    if role != UserRole.ANGGOTA:
        return None

    if not member_id:
        raise HTTPException(
            status_code=422,
            detail="Akun dengan role anggota wajib ditautkan ke data anggota.",
        )

    member = await Member.get(parse_object_id(member_id, "ID anggota"))
    if member is None:
        raise HTTPException(status_code=404, detail="Data anggota tidak ditemukan.")

    query: dict = {"memberId": member_id}
    if exclude_user_id is not None:
        query["_id"] = {"$ne": exclude_user_id}
    if await User.find_one(query):
        raise HTTPException(
            status_code=409,
            detail="Data anggota tersebut sudah ditautkan ke akun lain.",
        )

    return member_id


async def ensure_not_last_admin(user: User) -> None:
    if user.role != UserRole.ADMIN or not user.is_active:
        return
    active_admins = await User.find(
        {"role": UserRole.ADMIN.value, "is_active": True}
    ).count()
    if active_admins <= 1:
        raise HTTPException(
            status_code=409,
            detail="Tidak dapat menonaktifkan/mengubah role admin aktif terakhir.",
        )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreateRequest,
    request: Request,
    current_user: User = Depends(admin_only),
):
    if await User.find_one(User.username == payload.username):
        raise HTTPException(status_code=409, detail="Username sudah digunakan.")

    if await User.find_one(User.email == payload.email):
        raise HTTPException(status_code=409, detail="Email sudah digunakan.")

    member_id = await validate_member_link(payload.role, payload.memberId)

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        role=payload.role,
        memberId=member_id,
    )
    await user.insert()

    await log_audit(
        action=AuditAction.CREATE,
        module=AuditModule.USER,
        description=f"Membuat pengguna {user.username} ({user.role.value})",
        user=current_user,
        reference_id=str(user.id),
        ip_address=client_ip(request),
    )

    return to_response(user)


@router.get("", response_model=list[UserResponse])
async def list_users(
    search: str | None = Query(default=None),
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    pagination: PageParams = Depends(Pagination()),
    current_user: User = Depends(admin_only),
):
    query: dict = {}
    if search and search.strip():
        regex = search_regex(search)
        query["$or"] = [{"username": regex}, {"name": regex}, {"email": regex}]
    if role:
        query["role"] = role.value
    if is_active is not None:
        query["is_active"] = is_active

    users = await pagination.apply(User.find(query).sort("name"))
    return [to_response(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user: User = Depends(admin_only)):
    return to_response(await get_user_or_404(user_id))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    request: Request,
    current_user: User = Depends(admin_only),
):
    user = await get_user_or_404(user_id)

    if await User.find_one({"email": payload.email, "_id": {"$ne": user.id}}):
        raise HTTPException(status_code=409, detail="Email sudah digunakan.")

    if user.id == current_user.id and (
        not payload.is_active or payload.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=409,
            detail="Anda tidak dapat menonaktifkan atau menurunkan role akun sendiri.",
        )

    if payload.role != UserRole.ADMIN or not payload.is_active:
        await ensure_not_last_admin(user)

    member_id = await validate_member_link(payload.role, payload.memberId, user.id)

    changes = []
    if user.role != payload.role:
        changes.append(f"role {user.role.value} -> {payload.role.value}")
    if user.is_active != payload.is_active:
        changes.append("aktif" if payload.is_active else "nonaktif")

    role_or_status_changed = user.role != payload.role or (
        user.is_active and not payload.is_active
    )

    user.email = payload.email
    user.name = payload.name
    user.role = payload.role
    user.is_active = payload.is_active
    user.memberId = member_id
    if role_or_status_changed:
        # Paksa login ulang agar hak akses baru langsung berlaku.
        user.tokenVersion += 1
    user.updatedAt = utc_now()
    await user.save()

    await log_audit(
        action=AuditAction.UPDATE,
        module=AuditModule.USER,
        description=f"Mengubah pengguna {user.username}"
        + (f" ({', '.join(changes)})" if changes else ""),
        user=current_user,
        reference_id=str(user.id),
        ip_address=client_ip(request),
    )

    return to_response(user)


@router.delete("/{user_id}", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(admin_only),
):
    """Pengguna tidak dihapus permanen agar jejak audit tetap utuh."""
    user = await get_user_or_404(user_id)

    if user.id == current_user.id:
        raise HTTPException(status_code=409, detail="Anda tidak dapat menonaktifkan akun sendiri.")

    await ensure_not_last_admin(user)

    user.is_active = False
    user.tokenVersion += 1
    user.updatedAt = utc_now()
    await user.save()

    await log_audit(
        action=AuditAction.DELETE,
        module=AuditModule.USER,
        description=f"Menonaktifkan pengguna {user.username}",
        user=current_user,
        reference_id=str(user.id),
        ip_address=client_ip(request),
    )

    return to_response(user)


@router.post("/{user_id}/reset-password", response_model=UserResponse)
async def reset_password(
    user_id: str,
    payload: ResetPasswordRequest,
    request: Request,
    current_user: User = Depends(admin_only),
):
    """Reset password oleh admin (PRD §8). Semua sesi user tsb diakhiri."""
    user = await get_user_or_404(user_id)

    user.password_hash = hash_password(payload.new_password)
    user.tokenVersion += 1
    user.updatedAt = utc_now()
    await user.save()

    await log_audit(
        action=AuditAction.PASSWORD_RESET,
        module=AuditModule.USER,
        description=f"Reset password pengguna {user.username}",
        user=current_user,
        reference_id=str(user.id),
        ip_address=client_ip(request),
    )

    return to_response(user)
