"""
Odoo Operations API routes - Flutter Compatible

Unified endpoint for all Odoo operations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from loguru import logger

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/systems", tags=["Odoo Operations"])
security = HTTPBearer()


class OdooOperationRequest(BaseModel):
    """Request model for Odoo operations"""
    model: str
    domain: Optional[List] = []
    fields: Optional[List[str]] = None
    limit: Optional[int] = 80
    offset: Optional[int] = 0
    order: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    ids: Optional[List[int]] = None
    values: Optional[Dict[str, Any]] = None
    specification: Optional[Dict[str, Any]] = None
    method: Optional[str] = None
    args: Optional[List] = None
    kwargs: Optional[Dict[str, Any]] = None


@router.post("/{system_id}/odoo/{operation}")
async def execute_odoo_operation(
    system_id: str,
    operation: str,
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute any Odoo operation through unified endpoint (Flutter compatible)

    This endpoint provides a unified interface for all Odoo RPC operations.

    Supported operations:
    - search_read: Search and read records
    - read: Read specific records by IDs
    - create: Create new record
    - write: Update existing records
    - unlink: Delete records
    - web_search_read: Web search read (Odoo 14+)
    - web_read: Web read (Odoo 14+)
    - web_save: Web save (Odoo 14+)
    - call_kw: Call any Odoo method
    - search_count: Count search results
    - fields_get: Get model fields information

    Args:
        system_id: System identifier (e.g., "odoo-prod")
        operation: Operation name
        request_data: Operation-specific data
        current_user: Current authenticated user
        db: Database session

    Returns:
        {
            "result": [...] or {...} or int or bool
        }

    Example:
        POST /api/v1/systems/odoo-prod/odoo/search_read
        {
            "model": "product.product",
            "domain": [],
            "fields": ["id", "name", "price"],
            "limit": 10
        }

    Raises:
        HTTPException: If operation fails or is invalid
    """

    # Validate operation
    valid_operations = [
        'search_read', 'read', 'create', 'write', 'unlink',
        'web_search_read', 'web_read', 'web_save',
        'call_kw', 'search_count', 'fields_get',
        'search', 'name_search', 'name_get'
    ]

    if operation not in valid_operations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid operation: {operation}. Must be one of {valid_operations}"
        )

    logger.info(
        f"User {current_user.username} executing {operation} on {system_id} "
        f"for model {request_data.get('model', 'N/A')}"
    )

    try:
        # Execute operation based on type
        result = await execute_operation_impl(
            system_id=system_id,
            operation=operation,
            data=request_data,
            user_id=current_user.id
        )

        return {"result": result}

    except ValueError as e:
        logger.error(f"Validation error in {operation}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Operation {operation} failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Operation failed: {str(e)}"
        )


