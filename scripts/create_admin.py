#!/usr/bin/env python3
"""
Create an admin user for the application.
"""
import asyncio
import sys
from pathlib import Path
import getpass

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.core.graph_db import graph_db
from app.crud.user import user_crud
from app.schemas.user import UserCreate
from app.models.user_list import UserList


async def create_admin_user():
    """Create an admin user interactively."""
    print("👤 Creating admin user...")
    
    # Get user input
    email = input("Enter admin email: ")
    username = input("Enter admin username: ")
    password = getpass.getpass("Enter admin password: ")
    city = input("Enter admin city: ")
    nickname = input("Enter admin nickname (optional): ") or None
    
    try:
        async with AsyncSessionLocal() as db:
            # Check if user already exists
            existing_user = await user_crud.get_by_email(db, email=email)
            if existing_user:
                print(f"❌ User with email {email} already exists!")
                return False
            
            existing_user = await user_crud.get_by_username(db, username=username)
            if existing_user:
                print(f"❌ User with username {username} already exists!")
                return False
            
            # Create user
            user_create = UserCreate(
                email=email,
                username=username,
                password=password,
                city=city,
                nickname=nickname
            )
            
            user = await user_crud.create(db, user_create=user_create)
            
            # Create user node in Neo4j
            await graph_db.connect()
            await graph_db.create_user_node(user.id, user.username, user.email)
            
            # Create default lists
            default_lists = [
                UserList(
                    name="Liked Places",
                    description="Places you liked",
                    user_id=user.id,
                    is_default=True,
                    list_type="liked",
                    is_public=False
                ),
                UserList(
                    name="Disliked Places", 
                    description="Places you disliked",
                    user_id=user.id,
                    is_default=True,
                    list_type="disliked",
                    is_public=False
                )
            ]
            
            for default_list in default_lists:
                db.add(default_list)
            
            await db.commit()
            
            print(f"✅ Admin user created successfully!")
            print(f"   - ID: {user.id}")
            print(f"   - Email: {user.email}")
            print(f"   - Username: {user.username}")
            print(f"   - City: {user.city}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    finally:
        await graph_db.close()


if __name__ == "__main__":
    success = asyncio.run(create_admin_user())
    sys.exit(0 if success else 1)
