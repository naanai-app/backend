from neo4j import AsyncGraphDatabase
from typing import Dict, List, Optional
from app.core.config import settings


class GraphDatabase:
    def __init__(self):
        self.driver = None
    
    async def connect(self):
        """Initialize Neo4j connection"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            # Test the connection
            await self.driver.verify_connectivity()
            print(f"✅ Connected to Neo4j at {settings.NEO4J_URI}")
        except Exception as e:
            print(f"❌ Failed to connect to Neo4j: {e}")
            self.driver = None
            raise
    
    async def close(self):
        """Close Neo4j connection"""
        if self.driver:
            await self.driver.close()
    
    async def create_user_node(self, user_id: int, username: str, email: str):
        """Create a user node in the graph"""
        async with self.driver.session() as session:
            await session.run(
                "MERGE (u:User {id: $user_id, username: $username, email: $email})",
                user_id=user_id, username=username, email=email
            )
    
    async def create_follow_relationship(self, follower_id: int, followed_id: int):
        """Create a FOLLOWS relationship between users"""
        async with self.driver.session() as session:
            await session.run(
                """
                MATCH (follower:User {id: $follower_id})
                MATCH (followed:User {id: $followed_id})
                MERGE (follower)-[:FOLLOWS]->(followed)
                """,
                follower_id=follower_id, followed_id=followed_id
            )
    
    async def remove_follow_relationship(self, follower_id: int, followed_id: int):
        """Remove a FOLLOWS relationship between users"""
        async with self.driver.session() as session:
            await session.run(
                """
                MATCH (follower:User {id: $follower_id})-[r:FOLLOWS]->(followed:User {id: $followed_id})
                DELETE r
                """,
                follower_id=follower_id, followed_id=followed_id
            )
    
    async def get_followers(self, user_id: int) -> List[Dict]:
        """Get all followers of a user"""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (follower:User)-[:FOLLOWS]->(user:User {id: $user_id})
                RETURN follower.id as id, follower.username as username
                """,
                user_id=user_id
            )
            return [record.data() async for record in result]
    
    async def get_following(self, user_id: int) -> List[Dict]:
        """Get all users that a user is following"""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (user:User {id: $user_id})-[:FOLLOWS]->(following:User)
                RETURN following.id as id, following.username as username
                """,
                user_id=user_id
            )
            return [record.data() async for record in result]
    
    async def get_friends(self, user_id: int) -> List[Dict]:
        """Get mutual followers (friends) of a user"""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (user:User {id: $user_id})-[:FOLLOWS]->(friend:User)
                MATCH (friend)-[:FOLLOWS]->(user)
                RETURN friend.id as id, friend.username as username
                """,
                user_id=user_id
            )
            return [record.data() async for record in result]
    
    async def is_following(self, follower_id: int, followed_id: int) -> bool:
        """Check if one user follows another"""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (follower:User {id: $follower_id})-[:FOLLOWS]->(followed:User {id: $followed_id})
                RETURN COUNT(*) as count
                """,
                follower_id=follower_id, followed_id=followed_id
            )
            record = await result.single()
            return record["count"] > 0
    
    async def get_recommended_users(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user recommendations based on mutual connections"""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (user:User {id: $user_id})-[:FOLLOWS]->(friend:User)-[:FOLLOWS]->(recommendation:User)
                WHERE NOT (user)-[:FOLLOWS]->(recommendation) AND recommendation.id <> $user_id
                RETURN recommendation.id as id, recommendation.username as username, 
                       COUNT(*) as mutual_connections
                ORDER BY mutual_connections DESC
                LIMIT $limit
                """,
                user_id=user_id, limit=limit
            )
            return [record.data() async for record in result]


# Global graph database instance
graph_db = GraphDatabase()


async def get_graph_db():
    """Dependency to get graph database instance"""
    return graph_db
