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
from app.models.category import Category
from app.models.place import Place, PlaceCategory
from app.models.user import User
from app.models.post import Post, PostLike, Comment
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


async def seed_posts_and_interactions(db: AsyncSession):
    """Seed demo posts, likes, and comments."""
    from sqlalchemy import select
    
    # Get demo user and places
    user_result = await db.execute(select(User).where(User.email == "demo@example.com"))
    demo_user = user_result.scalar_one_or_none()
    
    places_result = await db.execute(select(Place))
    places = list(places_result.scalars().all())
    
    if not demo_user or not places:
        print("⚠️  Cannot seed posts: demo user or places not found")
        return
    
    # Create additional demo users for interactions
    demo_users_data = [
        {
            "email": "alice@example.com",
            "username": "alice_explorer",
            "hashed_password": get_password_hash("alice123"),
            "city": "New York",
            "nickname": "Alice Explorer",
            "bio": "Love discovering new places in the city!",
            "is_active": True,
            "is_verified": True
        },
        {
            "email": "bob@example.com",
            "username": "bob_foodie",
            "hashed_password": get_password_hash("bob123"),
            "city": "New York", 
            "nickname": "Bob Foodie",
            "bio": "Food enthusiast and restaurant reviewer",
            "is_active": True,
            "is_verified": True
        }
    ]
    
    demo_users = [demo_user]
    for user_data in demo_users_data:
        result = await db.execute(select(User).where(User.email == user_data["email"]))
        existing = result.scalar_one_or_none()
        if not existing:
            new_user = User(**user_data)
            db.add(new_user)
            await db.flush()
            demo_users.append(new_user)
            # Create user node in Neo4j (if connected)
            try:
                if not graph_db.driver:
                    await graph_db.connect()
                await graph_db.create_user_node(new_user.id, new_user.username, new_user.email)
            except Exception as e:
                print(f"⚠️  Could not create Neo4j node for {new_user.username}: {e}")
        else:
            demo_users.append(existing)
    
    # Sample posts data
    posts_data = [
        {
            "content": "Just visited Central Park and it was absolutely beautiful! Perfect weather for a morning jog. 🌳🏃‍♂️",
            "author_id": demo_users[0].id,
            "place_id": places[0].id if len(places) > 0 else None
        },
        {
            "content": "The Metropolitan Museum has an amazing new exhibition! Spent the whole afternoon there. Highly recommend! 🎨",
            "author_id": demo_users[1].id if len(demo_users) > 1 else demo_users[0].id,
            "place_id": places[1].id if len(places) > 1 else None
        },
        {
            "content": "Best pizza slice in NYC! Joe's Pizza never disappoints. The classic cheese slice is perfection. 🍕",
            "author_id": demo_users[2].id if len(demo_users) > 2 else demo_users[0].id,
            "place_id": places[2].id if len(places) > 2 else None
        },
        {
            "content": "Blue Bottle Coffee has the perfect atmosphere for working. Great coffee and friendly staff! ☕️💻",
            "author_id": demo_users[0].id,
            "place_id": places[3].id if len(places) > 3 else None
        },
        {
            "content": "Times Square at night is something else! So much energy and lights everywhere. Tourist trap but worth experiencing once! ✨",
            "author_id": demo_users[1].id if len(demo_users) > 1 else demo_users[0].id,
            "place_id": places[4].id if len(places) > 4 else None
        }
    ]
    
    created_posts = []
    for post_data in posts_data:
        post = Post(**post_data)
        db.add(post)
        await db.flush()
        created_posts.append(post)
    
    # Add likes to posts
    likes_data = [
        {"user_id": demo_users[1].id if len(demo_users) > 1 else demo_users[0].id, "post_id": created_posts[0].id},
        {"user_id": demo_users[2].id if len(demo_users) > 2 else demo_users[0].id, "post_id": created_posts[0].id},
        {"user_id": demo_users[0].id, "post_id": created_posts[1].id},
        {"user_id": demo_users[2].id if len(demo_users) > 2 else demo_users[0].id, "post_id": created_posts[1].id},
        {"user_id": demo_users[0].id, "post_id": created_posts[2].id},
        {"user_id": demo_users[1].id if len(demo_users) > 1 else demo_users[0].id, "post_id": created_posts[2].id},
    ]
    
    for like_data in likes_data:
        # Check if like already exists
        result = await db.execute(
            select(PostLike).where(
                PostLike.user_id == like_data["user_id"],
                PostLike.post_id == like_data["post_id"]
            )
        )
        if not result.scalar_one_or_none():
            like = PostLike(**like_data)
            db.add(like)
    
    # Add comments to posts
    comments_data = [
        {
            "content": "I love running there too! What's your favorite route?",
            "author_id": demo_users[1].id if len(demo_users) > 1 else demo_users[0].id,
            "post_id": created_posts[0].id
        },
        {
            "content": "The sculpture garden is my favorite part of the Met!",
            "author_id": demo_users[0].id,
            "post_id": created_posts[1].id
        },
        {
            "content": "Have you tried their pepperoni slice? It's incredible!",
            "author_id": demo_users[1].id if len(demo_users) > 1 else demo_users[0].id,
            "post_id": created_posts[2].id
        },
        {
            "content": "Their cold brew is the best in the city!",
            "author_id": demo_users[2].id if len(demo_users) > 2 else demo_users[0].id,
            "post_id": created_posts[3].id
        },
        {
            "content": "Great photo spot but so crowded! Best to go early morning.",
            "author_id": demo_users[0].id,
            "post_id": created_posts[4].id
        }
    ]
    
    for comment_data in comments_data:
        comment = Comment(**comment_data)
        db.add(comment)
    
    await db.commit()
    print(f"✅ Seeded {len(created_posts)} posts, {len(likes_data)} likes, and {len(comments_data)} comments")


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
    custom_lists_data = [
        {
            "name": "Weekend Getaways",
            "description": "Perfect places to visit on weekends",
            "user_id": users[0].id,
            "list_type": "custom",
            "is_public": True
        },
        {
            "name": "Coffee Spots",
            "description": "My favorite coffee places in the city",
            "user_id": users[1].id if len(users) > 1 else users[0].id,
            "list_type": "custom", 
            "is_public": True
        },
        {
            "name": "Date Night Ideas",
            "description": "Romantic places for special occasions",
            "user_id": users[2].id if len(users) > 2 else users[0].id,
            "list_type": "custom",
            "is_public": False
        },
        {
            "name": "Must Visit NYC",
            "description": "Essential NYC experiences for visitors",
            "user_id": users[0].id,
            "list_type": "custom",
            "is_public": True
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
    
    # Add places to lists
    list_items_data = [
        # Weekend Getaways
        {"list_id": created_lists[0].id, "place_id": places[0].id, "user_id": created_lists[0].user_id, "notes": "Perfect for morning runs", "rating": 5},
        {"list_id": created_lists[0].id, "place_id": places[1].id, "user_id": created_lists[0].user_id, "notes": "Great for cultural weekends", "rating": 5},
        
        # Coffee Spots (if we have a second list)
        {"list_id": created_lists[1].id if len(created_lists) > 1 else created_lists[0].id, 
         "place_id": places[3].id if len(places) > 3 else places[0].id, 
         "user_id": created_lists[1].user_id if len(created_lists) > 1 else created_lists[0].user_id, 
         "notes": "Best cold brew in town", "rating": 4},
        
        # Must Visit NYC
        {"list_id": created_lists[3].id if len(created_lists) > 3 else created_lists[0].id,
         "place_id": places[4].id if len(places) > 4 else places[0].id,
         "user_id": created_lists[3].user_id if len(created_lists) > 3 else created_lists[0].user_id,
         "notes": "Iconic NYC experience", "rating": 4},
        {"list_id": created_lists[3].id if len(created_lists) > 3 else created_lists[0].id,
         "place_id": places[2].id if len(places) > 2 else places[0].id,
         "user_id": created_lists[3].user_id if len(created_lists) > 3 else created_lists[0].user_id,
         "notes": "Authentic NYC pizza", "rating": 5}
    ]
    
    for item_data in list_items_data:
        if created_lists:  # Only add if we have lists
            list_item = UserListItem(**item_data)
            db.add(list_item)
    
    await db.commit()
    print(f"✅ Seeded {len(created_lists)} user lists with {len(list_items_data)} items")


async def seed_initial_data():
    """Seed all initial data."""
    async with AsyncSessionLocal() as db:
        await seed_categories(db)
        await seed_demo_user(db)
        await seed_demo_places(db)
        await seed_posts_and_interactions(db)
        await seed_user_lists(db)


if __name__ == "__main__":
    asyncio.run(seed_initial_data())
