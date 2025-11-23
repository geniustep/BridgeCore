"""
CRUD Operations for Odoo

This module provides basic CRUD operations for Odoo:
- create: Create new record(s)
- read: Read record(s) by ID
- write: Update record(s)
- unlink: Delete record(s)
"""
from typing import Any, Dict, List, Optional, Union
from loguru import logger

from .base import OdooOperationsService


class CRUDOperations(OdooOperationsService):
    """
    CRUD operations for Odoo models

    This class provides the fundamental Create, Read, Update, Delete operations
    for any Odoo model. All operations handle proper error handling, logging,
    and return standardized responses.

    Example:
        >>> service = CRUDOperations(
        ...     odoo_url="https://demo.odoo.com",
        ...     database="demo",
        ...     username="admin",
        ...     password="admin123"
        ... )
        >>> # Create a new partner
        >>> partner_id = await service.create(
        ...     'res.partner',
        ...     {'name': 'New Customer', 'email': 'customer@example.com'}
        ... )
        >>> # Read the partner
        >>> partner = await service.read('res.partner', [partner_id], ['name', 'email'])
        >>> # Update the partner
        >>> await service.write('res.partner', [partner_id], {'phone': '+1234567890'})
        >>> # Delete the partner
        >>> await service.unlink('res.partner', [partner_id])
    """

    async def create(
        self,
        model: str,
        values: Union[Dict[str, Any], List[Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None
    ) -> Union[int, List[int]]:
        """
        Create new record(s) in Odoo

        Args:
            model: Model name (e.g., 'res.partner', 'sale.order')
            values: Dictionary of field values for single record,
                    or list of dictionaries for batch creation
            context: Additional context values

        Returns:
            int: Created record ID (single record)
            List[int]: List of created record IDs (batch creation)

        Raises:
            OdooExecutionError: If creation fails
            OdooPermissionDeniedException: If no create access
            OdooModelNotFoundException: If model doesn't exist

        Example:
            >>> # Create single record
            >>> partner_id = await service.create(
            ...     'res.partner',
            ...     {
            ...         'name': 'John Doe',
            ...         'email': 'john@example.com',
            ...         'is_company': False,
            ...         'customer_rank': 1
            ...     }
            ... )
            >>> print(f"Created partner ID: {partner_id}")

            >>> # Create multiple records (batch)
            >>> partner_ids = await service.create(
            ...     'res.partner',
            ...     [
            ...         {'name': 'Partner 1', 'email': 'p1@example.com'},
            ...         {'name': 'Partner 2', 'email': 'p2@example.com'},
            ...         {'name': 'Partner 3', 'email': 'p3@example.com'}
            ...     ]
            ... )
            >>> print(f"Created {len(partner_ids)} partners")
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        # Determine if batch or single creation
        is_batch = isinstance(values, list)

        logger.info(
            f"Creating {'batch of ' + str(len(values)) + ' records' if is_batch else 'record'} in {model}",
            extra={
                "model": model,
                "batch": is_batch,
                "count": len(values) if is_batch else 1
            }
        )

        result = await self._execute_kw(
            model=model,
            method="create",
            args=[values],
            kwargs=kwargs
        )

        if is_batch:
            logger.info(f"Created {len(result)} records in {model}: {result}")
        else:
            logger.info(f"Created record in {model} with ID: {result}")

        return result

    async def read(
        self,
        model: str,
        ids: List[int],
        fields: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Read records by ID

        Retrieve specific fields from records with known IDs.
        More efficient than search_read when IDs are known.

        Args:
            model: Model name
            ids: List of record IDs to read
            fields: List of fields to read. If None, reads all fields.
            context: Additional context values

        Returns:
            List[Dict[str, Any]]: List of records with requested fields

        Raises:
            OdooExecutionError: If read fails
            OdooPermissionDeniedException: If no read access
            OdooRecordNotFoundException: If record doesn't exist

        Example:
            >>> # Read specific fields from records
            >>> partners = await service.read(
            ...     'res.partner',
            ...     [1, 2, 3],
            ...     ['name', 'email', 'phone', 'street', 'city']
            ... )
            >>> for partner in partners:
            ...     print(f"{partner['id']}: {partner['name']} - {partner['email']}")

            >>> # Read all fields
            >>> full_partner = await service.read('res.partner', [1])
            >>> print(full_partner[0].keys())  # All available fields
        """
        kwargs: Dict[str, Any] = {}
        if fields:
            kwargs["fields"] = fields
        if context:
            kwargs["context"] = context

        if not ids:
            logger.warning(f"Read called with empty ids for {model}")
            return []

        logger.debug(
            f"Reading {len(ids)} records from {model}",
            extra={
                "model": model,
                "ids": ids,
                "fields": fields
            }
        )

        result = await self._execute_kw(
            model=model,
            method="read",
            args=[ids],
            kwargs=kwargs
        )

        records = result if isinstance(result, list) else []

        logger.debug(f"Read {len(records)} records from {model}")
        return records

    async def write(
        self,
        model: str,
        ids: List[int],
        values: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update existing records

        Args:
            model: Model name
            ids: List of record IDs to update
            values: Dictionary of field values to update
            context: Additional context values

        Returns:
            bool: True if update was successful

        Raises:
            OdooExecutionError: If update fails
            OdooPermissionDeniedException: If no write access
            OdooRecordNotFoundException: If record doesn't exist

        Example:
            >>> # Update single record
            >>> success = await service.write(
            ...     'res.partner',
            ...     [partner_id],
            ...     {
            ...         'name': 'Updated Name',
            ...         'phone': '+1234567890'
            ...     }
            ... )

            >>> # Update multiple records with same values
            >>> await service.write(
            ...     'sale.order',
            ...     [order1_id, order2_id, order3_id],
            ...     {'tag_ids': [(6, 0, [tag_id])]}
            ... )
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        if not ids:
            logger.warning(f"Write called with empty ids for {model}")
            return False

        logger.info(
            f"Updating {len(ids)} records in {model}",
            extra={
                "model": model,
                "ids": ids,
                "fields_updated": list(values.keys())
            }
        )

        result = await self._execute_kw(
            model=model,
            method="write",
            args=[ids, values],
            kwargs=kwargs
        )

        success = bool(result)
        logger.info(f"Updated records in {model}: {ids} - Success: {success}")
        return success

    async def unlink(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Delete records

        Permanently removes records from the database.
        Use with caution - this cannot be undone.

        Args:
            model: Model name
            ids: List of record IDs to delete
            context: Additional context values

        Returns:
            bool: True if deletion was successful

        Raises:
            OdooExecutionError: If deletion fails
            OdooPermissionDeniedException: If no unlink access
            OdooRecordNotFoundException: If record doesn't exist

        Example:
            >>> # Delete single record
            >>> success = await service.unlink('res.partner', [partner_id])

            >>> # Delete multiple records
            >>> await service.unlink(
            ...     'sale.order.line',
            ...     [line1_id, line2_id, line3_id]
            ... )
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        if not ids:
            logger.warning(f"Unlink called with empty ids for {model}")
            return False

        logger.info(
            f"Deleting {len(ids)} records from {model}",
            extra={"model": model, "ids": ids}
        )

        result = await self._execute_kw(
            model=model,
            method="unlink",
            args=[ids],
            kwargs=kwargs
        )

        success = bool(result)
        logger.info(f"Deleted records from {model}: {ids} - Success: {success}")
        return success

    async def create_or_update(
        self,
        model: str,
        domain: List,
        values: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a record if it doesn't exist, otherwise update it

        This is a convenience method that combines search and create/write.

        Args:
            model: Model name
            domain: Search domain to find existing record
            values: Field values to create/update
            context: Additional context values

        Returns:
            Dict containing:
                - id: Record ID
                - created: True if new record was created
                - updated: True if existing record was updated

        Example:
            >>> result = await service.create_or_update(
            ...     'res.partner',
            ...     [['email', '=', 'john@example.com']],
            ...     {
            ...         'name': 'John Doe',
            ...         'email': 'john@example.com',
            ...         'phone': '+1234567890'
            ...     }
            ... )
            >>> if result['created']:
            ...     print(f"Created new partner with ID: {result['id']}")
            >>> else:
            ...     print(f"Updated existing partner ID: {result['id']}")
        """
        from .search_ops import SearchOperations

        # Search for existing record
        search_service = SearchOperations(
            odoo_url=self.odoo_url,
            database=self.database,
            username=self.username,
            password=self.password,
            context=self.base_context,
            session_id=self._session_id
        )

        # Copy authentication state
        search_service._uid = self._uid
        search_service._client = self._client

        existing_ids = await search_service.search(
            model=model,
            domain=domain,
            limit=1,
            context=context
        )

        if existing_ids:
            # Update existing record
            record_id = existing_ids[0]
            await self.write(model, [record_id], values, context)
            return {"id": record_id, "created": False, "updated": True}
        else:
            # Create new record
            record_id = await self.create(model, values, context)
            return {"id": record_id, "created": True, "updated": False}

    async def batch_update(
        self,
        model: str,
        updates: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update multiple records with different values

        Args:
            model: Model name
            updates: List of dicts with 'id' and 'values' keys
            context: Additional context values

        Returns:
            Dict containing:
                - success: List of successfully updated IDs
                - failed: List of failed updates with errors

        Example:
            >>> results = await service.batch_update(
            ...     'res.partner',
            ...     [
            ...         {'id': 1, 'values': {'name': 'Updated 1'}},
            ...         {'id': 2, 'values': {'name': 'Updated 2'}},
            ...         {'id': 3, 'values': {'name': 'Updated 3'}}
            ...     ]
            ... )
            >>> print(f"Updated: {results['success']}")
            >>> print(f"Failed: {results['failed']}")
        """
        success = []
        failed = []

        for update in updates:
            record_id = update.get('id')
            values = update.get('values', {})

            if not record_id:
                failed.append({"id": None, "error": "Missing record ID"})
                continue

            try:
                await self.write(model, [record_id], values, context)
                success.append(record_id)
            except Exception as e:
                failed.append({"id": record_id, "error": str(e)})

        return {"success": success, "failed": failed}
