from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.models.user_list import UserList, UserListItem, ListVisibility
from app.models.place import Place, PlaceCategory
from app.schemas.user_list import UserListCreate, UserListUpdate, UserListItemCreate, UserListItemUpdate


class UserListCRUD:
    async def get(self, db: AsyncSession, list_id: int) -> Optional[UserList]:
        """Get user list by ID with items"""
        result = await db.execute(
            select(UserList)
            .options(
                selectinload(UserList.items).selectinload(UserListItem.place)
                .selectinload(Place.categories).selectinload(PlaceCategory.category)
            )
            .where(UserList.id == list_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(
        self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[UserList]:
        """Get user lists by user ID"""
        result = await db.execute(
            select(UserList)
            .options(
                selectinload(UserList.items).selectinload(UserListItem.place)
                .selectinload(Place.categories).selectinload(PlaceCategory.category)
            )
            .where(UserList.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_default_list(self, db: AsyncSession, user_id: int, list_type: str) -> Optional[UserList]:
        """Get default list by type (liked/disliked)"""
        result = await db.execute(
            select(UserList).where(
                and_(
                    UserList.user_id == user_id,
                    UserList.list_type == list_type,
                    UserList.is_default == True
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, list_create: UserListCreate, user_id: int) -> UserList:
        """Create new user list"""
        db_list = UserList(**list_create.dict(), user_id=user_id)
        db.add(db_list)
        await db.commit()
        await db.refresh(db_list)
        return await self.get(db, db_list.id)

    async def update(self, db: AsyncSession, user_list: UserList, list_update: UserListUpdate) -> UserList:
        """Update user list"""
        update_data = list_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(user_list, field, value)
        
        await db.commit()
        await db.refresh(user_list)
        return await self.get(db, user_list.id)

    async def delete(self, db: AsyncSession, user_list: UserList) -> bool:
        """Delete user list"""
        if user_list.is_default:
            return False  # Cannot delete default lists
        
        await db.delete(user_list)
        await db.commit()
        return True

    async def create_default_lists(self, db: AsyncSession, user_id: int) -> List[UserList]:
        """Create default liked and disliked lists for a new user"""
        default_lists = []
        
        # Create liked places list
        liked_list = UserList(
            name="Liked Places",
            description="Places I like and recommend",
            user_id=user_id,
            is_default=True,
            list_type="liked",
            visibility=ListVisibility.PRIVATE
        )
        db.add(liked_list)
        default_lists.append(liked_list)
        
        # Create disliked places list
        disliked_list = UserList(
            name="Disliked Places",
            description="Places I don't recommend",
            user_id=user_id,
            is_default=True,
            list_type="disliked",
            visibility=ListVisibility.PRIVATE
        )
        db.add(disliked_list)
        default_lists.append(disliked_list)
        
        await db.commit()
        for list_item in default_lists:
            await db.refresh(list_item)
        
        return default_lists


class UserListItemCRUD:
    async def get(self, db: AsyncSession, item_id: int) -> Optional[UserListItem]:
        """Get list item by ID"""
        result = await db.execute(
            select(UserListItem)
            .options(
                selectinload(UserListItem.place)
                .selectinload(Place.categories).selectinload(PlaceCategory.category)
            )
            .where(UserListItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def get_by_list(
        self, db: AsyncSession, list_id: int, skip: int = 0, limit: int = 100
    ) -> List[UserListItem]:
        """Get items in a list"""
        result = await db.execute(
            select(UserListItem)
            .options(
                selectinload(UserListItem.place)
                .selectinload(Place.categories).selectinload(PlaceCategory.category)
            )
            .where(UserListItem.list_id == list_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def add_to_list(self, db: AsyncSession, list_id: int, item_create: UserListItemCreate) -> UserListItem:
        """Add place to user list"""
        # Check if place already exists in list
        result = await db.execute(
            select(UserListItem).where(
                UserListItem.list_id == list_id,
                UserListItem.place_id == item_create.place_id
            )
        )
        existing_item = result.scalar_one_or_none()
        
        if existing_item:
            # Update existing item
            existing_item.rating = item_create.rating
            await db.commit()
            await db.refresh(existing_item)
            return existing_item
        
        # Create new item
        db_item = UserListItem(
            list_id=list_id,
            **item_create.dict()
        )
        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        return db_item

    async def update(self, db: AsyncSession, item: UserListItem, item_update: UserListItemUpdate) -> UserListItem:
        """Update list item"""
        update_data = item_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(item, field, value)
        
        await db.commit()
        await db.refresh(item)
        return item

    async def remove_from_list(self, db: AsyncSession, item: UserListItem) -> bool:
        """Remove item from list"""
        await db.delete(item)
        await db.commit()
        return True

    async def quick_add_to_default_list(
        self, db: AsyncSession, user_id: int, place_id: int, list_type: str, rating: Optional[int] = None
    ) -> Optional[UserListItem]:
        """Quick add place to default liked/disliked list"""
        # Get the default list
        result = await db.execute(
            select(UserList).where(
                and_(
                    UserList.user_id == user_id,
                    UserList.list_type == list_type,
                    UserList.is_default == True
                )
            )
        )
        default_list = result.scalar_one_or_none()
        
        if not default_list:
            return None
        
        item_create = UserListItemCreate(place_id=place_id, rating=rating)
        return await self.add_to_list(db, default_list.id, item_create)


user_list_crud = UserListCRUD()
user_list_item_crud = UserListItemCRUD()
