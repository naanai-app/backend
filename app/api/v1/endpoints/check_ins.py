from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.crud.check_in import check_in_crud, comment_crud 
from app.schemas.check_in import CheckIn, CheckInCreate, CheckInUpdate, Comment, CommentCreate, CommentUpdate
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[CheckIn])
async def read_check_ins(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, lte=100),
) -> Any:
    """
    Retrieve check ins.
    """
    check_ins = await check_in_crud.get_multi(db, skip=skip, limit=limit)
    return check_ins


@router.post("/", response_model=CheckIn)
async def create_check_in(
    *,
    db: AsyncSession = Depends(get_db),
    check_in: CheckInCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new check in.
    """
    check_in = await check_in_crud.create(db=db, check_in_create=check_in, author_id=current_user.id)
    return check_in


@router.get("/{check_in_id}", response_model=CheckIn)
async def read_check_in(
    *,
    db: AsyncSession = Depends(get_db),
    check_in_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get check_in by ID.
    """
    check_in = await check_in_crud.get(db=db, check_in_id=check_in_id)
    if not check_in:
        raise HTTPException(status_code=404, detail="Check-In not found")
    return check_in


@router.put("/{check_in_id}", response_model=CheckIn)
async def update_check_in(
    *,
    db: AsyncSession = Depends(get_db),
    check_in_id: int,
    check_in_in: CheckInUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a check_in.
    """
    check_in = await check_in_crud.get(db=db, check_in_id=check_in_id)
    if not check_in:
        raise HTTPException(status_code=404, detail="Check-In not found")
    
    if check_in.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    check_in = await check_in_crud.update(db=db, check_in=check_in, check_in_update=check_in_in)
    return check_in


@router.delete("/{check_in_id}")
async def delete_check_in(
    *,
    db: AsyncSession = Depends(get_db),
    check_in_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a check_in.
    """
    check_in = await check_in_crud.get(db=db, check_in_id=check_in_id)
    if not check_in:
        raise HTTPException(status_code=404, detail="Check-In not found")
    
    if check_in.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    await check_in_crud.delete(db=db, check_in=check_in)
    return {"message": "Check-In deleted successfully"}


@router.post("/{check_in_id}/like")
async def like_check_in(
    *,
    db: AsyncSession = Depends(get_db),
    check_in_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Like a check_in.
    """
    # Check if check_in exists
    check_in = await check_in_crud.get(db=db, check_in_id=check_in_id)
    if not check_in:
        raise HTTPException(status_code=404, detail="Check-In not found")
    
    success = await check_in_crud.like_check_in(db=db, check_in_id=check_in_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Check-In already liked")
    
    return {"message": "Check-In liked successfully"}


@router.delete("/{check_in_id}/like")
async def unlike_check_in(
    *,
    db: AsyncSession = Depends(get_db),
    check_in_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Unlike a check_in.
    """
    # Check if check_in exists
    check_in = await check_in_crud.get(db=db, check_in_id=check_in_id)
    if not check_in:
        raise HTTPException(status_code=404, detail="Check-In not found")
    
    success = await check_in_crud.unlike_check_in(db=db, check_in_id=check_in_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Check-In not liked")
    
    return {"message": "Check-In unliked successfully"}


@router.get("/{check_in_id}/comments", response_model=List[Comment])
async def read_check_in_comments(
    *,
    db: AsyncSession = Depends(get_db),
    check_in_id: int,
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, lte=100),
) -> Any:
    """
    Get comments for a check_in.
    """
    comments = await comment_crud.get_by_check_in(db=db, check_in_id=check_in_id, skip=skip, limit=limit)
    return comments


@router.post("/{check_in_id}/comments", response_model=Comment)
async def create_comment(
    *,
    db: AsyncSession = Depends(get_db),
    check_in_id: int,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new comment on a check_in.
    """
    # Check if check_in exists
    check_in = await check_in_crud.get(db=db, check_in_id=check_in_id)
    if not check_in:
        raise HTTPException(status_code=404, detail="check_in not found")
    
    comment = await comment_crud.create(
        db=db, comment_create=comment_in, check_in_id=check_in_id, author_id=current_user.id
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


@router.get("/user/{user_id}", response_model=List[CheckIn])
async def read_user_check_ins(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, lte=100),
) -> Any:
    """
    Get check_ins by a specific user.
    """
    check_ins = await check_in_crud.get_by_user(db=db, user_id=user_id, skip=skip, limit=limit)
    return check_ins
