"""
Permission Operations for Odoo

This module provides permission-related operations:
- check_access_rights: Check if user has rights for an operation
"""
from typing import Any, Dict, List, Optional
from loguru import logger

from .base import OdooOperationsService


class PermissionOperations(OdooOperationsService):
    """
    Permission operations for Odoo models

    These operations allow checking user permissions before
    attempting operations, useful for UI adaptation.

    Example:
        >>> service = PermissionOperations(...)
        >>> can_create = await service.check_access_rights(
        ...     'sale.order', 'create'
        ... )
        >>> if can_create:
        ...     # Show create button
    """

    async def check_access_rights(
        self,
        model: str,
        operation: str,
        raise_exception: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if current user has rights for an operation

        Verifies user permissions for CRUD operations on a model.
        Use this to conditionally show/hide UI elements.

        Args:
            model: Model name
            operation: Operation type ('create', 'read', 'write', 'unlink')
            raise_exception: If True, raises AccessError instead of returning False
            context: Additional context

        Returns:
            bool: True if user has the right, False otherwise

        Raises:
            OdooPermissionDeniedException: If raise_exception=True and no access

        Example:
            >>> # Check multiple operations
            >>> can_read = await service.check_access_rights('sale.order', 'read')
            >>> can_write = await service.check_access_rights('sale.order', 'write')
            >>> can_delete = await service.check_access_rights('sale.order', 'unlink')
            >>>
            >>> if can_read:
            ...     print("User can view orders")
            >>> if can_write:
            ...     print("User can edit orders")
        """
        kwargs: Dict[str, Any] = {
            "raise_exception": raise_exception
        }
        if context:
            kwargs["context"] = context

        logger.debug(
            f"check_access_rights for {model}.{operation}",
            extra={"model": model, "operation": operation}
        )

        result = await self._execute_kw(
            model=model,
            method="check_access_rights",
            args=[operation],
            kwargs=kwargs
        )

        has_access = bool(result)

        logger.debug(
            f"Access rights for {model}.{operation}: {has_access}",
            extra={
                "model": model,
                "operation": operation,
                "has_access": has_access
            }
        )

        return has_access

    async def check_all_access_rights(
        self,
        model: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, bool]:
        """
        Check all CRUD operations for a model

        Convenience method to check all standard operations at once.

        Args:
            model: Model name
            context: Additional context

        Returns:
            Dict with operations as keys and bool values

        Example:
            >>> rights = await service.check_all_access_rights('sale.order')
            >>> print(rights)
            >>> # {'create': True, 'read': True, 'write': True, 'unlink': False}
        """
        operations = ['create', 'read', 'write', 'unlink']
        rights = {}

        for op in operations:
            rights[op] = await self.check_access_rights(
                model, op, False, context
            )

        return rights

    async def check_access_rules(
        self,
        model: str,
        ids: List[int],
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check access rules for specific records

        Checks if user can perform operation on specific records,
        considering record rules (ir.rule).

        Args:
            model: Model name
            ids: List of record IDs to check
            operation: Operation type
            context: Additional context

        Returns:
            bool: True if access is granted

        Example:
            >>> # Check if user can delete these specific records
            >>> can_delete = await service.check_access_rules(
            ...     'sale.order',
            ...     [1, 2, 3],
            ...     'unlink'
            ... )
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        logger.debug(
            f"check_access_rules for {model}.{operation}",
            extra={"model": model, "operation": operation, "ids": ids}
        )

        try:
            result = await self._execute_kw(
                model=model,
                method="check_access_rule",
                args=[ids, operation],
                kwargs=kwargs
            )
            return True
        except Exception as e:
            logger.debug(f"Access rule check failed: {e}")
            return False

    async def get_user_permissions(
        self,
        models: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, bool]]:
        """
        Get permissions for multiple models

        Batch check permissions for multiple models.
        Useful for initializing app with user capabilities.

        Args:
            models: List of model names
            context: Additional context

        Returns:
            Dict mapping model name to permissions dict

        Example:
            >>> perms = await service.get_user_permissions([
            ...     'sale.order',
            ...     'purchase.order',
            ...     'account.move'
            ... ])
            >>> for model, rights in perms.items():
            ...     print(f"{model}: {rights}")
        """
        permissions = {}

        for model in models:
            permissions[model] = await self.check_all_access_rights(
                model, context
            )

        return permissions
