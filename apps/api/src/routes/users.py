"""
User routes for authenticated user operations.
Includes profile retrieval and updates.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.dependencies import get_current_user
from src.schemas.user import UserResponse, UserUpdate
from src.models.user import User
from src.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Get authenticated user's profile information. Requires valid JWT token."
)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.

    **Authentication Required:** JWT token in Authorization header.

    Returns complete user profile including onboarding data.
    """
    return UserResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update authenticated user's profile and onboarding data. Requires valid JWT token."
)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current authenticated user's profile.

    **Authentication Required:** JWT token in Authorization header.

    Allows updating onboarding fields:
    - exam_date
    - target_score
    - daily_study_time
    - knowledge_level
    - motivation
    - referral_source
    - dark_mode

    Returns updated user profile.
    """
    # Update user fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    # Invalidate user cache so subsequent requests get fresh data
    try:
        from src.db.redis_client import get_redis
        redis = await get_redis()
        cache_key = f"user_cache:{str(current_user.id)}"
        await redis.delete(cache_key)
    except Exception:
        # Cache invalidation failure is not critical
        pass

    return UserResponse.model_validate(current_user)
