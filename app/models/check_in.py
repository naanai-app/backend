from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class CheckInVisibility(str, enum.Enum):
    PRIVATE = "private"
    PUBLIC = "public"
    FRIENDS = "friends"


class CheckIn(Base):
    __tablename__ = "check_ins"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=True)  # Check-in to a place
    visibility = Column(Enum(CheckInVisibility), nullable=False, default=CheckInVisibility.PUBLIC)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    author = relationship("User", back_populates="check_ins")
    place = relationship("Place", back_populates="check_ins")
    photos = relationship("CheckInPhoto", back_populates="check_in", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="check_in", cascade="all, delete-orphan")
    likes = relationship("CheckInLike", back_populates="check_in", cascade="all, delete-orphan")


class CheckInPhoto(Base):
    __tablename__ = "check_in_photos"

    id = Column(Integer, primary_key=True, index=True)
    check_in_id = Column(Integer, ForeignKey("check_ins.id", ondelete="CASCADE"), nullable=False)
    s3_url = Column(String, nullable=False)  # S3 link to the photo
    s3_key = Column(String, nullable=False)  # S3 object key for deletion
    order = Column(Integer, default=0)  # Order of photos in the check-in
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    check_in = relationship("CheckIn", back_populates="photos")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    check_in_id = Column(Integer, ForeignKey("check_ins.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    author = relationship("User", back_populates="comments")
    check_in = relationship("CheckIn", back_populates="comments")


class CheckInLike(Base):
    __tablename__ = "check_in_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    check_in_id = Column(Integer, ForeignKey("check_ins.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="check_in_likes")
    check_in = relationship("CheckIn", back_populates="likes")

    # Ensure a user can only like a check-in once
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
