from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.user import UserPublic
from app.schemas.place import Place


class PostBase(BaseModel):
    content: str
    image_url: Optional[str] = None
    place_id: Optional[int] = None


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    content: Optional[str] = None
    image_url: Optional[str] = None


class CommentBase(BaseModel):
    content: str
    parent_comment_id: Optional[int] = None


class CommentCreate(CommentBase):
    pass


class CommentUpdate(BaseModel):
    content: Optional[str] = None


class Comment(CommentBase):
    id: int
    author_id: int
    post_id: int
    author: UserPublic
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    replies: List['Comment'] = []

    class Config:
        from_attributes = True


class PostLike(BaseModel):
    id: int
    user_id: int
    post_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class Post(PostBase):
    id: int
    author_id: int
    author: UserPublic
    place: Optional[Place] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    comments: List[Comment] = []
    likes: List[PostLike] = []
    likes_count: int = 0
    comments_count: int = 0
    is_liked_by_user: bool = False

    class Config:
        from_attributes = True


# Update forward references
Comment.model_rebuild()
