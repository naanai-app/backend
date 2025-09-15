#!/usr/bin/env python3
"""
Seed initial data for the application.
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.core.graph_db import graph_db
from sqlalchemy import select
from app.models.category import Category
from app.models.place import Place, PlaceCategory
from app.models.user import User
from app.models.check_in import CheckIn, Comment, CheckInLike
from app.models.user_list import UserList, UserListItem
from app.core.security import get_password_hash


async def seed_categories(db: AsyncSession):
    """Seed initial categories."""
    categories_data = [
        {"title": "Restaurant", "color": "#FF6B6B", "description": "Restaurants and dining establishments"},
        {"title": "Cafe", "color": "#4ECDC4", "description": "Coffee shops and cafes"},
        {"title": "Bar", "color": "#45B7D1", "description": "Bars and nightlife venues"},
        {"title": "Shopping", "color": "#96CEB4", "description": "Shopping centers and stores"},
        {"title": "Entertainment", "color": "#FFEAA7", "description": "Entertainment venues and activities"},
        {"title": "Park", "color": "#81ECEC", "description": "Parks and outdoor spaces"},
        {"title": "Museum", "color": "#A29BFE", "description": "Museums and cultural sites"},
        {"title": "Hotel", "color": "#FD79A8", "description": "Hotels and accommodations"},
        {"title": "Gym", "color": "#FDCB6E", "description": "Fitness centers and gyms"},
        {"title": "Hospital", "color": "#E17055", "description": "Medical facilities"},
        {"title": "School", "color": "#00B894", "description": "Educational institutions"},
        {"title": "Transport", "color": "#6C5CE7", "description": "Transportation hubs"},
    ]
    
    for cat_data in categories_data:
        # Check if category already exists
        from sqlalchemy import select
        result = await db.execute(select(Category).where(Category.title == cat_data["title"]))
        existing = result.scalar_one_or_none()
        if not existing:
            category = Category(**cat_data)
            db.add(category)
    
    await db.commit()
    print(f"✅ Seeded {len(categories_data)} categories")


async def seed_demo_user(db: AsyncSession):
    """Seed a demo user for testing."""
    demo_user_data = {
        "email": "demo@example.com",
        "username": "demo_user",
        "hashed_password": get_password_hash("demo123"),
        "city": "New York",
        "nickname": "Demo User",
        "bio": "This is a demo user for testing the application",
        "is_active": True,
        "is_verified": True
    }
    
    # Check if demo user already exists
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == demo_user_data["email"]))
    existing_user = result.scalar_one_or_none()
    
    if not existing_user:
        demo_user = User(**demo_user_data)
        db.add(demo_user)
        await db.commit()
        await db.refresh(demo_user)
        
        # Create user node in Neo4j (if connected)
        try:
            if not graph_db.driver:
                await graph_db.connect()
            await graph_db.create_user_node(demo_user.id, demo_user.username, demo_user.email)
        except Exception as e:
            print(f"⚠️  Could not create Neo4j node for {demo_user.username}: {e}")
        
        print(f"✅ Created demo user: {demo_user.email}")
        return demo_user
    else:
        print(f"ℹ️  Demo user already exists: {existing_user.email}")
        return existing_user


async def seed_demo_places(db: AsyncSession):
    """Seed some demo places."""
    places_data = [
        {
            "title": "Central Park",
            "description": "A large public park in Manhattan, New York City",
            "city": "New York",
            "address": "New York, NY 10024, USA",
            "latitude": 40.7829,
            "longitude": -73.9654,
            "rating": 4.6,
            "price_level": 1,
            "categories": ["Park"]
        },
        {
            "title": "The Metropolitan Museum of Art",
            "description": "One of the world's largest and most prestigious art museums",
            "city": "New York",
            "address": "1000 5th Ave, New York, NY 10028, USA",
            "latitude": 40.7794,
            "longitude": -73.9632,
            "rating": 4.7,
            "price_level": 2,
            "categories": ["Museum"]
        },
        {
            "title": "Joe's Pizza",
            "description": "Famous New York pizza joint",
            "city": "New York",
            "address": "7 Carmine St, New York, NY 10014, USA",
            "latitude": 40.7308,
            "longitude": -74.0023,
            "rating": 4.3,
            "price_level": 2,
            "categories": ["Restaurant"]
        },
        {
            "title": "Blue Bottle Coffee",
            "description": "Specialty coffee roaster and retailer",
            "city": "New York",
            "address": "54 Mint Plaza, San Francisco, CA 94103, USA",
            "latitude": 37.7849,
            "longitude": -122.4094,
            "rating": 4.2,
            "price_level": 2,
            "categories": ["Cafe"]
        },
        {
            "title": "Times Square",
            "description": "Major commercial intersection and entertainment center",
            "city": "New York",
            "address": "Times Square, New York, NY 10036, USA",
            "latitude": 40.7580,
            "longitude": -73.9855,
            "rating": 4.1,
            "price_level": 3,
            "categories": ["Entertainment"]
        }
    ]
    
    # Get categories for mapping
    from sqlalchemy import select
    result = await db.execute(select(Category))
    categories = {cat.title: cat for cat in result.scalars().all()}
    
    for place_data in places_data:
        # Check if place already exists
        result = await db.execute(select(Place).where(Place.title == place_data["title"]))
        existing_place = result.scalar_one_or_none()
        
        if not existing_place:
            category_names = place_data.pop("categories", [])
            place = Place(**place_data)
            db.add(place)
            await db.flush()  # Get the ID
            
            # Add categories
            for cat_name in category_names:
                if cat_name in categories:
                    place_category = PlaceCategory(
                        place_id=place.id,
                        category_id=categories[cat_name].id
                    )
                    db.add(place_category)
    
    await db.commit()
    print(f"✅ Seeded {len(places_data)} demo places")

async def seed_check_ins_and_interactions(db: AsyncSession):
    """Seed check-ins, likes, and comments."""
    # Get users and places
    users_result = await db.execute(select(User))
    users = list(users_result.scalars().all())
    
    places_result = await db.execute(select(Place))
    places = list(places_result.scalars().all())
    
    if not users or not places:
        print("⚠️  Cannot seed check-ins: users or places not found")
        return
    
    # Create check-ins data
    check_ins_data = [
        {
            "content": "Amazing brunch at this cozy cafe! The avocado toast was perfect 🥑",
            "author_id": users[0].id,
            "place_id": places[0].id if places else None,
            "image_url": "https://example.com/brunch.jpg"
        },
        {
            "content": "Great atmosphere for a date night. Highly recommend the pasta!",
            "author_id": users[1].id if len(users) > 1 else users[0].id,
            "place_id": places[1].id if len(places) > 1 else places[0].id,
        },
        {
            "content": "Perfect spot for remote work. Fast wifi and great coffee ☕",
            "author_id": users[0].id,
            "place_id": places[2].id if len(places) > 2 else places[0].id,
        },
        {
            "content": "Had an incredible dinner here last night. The service was outstanding!",
            "author_id": users[2].id if len(users) > 2 else users[0].id,
            "place_id": places[0].id,
        }
    ]
    
    created_check_ins = []
    for check_in_data in check_ins_data:
        # Check if check-in already exists (by content and author)
        result = await db.execute(
            select(CheckIn).where(
                CheckIn.content == check_in_data["content"],
                CheckIn.author_id == check_in_data["author_id"]
            )
        )
        existing_check_in = result.scalar_one_or_none()
        
        if not existing_check_in:
            check_in = CheckIn(**check_in_data)
            db.add(check_in)
            created_check_ins.append(check_in)
    
    await db.commit()
    
    # Refresh created check-ins to get their IDs
    for check_in in created_check_ins:
        await db.refresh(check_in)
    
    # Create likes
    likes_data = []
    if created_check_ins:
        # Each user likes different check-ins
        for i, user in enumerate(users[:3]):  # Limit to first 3 users
            for j, check_in in enumerate(created_check_ins):
                if (i + j) % 2 == 0:  # Some variety in likes
                    likes_data.append({
                        "user_id": user.id,
                        "check_in_id": check_in.id
                    })
    
    for like_data in likes_data:
        # Check if like already exists
        result = await db.execute(
            select(CheckInLike).where(
                CheckInLike.user_id == like_data["user_id"],
                CheckInLike.check_in_id == like_data["check_in_id"]
            )
        )
        existing_like = result.scalar_one_or_none()
        
        if not existing_like:
            like = CheckInLike(**like_data)
            db.add(like)
    
    # Create comments
    comments_data = []
    if created_check_ins:
        comments_data = [
            {
                "content": "Looks delicious! I need to try this place.",
                "author_id": users[1].id if len(users) > 1 else users[0].id,
                "check_in_id": created_check_ins[0].id
            },
            {
                "content": "I was there last week too! Great recommendation.",
                "author_id": users[2].id if len(users) > 2 else users[0].id,
                "check_in_id": created_check_ins[0].id
            },
            {
                "content": "Thanks for the tip about the wifi!",
                "author_id": users[1].id if len(users) > 1 else users[0].id,
                "check_in_id": created_check_ins[2].id if len(created_check_ins) > 2 else created_check_ins[0].id
            }
        ]
    
    for comment_data in comments_data:
        # Check if comment already exists
        result = await db.execute(
            select(Comment).where(
                Comment.content == comment_data["content"],
                Comment.author_id == comment_data["author_id"],
                Comment.check_in_id == comment_data["check_in_id"]
            )
        )
        existing_comment = result.scalar_one_or_none()
        
        if not existing_comment:
            comment = Comment(**comment_data)
            db.add(comment)
    
    await db.commit()
    print(f"✅ Seeded {len(created_check_ins)} check-ins with {len(likes_data)} likes and {len(comments_data)} comments")


async def seed_user_lists(db: AsyncSession):
    """Seed demo user lists."""
    from sqlalchemy import select
    
    # Get demo users and places
    users_result = await db.execute(select(User))
    users = list(users_result.scalars().all())
    
    places_result = await db.execute(select(Place))
    places = list(places_result.scalars().all())
    
    if not users or not places:
        print("⚠️  Cannot seed user lists: users or places not found")
        return
    
    # Create default lists for each user (liked/disliked are auto-created by the system)
    from app.models.user_list import ListVisibility
    custom_lists_data = [
        {
            "name": "Weekend Getaways",
            "description": "Perfect places to visit on weekends",
            "user_id": users[0].id,
            "list_type": "custom",
            "visibility": ListVisibility.PUBLIC
        },
        {
            "name": "Coffee Spots",
            "description": "My favorite coffee places in the city",
            "user_id": users[1].id if len(users) > 1 else users[0].id,
            "list_type": "custom", 
            "visibility": ListVisibility.PUBLIC
        },
        {
            "name": "Date Night Ideas",
            "description": "Romantic places for special occasions",
            "user_id": users[2].id if len(users) > 2 else users[0].id,
            "list_type": "custom",
            "visibility": ListVisibility.PRIVATE
        },
        {
            "name": "Must Visit NYC",
            "description": "Essential NYC experiences for visitors",
            "user_id": users[0].id,
            "list_type": "custom",
            "visibility": ListVisibility.FRIENDS
        }
    ]
    
    created_lists = []
    for list_data in custom_lists_data:
        # Check if list already exists
        result = await db.execute(
            select(UserList).where(
                UserList.name == list_data["name"],
                UserList.user_id == list_data["user_id"]
            )
        )
        if not result.scalar_one_or_none():
            user_list = UserList(**list_data)
            db.add(user_list)
            await db.flush()
            created_lists.append(user_list)
    
    # Create list items data (removed user_id and notes fields)
    list_items_data = []
    if created_lists and places:
        list_items_data = [
            {"list_id": created_lists[0].id, "place_id": places[0].id, "rating": 5},
            {"list_id": created_lists[0].id, "place_id": places[1].id, "rating": 4},
            {"list_id": created_lists[1].id, "place_id": places[2].id, "rating": 5},
            {"list_id": created_lists[2].id, "place_id": places[0].id, "rating": 3},
            {"list_id": created_lists[3].id if len(created_lists) > 3 else created_lists[0].id, "place_id": places[4].id if len(places) > 4 else places[0].id, "rating": 4},
            {"list_id": created_lists[3].id if len(created_lists) > 3 else created_lists[0].id, "place_id": places[2].id if len(places) > 2 else places[0].id, "rating": 5}
        ]
    
    for item_data in list_items_data:
        if created_lists:  # Only add if we have lists
            list_item = UserListItem(**item_data)
            db.add(list_item)
    
    await db.commit()
    print(f"✅ Seeded {len(created_lists)} user lists with {len(list_items_data)} items")


async def seed_follow_relationships():
    """Seed follow relationships between users in Neo4j"""
    try:
        if not graph_db.driver:
            await graph_db.connect()
        
        # Get all users from PostgreSQL
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            result = await db.execute(select(User))
            users = list(result.scalars().all())
        
        if len(users) < 2:
            print("⚠️  Need at least 2 users to create follow relationships")
            return
        
        # Create some follow relationships
        follow_relationships = []
        
        if len(users) >= 3:
            # Demo user follows Alice and Bob
            follow_relationships.extend([
                (users[0].id, users[1].id),  # demo -> alice
                (users[0].id, users[2].id),  # demo -> bob
                (users[1].id, users[0].id),  # alice -> demo (mutual)
                (users[1].id, users[2].id),  # alice -> bob
                (users[2].id, users[1].id),  # bob -> alice (mutual)
            ])
        elif len(users) == 2:
            # Just mutual follow between demo and alice
            follow_relationships.extend([
                (users[0].id, users[1].id),  # demo -> alice
                (users[1].id, users[0].id),  # alice -> demo
            ])
        
        # Create follow relationships in Neo4j
        for follower_id, followed_id in follow_relationships:
            try:
                await graph_db.create_follow_relationship(follower_id, followed_id)
            except Exception as e:
                print(f"⚠️  Could not create follow relationship {follower_id} -> {followed_id}: {e}")
        
        print(f"✅ Seeded {len(follow_relationships)} follow relationships")
        
    except Exception as e:
        print(f"⚠️  Could not seed follow relationships: {e}")


async def seed_initial_data():
    """Seed all initial data."""
    async with AsyncSessionLocal() as db:
        await seed_categories(db)
        await seed_demo_user(db)
        await seed_demo_places(db)
        await seed_check_ins_and_interactions(db)
        await seed_user_lists(db)
        await seed_follow_relationships()


if __name__ == "__main__":
    asyncio.run(seed_initial_data())