async def execute_operation_impl(
    system_id: str,
    operation: str,
    data: Dict[str, Any],
    user_id: int
) -> Any:
    """
    Implementation of Odoo operations

    This is a mock implementation. In production, replace with actual
    Odoo RPC calls using xmlrpc or jsonrpc.

    Args:
        system_id: System identifier
        operation: Operation name
        data: Operation data
        user_id: User ID for audit

    Returns:
        Operation result
    """

    # TODO: Replace with actual Odoo adapter/connector
    # Example: adapter = get_odoo_adapter(system_id)
    # return await adapter.execute(operation, data)

    model = data.get("model")
    if not model and operation not in ["call_kw"]:
        raise ValueError("Model is required for this operation")

    # Mock implementations for each operation
    if operation == "search_read":
        # Return mock records
        domain = data.get("domain", [])
        fields = data.get("fields")
        limit = data.get("limit", 80)
        offset = data.get("offset", 0)

        logger.debug(
            f"search_read: model={model}, domain={domain}, "
            f"fields={fields}, limit={limit}, offset={offset}"
        )

        return [
            {
                "id": i + offset + 1,
                "name": f"Mock {model} {i + offset + 1}",
                "display_name": f"Mock Record {i + offset + 1}",
            }
            for i in range(min(limit, 10))
        ]

    elif operation == "read":
        # Return mock records by IDs
        ids = data.get("ids", [])
        fields = data.get("fields")

        logger.debug(f"read: model={model}, ids={ids}, fields={fields}")

        return [
            {
                "id": record_id,
                "name": f"Mock {model} {record_id}",
                "display_name": f"Mock Record {record_id}",
            }
            for record_id in ids
        ]

    elif operation == "create":
        # Return mock created ID
        values = data.get("values", {})

        logger.debug(f"create: model={model}, values={values}")

        # Return the new record ID
        return 123

    elif operation == "write":
        # Return success
        ids = data.get("ids", [])
        values = data.get("values", {})

        logger.debug(f"write: model={model}, ids={ids}, values={values}")

        return True

    elif operation == "unlink":
        # Return success
        ids = data.get("ids", [])

        logger.debug(f"unlink: model={model}, ids={ids}")

        return True

    elif operation == "search_count":
        # Return mock count
        domain = data.get("domain", [])

        logger.debug(f"search_count: model={model}, domain={domain}")

        return 42

    elif operation == "search":
        # Return mock IDs
        domain = data.get("domain", [])
        limit = data.get("limit", 80)
        offset = data.get("offset", 0)

        logger.debug(
            f"search: model={model}, domain={domain}, "
            f"limit={limit}, offset={offset}"
        )

        return list(range(offset + 1, offset + limit + 1))

    elif operation == "fields_get":
        # Return mock fields
        fields = data.get("fields")

        logger.debug(f"fields_get: model={model}, fields={fields}")

        return {
            "id": {
                "type": "integer",
                "string": "ID",
                "readonly": True
            },
            "name": {
                "type": "char",
                "string": "Name",
                "required": True
            },
            "display_name": {
                "type": "char",
                "string": "Display Name",
                "readonly": True
            },
        }

    elif operation == "name_search":
        # Return mock name search results
        name = data.get("name", "")
        domain = data.get("domain", [])
        limit = data.get("limit", 100)

        logger.debug(
            f"name_search: model={model}, name={name}, "
            f"domain={domain}, limit={limit}"
        )

        return [
            (i + 1, f"Mock {model} {i + 1}")
            for i in range(min(limit, 10))
        ]

    elif operation == "name_get":
        # Return mock name get results
        ids = data.get("ids", [])

        logger.debug(f"name_get: model={model}, ids={ids}")

        return [
            (record_id, f"Mock {model} {record_id}")
            for record_id in ids
        ]

    elif operation in ["web_search_read", "web_read", "web_save"]:
        # Return mock data for web methods (Odoo 14+)
        specification = data.get("specification", {})

        logger.debug(
            f"{operation}: model={model}, "
            f"specification={specification}"
        )

        if operation == "web_search_read":
            return {
                "records": [
                    {
                        "id": i + 1,
                        "name": f"Mock {model} {i + 1}",
                    }
                    for i in range(10)
                ],
                "length": 10,
            }
        elif operation == "web_read":
            return [
                {
                    "id": 1,
                    "name": f"Mock {model} 1",
                }
            ]
        else:  # web_save
            return [123]

    elif operation == "call_kw":
        # Call any Odoo method
        method = data.get("method")
        args = data.get("args", [])
        kwargs = data.get("kwargs", {})

        logger.debug(
            f"call_kw: model={model}, method={method}, "
            f"args={args}, kwargs={kwargs}"
        )

        return {"success": True, "method": method}

    else:
        raise ValueError(f"Operation {operation} not implemented")


@router.get("/{system_id}/odoo/models")
async def list_odoo_models(
    system_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    List available Odoo models (optional helper endpoint)

    Args:
        system_id: System identifier
        current_user: Current authenticated user

    Returns:
        List of available models
    """
    # TODO: Get actual models from Odoo
    # This would typically call ir.model.search_read()

    return {
        "result": [
            {"model": "res.partner", "name": "Contact"},
            {"model": "product.product", "name": "Product"},
            {"model": "sale.order", "name": "Sales Order"},
            {"model": "account.move", "name": "Invoice"},
            {"model": "stock.picking", "name": "Transfer"},
        ]
    }
