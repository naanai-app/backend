import json
import logging
from typing import List, Optional

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RecommendationCache:
    def __init__(self) -> None:
        self._redis: Optional[Redis] = None

    async def _get_client(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(settings.RECOMMENDATION_CACHE_REDIS_URL, decode_responses=True)
        return self._redis

    def _cache_key(self, user_id: int) -> str:
        return f"{settings.REDIS_RECOMMENDATION_LAST_BATCH_PREFIX}:{user_id}"

    async def get_last_batch_place_ids(self, user_id: int) -> List[int]:
        try:
            redis = await self._get_client()
            raw = await redis.get(self._cache_key(user_id))
            if not raw:
                return []

            values = json.loads(raw)
            if not isinstance(values, list):
                return []

            return [int(value) for value in values]
        except Exception:
            logger.exception("Failed to read recommendations cache")
            return []

    async def set_last_batch_place_ids(self, user_id: int, place_ids: List[int]) -> None:
        key = self._cache_key(user_id)
        try:
            redis = await self._get_client()
            if not place_ids:
                await redis.delete(key)
                return

            unique_ids = list(dict.fromkeys(place_ids))
            await redis.set(
                key,
                json.dumps(unique_ids),
                ex=settings.REDIS_RECOMMENDATION_LAST_BATCH_TTL_SECONDS,
            )
        except Exception:
            logger.exception("Failed to update recommendations cache")

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


recommendation_cache = RecommendationCache()
