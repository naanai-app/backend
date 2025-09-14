from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.graph_db import get_graph_db
from app.crud.user import user_crud
from app.schemas.user import User, UserUpdate, UserPublic, UserStats
from app.models.user import User as UserModel

router = APIRouter()


@router.get("/me", response_model=User)
async def read_user_me(
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me", response_model=User)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    user = await user_crud.update(db, user=current_user, user_update=user_in)
    return user


@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user = await user_crud.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=404, detail="The user with this id does not exist in the system"
        )
    return user


@router.post("/follow/{user_id}")
async def follow_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    graph_db = Depends(get_graph_db),
) -> Any:
    """
    Follow a user.
    """
    if current_user.id == user_id:
        raise HTTPException(
            status_code=400, detail="You cannot follow yourself"
        )
    
    # Check if already following
    is_following = await graph_db.is_following(current_user.id, user_id)
    if is_following:
        raise HTTPException(
            status_code=400, detail="You are already following this user"
        )
    
    await graph_db.create_follow_relationship(current_user.id, user_id)
    return {"message": "Successfully followed user"}


@router.delete("/follow/{user_id}")
async def unfollow_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_active_user),
    graph_db = Depends(get_graph_db),
) -> Any:
    """
    Unfollow a user.
    """
    if current_user.id == user_id:
        raise HTTPException(
            status_code=400, detail="You cannot unfollow yourself"
        )
    
    # Check if following
    is_following = await graph_db.is_following(current_user.id, user_id)
    if not is_following:
        raise HTTPException(
            status_code=400, detail="You are not following this user"
        )
    
    await graph_db.remove_follow_relationship(current_user.id, user_id)
    return {"message": "Successfully unfollowed user"}


@router.get("/{user_id}/followers", response_model=List[UserPublic])
async def get_user_followers(
    user_id: int,
    graph_db = Depends(get_graph_db),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get user's followers.
    """
    followers_data = await graph_db.get_followers(user_id)
    
    # Get full user data from PostgreSQL
    followers = []
    for follower_data in followers_data:
        user = await user_crud.get(db, user_id=follower_data["id"])
        if user:
            followers.append(user)
    
    return followers


@router.get("/{user_id}/following", response_model=List[UserPublic])
async def get_user_following(
    user_id: int,
    graph_db = Depends(get_graph_db),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get users that this user is following.
    """
    following_data = await graph_db.get_following(user_id)
    
    # Get full user data from PostgreSQL
    following = []
    for following_user_data in following_data:
        user = await user_crud.get(db, user_id=following_user_data["id"])
        if user:
            following.append(user)
    
    return following


@router.get("/{user_id}/friends", response_model=List[UserPublic])
async def get_user_friends(
    user_id: int,
    graph_db = Depends(get_graph_db),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get user's friends (mutual followers).
    """
    friends_data = await graph_db.get_friends(user_id)
    
    # Get full user data from PostgreSQL
    friends = []
    for friend_data in friends_data:
        user = await user_crud.get(db, user_id=friend_data["id"])
        if user:
            friends.append(user)
    
    return friends


@router.get("/{user_id}/stats", response_model=UserStats)
async def get_user_stats(
    user_id: int,
    graph_db = Depends(get_graph_db),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Get user statistics.
    """
    followers = await graph_db.get_followers(user_id)
    following = await graph_db.get_following(user_id)
    friends = await graph_db.get_friends(user_id)
    
    # TODO: Add posts and lists count from PostgreSQL
    # For now, return 0 as placeholder
    
    return UserStats(
        followers_count=len(followers),
        following_count=len(following),
        friends_count=len(friends),
        posts_count=0,  # TODO: Implement
        lists_count=0   # TODO: Implement
    )


@router.get("/recommendations/users", response_model=List[UserPublic])
async def get_user_recommendations(
    current_user: UserModel = Depends(get_current_active_user),
    graph_db = Depends(get_graph_db),
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
) -> Any:
    """
    Get user recommendations based on mutual connections.
    """
    recommendations_data = await graph_db.get_recommended_users(current_user.id, limit)
    
    # Get full user data from PostgreSQL
    recommendations = []
    for rec_data in recommendations_data:
        user = await user_crud.get(db, user_id=rec_data["id"])
        if user:
            recommendations.append(user)
    
    return recommendations
