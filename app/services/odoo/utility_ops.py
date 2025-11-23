"""
Utility Operations for Odoo

This module provides utility operations:
- exists: Check if records exist
"""
from typing import Any, Dict, List, Optional
from loguru import logger

from .base import OdooOperationsService


class UtilityOperations(OdooOperationsService):
    """
    Utility operations for Odoo models

    These operations provide helper functionality for common tasks.

    Example:
        >>> service = UtilityOperations(...)
        >>> # Check which records still exist
        >>> existing = await service.exists('res.partner', [1, 2, 999])
        >>> print(existing)  # [1, 2] (999 doesn't exist)
    """

    async def exists(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> List[int]:
        """
        Check which records exist

        Returns IDs of records that actually exist in the database.
        Useful for validating references before operations.

        Args:
            model: Model name
            ids: List of record IDs to check
            context: Additional context

        Returns:
            List[int]: IDs of existing records

        Example:
            >>> # Check if partners still exist
            >>> existing_ids = await service.exists(
            ...     'res.partner',
            ...     [1, 2, 3, 999, 1000]
            ... )
            >>> # Returns: [1, 2, 3] (if 999 and 1000 don't exist)

            >>> # Use for cleanup
            >>> invalid_ids = set(ids) - set(existing_ids)
            >>> print(f"Invalid IDs: {invalid_ids}")
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        if not ids:
            return []

        logger.debug(
            f"exists check for {model}",
            extra={"model": model, "ids": ids}
        )

        result = await self._execute_kw(
            model=model,
            method="exists",
            args=[ids],
            kwargs=kwargs
        )

        # exists() returns recordset, we need to extract IDs
        if isinstance(result, list):
            existing = result
        elif hasattr(result, 'ids'):
            existing = result.ids
        else:
            existing = []

        logger.debug(
            f"exists: {len(existing)}/{len(ids)} records exist in {model}",
            extra={
                "model": model,
                "requested": len(ids),
                "existing": len(existing)
            }
        )

        return existing

    async def exists_single(
        self,
        model: str,
        record_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if a single record exists

        Convenience method for checking single record existence.

        Args:
            model: Model name
            record_id: Record ID to check
            context: Additional context

        Returns:
            bool: True if record exists

        Example:
            >>> if await service.exists_single('res.partner', 123):
            ...     print("Partner exists")
        """
        existing = await self.exists(model, [record_id], context)
        return record_id in existing

    async def browse(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> List[int]:
        """
        Browse records (validate and return existing IDs)

        Similar to exists but commonly used term in Odoo.

        Args:
            model: Model name
            ids: List of record IDs
            context: Additional context

        Returns:
            List[int]: IDs of existing records
        """
        return await self.exists(model, ids, context)

    async def validate_references(
        self,
        references: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate multiple model references

        Batch validate references across different models.

        Args:
            references: List of dicts with 'model' and 'ids' keys
            context: Additional context

        Returns:
            Dict with validation results

        Example:
            >>> results = await service.validate_references([
            ...     {'model': 'res.partner', 'ids': [1, 2, 3]},
            ...     {'model': 'product.product', 'ids': [10, 20]},
            ...     {'model': 'sale.order', 'ids': [100, 200]}
            ... ])
            >>> for ref in results['valid']:
            ...     print(f"{ref['model']}: {ref['existing']}")
        """
        results = {
            'valid': [],
            'invalid': []
        }

        for ref in references:
            model = ref['model']
            ids = ref['ids']

            existing = await self.exists(model, ids, context)
            missing = list(set(ids) - set(existing))

            result_item = {
                'model': model,
                'requested': ids,
                'existing': existing,
                'missing': missing
            }

            if missing:
                results['invalid'].append(result_item)
            else:
                results['valid'].append(result_item)

        return results

    async def get_record_count(
        self,
        model: str,
        domain: Optional[List] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Get total record count for a model

        Alias for search_count for convenience.

        Args:
            model: Model name
            domain: Filter domain
            context: Additional context

        Returns:
            int: Number of records
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        result = await self._execute_kw(
            model=model,
            method="search_count",
            args=[domain or []],
            kwargs=kwargs
        )

        return result if isinstance(result, int) else 0

    async def get_xmlid(
        self,
        model: str,
        record_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Get XML ID (External ID) for a record

        Args:
            model: Model name
            record_id: Record ID
            context: Additional context

        Returns:
            str or None: External ID if exists

        Example:
            >>> xmlid = await service.get_xmlid('res.country', 1)
            >>> print(xmlid)  # 'base.us'
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        try:
            result = await self._execute_kw(
                model="ir.model.data",
                method="search_read",
                args=[[
                    ['model', '=', model],
                    ['res_id', '=', record_id]
                ]],
                kwargs={
                    "fields": ['module', 'name'],
                    "limit": 1,
                    **kwargs
                }
            )

            if result:
                module = result[0]['module']
                name = result[0]['name']
                return f"{module}.{name}"
            return None

        except Exception as e:
            logger.error(f"Failed to get xmlid: {e}")
            return None
