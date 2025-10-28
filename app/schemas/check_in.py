from pydantic import BaseModel, field_serializer, model_validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum
from app.schemas.user import UserPublic
from app.schemas.place import Place


class CheckInVisibilityEnum(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"
    FRIENDS = "friends"


class CheckInPhotoBase(BaseModel):
    s3_url: str
    s3_key: str
    order: int = 0


class CheckInPhotoCreate(CheckInPhotoBase):
    pass


class CheckInPhoto(CheckInPhotoBase):
    id: int
    check_in_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CheckInBase(BaseModel):
    content: str
    place_id: Optional[int] = None
    visibility: CheckInVisibilityEnum = CheckInVisibilityEnum.PUBLIC


class CheckInCreate(CheckInBase):
    photos: Optional[List[CheckInPhotoCreate]] = []


class CheckInUpdate(BaseModel):
    content: Optional[str] = None
    visibility: Optional[CheckInVisibilityEnum] = None


class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    content: Optional[str] = None


class Comment(CommentBase):
    id: int
    author_id: int
    check_in_id: int
    author: UserPublic
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CheckInLike(BaseModel):
    id: int
    user_id: int
    check_in_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CheckIn(CheckInBase):
    id: int
    author_id: int
    author: UserPublic
    place: Optional[Place] = None
    photos: List[CheckInPhoto] = []
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    comments: List[Comment] = []
    likes: List[CheckInLike] = []
    likes_count: int = 0
    comments_count: int = 0
    is_liked_by_user: bool = False

    @model_validator(mode='before')
    @classmethod
    def prepare_check_in_data(cls, data: Any) -> Any:
        """Prepare CheckIn data by handling place categories and calculating counts"""
        if hasattr(data, '__dict__'):
            # Create a dict copy for SQLAlchemy objects
            result = {}
            # Copy all fields from the model
            for field in data.__table__.columns:
                result[field.name] = getattr(data, field.name, None)
            
            # Handle relationships
            result['author'] = getattr(data, 'author', None)
            result['place'] = getattr(data, 'place', None)
            result['photos'] = getattr(data, 'photos', [])
            result['comments'] = getattr(data, 'comments', [])
            result['likes'] = getattr(data, 'likes', [])
            
            # Handle is_liked_by_user
            result['is_liked_by_user'] = getattr(data, 'is_liked_by_user', False)
            
            # Calculate counts
            result['likes_count'] = len(result['likes']) if result['likes'] else 0
            result['comments_count'] = len(result['comments']) if result['comments'] else 0
            
            return result
        
        return data

    class Config:
        from_attributes = True

# Update forward references
Comment.model_rebuild()
