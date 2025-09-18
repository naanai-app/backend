from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload

from app.models.check_in import CheckIn, Comment, CheckInLike
from app.models.place import Place, PlaceCategory
from app.schemas.check_in import CheckInCreate, CheckInUpdate, CommentCreate, CommentUpdate, CheckIn as CheckInSchema
from app.schemas.place import Place as PlaceSchema


def _prepare_check_in_for_response(check_in: CheckIn) -> CheckInSchema:
    """Prepare check-in object for Pydantic serialization by extracting place categories"""
    # Handle place with categories
    place_schema = None
    if hasattr(check_in, 'place') and check_in.place:
        # Extract actual Category objects from PlaceCategory relationships
        categories = []
        if hasattr(check_in.place, 'categories') and check_in.place.categories:
            for place_category in check_in.place.categories:
                if hasattr(place_category, 'category') and place_category.category:
                    categories.append(place_category.category)
        
        place_schema = PlaceSchema(
            id=check_in.place.id,
            title=check_in.place.title,
            description=check_in.place.description,
            city=check_in.place.city,
            address=check_in.place.address,
            latitude=check_in.place.latitude,
            longitude=check_in.place.longitude,
            google_place_id=check_in.place.google_place_id,
            phone=check_in.place.phone,
            website=check_in.place.website,
            price_level=check_in.place.price_level,
            image_url=check_in.place.image_url,
            rating=check_in.place.rating,
            created_at=check_in.place.created_at,
            updated_at=check_in.place.updated_at,
            categories=categories
        )
    
    # Create CheckIn Pydantic model
    return CheckInSchema(
        id=check_in.id,
        content=check_in.content,
        image_url=check_in.image_url,
        author_id=check_in.author_id,
        place_id=check_in.place_id,
        author=check_in.author,
        place=place_schema,
        is_active=check_in.is_active,
        created_at=check_in.created_at,
        updated_at=check_in.updated_at,
        comments=check_in.comments if hasattr(check_in, 'comments') else [],
        likes=check_in.likes if hasattr(check_in, 'likes') else [],
        likes_count=len(check_in.likes) if hasattr(check_in, 'likes') else 0,
        comments_count=len(check_in.comments) if hasattr(check_in, 'comments') else 0,
        is_liked_by_user=False  # This would need user context to determine
    )


class CheckInCRUD:
    async def get(self, db: AsyncSession, check_in_id: int) -> Optional[CheckInSchema]:
        """Get check-in by ID with all relationships"""
        result = await db.execute(
            select(CheckIn)
            .options(
                selectinload(CheckIn.author),
                selectinload(CheckIn.place).selectinload(Place.categories).selectinload(PlaceCategory.category),
                selectinload(CheckIn.comments).selectinload(Comment.author),
                selectinload(CheckIn.likes).selectinload(CheckInLike.user)
            )
            .where(CheckIn.id == check_in_id)
        )
        check_in = result.scalar_one_or_none()
        return _prepare_check_in_for_response(check_in) if check_in else None

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[CheckInSchema]:
        """Get multiple check-ins ordered by creation date"""
        result = await db.execute(
            select(CheckIn)
            .options(
                selectinload(CheckIn.author),
                selectinload(CheckIn.place).selectinload(Place.categories).selectinload(PlaceCategory.category),
                selectinload(CheckIn.comments).selectinload(Comment.author),
                selectinload(CheckIn.likes)
            )
            .where(CheckIn.is_active == True)
            .order_by(desc(CheckIn.created_at))
            .offset(skip)
            .limit(limit)
        )
        check_ins = result.scalars().all()
        return [_prepare_check_in_for_response(check_in) for check_in in check_ins]

    async def get_by_user(
        self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[CheckInSchema]:
        """Get check-ins by user"""
        result = await db.execute(
            select(CheckIn)
            .options(
                selectinload(CheckIn.author),
                selectinload(CheckIn.place).selectinload(Place.categories).selectinload(PlaceCategory.category),
                selectinload(CheckIn.comments).selectinload(Comment.author),
                selectinload(CheckIn.likes)
            )
            .where(and_(CheckIn.author_id == user_id, CheckIn.is_active == True))
            .order_by(desc(CheckIn.created_at))
            .offset(skip)
            .limit(limit)
        )
        check_ins = result.scalars().all()
        return [_prepare_check_in_for_response(check_in) for check_in in check_ins]

    async def create(self, db: AsyncSession, check_in_create: CheckInCreate, author_id: int) -> CheckInSchema:
        """Create new check-in"""
        db_check_in = CheckIn(**check_in_create.dict(), author_id=author_id)
        db.add(db_check_in)
        await db.commit()
        await db.refresh(db_check_in)
        return await self.get(db, db_check_in.id)

    async def update(self, db: AsyncSession, check_in: CheckIn, check_in_update: CheckInUpdate) -> CheckInSchema:
        """Update check-in"""
        update_data = check_in_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(check_in, field, value)
        
        await db.commit()
        await db.refresh(check_in)
        return await self.get(db, check_in.id)

    async def delete(self, db: AsyncSession, check_in: CheckIn) -> CheckIn:
        """Soft delete check-in"""
        check_in.is_active = False
        await db.commit()
        await db.refresh(check_in)
        return check_in

    async def like_check_in(self, db: AsyncSession, check_in_id: int, user_id: int) -> bool:
        """Like a check-in"""
        # Check if already liked
        result = await db.execute(
            select(CheckInLike).where(
                and_(CheckInLike.check_in_id == check_in_id, CheckInLike.user_id == user_id)
            )
        )
        existing_like = result.scalar_one_or_none()
        
        if existing_like:
            return False  # Already liked
        
        like = CheckInLike(check_in_id=check_in_id, user_id=user_id)
        db.add(like)
        await db.commit()
        return True

    async def unlike_check_in(self, db: AsyncSession, check_in_id: int, user_id: int) -> bool:
        """Unlike a check-in"""
        result = await db.execute(
            select(CheckInLike).where(
                and_(CheckInLike.check_in_id == check_in_id, CheckInLike.user_id == user_id)
            )
        )
        like = result.scalar_one_or_none()
        
        if not like:
            return False  # Not liked
        
        await db.delete(like)
        await db.commit()
        return True


class CommentCRUD:
    async def get(self, db: AsyncSession, comment_id: int) -> Optional[Comment]:
        """Get comment by ID"""
        result = await db.execute(
            select(Comment)
            .options(selectinload(Comment.author))
            .where(Comment.id == comment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_check_in(
        self, db: AsyncSession, check_in_id: int, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        """Get comments for a check-in"""
        result = await db.execute(
            select(Comment)
            .options(selectinload(Comment.author))
            .where(and_(Comment.check_in_id == check_in_id, Comment.is_active == True))
            .order_by(Comment.created_at)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, comment_create: CommentCreate, check_in_id: int, author_id: int) -> Comment:
        """Create new comment"""
        db_comment = Comment(**comment_create.dict(), check_in_id=check_in_id, author_id=author_id)
        db.add(db_comment)
        await db.commit()
        await db.refresh(db_comment)
        return await self.get(db, db_comment.id)

    async def update(self, db: AsyncSession, comment: Comment, comment_update: CommentUpdate) -> Comment:
        """Update comment"""
        update_data = comment_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(comment, field, value)
        
        await db.commit()
        await db.refresh(comment)
        return comment

    async def delete(self, db: AsyncSession, comment: Comment) -> Comment:
        """Soft delete comment"""
        comment.is_active = False
        await db.commit()
        await db.refresh(comment)
        return comment


check_in_crud = CheckInCRUD()
comment_crud = CommentCRUD()
