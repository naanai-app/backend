from typing import Dict, List, Optional

import grpc
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

from app.core.config import settings


def _build_proto_classes() -> Dict[str, type]:
    file_desc = descriptor_pb2.FileDescriptorProto()
    file_desc.name = "recommendation.proto"
    file_desc.package = "recommendation"
    file_desc.syntax = "proto3"

    recommendation_request = file_desc.message_type.add()
    recommendation_request.name = "RecommendationRequest"

    request_filters_entry = recommendation_request.nested_type.add()
    request_filters_entry.name = "FiltersEntry"
    request_filters_entry.options.map_entry = True
    request_filters_entry.field.add(name="key", number=1, label=1, type=9)
    request_filters_entry.field.add(name="value", number=2, label=1, type=9)

    recommendation_request.field.add(name="user_id", number=1, label=1, type=5)
    recommendation_request.field.add(name="top_k", number=2, label=1, type=5)
    recommendation_request.field.add(name="exclude_seen", number=3, label=1, type=8)
    recommendation_request.field.add(
        name="filters",
        number=4,
        label=3,
        type=11,
        type_name=".recommendation.RecommendationRequest.FiltersEntry",
    )

    similar_places_request = file_desc.message_type.add()
    similar_places_request.name = "SimilarPlacesRequest"

    similar_filters_entry = similar_places_request.nested_type.add()
    similar_filters_entry.name = "FiltersEntry"
    similar_filters_entry.options.map_entry = True
    similar_filters_entry.field.add(name="key", number=1, label=1, type=9)
    similar_filters_entry.field.add(name="value", number=2, label=1, type=9)

    similar_places_request.field.add(name="place_id", number=1, label=1, type=5)
    similar_places_request.field.add(name="top_k", number=2, label=1, type=5)
    similar_places_request.field.add(
        name="filters",
        number=3,
        label=3,
        type=11,
        type_name=".recommendation.SimilarPlacesRequest.FiltersEntry",
    )

    place_recommendation = file_desc.message_type.add()
    place_recommendation.name = "PlaceRecommendation"

    metadata_entry = place_recommendation.nested_type.add()
    metadata_entry.name = "MetadataEntry"
    metadata_entry.options.map_entry = True
    metadata_entry.field.add(name="key", number=1, label=1, type=9)
    metadata_entry.field.add(name="value", number=2, label=1, type=9)

    place_recommendation.field.add(name="place_id", number=1, label=1, type=5)
    place_recommendation.field.add(name="score", number=2, label=1, type=2)
    place_recommendation.field.add(name="rank", number=3, label=1, type=5)
    place_recommendation.field.add(
        name="metadata",
        number=4,
        label=3,
        type=11,
        type_name=".recommendation.PlaceRecommendation.MetadataEntry",
    )

    recommendation_response = file_desc.message_type.add()
    recommendation_response.name = "RecommendationResponse"
    recommendation_response.field.add(name="user_id", number=1, label=1, type=5)
    recommendation_response.field.add(
        name="recommendations",
        number=2,
        label=3,
        type=11,
        type_name=".recommendation.PlaceRecommendation",
    )
    recommendation_response.field.add(name="generated_at", number=3, label=1, type=9)
    recommendation_response.field.add(name="model_version", number=4, label=1, type=9)

    pool = descriptor_pool.DescriptorPool()
    pool.Add(file_desc)

    return {
        "RecommendationRequest": message_factory.GetMessageClass(
            pool.FindMessageTypeByName("recommendation.RecommendationRequest")
        ),
        "SimilarPlacesRequest": message_factory.GetMessageClass(
            pool.FindMessageTypeByName("recommendation.SimilarPlacesRequest")
        ),
        "RecommendationResponse": message_factory.GetMessageClass(
            pool.FindMessageTypeByName("recommendation.RecommendationResponse")
        ),
    }


_PROTO_CLASSES = _build_proto_classes()
RecommendationRequest = _PROTO_CLASSES["RecommendationRequest"]
SimilarPlacesRequest = _PROTO_CLASSES["SimilarPlacesRequest"]
RecommendationResponse = _PROTO_CLASSES["RecommendationResponse"]


class RecommendationGrpcClient:
    def __init__(self) -> None:
        self._channel: Optional[grpc.aio.Channel] = None
        self._get_recommendations = None
        self._get_similar_places = None

    def _target(self) -> str:
        return f"{settings.RECOMMENDATION_GRPC_HOST}:{settings.RECOMMENDATION_GRPC_PORT}"

    def _ensure_client(self) -> None:
        if self._channel:
            return

        self._channel = grpc.aio.insecure_channel(self._target())
        self._get_recommendations = self._channel.unary_unary(
            "/recommendation.RecommendationService/GetRecommendations",
            request_serializer=lambda msg: msg.SerializeToString(),
            response_deserializer=RecommendationResponse.FromString,
        )
        self._get_similar_places = self._channel.unary_unary(
            "/recommendation.RecommendationService/GetSimilarPlaces",
            request_serializer=lambda msg: msg.SerializeToString(),
            response_deserializer=RecommendationResponse.FromString,
        )

    async def close(self) -> None:
        if self._channel:
            await self._channel.close()
            self._channel = None
            self._get_recommendations = None
            self._get_similar_places = None

    async def get_recommendation_place_ids(
        self,
        user_id: int,
        top_k: int,
        exclude_seen: bool,
        filters: Optional[Dict[str, str]] = None,
    ) -> List[int]:
        self._ensure_client()
        request = RecommendationRequest(
            user_id=user_id,
            top_k=top_k,
            exclude_seen=exclude_seen,
            filters=filters or {},
        )
        response = await self._get_recommendations(
            request,
            timeout=settings.RECOMMENDATION_GRPC_TIMEOUT_SECONDS,
        )
        return [item.place_id for item in response.recommendations]

    async def get_similar_place_ids(
        self,
        place_id: int,
        top_k: int,
        filters: Optional[Dict[str, str]] = None,
    ) -> List[int]:
        self._ensure_client()
        request = SimilarPlacesRequest(
            place_id=place_id,
            top_k=top_k,
            filters=filters or {},
        )
        response = await self._get_similar_places(
            request,
            timeout=settings.RECOMMENDATION_GRPC_TIMEOUT_SECONDS,
        )
        return [item.place_id for item in response.recommendations]


recommendation_grpc_client = RecommendationGrpcClient()


def get_recommendation_grpc_client() -> RecommendationGrpcClient:
    return recommendation_grpc_client
