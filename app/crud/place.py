from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.place import Place, PlaceCategory, PlacePhoto, PlaceReview, PlaceOptions
from app.models.category import Category
from app.schemas.place import PlaceCreate, PlaceUpdate, PlaceSearch, Place as PlaceSchema




class PlaceCRUD:
    async def get(self, db: AsyncSession, place_id: int) -> Optional[PlaceSchema]:
        """Get place by ID with all relationships"""
        result = await db.execute(
            select(Place)
            .options(
                selectinload(Place.primary_category),
                selectinload(Place.categories).selectinload(PlaceCategory.category),
                selectinload(Place.photos),
                selectinload(Place.reviews),
                selectinload(Place.options)
            )
            .where(Place.id == place_id)
        )
        place = result.scalar_one_or_none()
        return PlaceSchema.model_validate(place) if place else None

    async def get_multi(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[PlaceSchema]:
        """Get multiple places"""
        result = await db.execute(
            select(Place)
            .options(
                selectinload(Place.primary_category),
                selectinload(Place.categories).selectinload(PlaceCategory.category),
                selectinload(Place.photos),
                selectinload(Place.reviews),
                selectinload(Place.options)
            )
            .offset(skip)
            .limit(limit)
        )
        places = result.scalars().all()
        return [PlaceSchema.model_validate(place) for place in places]

    async def create(self, db: AsyncSession, place_create: PlaceCreate) -> PlaceSchema:
        """Create new place"""
        # Check if place with this google_place_id already exists
        if place_create.google_place_id:
            existing_result = await db.execute(
                select(Place).where(Place.google_place_id == place_create.google_place_id)
            )
            existing_place = existing_result.scalar_one_or_none()
            if existing_place:
                # Return existing place with all relationships loaded
                return await self.get(db, existing_place.id)
        
        place_data = place_create.dict(exclude={"category_ids", "photos", "reviews", "options"})
        db_place = Place(**place_data)
        
        db.add(db_place)
        await db.flush()  # Get the ID without committing
        
        # Add categories
        for category_id in place_create.category_ids:
            place_category = PlaceCategory(
                place_id=db_place.id,
                category_id=category_id
            )
            db.add(place_category)
        
        # Add photos
        if place_create.photos:
            for photo_data in place_create.photos:
                db_photo = PlacePhoto(
                    place_id=db_place.id,
                    **photo_data.dict()
                )
                db.add(db_photo)
        
        # Add reviews
        if place_create.reviews:
            for review_data in place_create.reviews:
                db_review = PlaceReview(
                    place_id=db_place.id,
                    **review_data.dict()
                )
                db.add(db_review)
        
        # Add options
        if place_create.options:
            db_options = PlaceOptions(
                place_id=db_place.id,
                **place_create.options.dict()
            )
            db.add(db_options)
        
        await db.commit()
        await db.refresh(db_place)
        return await self.get(db, db_place.id)

    async def update(self, db: AsyncSession, place_id: int, place_update: PlaceUpdate) -> PlaceSchema:
        """Update place"""
        # Get the SQLAlchemy model object
        result = await db.execute(select(Place).where(Place.id == place_id))
        place = result.scalar_one_or_none()
        if not place:
            raise ValueError(f"Place with id {place_id} not found")
        
        update_data = place_update.dict(exclude_unset=True, exclude={"category_ids"})
        
        for field, value in update_data.items():
            setattr(place, field, value)
        
        # Update categories if provided
        if place_update.category_ids is not None:
            # Remove existing categories
            await db.execute(
                select(PlaceCategory).where(PlaceCategory.place_id == place.id)
            )
            
            # Add new categories
            for category_id in place_update.category_ids:
                place_category = PlaceCategory(
                    place_id=place.id,
                    category_id=category_id
                )
                db.add(place_category)
        
        await db.commit()
        await db.refresh(place)
        
        # Get the updated place with all relationships loaded
        result = await db.execute(
            select(Place)
            .options(
                selectinload(Place.categories).selectinload(PlaceCategory.category)
            )
            .where(Place.id == place.id)
        )
        updated_place = result.scalar_one()
        return PlaceSchema.model_validate(updated_place)

    async def search(self, db: AsyncSession, search: PlaceSearch, skip: int = 0, limit: int = 100) -> List[PlaceSchema]:
        """Search places with filters"""
        query = select(Place).options(
            selectinload(Place.categories).selectinload(PlaceCategory.category)
        )
        
        conditions = []
        
        # Text search in name and description
        if search.query:
            text_condition = or_(
                Place.name.ilike(f"%{search.query}%"),
                Place.description.ilike(f"%{search.query}%")
            )
            conditions.append(text_condition)
        
        # Rating filter
        if search.min_rating:
            conditions.append(Place.rating >= search.min_rating)
        
        # Location-based search (radius)
        if search.latitude and search.longitude and search.radius_km:
            # Simple distance calculation (for more accuracy, use PostGIS)
            lat_diff = func.abs(Place.latitude - search.latitude)
            lng_diff = func.abs(Place.longitude - search.longitude)
            distance = func.sqrt(lat_diff * lat_diff + lng_diff * lng_diff)
            # Rough conversion: 1 degree ≈ 111 km
            conditions.append(distance <= (search.radius_km / 111.0))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Category filter
        if search.category_ids:
            query = query.join(PlaceCategory).where(
                PlaceCategory.category_id.in_(search.category_ids)
            )
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        places = result.scalars().all()
        return [PlaceSchema.model_validate(place) for place in places]

    async def get_by_google_place_id(self, db: AsyncSession, google_place_id: str) -> Optional[PlaceSchema]:
        """Get place by Google Place ID"""
        result = await db.execute(
            select(Place)
            .options(
                selectinload(Place.primary_category),
                selectinload(Place.categories).selectinload(PlaceCategory.category),
                selectinload(Place.photos),
                selectinload(Place.reviews),
                selectinload(Place.options)
            )
            .where(Place.google_place_id == google_place_id)
        )
        place = result.scalar_one_or_none()
        return PlaceSchema.model_validate(place) if place else None


place_crud = PlaceCRUD()
