"""
Custom Operations for Odoo

This module provides custom method calling capabilities:
- call_method: Call any public method on a model
- Action helpers: action_confirm, button_cancel, etc.
"""
from typing import Any, Dict, List, Optional
import time
from loguru import logger

from .base import OdooOperationsService


class CustomOperations(OdooOperationsService):
    """
    Custom operations for Odoo models

    Provides the ability to call any public method on Odoo models,
    including workflow actions and custom business logic.

    Example:
        >>> service = CustomOperations(...)
        >>> # Confirm a sale order
        >>> await service.action_confirm('sale.order', [order_id])
        >>>
        >>> # Call custom method
        >>> result = await service.call_method(
        ...     'sale.order',
        ...     'custom_calculation_method',
        ...     args=[[order_id], param1, param2],
        ...     kwargs={'option': True}
        ... )
    """

    async def call_method(
        self,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Call any public method on a model

        Generic method to call any Odoo model method.
        Use this for custom methods not covered by standard operations.

        Args:
            model: Model name
            method: Method name to call
            args: Positional arguments (typically starts with record IDs)
            kwargs: Keyword arguments
            context: Additional context

        Returns:
            Any: Result from the method

        Raises:
            OdooExecutionError: If method call fails
            OdooPermissionDeniedException: If method not allowed

        Example:
            >>> # Call button method
            >>> result = await service.call_method(
            ...     'sale.order',
            ...     'action_confirm',
            ...     args=[[order_id]]
            ... )

            >>> # Call method with parameters
            >>> result = await service.call_method(
            ...     'stock.picking',
            ...     'action_assign',
            ...     args=[[picking_id]]
            ... )

            >>> # Call custom method with kwargs
            >>> result = await service.call_method(
            ...     'your.model',
            ...     'custom_process',
            ...     args=[[record_id], 'param1'],
            ...     kwargs={'option': True, 'value': 100}
            ... )
        """
        method_kwargs: Dict[str, Any] = kwargs.copy() if kwargs else {}
        if context:
            if "context" in method_kwargs:
                method_kwargs["context"].update(context)
            else:
                method_kwargs["context"] = context

        start_time = time.time()
        
        # Escape curly braces in args for .format()
        args_safe = str(args).replace('{', '{{').replace('}', '}}')
        logger.info(
            "🔧 [CALL_KW] Starting call_kw operation\n"
            "   Model: {}\n"
            "   Method: {}\n"
            "   Args: {}\n"
            "   Kwargs keys: {}".format(
                str(model),
                str(method),
                args_safe,
                list(method_kwargs.keys()) if method_kwargs else []
            )
        )

        try:
            result = await self._execute_kw(
                model=model,
                method=method,
                args=args or [],
                kwargs=method_kwargs
            )

            duration = (time.time() - start_time) * 1000
            result_preview = str(result)[:200] if result else "None"
            result_preview_safe = result_preview.replace('{', '{{').replace('}', '}}')
            
            logger.info(
                "✅ [CALL_KW] Completed successfully\n"
                "   Model: {}\n"
                "   Method: {}\n"
                "   Result preview: {}\n"
                "   Duration: {:.2f}ms".format(
                    str(model),
                    str(method),
                    result_preview_safe,
                    duration
                )
            )
            
            return result
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            error_msg = str(e).replace('{', '{{').replace('}', '}}')
            logger.error(
                "❌ [CALL_KW] Error: {}\n"
                "   Model: {}\n"
                "   Method: {}\n"
                "   Duration: {:.2f}ms".format(
                    error_msg,
                    str(model),
                    str(method),
                    duration
                ),
                exc_info=True
            )
            raise

    # ==================== Sale Order Actions ====================

    async def action_confirm(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Confirm records (generic action_confirm)

        Commonly used for sale.order, purchase.order, etc.

        Args:
            model: Model name
            ids: Record IDs to confirm
            context: Additional context

        Returns:
            Result from action_confirm

        Example:
            >>> await service.action_confirm('sale.order', [order_id])
        """
        return await self.call_method(
            model=model,
            method="action_confirm",
            args=[ids],
            context=context
        )

    async def action_cancel(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Cancel records (generic action_cancel)

        Args:
            model: Model name
            ids: Record IDs to cancel
            context: Additional context

        Returns:
            Result from action_cancel

        Example:
            >>> await service.action_cancel('sale.order', [order_id])
        """
        return await self.call_method(
            model=model,
            method="action_cancel",
            args=[ids],
            context=context
        )

    async def action_draft(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Set records to draft state

        Args:
            model: Model name
            ids: Record IDs
            context: Additional context

        Returns:
            Result from action_draft
        """
        return await self.call_method(
            model=model,
            method="action_draft",
            args=[ids],
            context=context
        )

    async def button_cancel(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Cancel via button (button_cancel)

        Some models use button_cancel instead of action_cancel.

        Args:
            model: Model name
            ids: Record IDs
            context: Additional context

        Returns:
            Result from button_cancel
        """
        return await self.call_method(
            model=model,
            method="button_cancel",
            args=[ids],
            context=context
        )

    # ==================== Invoice Actions ====================

    async def action_post(
        self,
        ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Post invoices/journal entries

        Args:
            ids: Record IDs to post
            context: Additional context

        Returns:
            Result from action_post

        Example:
            >>> await service.action_post([invoice_id])
        """
        return await self.call_method(
            model="account.move",
            method="action_post",
            args=[ids],
            context=context
        )

    async def button_draft(
        self,
        model: str,
        ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Reset to draft via button

        Args:
            model: Model name
            ids: Record IDs
            context: Additional context

        Returns:
            Result from button_draft
        """
        return await self.call_method(
            model=model,
            method="button_draft",
            args=[ids],
            context=context
        )

    # ==================== Stock/Inventory Actions ====================

    async def action_assign(
        self,
        ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Assign/reserve stock for pickings

        Args:
            ids: Picking IDs
            context: Additional context

        Returns:
            Result from action_assign

        Example:
            >>> await service.action_assign([picking_id])
        """
        return await self.call_method(
            model="stock.picking",
            method="action_assign",
            args=[ids],
            context=context
        )

    async def button_validate(
        self,
        ids: List[int],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Validate stock pickings

        Args:
            ids: Picking IDs
            context: Additional context

        Returns:
            Result from button_validate

        Example:
            >>> await service.button_validate([picking_id])
        """
        return await self.call_method(
            model="stock.picking",
            method="button_validate",
            args=[ids],
            context=context
        )

    # ==================== Message/Activity Actions ====================

    async def message_post(
        self,
        model: str,
        ids: List[int],
        body: str,
        message_type: str = "comment",
        subtype_xmlid: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Post a message on records

        Args:
            model: Model name
            ids: Record IDs
            body: Message body (HTML)
            message_type: Type of message ('comment', 'notification')
            subtype_xmlid: Message subtype XML ID
            context: Additional context

        Returns:
            Created message ID(s)

        Example:
            >>> await service.message_post(
            ...     'sale.order',
            ...     [order_id],
            ...     body="<p>Order confirmed!</p>",
            ...     message_type="comment"
            ... )
        """
        kwargs = {
            "body": body,
            "message_type": message_type
        }
        if subtype_xmlid:
            kwargs["subtype_xmlid"] = subtype_xmlid

        return await self.call_method(
            model=model,
            method="message_post",
            args=[ids],
            kwargs=kwargs,
            context=context
        )

    # ==================== Generic Workflow Actions ====================

    async def execute_workflow(
        self,
        model: str,
        ids: List[int],
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute generic workflow action

        Wrapper for calling common workflow actions.

        Args:
            model: Model name
            ids: Record IDs
            action: Action method name
            context: Additional context

        Returns:
            Action result

        Example:
            >>> # Confirm order
            >>> await service.execute_workflow(
            ...     'sale.order', [1], 'action_confirm'
            ... )
            >>> # Validate picking
            >>> await service.execute_workflow(
            ...     'stock.picking', [10], 'button_validate'
            ... )
        """
        return await self.call_method(
            model=model,
            method=action,
            args=[ids],
            context=context
        )

    async def get_available_actions(
        self,
        model: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Get common available actions for a model

        Returns a list of commonly available actions based on model type.
        This is a helper method - actual availability depends on model.

        Args:
            model: Model name
            context: Additional context

        Returns:
            List of action method names

        Note:
            This returns suggested actions based on model patterns.
            Actual availability should be verified by calling the action.
        """
        common_actions = ['action_confirm', 'action_cancel', 'action_draft']

        model_specific = {
            'sale.order': ['action_confirm', 'action_cancel', 'action_draft', 'action_quotation_send'],
            'purchase.order': ['button_confirm', 'button_cancel', 'button_draft'],
            'account.move': ['action_post', 'button_draft', 'button_cancel'],
            'stock.picking': ['action_assign', 'button_validate', 'action_cancel'],
            'mrp.production': ['action_confirm', 'action_assign', 'button_mark_done', 'action_cancel'],
        }

        return model_specific.get(model, common_actions)
