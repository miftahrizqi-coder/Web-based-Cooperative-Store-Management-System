from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.security import create_access_token,hash_password,verify_password
from app.models.user import User
from app.core.config import settings

import jwt


router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginUserResponse(BaseModel):
    id: str
    name: str
    role: str


class LoginResponse(BaseModel):
    user: LoginUserResponse
    token: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    user = await User.find_one(
        User.username == payload.username
    )

    if user is None or not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    token = create_access_token(str(user.id))

    return LoginResponse(
        user=LoginUserResponse(
            id=str(user.id),
            name=user.name,
            role=user.role.value,
        ),
        token=token,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user = await User.get(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user

@router.get("/me", response_model=LoginUserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return LoginUserResponse(
        id=str(current_user.id),
        name=current_user.name,
        role=current_user.role.value,
    )

@router.post("/logout")
async def logout():
    return {"message": "Logout successful"}

@router.put("/password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
):
    if not verify_password(
        payload.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    current_user.password_hash = hash_password(payload.new_password)
    await current_user.save()

    return {"message": "Password changed successfully"}