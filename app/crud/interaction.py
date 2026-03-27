from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime

from app.models.place import UserInteraction, InteractionType
from app.schemas.place import UserInteractionCreate, UserInteraction as UserInteractionSchema, InteractionTypeEnum


class InteractionCRUD:
    async def create(
        self, 
        db: AsyncSession, 
        user_id: int, 
        interaction_create: UserInteractionCreate
    ) -> UserInteractionSchema:
        """Create or update a user interaction (unique by user/place)."""
        existing_result = await db.execute(
            select(UserInteraction).where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.place_id == interaction_create.place_id,
                )
            )
        )
        db_interaction = existing_result.scalar_one_or_none()

        if db_interaction:
            db_interaction.interaction_type = InteractionType(interaction_create.interaction_type.value)
        else:
            db_interaction = UserInteraction(
                user_id=user_id,
                place_id=interaction_create.place_id,
                interaction_type=InteractionType(interaction_create.interaction_type.value),
            )
            db.add(db_interaction)

        await db.commit()
        await db.refresh(db_interaction)
        return UserInteractionSchema.model_validate(db_interaction)
    
    async def get_user_interactions(
        self,
        db: AsyncSession,
        user_id: int,
        interaction_type: Optional[InteractionType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserInteractionSchema]:
        """Get user interactions, optionally filtered by type"""
        query = select(UserInteraction).where(UserInteraction.user_id == user_id)
        
        if interaction_type:
            query = query.where(UserInteraction.interaction_type == interaction_type)
        
        query = query.order_by(desc(UserInteraction.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        interactions = result.scalars().all()
        return [UserInteractionSchema.model_validate(interaction) for interaction in interactions]
    
    async def get_place_interactions(
        self,
        db: AsyncSession,
        place_id: int,
        interaction_type: Optional[InteractionType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserInteractionSchema]:
        """Get interactions for a specific place"""
        query = select(UserInteraction).where(UserInteraction.place_id == place_id)
        
        if interaction_type:
            query = query.where(UserInteraction.interaction_type == interaction_type)
        
        query = query.order_by(desc(UserInteraction.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        interactions = result.scalars().all()
        return [UserInteractionSchema.model_validate(interaction) for interaction in interactions]
    
    async def get_user_place_interaction(
        self,
        db: AsyncSession,
        user_id: int,
        place_id: int,
        interaction_type: InteractionType
    ) -> Optional[UserInteractionSchema]:
        """Get a specific user-place interaction"""
        result = await db.execute(
            select(UserInteraction).where(
                and_(
                    UserInteraction.user_id == user_id,
                    UserInteraction.place_id == place_id,
                    UserInteraction.interaction_type == interaction_type
                )
            )
        )
        interaction = result.scalar_one_or_none()
        return UserInteractionSchema.model_validate(interaction) if interaction else None
    
    async def count_interactions_by_type(
        self,
        db: AsyncSession,
        place_id: int,
        interaction_type: InteractionType
    ) -> int:
        """Count interactions of a specific type for a place"""
        from sqlalchemy import func
        result = await db.execute(
            select(func.count(UserInteraction.id)).where(
                and_(
                    UserInteraction.place_id == place_id,
                    UserInteraction.interaction_type == interaction_type
                )
            )
        )
        return result.scalar_one()


interaction_crud = InteractionCRUD()
