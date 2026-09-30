from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.permissions import require_role
from app.models.member import Member, MemberStatus
from app.models.user import User, UserRole
from app.schemas.member import (
    MemberCreateRequest,
    MemberResponse,
    MemberUpdateRequest,
)


router = APIRouter(
    prefix="/api/members",
    tags=["Members"],
)


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


async def ensure_unique_member_number(
    member_number: str,
    exclude_id: ObjectId | None = None,
) -> None:
    query: dict = {
        "memberNumber": member_number,
    }

    if exclude_id is not None:
        query["_id"] = {"$ne": exclude_id}

    existing = await Member.find_one(query)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nomor anggota sudah digunakan.",
        )


@router.get(
    "",
    response_model=list[MemberResponse],
)
async def list_members(
    search: str | None = Query(default=None),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.KASIR,
        )
    ),
):
    query: dict = {}

    if search:
        query["$or"] = [
            {
                "memberNumber": {
                    "$regex": search,
                    "$options": "i",
                }
            },
            {
                "name": {
                    "$regex": search,
                    "$options": "i",
                }
            },
            {
                "phone": {
                    "$regex": search,
                    "$options": "i",
                }
            },
        ]

    members = await Member.find(query).to_list()

    return [
        to_response(member)
        for member in members
    ]


@router.get(
    "/{member_id}",
    response_model=MemberResponse,
)
async def get_member(
    member_id: str,
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.KASIR,
        )
    ),
):
    if not ObjectId.is_valid(member_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID anggota tidak valid.",
        )

    member = await Member.get(ObjectId(member_id))

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anggota tidak ditemukan.",
        )

    return to_response(member)


@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_member(
    data: MemberCreateRequest,
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    await ensure_unique_member_number(
        member_number=data.memberNumber,
    )

    now = datetime.now(timezone.utc)

    member = Member(
        memberNumber=data.memberNumber,
        name=data.name,
        phone=data.phone,
        email=data.email,
        address=data.address,
        joinedAt=data.joinedAt or now,
        status=data.status,
        createdAt=now,
        updatedAt=now,
    )

    await member.insert()

    return to_response(member)


@router.put(
    "/{member_id}",
    response_model=MemberResponse,
)
async def update_member(
    member_id: str,
    data: MemberUpdateRequest,
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    if not ObjectId.is_valid(member_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID anggota tidak valid.",
        )

    member = await Member.get(ObjectId(member_id))

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anggota tidak ditemukan.",
        )

    await ensure_unique_member_number(
        member_number=data.memberNumber,
        exclude_id=member.id,
    )

    member.memberNumber = data.memberNumber
    member.name = data.name
    member.phone = data.phone
    member.email = data.email
    member.address = data.address
    member.joinedAt = data.joinedAt
    member.status = data.status
    member.updatedAt = datetime.now(timezone.utc)

    await member.save()

    return to_response(member)


@router.delete(
    "/{member_id}",
    response_model=MemberResponse,
)
async def deactivate_member(
    member_id: str,
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    if not ObjectId.is_valid(member_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID anggota tidak valid.",
        )

    member = await Member.get(ObjectId(member_id))

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anggota tidak ditemukan.",
        )

    member.status = MemberStatus.INACTIVE
    member.updatedAt = datetime.now(timezone.utc)

    await member.save()

    return to_response(member)