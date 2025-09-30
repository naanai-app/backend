from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.expression import exists, and_, literal

from app.models.check_in import CheckIn, Comment, CheckInLike
from app.models.place import Place, PlaceCategory
from app.schemas.check_in import CheckInCreate, CheckInUpdate, CommentCreate, CommentUpdate, CheckIn as CheckInSchema
from app.schemas.place import Place as PlaceSchema




class CheckInCRUD:
    async def get(self, db: AsyncSession, check_in_id: int, current_user_id: Optional[int] = None) -> Optional[CheckInSchema]:
        """Get check-in by ID with all relationships and like status"""
        # Base query with is_liked_by_user subquery
        query = (
            select(
                CheckIn,
                exists().where(
                    and_(
                        CheckInLike.check_in_id == CheckIn.id,
                        CheckInLike.user_id == current_user_id
                    )
                ).label('is_liked_by_user') if current_user_id else literal(False).label('is_liked_by_user')
            )
            .options(
                selectinload(CheckIn.author),
                selectinload(CheckIn.place).selectinload(Place.categories).selectinload(PlaceCategory.category),
                selectinload(CheckIn.comments).selectinload(Comment.author),
                selectinload(CheckIn.likes).selectinload(CheckInLike.user)
            )
            .where(CheckIn.id == check_in_id)
        )
        
        result = await db.execute(query)
        row = result.first()
        
        if not row:
            return None
            
        check_in = row[0]
        check_in.is_liked_by_user = row[1]
        return CheckInSchema.model_validate(check_in)

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100, current_user_id: Optional[int] = None
    ) -> List[CheckInSchema]:
        """Get multiple check-ins ordered by creation date with like status"""
        # Base query with is_liked_by_user subquery
        query = (
            select(
                CheckIn,
                exists().where(
                    and_(
                        CheckInLike.check_in_id == CheckIn.id,
                        CheckInLike.user_id == current_user_id
                    )
                ).label('is_liked_by_user') if current_user_id else literal(False).label('is_liked_by_user')
            )
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
        
        result = await db.execute(query)
        
        # Map the results to include the is_liked_by_user flag
        check_ins = []
        for row in result.all():
            check_in = row[0]
            check_in.is_liked_by_user = row[1]
            check_ins.append(CheckInSchema.model_validate(check_in))
            
        return check_ins

    async def get_by_user(
        self, db: AsyncSession, user_id: int, current_user_id: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> List[CheckInSchema]:
        """Get check-ins by user with like status"""
        # Base query with is_liked_by_user subquery
        query = (
            select(
                CheckIn,
                exists().where(
                    and_(
                        CheckInLike.check_in_id == CheckIn.id,
                        CheckInLike.user_id == current_user_id
                    )
                ).label('is_liked_by_user') if current_user_id else literal(False).label('is_liked_by_user')
            )
            .options(
                selectinload(CheckIn.author),
                selectinload(CheckIn.place).selectinload(Place.categories).selectinload(PlaceCategory.category),
                selectinload(CheckIn.comments).selectinload(Comment.author),
                selectinload(CheckIn.likes)
            )
            .where(CheckIn.author_id == user_id, CheckIn.is_active == True)
            .order_by(desc(CheckIn.created_at))
            .offset(skip)
            .limit(limit)
        )
        
        result = await db.execute(query)
        
        # Map the results to include the is_liked_by_user flag
        check_ins = []
        for row in result.all():
            check_in = row[0]
            check_in.is_liked_by_user = row[1]
            check_ins.append(CheckInSchema.model_validate(check_in))
            
        return check_ins

    async def create(self, db: AsyncSession, check_in_create: CheckInCreate, author_id: int) -> CheckInSchema:
        """Create new check-in"""
        db_check_in = CheckIn(**check_in_create.dict(), author_id=author_id)
        db.add(db_check_in)
        await db.commit()
        await db.refresh(db_check_in)
        return await self.get(db, db_check_in.id)

    async def update(self, db: AsyncSession, check_in_id: int, check_in_update: CheckInUpdate, current_user_id: int) -> CheckInSchema:
        """Update check-in"""
        # Get the SQLAlchemy model object
        result = await db.execute(select(CheckIn).where(CheckIn.id == check_in_id))
        check_in = result.scalar_one_or_none()
        if not check_in:
            raise ValueError(f"CheckIn with id {check_in_id} not found")
        
        update_data = check_in_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(check_in, field, value)
        
        await db.commit()
        await db.refresh(check_in)
        return await self.get(db, check_in.id, current_user_id=current_user_id)

    async def delete(self, db: AsyncSession, check_in_id: int) -> bool:
        """Delete check-in"""
        # Get the SQLAlchemy model object
        result = await db.execute(select(CheckIn).where(CheckIn.id == check_in_id))
        check_in = result.scalar_one_or_none()
        if not check_in:
            raise ValueError(f"CheckIn with id {check_in_id} not found")
        
        await db.delete(check_in)
        await db.commit()
        return True

    async def is_check_in_liked(self, db: AsyncSession, check_in_id: int, user_id: int) -> bool:
        """Is check-in liked by this user already"""

        result = await db.execute(
            select(CheckInLike).where(
                and_(CheckInLike.check_in_id == check_in_id, CheckInLike.user_id == user_id)
            )
        )
        existing_like = result.scalar_one_or_none()
        
        if existing_like:
            return True
        else:
            return False

    async def like_check_in(self, db: AsyncSession, check_in_id: int, user_id: int) -> bool:
        """Like a check-in"""
        # Check if already liked
        
        existing_like = await self.is_check_in_liked(db, check_in_id, user_id)

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
