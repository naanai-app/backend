from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.crud.user_list import user_list_crud, user_list_item_crud
from app.schemas.user_list import UserList, UserListCreate, UserListUpdate, UserListItem, UserListItemCreate, UserListItemUpdate
from app.models.user import User
from app.models.user_list import ListVisibility, ListType

router = APIRouter()


@router.get("/", response_model=List[UserList])
async def read_user_lists(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, lte=100),
) -> Any:
    """
    Get current user's lists.
    """
    lists = await user_list_crud.get_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    return lists


@router.post("/", response_model=UserList)
async def create_user_list(
    *,
    db: AsyncSession = Depends(get_db),
    list_in: UserListCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new user list.
    """
    user_list = await user_list_crud.create(db=db, list_create=list_in, user_id=current_user.id)
    return user_list


@router.get("/{list_id}", response_model=UserList)
async def read_user_list(
    *,
    db: AsyncSession = Depends(get_db),
    list_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get user list by ID.
    """
    user_list = await user_list_crud.get(db=db, list_id=list_id)
    if not user_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    if user_list.user_id != current_user.id and user_list.visibility != ListVisibility.PUBLIC:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return user_list


@router.put("/{list_id}", response_model=UserList)
async def update_user_list(
    *,
    db: AsyncSession = Depends(get_db),
    list_id: int,
    list_in: UserListUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update user list.
    """
    user_list = await user_list_crud.get(db=db, list_id=list_id)
    if not user_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    if user_list.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    user_list = await user_list_crud.update(db=db, user_list=user_list, list_update=list_in)
    return user_list


@router.delete("/{list_id}")
async def delete_user_list(
    *,
    db: AsyncSession = Depends(get_db),
    list_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Delete user list.
    """
    user_list = await user_list_crud.get(db=db, list_id=list_id)
    if not user_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    if user_list.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    success = await user_list_crud.delete(db=db, user_list=user_list)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete default lists")
    
    return {"message": "List deleted successfully"}


@router.post("/{list_id}/items", response_model=UserListItem)
async def add_item_to_list(
    *,
    db: AsyncSession = Depends(get_db),
    list_id: int,
    item_in: UserListItemCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Add place to user list.
    """
    # Check if list exists and belongs to user
    user_list = await user_list_crud.get(db=db, list_id=list_id)
    if not user_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    if user_list.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    item = await user_list_item_crud.add_to_list(
        db=db, list_id=list_id, item_create=item_in
    )
    
    if not item:
        raise HTTPException(status_code=400, detail="Place already in list")
    
    return item


@router.get("/{list_id}/items", response_model=List[UserListItem])
async def read_list_items(
    *,
    db: AsyncSession = Depends(get_db),
    list_id: int,
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, lte=100),
) -> Any:
    """
    Get items in a user list.
    """
    # Check if list exists and user has access
    user_list = await user_list_crud.get(db=db, list_id=list_id)
    if not user_list:
        raise HTTPException(status_code=404, detail="List not found")
    
    if user_list.user_id != current_user.id and user_list.visibility != ListVisibility.PUBLIC:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    items = await user_list_item_crud.get_by_list(db=db, list_id=list_id, skip=skip, limit=limit)
    return items


@router.put("/items/{item_id}", response_model=UserListItem)
async def update_list_item(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
    item_in: UserListItemUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update list item.
    """
    item = await user_list_item_crud.get(db=db, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    item = await user_list_item_crud.update(db=db, item=item, item_update=item_in)
    return item


@router.delete("/items/{item_id}")
async def remove_item_from_list(
    *,
    db: AsyncSession = Depends(get_db),
    item_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Remove item from list.
    """
    item = await user_list_item_crud.get(db=db, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    await user_list_item_crud.remove_from_list(db=db, item=item)
    return {"message": "Item removed from list successfully"}


@router.post("/quick-like/{place_id}")
async def quick_like_place(
    *,
    db: AsyncSession = Depends(get_db),
    place_id: int,
    rating: int = Query(default=5, ge=1, le=5),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Quick add place to liked list.
    """
    item = await user_list_item_crud.quick_add_to_default_list(
        db=db, user_id=current_user.id, place_id=place_id, list_type="liked", rating=rating
    )
    
    if not item:
        raise HTTPException(status_code=400, detail="Could not add to liked list or already exists")
    
    return {"message": "Place added to liked list", "item": item}


@router.post("/quick-dislike/{place_id}")
async def quick_dislike_place(
    *,
    db: AsyncSession = Depends(get_db),
    place_id: int,
    rating: int = Query(default=1, ge=1, le=5),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Quick add place to disliked list.
    """
    item = await user_list_item_crud.quick_add_to_default_list(
        db=db, user_id=current_user.id, place_id=place_id, list_type="disliked", rating=rating
    )
    
    if not item:
        raise HTTPException(status_code=400, detail="Could not add to disliked list or already exists")
    
    return {"message": "Place added to disliked list", "item": item}


@router.get("/user/{user_id}", response_model=List[UserList])
async def read_public_user_lists(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, lte=100),
) -> Any:
    """
    Get public lists of a specific user.
    """
    lists = await user_list_crud.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
    # Filter only public lists
    public_lists = [lst for lst in lists if lst.visibility == ListVisibility.PUBLIC]
    return public_lists
