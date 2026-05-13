from typing import Any, List
import random

import grpc
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.recommendation_cache import recommendation_cache
from app.core.recommendation_grpc import (
    RecommendationGrpcClient,
    get_recommendation_grpc_client,
)
from app.crud.place import place_crud
from app.models.user import User as UserModel
from app.schemas.place import Place
from app.schemas.recommendation import (
    PlaceRecommendationRequest,
    SimilarPlacesRecommendationRequest,
)

router = APIRouter()


@router.post("/me/places", response_model=List[Place])
async def get_recommended_places_for_user(
    *,
    payload: PlaceRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    grpc_client: RecommendationGrpcClient = Depends(get_recommendation_grpc_client),
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:

    cached_place_ids = set(await recommendation_cache.get_last_batch_place_ids(current_user.id))

    try:
        place_ids = await grpc_client.get_recommendation_place_ids(
            user_id=current_user.id,
            top_k=payload.top_k,
            exclude_seen=payload.exclude_seen,
            filters=payload.filters,
        )
        random.shuffle(place_ids)
    except grpc.aio.AioRpcError as e:
        raise HTTPException(status_code=502, detail=f"Recommendation service error: {e.code().name}")

    place_ids = [place_id for place_id in place_ids if place_id not in cached_place_ids]

    places: List[Place] = []
    for place_id in place_ids:
        place = await place_crud.get(db, place_id=place_id)
        if place:
            places.append(place)

    await recommendation_cache.set_last_batch_place_ids(current_user.id, place_ids)

    return places


@router.post("/places/{place_id}/similar", response_model=List[Place])
async def get_similar_places(
    *,
    place_id: int,
    payload: SimilarPlacesRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    grpc_client: RecommendationGrpcClient = Depends(get_recommendation_grpc_client),
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    try:
        place_ids = await grpc_client.get_similar_place_ids(
            place_id=place_id,
            top_k=payload.top_k,
            filters=payload.filters,
        )
    except grpc.aio.AioRpcError as e:
        raise HTTPException(status_code=502, detail=f"Recommendation service error: {e.code().name}")

    places: List[Place] = []
    for recommended_place_id in place_ids:
        place = await place_crud.get(db, place_id=recommended_place_id)
        if place:
            places.append(place)

    return places
