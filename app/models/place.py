from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.core.database import Base


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    city = Column(String, nullable=False, index=True)
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    google_place_id = Column(String, nullable=True, unique=True)  # Google Maps Place ID
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    rating = Column(Float, nullable=True)  # Average rating
    price_level = Column(Integer, nullable=True)  # 1-4 scale
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    categories = relationship("PlaceCategory", back_populates="place", cascade="all, delete-orphan")
    check_ins = relationship("CheckIn", back_populates="place")
    list_items = relationship("UserListItem", back_populates="place")
    
    @hybrid_property
    def category_objects(self):
        """Get the actual Category objects from PlaceCategory relationships"""
        return [pc.category for pc in self.categories if pc.category]


class PlaceCategory(Base):
    __tablename__ = "place_categories"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(Integer, ForeignKey("places.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    place = relationship("Place", back_populates="categories")
    category = relationship("Category", back_populates="places")
