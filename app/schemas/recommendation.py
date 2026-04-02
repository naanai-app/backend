from typing import Dict

from pydantic import BaseModel, Field


class PlaceRecommendationRequest(BaseModel):
    top_k: int = 20
    exclude_seen: bool = True
    filters: Dict[str, str] = Field(default_factory=dict)


class SimilarPlacesRecommendationRequest(BaseModel):
    top_k: int = 20
    filters: Dict[str, str] = Field(default_factory=dict)
