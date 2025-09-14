from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload

from app.models.post import Post, Comment, PostLike
from app.models.place import Place
from app.schemas.post import PostCreate, PostUpdate, CommentCreate, CommentUpdate


class PostCRUD:
    async def get(self, db: AsyncSession, post_id: int) -> Optional[Post]:
        """Get post by ID with all relationships"""
        result = await db.execute(
            select(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.place).selectinload(Place.categories),
                selectinload(Post.comments).selectinload(Comment.author),
                selectinload(Post.likes).selectinload(PostLike.user)
            )
            .where(Post.id == post_id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        """Get multiple posts ordered by creation date"""
        result = await db.execute(
            select(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.place),
                selectinload(Post.comments).selectinload(Comment.author),
                selectinload(Post.likes)
            )
            .where(Post.is_active == True)
            .order_by(desc(Post.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_user(
        self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        """Get posts by user"""
        result = await db.execute(
            select(Post)
            .options(
                selectinload(Post.author),
                selectinload(Post.place),
                selectinload(Post.comments).selectinload(Comment.author),
                selectinload(Post.likes)
            )
            .where(and_(Post.author_id == user_id, Post.is_active == True))
            .order_by(desc(Post.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, post_create: PostCreate, author_id: int) -> Post:
        """Create new post"""
        db_post = Post(**post_create.dict(), author_id=author_id)
        db.add(db_post)
        await db.commit()
        await db.refresh(db_post)
        return await self.get(db, db_post.id)

    async def update(self, db: AsyncSession, post: Post, post_update: PostUpdate) -> Post:
        """Update post"""
        update_data = post_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(post, field, value)
        
        await db.commit()
        await db.refresh(post)
        return await self.get(db, post.id)

    async def delete(self, db: AsyncSession, post: Post) -> Post:
        """Soft delete post"""
        post.is_active = False
        await db.commit()
        await db.refresh(post)
        return post

    async def like_post(self, db: AsyncSession, post_id: int, user_id: int) -> bool:
        """Like a post"""
        # Check if already liked
        result = await db.execute(
            select(PostLike).where(
                and_(PostLike.post_id == post_id, PostLike.user_id == user_id)
            )
        )
        existing_like = result.scalar_one_or_none()
        
        if existing_like:
            return False  # Already liked
        
        like = PostLike(post_id=post_id, user_id=user_id)
        db.add(like)
        await db.commit()
        return True

    async def unlike_post(self, db: AsyncSession, post_id: int, user_id: int) -> bool:
        """Unlike a post"""
        result = await db.execute(
            select(PostLike).where(
                and_(PostLike.post_id == post_id, PostLike.user_id == user_id)
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

    async def get_by_post(
        self, db: AsyncSession, post_id: int, skip: int = 0, limit: int = 100
    ) -> List[Comment]:
        """Get comments for a post"""
        result = await db.execute(
            select(Comment)
            .options(selectinload(Comment.author))
            .where(and_(Comment.post_id == post_id, Comment.is_active == True))
            .order_by(Comment.created_at)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, comment_create: CommentCreate, post_id: int, author_id: int) -> Comment:
        """Create new comment"""
        db_comment = Comment(**comment_create.dict(), post_id=post_id, author_id=author_id)
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


post_crud = PostCRUD()
comment_crud = CommentCRUD()
