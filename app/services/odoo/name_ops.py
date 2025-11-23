"""
Name Operations for Odoo

This module provides name-related operations for Odoo:
- name_search: Search by name for Many2one fields
- name_get: Get display name for records
- name_create: Create record with just a name
"""
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger

from .base import OdooOperationsService


class NameOperations(OdooOperationsService):
    """
    Name operations for Odoo models

    These operations are primarily used for Many2one field interactions
    in forms and search dialogs.

    Example:
        >>> service = NameOperations(...)
        >>> # Search for customers by name
        >>> results = await service.name_search(
        ...     'res.partner',
        ...     name='Ahmed',
        ...     domain=[['customer_rank', '>', 0]],
        ...     limit=10
        ... )
        >>> for id, display_name in results:
        ...     print(f"{id}: {display_name}")
    """

    async def name_search(
        self,
        model: str,
        name: str = "",
        args: Optional[List] = None,
        operator: str = "ilike",
        limit: int = 100,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[int, str]]:
        """
        Search records by name

        Used for autocomplete in Many2one fields. Returns ID and display name.

        Args:
            model: Model name
            name: Search string
            args: Additional domain conditions
            operator: Search operator (default: 'ilike')
                Options: '=', 'ilike', 'like', '=ilike', '=like'
            limit: Maximum results
            context: Additional context

        Returns:
            List[Tuple[int, str]]: List of (id, display_name) tuples

        Example:
            >>> results = await service.name_search(
            ...     model='res.partner',
            ...     name='Ahmed',
            ...     args=[['is_company', '=', True]],
            ...     operator='ilike',
            ...     limit=10
            ... )
            >>> # Returns: [(1, 'Ahmed Company'), (5, 'Ahmed Trading')]
        """
        kwargs: Dict[str, Any] = {
            "name": name,
            "args": args or [],
            "operator": operator,
            "limit": limit
        }
        if context:
            kwargs["context"] = context

        logger.debug(
            f"name_search on {model}",
            extra={
                "model": model,
                "name": name,
                "operator": operator,
                "limit": limit
            }
        )

        result = await self._execute_kw(
            model=model,
            method="name_search",
            args=[],
            kwargs=kwargs
        )

        # Convert to list of tuples
        results = [(r[0], r[1]) for r in result] if result else []

        logger.debug(f"name_search returned {len(results)} results for {model}")
        return results

    async def name_get(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[int, str]]:
        """
        Get display names for records

        Returns the display name (name_get) for specified record IDs.
        The display name is computed based on the model's _rec_name field
        and _name_get method.

        Args:
            model: Model name
            ids: List of record IDs
            context: Additional context

        Returns:
            List[Tuple[int, str]]: List of (id, display_name) tuples

        Example:
            >>> names = await service.name_get(
            ...     model='res.partner',
            ...     ids=[1, 2, 3]
            ... )
            >>> # Returns: [(1, 'Company A'), (2, 'John Doe'), (3, 'Jane Smith')]
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        if not ids:
            return []

        logger.debug(
            f"name_get on {model}",
            extra={"model": model, "ids": ids}
        )

        result = await self._execute_kw(
            model=model,
            method="name_get",
            args=[ids],
            kwargs=kwargs
        )

        # Convert to list of tuples
        results = [(r[0], r[1]) for r in result] if result else []

        logger.debug(f"name_get returned {len(results)} names for {model}")
        return results

    async def name_create(
        self,
        model: str,
        name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[int, str]:
        """
        Create a record with just a name

        Quick creation method used in Many2one fields when the user
        types a name that doesn't exist and wants to create it.

        Args:
            model: Model name
            name: Name for the new record
            context: Additional context

        Returns:
            Tuple[int, str]: (id, display_name) of created record

        Example:
            >>> result = await service.name_create(
            ...     model='res.partner.category',
            ...     name='New Category'
            ... )
            >>> # Returns: (10, 'New Category')
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        logger.info(
            f"name_create on {model}",
            extra={"model": model, "name": name}
        )

        result = await self._execute_kw(
            model=model,
            method="name_create",
            args=[name],
            kwargs=kwargs
        )

        # Result is typically (id, display_name)
        if result and isinstance(result, (list, tuple)):
            created = (result[0], result[1])
            logger.info(f"name_create created {model} record: {created}")
            return created

        logger.warning(f"name_create returned unexpected result: {result}")
        return (0, "")

    async def get_display_names(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[int, str]:
        """
        Get display names as a dictionary

        Convenience method that returns names mapped by ID.

        Args:
            model: Model name
            ids: List of record IDs
            context: Additional context

        Returns:
            Dict[int, str]: Mapping of id -> display_name

        Example:
            >>> names = await service.get_display_names(
            ...     'res.partner',
            ...     [1, 2, 3]
            ... )
            >>> print(names[1])  # 'Company A'
        """
        results = await self.name_get(model, ids, context)
        return {id: name for id, name in results}
