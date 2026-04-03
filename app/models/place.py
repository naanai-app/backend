from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Boolean, JSON, Enum, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)  # Changed from title
    description = Column(Text, nullable=True)
    primary_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    address = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    rating = Column(Float, nullable=True)
    google_maps_uri = Column(String, nullable=True)
    website_uri = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    opening_hours = Column(JSON, nullable=True)  # Store as JSON
    user_rating_count = Column(Integer, nullable=True, default=0)
    google_place_id = Column(String, nullable=True, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    primary_category = relationship("Category", foreign_keys=[primary_category_id])
    categories = relationship("PlaceCategory", back_populates="place", cascade="all, delete-orphan")
    photos = relationship("PlacePhoto", back_populates="place", cascade="all, delete-orphan")
    reviews = relationship("PlaceReview", back_populates="place", cascade="all, delete-orphan")
    options = relationship("PlaceOptions", back_populates="place", uselist=False, cascade="all, delete-orphan")
    check_ins = relationship("CheckIn", back_populates="place")
    list_items = relationship("UserListItem", back_populates="place")
    interactions = relationship("UserInteraction", back_populates="place", cascade="all, delete-orphan")


class PlaceCategory(Base):
    __tablename__ = "place_categories"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(Integer, ForeignKey("places.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    place = relationship("Place", back_populates="categories")
    category = relationship("Category", back_populates="places")


class PlacePhoto(Base):
    __tablename__ = "place_photos"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(Integer, ForeignKey("places.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)  # Local file path
    media_url = Column(String, nullable=True)
    attributions = Column(JSON, nullable=True)  # Store attribution data as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    place = relationship("Place", back_populates="photos")


class PlaceReview(Base):
    __tablename__ = "place_reviews"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(Integer, ForeignKey("places.id", ondelete="CASCADE"), nullable=False)
    relative_publish_time_description = Column(String, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5 rating
    text = Column(Text, nullable=True) # en text
    original_text = Column(Text, nullable=True) # original text
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    place = relationship("Place", back_populates="reviews")


class PlaceOptions(Base):
    __tablename__ = "place_options"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(Integer, ForeignKey("places.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Business information
    business_status = Column(String, nullable=True)
    price_level = Column(Integer, nullable=True)
    
    # JSON fields for complex options
    payment_options = Column(JSON, nullable=True)
    parking_options = Column(JSON, nullable=True)
    fuel_options = Column(JSON, nullable=True)
    ev_charge_options = Column(JSON, nullable=True)
    price_range = Column(JSON, nullable=True)
    accessibility_options = Column(JSON, nullable=True)
    
    # Boolean service options
    takeout = Column(Boolean, nullable=True)
    delivery = Column(Boolean, nullable=True)
    dine_in = Column(Boolean, nullable=True)
    curbside_pickup = Column(Boolean, nullable=True)
    reservable = Column(Boolean, nullable=True)
    
    # Food service options
    serves_breakfast = Column(Boolean, nullable=True)
    serves_lunch = Column(Boolean, nullable=True)
    serves_dinner = Column(Boolean, nullable=True)
    serves_beer = Column(Boolean, nullable=True)
    serves_wine = Column(Boolean, nullable=True)
    serves_brunch = Column(Boolean, nullable=True)
    serves_vegetarian_food = Column(Boolean, nullable=True)
    serves_cocktails = Column(Boolean, nullable=True)
    serves_dessert = Column(Boolean, nullable=True)
    serves_coffee = Column(Boolean, nullable=True)
    
    # Amenities
    outdoor_seating = Column(Boolean, nullable=True)
    live_music = Column(Boolean, nullable=True)
    menu_for_children = Column(Boolean, nullable=True)
    good_for_children = Column(Boolean, nullable=True)
    allows_dogs = Column(Boolean, nullable=True)
    restroom = Column(Boolean, nullable=True)
    good_for_groups = Column(Boolean, nullable=True)
    good_for_watching_sports = Column(Boolean, nullable=True)
    pure_service_area_business = Column(Boolean, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    place = relationship("Place", back_populates="options")


class InteractionType(str, enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    SKIP = "skip"
    CHECK_IN = "check_in"
    OPEN = "open"


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    place_id = Column(Integer, ForeignKey("places.id", ondelete="CASCADE"), nullable=False)
    interaction_type = Column(Enum(InteractionType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        UniqueConstraint("user_id", "place_id", name="unique_user_place_interaction"),
    )

    # Relationships
    user = relationship("User", back_populates="interactions")
    place = relationship("Place", back_populates="interactions")
