"""
Search Operations for Odoo

This module provides search-related operations for Odoo:
- search: Returns IDs only
- search_read: Search + read in one operation
- search_count: Count matching records
"""
from typing import Any, Dict, List, Optional, Union
import time
from loguru import logger

from .base import OdooOperationsService


class SearchOperations(OdooOperationsService):
    """
    Search operations for Odoo models

    This class provides efficient search operations with support for:
    - Complex domain expressions
    - Pagination (limit, offset)
    - Sorting (order)
    - Field selection

    All operations support the standard Odoo domain syntax:
    - ['field', '=', value]
    - ['field', 'in', [list]]
    - ['field', 'ilike', 'pattern']
    - '&', '|', '!' for logical operations

    Example:
        >>> service = SearchOperations(
        ...     odoo_url="https://demo.odoo.com",
        ...     database="demo",
        ...     username="admin",
        ...     password="admin123"
        ... )
        >>> # Search for company partners
        >>> ids = await service.search(
        ...     model='res.partner',
        ...     domain=[['is_company', '=', True]],
        ...     limit=100
        ... )
        >>> # Search and read in one operation
        >>> partners = await service.search_read(
        ...     model='res.partner',
        ...     domain=[['customer_rank', '>', 0]],
        ...     fields=['name', 'email', 'phone'],
        ...     limit=50,
        ...     order='name ASC'
        ... )
    """

    async def search(
        self,
        model: str,
        domain: Optional[List] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[int]:
        """
        Search for records, returns IDs only

        This is the most efficient way to get record IDs matching criteria.
        Use this when you only need IDs for further operations.

        Args:
            model: Model name (e.g., 'res.partner', 'sale.order')
            domain: Search domain expression
                Example: [['is_company', '=', True], ['country_id', '=', 1]]
            limit: Maximum number of records to return
            offset: Number of records to skip (for pagination)
            order: Sort order (e.g., 'name ASC', 'create_date DESC, id ASC')
            context: Additional context values

        Returns:
            List[int]: List of record IDs matching the domain

        Raises:
            OdooExecutionError: If search fails
            OdooModelNotFoundException: If model doesn't exist
            OdooPermissionDeniedException: If no read access

        Example:
            >>> # Basic search
            >>> ids = await service.search('res.partner', [['is_company', '=', True]])
            >>> print(ids)  # [1, 5, 10, 15, ...]

            >>> # Search with pagination
            >>> page1_ids = await service.search('res.partner', [], limit=50, offset=0)
            >>> page2_ids = await service.search('res.partner', [], limit=50, offset=50)

            >>> # Complex domain
            >>> ids = await service.search(
            ...     'sale.order',
            ...     [
            ...         '|',
            ...         ['state', '=', 'sale'],
            ...         ['state', '=', 'done']
            ...     ],
            ...     order='date_order DESC'
            ... )
        """
        kwargs: Dict[str, Any] = {}

        if limit is not None:
            kwargs["limit"] = limit
        if offset is not None:
            kwargs["offset"] = offset
        if order:
            kwargs["order"] = order
        if context:
            kwargs["context"] = context

        logger.debug(
            f"Searching {model}",
            extra={
                "model": model,
                "domain": domain,
                "limit": limit,
                "offset": offset,
                "order": order
            }
        )

        result = await self._execute_kw(
            model=model,
            method="search",
            args=[domain or []],
            kwargs=kwargs
        )

        ids = result if isinstance(result, list) else []

        logger.debug(f"Search returned {len(ids)} IDs from {model}")
        return ids

    async def search_read(
        self,
        model: str,
        domain: Optional[List] = None,
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search and read records in one operation

        This combines search and read into a single efficient operation.
        Use this when you need both to find records and read their data.

        Args:
            model: Model name (e.g., 'res.partner', 'product.product')
            domain: Search domain expression
            fields: List of fields to read. If None, reads all fields.
                Example: ['name', 'email', 'phone', 'city']
            limit: Maximum number of records
            offset: Number of records to skip
            order: Sort order
            context: Additional context values

        Returns:
            List[Dict[str, Any]]: List of records with requested fields

        Raises:
            OdooExecutionError: If operation fails
            OdooModelNotFoundException: If model doesn't exist
            OdooPermissionDeniedException: If no read access

        Example:
            >>> # Get customer list with specific fields
            >>> customers = await service.search_read(
            ...     model='res.partner',
            ...     domain=[['customer_rank', '>', 0]],
            ...     fields=['name', 'email', 'phone'],
            ...     limit=100,
            ...     order='name ASC'
            ... )
            >>> for customer in customers:
            ...     print(f"{customer['name']}: {customer['email']}")

            >>> # Get recent orders
            >>> orders = await service.search_read(
            ...     model='sale.order',
            ...     domain=[['state', 'in', ['sale', 'done']]],
            ...     fields=['name', 'partner_id', 'amount_total', 'date_order'],
            ...     limit=20,
            ...     order='date_order DESC'
            ... )
        """
        kwargs: Dict[str, Any] = {}

        if fields:
            kwargs["fields"] = fields
        if limit is not None:
            kwargs["limit"] = limit
        if offset is not None:
            kwargs["offset"] = offset
        if order:
            kwargs["order"] = order
        if context:
            kwargs["context"] = context

        start_time = time.time()
        
        logger.info(
            "🔍 [SEARCHREAD] Starting search_read operation\n"
            "   Model: {}\n"
            "   Domain: {}\n"
            "   Fields: {}\n"
            "   Limit: {}\n"
            "   Offset: {}\n"
            "   Order: {}".format(
                str(model),
                domain,
                fields,
                limit,
                offset,
                order
            )
        )

        try:
            result = await self._execute_kw(
                model=model,
                method="search_read",
                args=[domain or []],
                kwargs=kwargs
            )

            records = result if isinstance(result, list) else []
            duration = (time.time() - start_time) * 1000

            logger.info(
                "✅ [SEARCHREAD] Completed successfully\n"
                "   Model: {}\n"
                "   Records returned: {}\n"
                "   Duration: {:.2f}ms".format(
                    str(model),
                    len(records),
                    duration
                )
            )

            return records
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = str(e).replace('{', '{{').replace('}', '}}')
            logger.error(
                "❌ [SEARCHREAD] Error: {}\n"
                "   Model: {}\n"
                "   Domain: {}\n"
                "   Duration: {:.2f}ms".format(
                    error_msg,
                    str(model),
                    domain,
                    duration
                ),
                exc_info=True
            )
            raise
        return records

    async def search_count(
        self,
        model: str,
        domain: Optional[List] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count records matching the domain

        This is the most efficient way to get the count of matching records.
        Use for pagination metadata or dashboard statistics.

        Args:
            model: Model name
            domain: Search domain expression
            context: Additional context values

        Returns:
            int: Count of records matching the domain

        Raises:
            OdooExecutionError: If operation fails
            OdooModelNotFoundException: If model doesn't exist

        Example:
            >>> # Count total customers
            >>> total = await service.search_count(
            ...     'res.partner',
            ...     [['customer_rank', '>', 0]]
            ... )
            >>> print(f"Total customers: {total}")

            >>> # Count orders by status for dashboard
            >>> draft_count = await service.search_count(
            ...     'sale.order',
            ...     [['state', '=', 'draft']]
            ... )
            >>> confirmed_count = await service.search_count(
            ...     'sale.order',
            ...     [['state', '=', 'sale']]
            ... )
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        logger.debug(
            f"search_count on {model}",
            extra={"model": model, "domain": domain}
        )

        result = await self._execute_kw(
            model=model,
            method="search_count",
            args=[domain or []],
            kwargs=kwargs
        )

        count = result if isinstance(result, int) else 0

        logger.debug(f"search_count returned {count} for {model}")
        return count

    async def paginated_search_read(
        self,
        model: str,
        domain: Optional[List] = None,
        fields: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 50,
        order: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search with pagination metadata

        Convenience method that returns records with pagination info.

        Args:
            model: Model name
            domain: Search domain
            fields: Fields to read
            page: Page number (1-based)
            page_size: Number of records per page
            order: Sort order
            context: Additional context

        Returns:
            Dict containing:
                - records: List of records
                - total: Total count
                - page: Current page
                - page_size: Records per page
                - pages: Total number of pages

        Example:
            >>> result = await service.paginated_search_read(
            ...     model='res.partner',
            ...     domain=[['is_company', '=', True]],
            ...     fields=['name', 'email'],
            ...     page=1,
            ...     page_size=25
            ... )
            >>> print(f"Page {result['page']} of {result['pages']}")
            >>> print(f"Total records: {result['total']}")
            >>> for record in result['records']:
            ...     print(record['name'])
        """
        # Calculate offset
        offset = (page - 1) * page_size

        # Get total count
        total = await self.search_count(model, domain, context)

        # Get records for current page
        records = await self.search_read(
            model=model,
            domain=domain,
            fields=fields,
            limit=page_size,
            offset=offset,
            order=order,
            context=context
        )

        # Calculate total pages
        pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return {
            "records": records,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1
        }
