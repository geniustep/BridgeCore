"""
Base Repository with query optimization
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, TypeVar, Generic, Type, Dict, Any

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository with performance optimizations

    Features:
    - Eager loading to avoid N+1 queries
    - Bulk operations
    - Filtering and pagination
    - Optimized queries
    """

    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(
        self,
        id: int,
        relationships: Optional[List[str]] = None
    ) -> Optional[T]:
        """
        Get a single record by ID with optional relationship loading

        Args:
            id: Record ID
            relationships: List of relationship names for eager loading

        Example:
            user = await repo.get_by_id(1, relationships=["systems", "audit_logs"])
        """
        query = select(self.model).where(self.model.id == id)

        # Load relationships eagerly to avoid N+1 problem
        if relationships:
            for rel in relationships:
                query = query.options(selectinload(getattr(self.model, rel)))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[T]:
        """
        Get multiple records with filtering and pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field:value filters
            order_by: Field name to order by (prefix with '-' for descending)

        Example:
            users = await repo.get_multi(
                skip=0,
                limit=10,
                filters={"is_active": True},
                order_by="-created_at"
            )
        """
        query = select(self.model)

        # Apply filters
        if filters:
            for key, value in filters.items():
                query = query.where(getattr(self.model, key) == value)

        # Apply ordering
        if order_by:
            if order_by.startswith("-"):
                query = query.order_by(getattr(self.model, order_by[1:]).desc())
            else:
                query = query.order_by(getattr(self.model, order_by))

        # Pagination
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, obj: T) -> T:
        """
        Create a new record

        Args:
            obj: Model instance to create

        Returns:
            Created instance
        """
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def bulk_create(self, objects: List[T]) -> List[T]:
        """
        Create multiple records in bulk (more efficient)

        Args:
            objects: List of model instances to create

        Returns:
            List of created instances
        """
        self.session.add_all(objects)
        await self.session.commit()
        return objects

    async def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Update a record by ID

        Args:
            id: Record ID
            data: Dictionary of fields to update

        Returns:
            Updated instance or None
        """
        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**data)
            .returning(self.model)
        )
        result = await self.session.execute(query)
        await self.session.commit()
        return result.scalar_one_or_none()

    async def delete(self, id: int) -> bool:
        """
        Delete a record by ID

        Args:
            id: Record ID

        Returns:
            True if deleted, False otherwise
        """
        query = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filters

        Args:
            filters: Dictionary of field:value filters

        Returns:
            Number of records
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(self.model)

        if filters:
            for key, value in filters.items():
                query = query.where(getattr(self.model, key) == value)

        result = await self.session.execute(query)
        return result.scalar()

    async def exists(self, id: int) -> bool:
        """
        Check if a record exists

        Args:
            id: Record ID

        Returns:
            True if exists, False otherwise
        """
        from sqlalchemy import exists as sql_exists

        query = select(sql_exists().where(self.model.id == id))
        result = await self.session.execute(query)
        return result.scalar()
