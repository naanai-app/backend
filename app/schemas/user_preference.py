from typing import List

from pydantic import BaseModel, Field

from app.schemas.place import Category


class UserPreferenceBase(BaseModel):
    preferred_category_ids: List[int] = Field(default_factory=list)


class UserPreferenceUpdate(BaseModel):
    preferred_category_ids: List[int] = Field(default_factory=list)


class UserPreference(UserPreferenceBase):
    user_id: int

    class Config:
        from_attributes = True


class UserPreferredCategoriesResponse(BaseModel):
    preferred_categories: List[Category] = Field(default_factory=list)
