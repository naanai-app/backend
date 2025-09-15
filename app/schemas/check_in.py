from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.user import UserPublic
from app.schemas.place import Place


class CheckInBase(BaseModel):
    content: str
    image_url: Optional[str] = None
    place_id: Optional[int] = None


class CheckInCreate(CheckInBase):
    pass


class CheckInUpdate(BaseModel):
    content: Optional[str] = None
    image_url: Optional[str] = None


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
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    comments: List[Comment] = []
    likes: List[CheckInLike] = []
    likes_count: int = 0
    comments_count: int = 0
    is_liked_by_user: bool = False

    class Config:
        from_attributes = True


# Update forward references
Comment.model_rebuild()
