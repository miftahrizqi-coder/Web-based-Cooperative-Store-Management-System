import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.core.deps import ADMIN, STAFF, client_ip, require_role
from app.core.utils import Pagination, PageParams, parse_object_id, search_regex, utc_now
from app.models.audit_log import AuditAction, AuditModule
from app.models.member import Member, MemberStatus
from app.models.sales import Sale, SaleStatus
from app.models.user import User, UserRole
from app.schemas.member import (
    MemberCreateRequest,
    MemberResponse,
    MemberStatsResponse,
    MemberUpdateRequest,
)
from app.schemas.sales import SaleResponse
from app.services.audit import log_audit
from app.services.sales import build_sale_responses, get_sale_or_404


router = APIRouter(prefix="/api/members", tags=["Members"])


def to_response(member: Member) -> MemberResponse:
    return MemberResponse(
        id=str(member.id),
        memberNumber=member.memberNumber,
        name=member.name,
        phone=member.phone,
        email=member.email,
        address=member.address,
        joinedAt=member.joinedAt,
        status=member.status,
        createdAt=member.createdAt,
        updatedAt=member.updatedAt,
    )


async def member_stats(member: Member) -> MemberStatsResponse:
    """Total belanja = penjualan COMPLETED dikurangi nilai retur (PRD §22)."""
    member_id = str(member.id)
    sales = await Sale.find(
        {"memberId": member_id, "status": SaleStatus.COMPLETED.value}
    ).sort("-createdAt").to_list()

    total = 0.0
    for sale in sales:
        returned = sum(
            (item.returnedQuantity * item.price) for item in sale.items
        )
        # Diskon dialokasikan proporsional terhadap nilai item yang diretur.
        ratio = (sale.total / sale.subtotal) if sale.subtotal else 1
        total += sale.total - returned * ratio

    return MemberStatsResponse(
        **to_response(member).model_dump(),
        transactionCount=len(sales),
        totalSpending=round(total, 2),
        lastTransactionAt=sales[0].createdAt if sales else None,
        hasUserAccount=bool(await User.find_one({"memberId": member_id})),
    )


async def get_member_or_404(member_id: str) -> Member:
    member = await Member.get(parse_object_id(member_id, "ID anggota"))
    if member is None:
        raise HTTPException(status_code=404, detail="Anggota tidak ditemukan.")
    return member


async def ensure_unique_member_number(member_number: str, exclude_id=None) -> None:
    query: dict = {"memberNumber": member_number}
    if exclude_id is not None:
        query["_id"] = {"$ne": exclude_id}
    if await Member.find_one(query):
        raise HTTPException(status_code=409, detail="Nomor anggota sudah digunakan.")


async def generate_member_number() -> str:
    """KOP-001, KOP-002, ... mengikuti nomor terbesar yang sudah ada."""
    highest = 0
    async for doc in Member.get_pymongo_collection().find(
        {"memberNumber": {"$regex": r"^KOP-\d+$"}}, {"memberNumber": 1}
    ):
        match = re.match(r"^KOP-(\d+)$", doc["memberNumber"])
        if match:
            highest = max(highest, int(match.group(1)))

    candidate = highest + 1
    while await Member.find_one({"memberNumber": f"KOP-{candidate:03d}"}):
        candidate += 1
    return f"KOP-{candidate:03d}"


async def get_own_member(current_user: User) -> Member:
    if not current_user.memberId:
        raise HTTPException(
            status_code=404,
            detail="Akun Anda belum ditautkan ke data anggota. Hubungi admin.",
        )
    return await get_member_or_404(current_user.memberId)


# ---------------------------------------------------------------------------
# Self-service anggota (PRD §6.4)
# ---------------------------------------------------------------------------


@router.get("/me", response_model=MemberStatsResponse)
async def get_my_profile(
    current_user: User = Depends(require_role(UserRole.ANGGOTA)),
):
    return await member_stats(await get_own_member(current_user))


@router.get("/me/transactions", response_model=list[SaleResponse])
async def get_my_transactions(
    pagination: PageParams = Depends(Pagination(default_page_size=20)),
    current_user: User = Depends(require_role(UserRole.ANGGOTA)),
):
    member = await get_own_member(current_user)
    sales = await pagination.apply(
        Sale.find({"memberId": str(member.id)}).sort("-createdAt")
    )
    return await build_sale_responses(sales, current_user)


