from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserList(Base):
    __tablename__ = "user_lists"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_default = Column(Boolean, default=False)  # For liked/disliked places
    list_type = Column(String, nullable=False)  # 'liked', 'disliked', 'custom'
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="user_lists")
    items = relationship("UserListItem", back_populates="list", cascade="all, delete-orphan")


class UserListItem(Base):
    __tablename__ = "user_list_items"

    id = Column(Integer, primary_key=True, index=True)
    list_id = Column(Integer, ForeignKey("user_lists.id"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text, nullable=True)  # User's personal notes about the place
    rating = Column(Integer, nullable=True)  # User's personal rating (1-5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    list = relationship("UserList", back_populates="items")
    place = relationship("Place", back_populates="list_items")
    user = relationship("User", back_populates="list_items")

    # Ensure a place can only be in a list once
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
