from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.crud.user_list import user_list_crud


class UserCRUD:
    async def get(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, user_create: UserCreate) -> User:
        """Create new user"""
        hashed_password = get_password_hash(user_create.password)
        
        db_user = User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=hashed_password,
            city=user_create.city,
            nickname=user_create.nickname,
            bio=user_create.bio,
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        # Create default liked/disliked lists for the new user
        await user_list_crud.create_default_lists(db, db_user.id)
        
        return db_user

    async def update(self, db: AsyncSession, user: User, user_update: UserUpdate) -> User:
        """Update user"""
        update_data = user_update.dict(exclude_unset=True)
        
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        return user

    async def authenticate(self, db: AsyncSession, password: str, username:str = None, email: str = None) -> Optional[User]:
        """Authenticate user"""
        if not username and not email:
            raise ValueError("Username or email must be provided")
        if email:
            user = await self.get_by_email(db, email)
        else:
            user = await self.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def is_active(self, user: User) -> bool:
        """Check if user is active"""
        return user.is_active

    async def deactivate(self, db: AsyncSession, user: User) -> User:
        """Deactivate user"""
        user.is_active = False
        await db.commit()
        await db.refresh(user)
        return user


user_crud = UserCRUD()
