from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from app.schemas.place import Place


class UserListBase(BaseModel):
    name: str
    description: Optional[str] = None
    list_type: str = "custom"
    is_public: bool = False

    @validator('list_type')
    def validate_list_type(cls, v):
        if v not in ['liked', 'disliked', 'custom']:
            raise ValueError('List type must be one of: liked, disliked, custom')
        return v


class UserListCreate(UserListBase):
    pass


class UserListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class UserListItemBase(BaseModel):
    place_id: int
    notes: Optional[str] = None
    rating: Optional[int] = None

    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v


class UserListItemCreate(UserListItemBase):
    pass


class UserListItemUpdate(BaseModel):
    notes: Optional[str] = None
    rating: Optional[int] = None

    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v


class UserListItem(UserListItemBase):
    id: int
    list_id: int
    user_id: int
    place: Place
    created_at: datetime

    class Config:
        from_attributes = True


class UserList(UserListBase):
    id: int
    user_id: int
    is_default: bool
    items: List[UserListItem] = []
    items_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
