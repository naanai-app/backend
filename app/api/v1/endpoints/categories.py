from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.crud.category import category_crud
from app.schemas.place import Category, CategoryCreate, CategoryUpdate
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[Category])
async def read_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, lte=100),
) -> Any:
    """
    Retrieve categories.
    """
    categories = await category_crud.get_multi(db, skip=skip, limit=limit)
    return categories


@router.post("/", response_model=Category)
async def create_category(
    *,
    db: AsyncSession = Depends(get_db),
    category_in: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new category.
    """
    # Check if category with this title already exists
    existing_category = await category_crud.get_by_title(db, title=category_in.title)
    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Category with this title already exists"
        )
    
    category = await category_crud.create(db=db, category_create=category_in)
    return category


@router.put("/{category_id}", response_model=Category)
async def update_category(
    *,
    db: AsyncSession = Depends(get_db),
    category_id: int,
    category_in: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a category.
    """
    category = await category_crud.get(db=db, category_id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if new title conflicts with existing category
    if category_in.title and category_in.title != category.title:
        existing_category = await category_crud.get_by_title(db, title=category_in.title)
        if existing_category:
            raise HTTPException(
                status_code=400,
                detail="Category with this title already exists"
            )
    
    category = await category_crud.update(db=db, category=category, category_update=category_in)
    return category


@router.get("/{category_id}", response_model=Category)
async def read_category(
    *,
    db: AsyncSession = Depends(get_db),
    category_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get category by ID.
    """
    category = await category_crud.get(db=db, category_id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.delete("/{category_id}")
async def delete_category(
    *,
    db: AsyncSession = Depends(get_db),
    category_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete a category.
    """
    success = await category_crud.delete(db=db, category_id=category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}
