"""
View Operations for Odoo

This module provides view and field metadata operations:
- fields_get: Get field definitions
- fields_view_get: Get view definition (legacy, <= Odoo 15)
- get_view: Get view definition (Odoo 16+)
- load_views: Load multiple views (legacy)
- get_views: Load multiple views (Odoo 16+)
"""
from typing import Any, Dict, List, Optional, Tuple, Union
from loguru import logger

from .base import OdooOperationsService


class ViewOperations(OdooOperationsService):
    """
    View and metadata operations for Odoo models

    These operations provide field definitions and view architectures,
    essential for dynamic form generation and field introspection.

    Example:
        >>> service = ViewOperations(...)
        >>> # Get field definitions
        >>> fields = await service.fields_get(
        ...     'res.partner',
        ...     ['name', 'email', 'phone']
        ... )
        >>> for field_name, field_info in fields.items():
        ...     print(f"{field_name}: {field_info['type']}")
    """

    async def fields_get(
        self,
        model: str,
        fields: Optional[List[str]] = None,
        attributes: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get field definitions for a model

        Returns metadata about fields including type, label, selection values,
        relation info, and more.

        Args:
            model: Model name
            fields: List of field names (None for all fields)
            attributes: List of attributes to return per field
                Common: 'string', 'type', 'required', 'readonly',
                        'selection', 'relation', 'domain', 'help'
            context: Additional context

        Returns:
            Dict[str, Dict]: Field name -> field attributes

        Example:
            >>> fields = await service.fields_get(
            ...     model='res.partner',
            ...     fields=['name', 'email', 'country_id', 'category_id'],
            ...     attributes=['string', 'type', 'required', 'relation']
            ... )
            >>> # Result:
            >>> # {
            >>> #     'name': {'string': 'Name', 'type': 'char', 'required': True},
            >>> #     'email': {'string': 'Email', 'type': 'char', 'required': False},
            >>> #     'country_id': {'string': 'Country', 'type': 'many2one', 'relation': 'res.country'},
            >>> #     'category_id': {'string': 'Tags', 'type': 'many2many', 'relation': 'res.partner.category'}
            >>> # }
        """
        kwargs: Dict[str, Any] = {}
        if fields:
            kwargs["allfields"] = fields
        if attributes:
            kwargs["attributes"] = attributes
        if context:
            kwargs["context"] = context

        logger.debug(
            f"fields_get for {model}",
            extra={
                "model": model,
                "fields": fields,
                "attributes": attributes
            }
        )

        result = await self._execute_kw(
            model=model,
            method="fields_get",
            args=[],
            kwargs=kwargs
        )

        fields_info = result if isinstance(result, dict) else {}

        logger.debug(f"fields_get returned {len(fields_info)} fields for {model}")
        return fields_info

    async def fields_view_get(
        self,
        model: str,
        view_id: Optional[int] = None,
        view_type: str = "form",
        toolbar: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get view definition (legacy method for Odoo <= 15)

        Returns the view architecture and field information for a specific view.

        Args:
            model: Model name
            view_id: Specific view ID (None for default view)
            view_type: View type ('form', 'tree', 'kanban', 'search', etc.)
            toolbar: Include toolbar actions
            context: Additional context

        Returns:
            Dict containing:
                - arch: XML view architecture
                - fields: Field definitions used in view
                - name: View name
                - view_id: View ID

        Note:
            This method is deprecated in Odoo 16+. Use get_view() instead.

        Example:
            >>> view = await service.fields_view_get(
            ...     model='res.partner',
            ...     view_type='form'
            ... )
            >>> print(view['arch'])  # XML architecture
        """
        kwargs: Dict[str, Any] = {
            "view_type": view_type,
            "toolbar": toolbar
        }
        if view_id:
            kwargs["view_id"] = view_id
        if context:
            kwargs["context"] = context

        logger.debug(
            f"fields_view_get for {model}",
            extra={
                "model": model,
                "view_id": view_id,
                "view_type": view_type
            }
        )

        result = await self._execute_kw(
            model=model,
            method="fields_view_get",
            args=[],
            kwargs=kwargs
        )

        return result if isinstance(result, dict) else {}

    async def get_view(
        self,
        model: str,
        view_id: Optional[int] = None,
        view_type: str = "form",
        options: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get view definition (Odoo 16+ method)

        Modern replacement for fields_view_get with improved structure.

        Args:
            model: Model name
            view_id: Specific view ID (None/False for default)
            view_type: View type ('form', 'list', 'kanban', 'search', etc.)
            options: View options (toolbar, load_filters, etc.)
            context: Additional context

        Returns:
            Dict containing view definition

        Example:
            >>> view = await service.get_view(
            ...     model='res.partner',
            ...     view_type='form',
            ...     options={'toolbar': True}
            ... )
        """
        kwargs: Dict[str, Any] = {
            "view_id": view_id or False,
            "view_type": view_type,
            "options": options or {}
        }
        if context:
            kwargs["context"] = context

        logger.debug(
            f"get_view for {model}",
            extra={
                "model": model,
                "view_id": view_id,
                "view_type": view_type
            }
        )

        result = await self._execute_kw(
            model=model,
            method="get_view",
            args=[],
            kwargs=kwargs
        )

        return result if isinstance(result, dict) else {}

    async def load_views(
        self,
        model: str,
        views: List[Tuple[Union[int, bool], str]],
        options: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load multiple views at once (legacy method)

        Efficient method to load multiple view types in a single request.

        Args:
            model: Model name
            views: List of (view_id, view_type) tuples
                Example: [(False, 'form'), (False, 'list'), (False, 'search')]
            options: Load options (toolbar, load_filters, etc.)
            context: Additional context

        Returns:
            Dict containing views indexed by view_type

        Example:
            >>> views = await service.load_views(
            ...     model='res.partner',
            ...     views=[(False, 'form'), (False, 'list'), (False, 'search')],
            ...     options={'toolbar': True, 'load_filters': True}
            ... )
            >>> form_view = views['fields_views']['form']
            >>> list_view = views['fields_views']['list']
        """
        kwargs: Dict[str, Any] = {
            "views": views,
            "options": options or {}
        }
        if context:
            kwargs["context"] = context

        logger.debug(
            f"load_views for {model}",
            extra={
                "model": model,
                "views": views
            }
        )

        result = await self._execute_kw(
            model=model,
            method="load_views",
            args=[],
            kwargs=kwargs
        )

        return result if isinstance(result, dict) else {}

    async def get_views(
        self,
        model: str,
        views: List[Tuple[Union[int, bool], str]],
        options: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Load multiple views at once (Odoo 16+ method)

        Modern replacement for load_views.

        Args:
            model: Model name
            views: List of (view_id, view_type) tuples
            options: Load options
            context: Additional context

        Returns:
            Dict containing views

        Example:
            >>> views = await service.get_views(
            ...     model='sale.order',
            ...     views=[(False, 'form'), (False, 'list')],
            ...     options={'toolbar': True}
            ... )
        """
        kwargs: Dict[str, Any] = {
            "views": views,
            "options": options or {}
        }
        if context:
            kwargs["context"] = context

        logger.debug(
            f"get_views for {model}",
            extra={
                "model": model,
                "views": views
            }
        )

        result = await self._execute_kw(
            model=model,
            method="get_views",
            args=[],
            kwargs=kwargs
        )

        return result if isinstance(result, dict) else {}

    async def get_field_info(
        self,
        model: str,
        field_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get detailed information about a single field

        Convenience method for getting info about one field.

        Args:
            model: Model name
            field_name: Field name
            context: Additional context

        Returns:
            Dict with field attributes

        Example:
            >>> info = await service.get_field_info('res.partner', 'country_id')
            >>> print(f"Type: {info['type']}")
            >>> print(f"Relation: {info.get('relation')}")
        """
        fields = await self.fields_get(model, [field_name], context=context)
        return fields.get(field_name, {})

    async def get_selection_values(
        self,
        model: str,
        field_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, str]]:
        """
        Get selection field options

        Convenience method for getting selection field values.

        Args:
            model: Model name
            field_name: Selection field name
            context: Additional context

        Returns:
            List of (value, label) tuples

        Example:
            >>> states = await service.get_selection_values(
            ...     'sale.order',
            ...     'state'
            ... )
            >>> # Returns: [('draft', 'Quotation'), ('sent', 'Quotation Sent'), ...]
        """
        fields = await self.fields_get(
            model,
            [field_name],
            attributes=['selection'],
            context=context
        )

        field_info = fields.get(field_name, {})
        selection = field_info.get('selection', [])

        return [(s[0], s[1]) for s in selection] if selection else []
