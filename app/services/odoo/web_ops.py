"""
Web Operations for Odoo

This module provides web-optimized operations:
- web_save: Save with specification (optimized for UI)
- web_read: Read with specification
- web_search_read: Search and read with specification
"""
from typing import Any, Dict, List, Optional
from loguru import logger

from .base import OdooOperationsService


class WebOperations(OdooOperationsService):
    """
    Web-optimized operations for Odoo

    These operations are designed for efficient communication between
    web clients and Odoo. They use specifications to define exactly
    what data to return, reducing payload size.

    The specification format allows:
    - Nested field reading for relational fields
    - Pagination of one2many fields
    - Custom ordering within relations

    Example:
        >>> service = WebOperations(...)
        >>> # Read order with nested line details
        >>> orders = await service.web_read(
        ...     model='sale.order',
        ...     ids=[order_id],
        ...     specification={
        ...         'name': {},
        ...         'partner_id': {'fields': {'name': {}, 'email': {}}},
        ...         'order_line': {
        ...             'fields': {
        ...                 'product_id': {'fields': {'name': {}}},
        ...                 'product_uom_qty': {},
        ...                 'price_unit': {},
        ...                 'price_subtotal': {}
        ...             },
        ...             'limit': 100,
        ...             'order': 'sequence ASC'
        ...         }
        ...     }
        ... )
    """

    async def web_save(
        self,
        model: str,
        ids: List[int],
        values: Dict[str, Any],
        specification: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Save records with specification

        Optimized save operation that returns data according to specification.
        Useful when you need to update and immediately display new values.

        Args:
            model: Model name
            ids: List of record IDs (empty for create)
            values: Values to save
            specification: Specification of fields to return
            context: Additional context

        Returns:
            List of updated records with specified fields

        Example:
            >>> result = await service.web_save(
            ...     model='sale.order',
            ...     ids=[order_id],
            ...     values={
            ...         'partner_id': customer_id,
            ...         'order_line': [
            ...             (0, 0, {'product_id': product_id, 'product_uom_qty': 5})
            ...         ]
            ...     },
            ...     specification={
            ...         'name': {},
            ...         'amount_total': {},
            ...         'order_line': {
            ...             'fields': {
            ...                 'name': {},
            ...                 'price_subtotal': {}
            ...             }
            ...         }
            ...     }
            ... )
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        logger.debug(
            f"web_save on {model}",
            extra={
                "model": model,
                "ids": ids,
                "spec_fields": list(specification.keys())
            }
        )

        result = await self._execute_kw(
            model=model,
            method="web_save",
            args=[ids, values, specification],
            kwargs=kwargs
        )

        return result if isinstance(result, list) else []

    async def web_read(
        self,
        model: str,
        ids: List[int],
        specification: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Read records with specification

        Optimized read that allows nested field reading and
        pagination of relational fields.

        Args:
            model: Model name
            ids: List of record IDs
            specification: Specification of fields to read
                Format: {
                    'field_name': {},  # Simple field
                    'many2one_field': {  # Related record
                        'fields': {
                            'name': {},
                            'email': {}
                        }
                    },
                    'one2many_field': {  # List of related records
                        'fields': {...},
                        'limit': 10,
                        'offset': 0,
                        'order': 'sequence ASC'
                    }
                }
            context: Additional context

        Returns:
            List of records with nested data

        Example:
            >>> orders = await service.web_read(
            ...     model='sale.order',
            ...     ids=[1, 2, 3],
            ...     specification={
            ...         'name': {},
            ...         'date_order': {},
            ...         'partner_id': {
            ...             'fields': {'name': {}, 'email': {}, 'phone': {}}
            ...         },
            ...         'order_line': {
            ...             'fields': {
            ...                 'product_id': {'fields': {'name': {}, 'default_code': {}}},
            ...                 'product_uom_qty': {},
            ...                 'price_unit': {},
            ...                 'discount': {},
            ...                 'price_subtotal': {}
            ...             },
            ...             'limit': 50,
            ...             'order': 'sequence ASC'
            ...         },
            ...         'amount_total': {},
            ...         'state': {}
            ...     }
            ... )
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        if not ids:
            return []

        logger.debug(
            f"web_read on {model}",
            extra={
                "model": model,
                "ids": ids,
                "spec_fields": list(specification.keys())
            }
        )

        result = await self._execute_kw(
            model=model,
            method="web_read",
            args=[ids, specification],
            kwargs=kwargs
        )

        return result if isinstance(result, list) else []

    async def web_search_read(
        self,
        model: str,
        domain: Optional[List] = None,
        specification: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None,
        count_limit: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search and read with specification

        Combines search and read with specification support.
        Returns records with length/count information.

        Args:
            model: Model name
            domain: Search domain
            specification: Fields specification
            limit: Maximum records
            offset: Records to skip
            order: Sort order
            count_limit: Limit for counting (performance)
            context: Additional context

        Returns:
            Dict containing:
                - records: List of records
                - length: Number of records returned
                - (optionally) total count

        Example:
            >>> result = await service.web_search_read(
            ...     model='sale.order',
            ...     domain=[['state', '=', 'sale']],
            ...     specification={
            ...         'name': {},
            ...         'partner_id': {'fields': {'name': {}}},
            ...         'amount_total': {},
            ...         'date_order': {}
            ...     },
            ...     limit=20,
            ...     offset=0,
            ...     order='date_order DESC'
            ... )
            >>> print(f"Found {result['length']} orders")
            >>> for order in result['records']:
            ...     print(f"{order['name']}: {order['amount_total']}")
        """
        kwargs: Dict[str, Any] = {
            "domain": domain or [],
            "specification": specification or {}
        }

        if limit is not None:
            kwargs["limit"] = limit
        if offset is not None:
            kwargs["offset"] = offset
        if order:
            kwargs["order"] = order
        if count_limit is not None:
            kwargs["count_limit"] = count_limit
        if context:
            kwargs["context"] = context

        logger.debug(
            f"web_search_read on {model}",
            extra={
                "model": model,
                "domain": domain,
                "limit": limit,
                "offset": offset,
                "spec_fields": list((specification or {}).keys())
            }
        )

        result = await self._execute_kw(
            model=model,
            method="web_search_read",
            args=[],
            kwargs=kwargs
        )

        if isinstance(result, dict):
            return result
        elif isinstance(result, list):
            return {"records": result, "length": len(result)}
        else:
            return {"records": [], "length": 0}

    def build_specification(
        self,
        fields: List[str],
        relations: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Helper to build specification from field list

        Args:
            fields: List of simple field names
            relations: Dict of relation field -> fields to include

        Returns:
            Specification dict

        Example:
            >>> spec = service.build_specification(
            ...     fields=['name', 'email', 'amount_total'],
            ...     relations={
            ...         'partner_id': ['name', 'email'],
            ...         'order_line': ['product_id', 'quantity', 'price']
            ...     }
            ... )
        """
        spec = {field: {} for field in fields}

        if relations:
            for rel_field, rel_fields in relations.items():
                spec[rel_field] = {
                    "fields": {f: {} for f in rel_fields}
                }

        return spec
