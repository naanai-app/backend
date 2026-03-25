import logging
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, PartialCredentialsError

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.place import PlacePhoto
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


def _build_s3_client():
    return boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    )


@router.get("/place-photos/{photo_id}")
async def get_place_photo(
    *,
    db: AsyncSession = Depends(get_db),
    photo_id: int,
    redirect: bool = Query(default=True),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Return a place photo by ID via presigned S3 redirect based on place google_place_id."""
    result = await db.execute(
        select(PlacePhoto)
        .options(selectinload(PlacePhoto.place))
        .where(PlacePhoto.id == photo_id)
    )
    photo = result.scalar_one_or_none()

    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    if not photo.place or not photo.place.google_place_id:
        raise HTTPException(status_code=404, detail="Place google_place_id not found")

    if not settings.AWS_S3_BUCKET:
        raise HTTPException(status_code=500, detail="AWS_S3_BUCKET is not configured")

    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        raise HTTPException(status_code=500, detail="AWS S3 credentials are not configured")

    siblings_result = await db.execute(
        select(PlacePhoto.id)
        .where(PlacePhoto.place_id == photo.place_id)
        .order_by(PlacePhoto.id.asc())
    )
    sibling_photo_ids = [row[0] for row in siblings_result.all()]

    try:
        photo_index = sibling_photo_ids.index(photo.id)
    except ValueError:
        raise HTTPException(status_code=500, detail="Could not resolve photo index")

    s3_key = f"bangkok_photos/{photo.place.google_place_id}_{photo_index}.jpg"
    print(s3_key)
    try:
        presigned_url = _build_s3_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_S3_BUCKET, "Key": s3_key},
            ExpiresIn=settings.MEDIA_PRESIGNED_URL_EXPIRE_SECONDS,
        )
    except (NoCredentialsError, PartialCredentialsError):
        raise HTTPException(status_code=500, detail="Invalid AWS S3 credentials")
    except (ClientError, BotoCoreError) as e:
        logger.exception("Failed to generate presigned URL", extra={"photo_id": photo_id, "s3_key": s3_key})
        raise HTTPException(status_code=500, detail=f"Could not generate media URL: {str(e)}")

    if redirect:
        return RedirectResponse(url=presigned_url, status_code=307)

    return {"url": presigned_url, "key": s3_key}