@router.get("/me/transactions/{sale_id}", response_model=SaleResponse)
async def get_my_transaction(
    sale_id: str,
    current_user: User = Depends(require_role(UserRole.ANGGOTA)),
):
    member = await get_own_member(current_user)
    sale = await get_sale_or_404(sale_id)
    if sale.memberId != str(member.id):
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan.")
    return (await build_sale_responses([sale], current_user))[0]


# ---------------------------------------------------------------------------
# Manajemen anggota
# ---------------------------------------------------------------------------


@router.get("", response_model=list[MemberResponse])
async def list_members(
    search: str | None = Query(default=None),
    status_filter: MemberStatus | None = Query(default=None, alias="status"),
    pagination: PageParams = Depends(Pagination()),
    current_user: User = Depends(require_role(*STAFF)),
):
    query: dict = {}

    if search and search.strip():
        regex = search_regex(search)
        query["$or"] = [{"memberNumber": regex}, {"name": regex}, {"phone": regex}]

    # Kasir memilih anggota di POS: hanya anggota aktif.
    if current_user.role == UserRole.KASIR:
        query["status"] = MemberStatus.ACTIVE.value
    elif status_filter:
        query["status"] = status_filter.value

    members = await pagination.apply(Member.find(query).sort("name"))
    return [to_response(m) for m in members]


@router.get("/{member_id}", response_model=MemberStatsResponse)
async def get_member(
    member_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PENGURUS)),
):
    return await member_stats(await get_member_or_404(member_id))


@router.get("/{member_id}/transactions", response_model=list[SaleResponse])
async def get_member_transactions(
    member_id: str,
    pagination: PageParams = Depends(Pagination(default_page_size=20)),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.PENGURUS)),
):
    await get_member_or_404(member_id)
    sales = await pagination.apply(Sale.find({"memberId": member_id}).sort("-createdAt"))
    return await build_sale_responses(sales, current_user)


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(
    data: MemberCreateRequest,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN)),
):
    member_number = (data.memberNumber or "").strip() or await generate_member_number()
    await ensure_unique_member_number(member_number)

    now = utc_now()
    member = Member(
        memberNumber=member_number,
        name=data.name.strip(),
        phone=data.phone.strip(),
        email=data.email,
        address=data.address,
        joinedAt=data.joinedAt or now,
        status=data.status,
        createdAt=now,
        updatedAt=now,
    )
    await member.insert()

    await log_audit(
        action=AuditAction.CREATE,
        module=AuditModule.MEMBER,
        description=f"Menambah anggota {member.memberNumber} - {member.name}",
        user=current_user,
        reference_id=str(member.id),
        ip_address=client_ip(request),
    )
    return to_response(member)


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: str,
    data: MemberUpdateRequest,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN)),
):
    member = await get_member_or_404(member_id)
    member_number = data.memberNumber.strip()
    await ensure_unique_member_number(member_number, exclude_id=member.id)

    old_status = member.status
    member.memberNumber = member_number
    member.name = data.name.strip()
    member.phone = data.phone.strip()
    member.email = data.email
    member.address = data.address
    member.joinedAt = data.joinedAt
    member.status = data.status
    member.updatedAt = utc_now()
    await member.save()

    await log_audit(
        action=AuditAction.UPDATE,
        module=AuditModule.MEMBER,
        description=(
            f"Mengubah anggota {member.memberNumber}"
            + (f" (status {old_status.value} -> {member.status.value})" if old_status != member.status else "")
        ),
        user=current_user,
        reference_id=str(member.id),
        ip_address=client_ip(request),
    )
    return to_response(member)


@router.delete("/{member_id}", response_model=MemberResponse)
async def deactivate_member(
    member_id: str,
    request: Request,
    current_user: User = Depends(require_role(*ADMIN)),
):
    """Anggota dinonaktifkan, tidak dihapus (direferensikan transaksi)."""
    member = await get_member_or_404(member_id)
    member.status = MemberStatus.INACTIVE
    member.updatedAt = utc_now()
    await member.save()

    await log_audit(
        action=AuditAction.DELETE,
        module=AuditModule.MEMBER,
        description=f"Menonaktifkan anggota {member.memberNumber}",
        user=current_user,
        reference_id=str(member.id),
        ip_address=client_ip(request),
    )
    return to_response(member)
