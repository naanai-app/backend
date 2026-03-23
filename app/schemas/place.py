from pydantic import BaseModel, validator, field_serializer, model_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum


class CategoryBase(BaseModel):
    title: str
    color: str
    description: Optional[str] = None

    @validator('color')
    def validate_color(cls, v):
        if not v.startswith('#') or len(v) != 7:
            raise ValueError('Color must be a valid hex color code (e.g., #ffffff)')
        return v


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    title: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None

    @validator('color')
    def validate_color(cls, v):
        if v and (not v.startswith('#') or len(v) != 7):
            raise ValueError('Color must be a valid hex color code (e.g., #ffffff)')
        return v


class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Photo schemas
class PlacePhotoBase(BaseModel):
    file_path: str
    attributions: Optional[List[Dict[str, Any]]] = None


class PlacePhotoCreate(PlacePhotoBase):
    pass


class PlacePhoto(PlacePhotoBase):
    id: int
    place_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Review schemas
class PlaceReviewBase(BaseModel):
    relative_publish_time_description: Optional[str] = None
    rating: Optional[int] = None
    text: Optional[str] = None
    original_text: Optional[str] = None


class PlaceReviewCreate(PlaceReviewBase):
    pass


class PlaceReview(PlaceReviewBase):
    id: int
    place_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Options schemas
class PlaceOptionsBase(BaseModel):
    business_status: Optional[str] = None
    price_level: Optional[int] = None
    payment_options: Optional[Dict[str, Any]] = None
    parking_options: Optional[Dict[str, Any]] = None
    fuel_options: Optional[Dict[str, Any]] = None
    ev_charge_options: Optional[Dict[str, Any]] = None
    price_range: Optional[Dict[str, Any]] = None
    accessibility_options: Optional[Dict[str, Any]] = None
    takeout: bool = False
    delivery: bool = False
    dine_in: bool = False
    curbside_pickup: bool = False
    reservable: bool = False
    serves_breakfast: bool = False
    serves_lunch: bool = False
    serves_dinner: bool = False
    serves_beer: bool = False
    serves_wine: bool = False
    serves_brunch: bool = False
    serves_vegetarian_food: bool = False
    serves_cocktails: bool = False
    serves_dessert: bool = False
    serves_coffee: bool = False
    outdoor_seating: bool = False
    live_music: bool = False
    menu_for_children: bool = False
    good_for_children: bool = False
    allows_dogs: bool = False
    restroom: bool = False
    good_for_groups: bool = False
    good_for_watching_sports: bool = False
    pure_service_area_business: bool = False


class PlaceOptionsCreate(PlaceOptionsBase):
    pass


class PlaceOptionsUpdate(BaseModel):
    business_status: Optional[str] = None
    price_level: Optional[int] = None
    payment_options: Optional[Dict[str, Any]] = None
    parking_options: Optional[Dict[str, Any]] = None
    fuel_options: Optional[Dict[str, Any]] = None
    ev_charge_options: Optional[Dict[str, Any]] = None
    price_range: Optional[Dict[str, Any]] = None
    accessibility_options: Optional[Dict[str, Any]] = None
    takeout: Optional[bool] = None
    delivery: Optional[bool] = None
    dine_in: Optional[bool] = None
    curbside_pickup: Optional[bool] = None
    reservable: Optional[bool] = None
    serves_breakfast: Optional[bool] = None
    serves_lunch: Optional[bool] = None
    serves_dinner: Optional[bool] = None
    serves_beer: Optional[bool] = None
    serves_wine: Optional[bool] = None
    serves_brunch: Optional[bool] = None
    serves_vegetarian_food: Optional[bool] = None
    serves_cocktails: Optional[bool] = None
    serves_dessert: Optional[bool] = None
    serves_coffee: Optional[bool] = None
    outdoor_seating: Optional[bool] = None
    live_music: Optional[bool] = None
    menu_for_children: Optional[bool] = None
    good_for_children: Optional[bool] = None
    allows_dogs: Optional[bool] = None
    restroom: Optional[bool] = None
    good_for_groups: Optional[bool] = None
    good_for_watching_sports: Optional[bool] = None
    pure_service_area_business: Optional[bool] = None


class PlaceOptions(PlaceOptionsBase):
    id: int
    place_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Place schemas
class PlaceBase(BaseModel):
    name: str
    description: Optional[str] = None
    primary_category_id: Optional[int] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = None
    google_maps_uri: Optional[str] = None
    website_uri: Optional[str] = None
    phone_number: Optional[str] = None
    opening_hours: Optional[Dict[str, Any]] = None
    user_rating_count: Optional[int] = None
    google_place_id: Optional[str] = None


class PlaceCreate(PlaceBase):
    category_ids: List[int] = []
    photos: Optional[List[PlacePhotoCreate]] = []
    reviews: Optional[List[PlaceReviewCreate]] = []
    options: Optional[PlaceOptionsCreate] = None


class PlaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    primary_category_id: Optional[int] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = None
    google_maps_uri: Optional[str] = None
    website_uri: Optional[str] = None
    phone_number: Optional[str] = None
    opening_hours: Optional[Dict[str, Any]] = None
    user_rating_count: Optional[int] = None
    google_place_id: Optional[str] = None
    category_ids: Optional[List[int]] = None


class Place(PlaceBase):
    id: int
    primary_category: Optional[Category] = None
    categories: List[Category] = []
    photos: List[PlacePhoto] = []
    reviews: List[PlaceReview] = []
    options: Optional[PlaceOptions] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    @model_validator(mode='before')
    @classmethod
    def extract_categories_from_place_categories(cls, data: Any) -> Any:
        """Extract Category objects from PlaceCategory relationships before validation"""
        if hasattr(data, 'categories') and data.categories:
            # Extract actual Category objects from PlaceCategory relationships
            categories = []
            for place_category in data.categories:
                if hasattr(place_category, 'category') and place_category.category:
                    categories.append(place_category.category)
            
            # Replace categories with extracted Category objects
            if hasattr(data, '__dict__'):
                # For SQLAlchemy objects, create a dict copy
                result = {}
                for field in cls.model_fields:
                    if field == 'categories':
                        result[field] = categories
                    else:
                        result[field] = getattr(data, field, None)
                return result
        
        return data

    class Config:
        from_attributes = True


class PlaceSearch(BaseModel):
    query: Optional[str] = None
    category_ids: Optional[List[int]] = None
    min_rating: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None


# Interaction schemas
class InteractionTypeEnum(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    SKIP = "skip"
    CHECK_IN = "check_in"
    OPEN = "open"


class UserInteractionCreate(BaseModel):
    place_id: int
    interaction_type: InteractionTypeEnum


class UserInteraction(BaseModel):
    id: int
    user_id: int
    place_id: int
    interaction_type: InteractionTypeEnum
    created_at: datetime

    class Config:
        from_attributes = True
