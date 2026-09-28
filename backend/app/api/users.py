from fastapi import APIRouter, HTTPException, status

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreateRequest, UserResponse


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