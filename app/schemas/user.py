from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    username: str
    city: str
    nickname: Optional[str] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    password: str

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v


class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    bio: Optional[str] = None
    city: Optional[str] = None
    password: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if v and len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInDB(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    profile_image_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserInDB):
    pass


class UserPublic(BaseModel):
    id: int
    username: str
    nickname: Optional[str] = None
    bio: Optional[str] = None
    city: str
    profile_image_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: Optional[int] = None


class UserFollow(BaseModel):
    follower_id: int
    followed_id: int


class UserStats(BaseModel):
    followers_count: int
    following_count: int
    friends_count: int
    check_ins_count: int
    lists_count: int
