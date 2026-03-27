from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.user_preference import UserPreferredCategory
from app.schemas.user_preference import UserPreference


class UserPreferenceCRUD:
    async def get(self, db: AsyncSession, user_id: int) -> Optional[UserPreference]:
        result = await db.execute(
            select(UserPreferredCategory.category_id)
            .where(UserPreferredCategory.user_id == user_id)
            .order_by(UserPreferredCategory.category_id.asc())
        )
        category_ids = [row[0] for row in result.all()]
        if not category_ids:
            return None

        return UserPreference(
            user_id=user_id,
            preferred_category_ids=category_ids,
        )

    async def get_or_create(self, db: AsyncSession, user_id: int) -> UserPreference:
        preference = await self.get(db, user_id)
        if preference:
            return preference

        return UserPreference(
            user_id=user_id,
            preferred_category_ids=[],
        )

    async def update_preferred_category_ids(
        self,
        db: AsyncSession,
        user_id: int,
        preferred_category_ids: list[int],
    ) -> UserPreference:
        normalized_ids = sorted({int(category_id) for category_id in preferred_category_ids})

        await db.execute(
            delete(UserPreferredCategory).where(UserPreferredCategory.user_id == user_id)
        )

        for category_id in normalized_ids:
            db.add(UserPreferredCategory(user_id=user_id, category_id=category_id))

        await db.commit()

        return UserPreference(
            user_id=user_id,
            preferred_category_ids=normalized_ids,
        )

    async def get_preferred_categories(self, db: AsyncSession, user_id: int) -> list[Category]:
        result = await db.execute(
            select(Category)
            .join(UserPreferredCategory, UserPreferredCategory.category_id == Category.id)
            .where(UserPreferredCategory.user_id == user_id)
            .order_by(Category.id.asc())
        )
        return result.scalars().all()


user_preference_crud = UserPreferenceCRUD()
