from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.category import Category
from app.schemas.place import CategoryCreate, CategoryUpdate


class CategoryCRUD:
    async def get(self, db: AsyncSession, category_id: int) -> Optional[Category]:
        """Get category by ID"""
        result = await db.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def get_by_title(self, db: AsyncSession, title: str) -> Optional[Category]:
        """Get category by title"""
        result = await db.execute(select(Category).where(Category.title == title))
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Category]:
        """Get multiple categories"""
        result = await db.execute(
            select(Category).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, category_create: CategoryCreate) -> Category:
        """Create new category"""
        db_category = Category(**category_create.dict())
        db.add(db_category)
        await db.commit()
        await db.refresh(db_category)
        return db_category

    async def update(self, db: AsyncSession, category: Category, category_update: CategoryUpdate) -> Category:
        """Update category"""
        update_data = category_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(category, field, value)
        
        await db.commit()
        await db.refresh(category)
        return category

    async def delete(self, db: AsyncSession, category_id: int) -> bool:
        """Delete category"""
        category = await self.get(db, category_id)
        if category:
            await db.delete(category)
            await db.commit()
            return True
        return False


category_crud = CategoryCRUD()
