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


def _build_photo_s3_key(google_place_id: str, photo_idx: int) -> str:
    return f"bangkok_photos/{google_place_id}_{photo_idx}.jpg"


@router.get("/place-photos/{photo_id}")
async def get_place_photo(
    *,
    db: AsyncSession = Depends(get_db),
    photo_id: int,
    redirect: bool = Query(default=True),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Return a place photo by ID via presigned S3 redirect based on place google_place_id and idx."""
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

    s3_key = _build_photo_s3_key(photo.place.google_place_id, photo.idx)

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


@router.get("/place-photos/by-place/{place_id}/{idx}")
async def get_place_photo_by_place_and_idx(
    *,
    db: AsyncSession = Depends(get_db),
    place_id: int,
    idx: int,
    redirect: bool = Query(default=True),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Return a place photo by place_id and idx via presigned S3 redirect."""
    result = await db.execute(
        select(PlacePhoto)
        .options(selectinload(PlacePhoto.place))
        .where(PlacePhoto.place_id == place_id, PlacePhoto.idx == idx)
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

    s3_key = _build_photo_s3_key(photo.place.google_place_id, photo.idx)

    try:
        presigned_url = _build_s3_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_S3_BUCKET, "Key": s3_key},
            ExpiresIn=settings.MEDIA_PRESIGNED_URL_EXPIRE_SECONDS,
        )
    except (NoCredentialsError, PartialCredentialsError):
        raise HTTPException(status_code=500, detail="Invalid AWS S3 credentials")
    except (ClientError, BotoCoreError) as e:
        logger.exception(
            "Failed to generate presigned URL",
            extra={"place_id": place_id, "idx": idx, "s3_key": s3_key},
        )
        raise HTTPException(status_code=500, detail=f"Could not generate media URL: {str(e)}")

    if redirect:
        return RedirectResponse(url=presigned_url, status_code=307)

    return {"url": presigned_url, "key": s3_key, "photo_id": photo.id}
