import json
import logging
from datetime import datetime, timezone
from typing import Optional

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class InteractionStreamProducer:
    def __init__(self) -> None:
        self._redis: Optional[Redis] = None

    async def _get_client(self) -> Redis:
        if self._redis is None:
            self._redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    async def publish_interaction_event(
        self,
        *,
        event_type: str,
        user_id: int,
        place_id: int,
        interaction_id: int,
        occurred_at: Optional[datetime] = None,
    ) -> None:
        if not settings.REDIS_STREAM_ENABLED:
            return

        event_time = occurred_at or datetime.now(timezone.utc)
        payload = {
            "event_type": event_type,
            "user_id": user_id,
            "place_id": place_id,
            "interaction_id": interaction_id,
            "occurred_at": event_time.isoformat(),
        }

        try:
            redis = await self._get_client()
            await redis.xadd(
                settings.REDIS_INTERACTION_STREAM_KEY,
                {"event": json.dumps(payload)},
            )
        except Exception:
            logger.exception("Failed to publish interaction event to Redis Stream")

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


interaction_stream_producer = InteractionStreamProducer()
