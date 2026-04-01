from typing import Optional, List
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.place import Place, PlaceCategory, PlacePhoto, PlaceReview, PlaceOptions
from app.models.category import Category
from app.schemas.place import PlaceCreate, PlaceUpdate, PlaceSearch, Place as PlaceSchema




class PlaceCRUD:
    def _build_s3_client(self):
        if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
            return None

        return boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        )

    def _generate_photo_media_urls(
        self,
        photo_count: int,
        google_place_id: Optional[str],
        photo_ids: Optional[List[int]] = None,
    ) -> List[str]:
        if photo_count <= 0:
            return []

        s3_client = self._build_s3_client()
        has_s3 = bool(s3_client and settings.AWS_S3_BUCKET and google_place_id)
        urls: List[str] = []

        for index in range(photo_count):
            generated_url: Optional[str] = None

            if has_s3:
                s3_key = f"bangkok_photos/{google_place_id}_{index}.jpg"
                try:
                    generated_url = s3_client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": settings.AWS_S3_BUCKET, "Key": s3_key},
                        ExpiresIn=settings.MEDIA_PRESIGNED_URL_EXPIRE_SECONDS,
                    )
                except (ClientError, BotoCoreError):
                    generated_url = None

            if not generated_url:
                photo_id = photo_ids[index] if photo_ids and index < len(photo_ids) else None
                generated_url = f"{settings.API_V1_STR}/media/place-photos/{photo_id}" if photo_id else ""

            urls.append(generated_url)

        return urls

    def _populate_photo_media_urls(self, place: PlaceSchema) -> PlaceSchema:
        if not place.photos:
            return place

        photo_ids = [photo.id for photo in place.photos]
        generated_urls = self._generate_photo_media_urls(
            photo_count=len(place.photos),
            google_place_id=place.google_place_id,
            photo_ids=photo_ids,
        )

        for index, photo in enumerate(place.photos):
            if index < len(generated_urls):
                photo.media_url = generated_urls[index]

        return place

    async def _refresh_and_persist_photo_urls_for_places(
        self,
        db: AsyncSession,
        places: List[Place],
    ) -> None:
        changed = False

        for place in places:
            if not place.photos:
                continue

            photo_ids = [photo.id for photo in place.photos]
            generated_urls = self._generate_photo_media_urls(
                photo_count=len(place.photos),
                google_place_id=place.google_place_id,
                photo_ids=photo_ids,
            )

            for index, photo in enumerate(place.photos):
                if index >= len(generated_urls):
                    continue
                generated_url = generated_urls[index]
                if photo.media_url != generated_url:
                    photo.media_url = generated_url
                    changed = True

        if changed:
            await db.commit()

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
        if not place:
            return None

        await self._refresh_and_persist_photo_urls_for_places(db, [place])
        return PlaceSchema.model_validate(place)

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
        await self._refresh_and_persist_photo_urls_for_places(db, places)
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
            created_photos: List[PlacePhoto] = []
            for photo_data in place_create.photos:
                db_photo = PlacePhoto(
                    place_id=db_place.id,
                    **photo_data.dict()
                )
                db.add(db_photo)
                created_photos.append(db_photo)

            await db.flush()

            generated_urls = self._generate_photo_media_urls(
                photo_count=len(created_photos),
                google_place_id=db_place.google_place_id,
                photo_ids=[photo.id for photo in created_photos],
            )

            for index, db_photo in enumerate(created_photos):
                db_photo.media_url = generated_urls[index] if index < len(generated_urls) else ""
        
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
                selectinload(Place.categories).selectinload(PlaceCategory.category),
                selectinload(Place.photos),
                selectinload(Place.reviews),
                selectinload(Place.options),
            )
            .where(Place.id == place.id)
        )
        updated_place = result.scalar_one()
        await self._refresh_and_persist_photo_urls_for_places(db, [updated_place])
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
        await self._refresh_and_persist_photo_urls_for_places(db, places)
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
        if not place:
            return None

        await self._refresh_and_persist_photo_urls_for_places(db, [place])
        return PlaceSchema.model_validate(place)


place_crud = PlaceCRUD()
