from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from app.schemas.place import Place
from app.models.user_list import ListVisibility, ListType


class UserListBase(BaseModel):
    name: str
    description: Optional[str] = None
    visibility: ListVisibility = ListVisibility.PRIVATE


class UserListCreate(UserListBase):
    pass


class UserListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[ListVisibility] = None


class UserListItemBase(BaseModel):
    place_id: int
    rating: Optional[int] = None

    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v


class UserListItemCreate(UserListItemBase):
    pass


class UserListItemUpdate(BaseModel):
    rating: Optional[int] = None

    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v


class UserListItem(UserListItemBase):
    id: int
    list_id: int
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
    list_type: ListType
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
