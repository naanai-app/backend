from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, places, check_ins, categories, user_lists, media, user_preferences

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(places.router, prefix="/places", tags=["places"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(check_ins.router, prefix="/check_ins", tags=["check-ins"])
api_router.include_router(user_lists.router, prefix="/lists", tags=["user-lists"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(user_preferences.router, prefix="/preferences", tags=["user-preferences"])
