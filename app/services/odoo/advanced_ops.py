"""
Advanced Operations for Odoo

This module provides advanced operations for Odoo:
- onchange: Calculate values automatically when fields change
- read_group: Grouped data aggregation for reports/dashboards
- default_get: Get default values for new records
- copy: Duplicate existing records
"""
from typing import Any, Dict, List, Optional, Union
from loguru import logger

from .base import OdooOperationsService


class AdvancedOperations(OdooOperationsService):
    """
    Advanced operations for Odoo models

    This class provides sophisticated operations beyond basic CRUD:
    - onchange: Critical for form logic and automatic field calculations
    - read_group: Essential for reports and dashboards
    - default_get: Required for initializing new record forms
    - copy: Efficient record duplication

    Example:
        >>> service = AdvancedOperations(
        ...     odoo_url="https://demo.odoo.com",
        ...     database="demo",
        ...     username="admin",
        ...     password="admin123"
        ... )
        >>> # Calculate price when product changes
        >>> result = await service.onchange(
        ...     model='sale.order.line',
        ...     ids=[],
        ...     values={'order_id': 1, 'product_id': 50, 'product_uom_qty': 5},
        ...     field_name='product_id',
        ...     field_onchange={'product_id': '1', 'price_unit': '1'}
        ... )
        >>> print(f"Calculated price: {result['value'].get('price_unit')}")
    """

    async def onchange(
        self,
        model: str,
        ids: List[int],
        values: Dict[str, Any],
        field_name: str,
        field_onchange: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute onchange to calculate values automatically

        This is CRITICAL for proper form behavior in Odoo. When a field changes,
        onchange calculates related field values (e.g., price from product).

        Args:
            model: Model name (e.g., 'sale.order.line')
            ids: List of record IDs (empty [] for new record)
            values: Current field values of the record
            field_name: Name of the field that changed
            field_onchange: Specification of fields that have onchange
                Format: {'field_name': '1', 'another_field': '1'}
                The value '1' indicates the field participates in onchange

        Returns:
            Dict containing:
                - value: Dict of computed field values
                - warning: Optional warning message
                - domain: Optional updated field domains

        Raises:
            OdooExecutionError: If onchange fails

        Example:
            >>> # When product_id changes on sale order line
            >>> result = await service.onchange(
            ...     model='sale.order.line',
            ...     ids=[],  # New line
            ...     values={
            ...         'order_id': 100,
            ...         'product_id': 50,
            ...         'product_uom_qty': 5.0
            ...     },
            ...     field_name='product_id',
            ...     field_onchange={
            ...         'product_id': '1',
            ...         'price_unit': '1',
            ...         'discount': '1',
            ...         'tax_id': '1',
            ...         'name': '1'
            ...     }
            ... )
            >>> # Result contains calculated values
            >>> print(f"Price: {result['value']['price_unit']}")
            >>> print(f"Description: {result['value']['name']}")

            >>> # Handle quantity change
            >>> result = await service.onchange(
            ...     model='sale.order.line',
            ...     ids=[line_id],
            ...     values={
            ...         'order_id': 100,
            ...         'product_id': 50,
            ...         'product_uom_qty': 10.0  # Changed from 5 to 10
            ...     },
            ...     field_name='product_uom_qty',
            ...     field_onchange={
            ...         'product_uom_qty': '1',
            ...         'price_subtotal': '1'
            ...     }
            ... )
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        logger.debug(
            f"Onchange on {model}.{field_name}",
            extra={
                "model": model,
                "ids": ids,
                "field_name": field_name,
                "values_keys": list(values.keys())
            }
        )

        result = await self._execute_kw(
            model=model,
            method="onchange",
            args=[ids, values, field_name, field_onchange],
            kwargs=kwargs
        )

        onchange_result = result if isinstance(result, dict) else {}

        # Log any warnings
        if onchange_result.get('warning'):
            logger.warning(
                f"Onchange warning for {model}.{field_name}: {onchange_result['warning']}"
            )

        logger.debug(
            f"Onchange result for {model}.{field_name}",
            extra={
                "computed_fields": list(onchange_result.get('value', {}).keys()),
                "has_warning": bool(onchange_result.get('warning')),
                "has_domain": bool(onchange_result.get('domain'))
            }
        )

        return onchange_result

    async def read_group(
        self,
        model: str,
        domain: Optional[List] = None,
        fields: Optional[List[str]] = None,
        groupby: Optional[List[str]] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        orderby: Optional[str] = None,
        lazy: bool = True,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Read grouped/aggregated data

        Essential for reports and dashboards. Performs GROUP BY operations
        on the database level for efficient aggregation.

        Args:
            model: Model name
            domain: Search domain to filter records before grouping
            fields: Fields to aggregate (e.g., ['amount_total:sum'])
                Supports aggregation functions: sum, avg, min, max, count
            groupby: Fields to group by (e.g., ['partner_id', 'state'])
            offset: Offset for pagination of groups
            limit: Maximum number of groups to return
            orderby: Sort order for groups (e.g., 'amount_total desc')
            lazy: If True, only first level of groupby is done
            context: Additional context values

        Returns:
            List[Dict]: List of grouped records with aggregated values
                Each group contains:
                - Groupby field values
                - Aggregated field values
                - __domain: Domain to get records in this group
                - __count: Number of records in group (when lazy=True)

        Raises:
            OdooExecutionError: If operation fails

        Example:
            >>> # Sales by customer
            >>> sales_by_customer = await service.read_group(
            ...     model='sale.order',
            ...     domain=[['state', '=', 'sale']],
            ...     fields=['amount_total:sum'],
            ...     groupby=['partner_id'],
            ...     orderby='amount_total desc',
            ...     limit=10
            ... )
            >>> for group in sales_by_customer:
            ...     customer_name = group['partner_id'][1]
            ...     total = group['amount_total']
            ...     print(f"{customer_name}: ${total}")

            >>> # Orders by state and month
            >>> orders_by_state_month = await service.read_group(
            ...     model='sale.order',
            ...     domain=[],
            ...     fields=['id:count', 'amount_total:sum'],
            ...     groupby=['state', 'date_order:month']
            ... )

            >>> # Product sales with average
            >>> product_stats = await service.read_group(
            ...     model='sale.order.line',
            ...     domain=[['order_id.state', '=', 'sale']],
            ...     fields=['product_uom_qty:sum', 'price_unit:avg'],
            ...     groupby=['product_id']
            ... )
        """
        kwargs: Dict[str, Any] = {"lazy": lazy}

        if offset is not None:
            kwargs["offset"] = offset
        if limit is not None:
            kwargs["limit"] = limit
        if orderby:
            kwargs["orderby"] = orderby
        if context:
            kwargs["context"] = context

        logger.debug(
            f"read_group on {model}",
            extra={
                "model": model,
                "domain": domain,
                "fields": fields,
                "groupby": groupby,
                "orderby": orderby
            }
        )

        result = await self._execute_kw(
            model=model,
            method="read_group",
            args=[domain or [], fields or [], groupby or []],
            kwargs=kwargs
        )

        groups = result if isinstance(result, list) else []

        logger.debug(f"read_group returned {len(groups)} groups from {model}")
        return groups

    async def default_get(
        self,
        model: str,
        fields: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get default values for fields

        Returns the default values that would be used when creating a new record.
        Essential for initializing forms with proper defaults.

        Args:
            model: Model name
            fields: List of field names to get defaults for
            context: Additional context values (can affect defaults)

        Returns:
            Dict[str, Any]: Dictionary of field -> default value

        Raises:
            OdooExecutionError: If operation fails

        Example:
            >>> # Get defaults for new sale order
            >>> defaults = await service.default_get(
            ...     model='sale.order',
            ...     fields=['partner_id', 'date_order', 'pricelist_id', 'warehouse_id']
            ... )
            >>> print(f"Default date: {defaults.get('date_order')}")
            >>> print(f"Default pricelist: {defaults.get('pricelist_id')}")

            >>> # Defaults can be affected by context
            >>> defaults = await service.default_get(
            ...     model='sale.order',
            ...     fields=['partner_id', 'pricelist_id'],
            ...     context={'default_partner_id': 10}
            ... )
            >>> print(f"Partner: {defaults.get('partner_id')}")  # Should be 10
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        logger.debug(
            f"default_get for {model}",
            extra={"model": model, "fields": fields}
        )

        result = await self._execute_kw(
            model=model,
            method="default_get",
            args=[fields],
            kwargs=kwargs
        )

        defaults = result if isinstance(result, dict) else {}

        logger.debug(
            f"default_get returned {len(defaults)} defaults for {model}",
            extra={"defaults_keys": list(defaults.keys())}
        )

        return defaults

    async def copy(
        self,
        model: str,
        record_id: int,
        default: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Duplicate a record

        Creates a copy of the record with optional override values.
        The copy respects copy=False attributes on fields.

        Args:
            model: Model name
            record_id: ID of the record to copy
            default: Dictionary of values to override in the copy
            context: Additional context values

        Returns:
            int: ID of the newly created copy

        Raises:
            OdooExecutionError: If copy fails
            OdooRecordNotFoundException: If source record doesn't exist

        Example:
            >>> # Simple copy
            >>> new_partner_id = await service.copy(
            ...     model='res.partner',
            ...     record_id=original_partner_id
            ... )

            >>> # Copy with modified values
            >>> new_order_id = await service.copy(
            ...     model='sale.order',
            ...     record_id=original_order_id,
            ...     default={
            ...         'date_order': '2024-12-01',
            ...         'client_order_ref': 'COPY-REF-001'
            ...     }
            ... )

            >>> # Copy product with new code
            >>> new_product_id = await service.copy(
            ...     model='product.template',
            ...     record_id=product_id,
            ...     default={
            ...         'name': 'Copy of Product',
            ...         'default_code': 'PROD-COPY-001'
            ...     }
            ... )
        """
        kwargs: Dict[str, Any] = {}
        if context:
            kwargs["context"] = context

        logger.info(
            f"Copying {model} record {record_id}",
            extra={
                "model": model,
                "record_id": record_id,
                "default_keys": list(default.keys()) if default else []
            }
        )

        result = await self._execute_kw(
            model=model,
            method="copy",
            args=[record_id, default or {}],
            kwargs=kwargs
        )

        new_id = result if isinstance(result, int) else 0

        if new_id:
            logger.info(f"Copied {model} record {record_id} -> {new_id}")
        else:
            logger.error(f"Failed to copy {model} record {record_id}")

        return new_id

    async def get_report_data(
        self,
        model: str,
        domain: Optional[List] = None,
        measures: Optional[List[str]] = None,
        dimensions: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get report data with measures and dimensions

        Convenience method for building reports with aggregated data.
        Wraps read_group with a more intuitive API.

        Args:
            model: Model name
            domain: Filter domain
            measures: List of measure fields (e.g., ['amount_total', 'quantity'])
            dimensions: List of dimension fields (e.g., ['partner_id', 'date:month'])
            context: Additional context

        Returns:
            List of aggregated data points

        Example:
            >>> # Sales report
            >>> data = await service.get_report_data(
            ...     model='sale.order',
            ...     domain=[['state', 'in', ['sale', 'done']]],
            ...     measures=['amount_total', 'id'],
            ...     dimensions=['partner_id', 'date_order:month']
            ... )
        """
        # Convert measures to read_group format
        fields = [f"{m}:sum" if ':' not in m else m for m in (measures or [])]

        return await self.read_group(
            model=model,
            domain=domain,
            fields=fields,
            groupby=dimensions or [],
            context=context
        )
