from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.crud.post import post_crud, comment_crud
from app.schemas.post import Post, PostCreate, PostUpdate, Comment, CommentCreate, CommentUpdate
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[Post])
async def read_posts(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = Query(default=100, lte=100),
) -> Any:
    """
    Retrieve posts.
    """
    posts = await post_crud.get_multi(db, skip=skip, limit=limit)
    return posts


@router.post("/", response_model=Post)
async def create_post(
    *,
    db: AsyncSession = Depends(get_db),
    post_in: PostCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new post.
    """
    post = await post_crud.create(db=db, post_create=post_in, author_id=current_user.id)
    return post


@router.get("/{post_id}", response_model=Post)
async def read_post(
    *,
    db: AsyncSession = Depends(get_db),
    post_id: int,
) -> Any:
    """
    Get post by ID.
    """
    post = await post_crud.get(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/{post_id}", response_model=Post)
async def update_post(
    *,
    db: AsyncSession = Depends(get_db),
    post_id: int,
    post_in: PostUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a post.
    """
    post = await post_crud.get(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    post = await post_crud.update(db=db, post=post, post_update=post_in)
    return post


@router.delete("/{post_id}")
async def delete_post(
    *,
    db: AsyncSession = Depends(get_db),
    post_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a post.
    """
    post = await post_crud.get(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    await post_crud.delete(db=db, post=post)
    return {"message": "Post deleted successfully"}


@router.post("/{post_id}/like")
async def like_post(
    *,
    db: AsyncSession = Depends(get_db),
    post_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Like a post.
    """
    # Check if post exists
    post = await post_crud.get(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    success = await post_crud.like_post(db=db, post_id=post_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Post already liked")
    
    return {"message": "Post liked successfully"}


@router.delete("/{post_id}/like")
async def unlike_post(
    *,
    db: AsyncSession = Depends(get_db),
    post_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Unlike a post.
    """
    # Check if post exists
    post = await post_crud.get(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    success = await post_crud.unlike_post(db=db, post_id=post_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Post not liked")
    
    return {"message": "Post unliked successfully"}


@router.get("/{post_id}/comments", response_model=List[Comment])
async def read_post_comments(
    *,
    db: AsyncSession = Depends(get_db),
    post_id: int,
    skip: int = 0,
    limit: int = Query(default=100, lte=100),
) -> Any:
    """
    Get comments for a post.
    """
    comments = await comment_crud.get_by_post(db=db, post_id=post_id, skip=skip, limit=limit)
    return comments


@router.post("/{post_id}/comments", response_model=Comment)
async def create_comment(
    *,
    db: AsyncSession = Depends(get_db),
    post_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new comment on a post.
    """
    # Check if post exists
    post = await post_crud.get(db=db, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comment = await comment_crud.create(
        db=db, comment_create=comment_in, post_id=post_id, author_id=current_user.id
    )
    return comment


@router.put("/comments/{comment_id}", response_model=Comment)
async def update_comment(
    *,
    db: AsyncSession = Depends(get_db),
    comment_id: int,
    comment_in: CommentUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a comment.
    """
    comment = await comment_crud.get(db=db, comment_id=comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    comment = await comment_crud.update(db=db, comment=comment, comment_update=comment_in)
    return comment


@router.delete("/comments/{comment_id}")
async def delete_comment(
    *,
    db: AsyncSession = Depends(get_db),
    comment_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a comment.
    """
    comment = await comment_crud.get(db=db, comment_id=comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    await comment_crud.delete(db=db, comment=comment)
    return {"message": "Comment deleted successfully"}


@router.get("/user/{user_id}", response_model=List[Post])
async def read_user_posts(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    skip: int = 0,
    limit: int = Query(default=100, lte=100),
) -> Any:
    """
    Get posts by a specific user.
    """
    posts = await post_crud.get_by_user(db=db, user_id=user_id, skip=skip, limit=limit)
    return posts
