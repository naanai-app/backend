from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.crud.user_preference import user_preference_crud
from app.models.user import User as UserModel
from app.schemas.user_preference import UserPreferenceUpdate, UserPreferredCategoriesResponse

router = APIRouter()


@router.get("/me", response_model=UserPreferredCategoriesResponse)
async def get_my_preferences(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """Get current user's saved preferred category IDs."""
    await user_preference_crud.get_or_create(db, current_user.id)
    categories = await user_preference_crud.get_preferred_categories(db, current_user.id)
    return {
        "preferred_categories": categories,
    }


@router.put("/me", response_model=UserPreferredCategoriesResponse)
async def update_my_preferences(
    *,
    db: AsyncSession = Depends(get_db),
    preference_in: UserPreferenceUpdate,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """Update current user's preferred category IDs."""
    await user_preference_crud.update_preferred_category_ids(
        db,
        current_user.id,
        preference_in.preferred_category_ids,
    )
    categories = await user_preference_crud.get_preferred_categories(db, current_user.id)
    return {
        "preferred_categories": categories,
    }
