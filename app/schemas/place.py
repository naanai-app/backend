from pydantic import BaseModel, validator, field_serializer, model_validator
from typing import Optional, List, Any
from datetime import datetime


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


class PlaceBase(BaseModel):
    title: str
    description: Optional[str] = None
    city: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_place_id: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    price_level: Optional[int] = None
    image_url: Optional[str] = None

    @validator('price_level')
    def validate_price_level(cls, v):
        if v is not None and (v < 1 or v > 4):
            raise ValueError('Price level must be between 1 and 4')
        return v


class PlaceCreate(PlaceBase):
    category_ids: List[int] = []


class PlaceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_place_id: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    price_level: Optional[int] = None
    image_url: Optional[str] = None
    category_ids: Optional[List[int]] = None

    @validator('price_level')
    def validate_price_level(cls, v):
        if v is not None and (v < 1 or v > 4):
            raise ValueError('Price level must be between 1 and 4')
        return v


class Place(PlaceBase):
    id: int
    rating: Optional[float] = None
    categories: List[Category] = []
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
    city: Optional[str] = None
    category_ids: Optional[List[int]] = None
    min_rating: Optional[float] = None
    max_price_level: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None
