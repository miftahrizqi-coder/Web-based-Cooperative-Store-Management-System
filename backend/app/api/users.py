from fastapi import APIRouter, HTTPException, status
from beanie import PydanticObjectId

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreateRequest, UserResponse, UserUpdateRequest


router = APIRouter(prefix="/api/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(payload: UserCreateRequest):
    existing_username = await User.find_one(
        User.username == payload.username
    )

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    existing_email = await User.find_one(
        User.email == payload.email
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        role=payload.role,
    )

    await user.insert()

    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
    )

@router.get("", response_model=list[UserResponse])
async def get_users():
    users = await User.find_all().to_list()

    return [
        UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            name=user.name,
            role=user.role.value,
            is_active=user.is_active,
        )
        for user in users
    ]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: PydanticObjectId):
    user = await User.get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
    )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: PydanticObjectId,
    payload: UserUpdateRequest,
):
    user = await User.get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    existing_email = await User.find_one(
        User.email == payload.email,
        User.id != user_id,
    )

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    user.email = payload.email
    user.name = payload.name
    user.role = payload.role
    user.is_active = payload.is_active

    await user.save()

    return UserResponse(
        id=str(user.id),
        username=user.username,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
    )

@router.delete("/{user_id}")
async def delete_user(user_id: PydanticObjectId):
    user = await User.get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_active = False
    await user.save()

    return {"message": "User deactivated successfully"}