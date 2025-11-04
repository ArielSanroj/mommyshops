"""
User personalization profile endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database.models import User
from app.dependencies import get_database, require_auth
from app.schemas.profile import UserProfileCreate, UserProfileResponse

router = APIRouter(prefix="/profile", tags=["profile"])


def _user_to_profile(user: User) -> UserProfileResponse:
    return UserProfileResponse(
        skin_type=user.skin_face,
        hair_type=user.hair_type,
        face_shape=getattr(user, "face_shape", None),
        skin_concerns=user.goals_face or [],
        hair_concerns=user.goals_hair or [],
        overall_goals=user.conditions or [],
        updated_at=user.updated_at,
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(require_auth),
) -> UserProfileResponse:
    """
    Retrieve the personalization profile for the authenticated user.
    """
    return _user_to_profile(current_user)


@router.put("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def upsert_my_profile(
    payload: UserProfileCreate,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_database),
) -> UserProfileResponse:
    """
    Create or update the personalization profile for the authenticated user.
    """
    current_user.skin_face = payload.skin_type
    current_user.hair_type = payload.hair_type
    setattr(current_user, "face_shape", payload.face_shape)
    current_user.goals_face = payload.skin_concerns or []
    current_user.goals_hair = payload.hair_concerns or []
    current_user.conditions = payload.overall_goals or []

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return _user_to_profile(current_user)
