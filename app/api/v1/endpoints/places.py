from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.crud.place import place_crud
from app.schemas.place import Place, PlaceCreate, PlaceUpdate, PlaceSearch
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[Place])
async def read_places(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, lte=100),
) -> Any:
    """
    Retrieve places.
    """
    places = await place_crud.get_multi(db, skip=skip, limit=limit)
    return places


@router.post("/", response_model=Place)
async def create_place(
    *,
    db: AsyncSession = Depends(get_db),
    place_in: PlaceCreate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Create new place.
    """
    place = await place_crud.create(db=db, place_create=place_in)
    return place


@router.put("/{place_id}", response_model=Place)
async def update_place(
    *,
    db: AsyncSession = Depends(get_db),
    place_id: int,
    place_in: PlaceUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update a place.
    """
    place = await place_crud.get(db=db, place_id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    place = await place_crud.update(db=db, place=place, place_update=place_in)
    return place


@router.get("/{place_id}", response_model=Place)
async def read_place(
    *,
    db: AsyncSession = Depends(get_db),
    place_id: int,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get place by ID.
    """
    place = await place_crud.get(db=db, place_id=place_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place


@router.post("/search", response_model=List[Place])
async def search_places(
    *,
    db: AsyncSession = Depends(get_db),
    search: PlaceSearch,
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = Query(default=100, lte=100),
) -> Any:
    """
    Search places with filters.
    """
    places = await place_crud.search(db=db, search=search, skip=skip, limit=limit)
    return places
