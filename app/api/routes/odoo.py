"""
Odoo Operations API routes - Flutter Compatible

Unified endpoint for all Odoo operations with caching and optimization
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from loguru import logger
import time

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.cache_service import CacheService
from app.services.query_optimizer import query_optimizer
from app.core.monitoring import record_cache_hit, record_cache_miss, record_api_operation
from app.core.config import settings
from app.api.routes.websocket import manager as ws_manager

router = APIRouter(prefix="/api/v1/systems", tags=["Odoo Operations"])
security = HTTPBearer()

# Initialize cache service
cache_service = CacheService(settings.REDIS_URL)


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

    This endpoint provides a unified interface for all Odoo RPC operations
    with automatic caching and query optimization.

    Features:
    - Redis caching for read operations (10x faster responses)
    - Query optimization to prevent N+1 queries
    - Automatic cache invalidation on writes
    - Prometheus metrics tracking

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
            "result": [...] or {...} or int or bool,
            "cached": bool (optional),
            "optimized": bool (optional)
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
    start_time = time.time()

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

    model = request_data.get('model', 'N/A')
    logger.info(
        f"User {current_user.username} executing {operation} on {system_id} "
        f"for model {model}"
    )

    try:
        cached = False
        optimized = False

        # Check if operation should be cached
        if query_optimizer.should_cache(operation):
            # Generate cache key
            cache_key = query_optimizer.generate_cache_key(
                system_id=system_id,
                operation=operation,
                model=model,
                domain=str(request_data.get('domain', [])),
                fields=str(request_data.get('fields', [])),
                limit=request_data.get('limit'),
                offset=request_data.get('offset'),
                ids=str(request_data.get('ids', []))
            )

            # Try to get from cache
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache HIT for {operation} on {model}")
                record_cache_hit(operation)

                # Record metrics
                duration = time.time() - start_time
                record_api_operation("odoo", model, operation, duration, True)

                return {
                    "result": cached_result,
                    "cached": True
                }

            logger.debug(f"Cache MISS for {operation} on {model}")
            record_cache_miss(operation)

        # Optimize query parameters
        if operation in ['search_read', 'web_search_read']:
            # Optimize fields
            original_fields = request_data.get('fields')
            optimized_fields = query_optimizer.optimize_fields(
                model=model,
                fields=original_fields,
                expand_relations=True
            )
            if optimized_fields != original_fields:
                request_data['fields'] = optimized_fields
                optimized = True

            # Optimize domain
            original_domain = request_data.get('domain', [])
            optimized_domain = query_optimizer.optimize_domain(original_domain)
            if optimized_domain != original_domain:
                request_data['domain'] = optimized_domain
                optimized = True

            # Optimize limit
            original_limit = request_data.get('limit')
            optimized_limit = query_optimizer.optimize_limit(original_limit, operation)
            if optimized_limit != original_limit:
                request_data['limit'] = optimized_limit
                optimized = True

            # Add order if not specified
            if not request_data.get('order'):
                request_data['order'] = query_optimizer.optimize_order(None, model)

        # Execute operation
        result = await execute_operation_impl(
            system_id=system_id,
            operation=operation,
            data=request_data,
            user_id=current_user.id
        )

        # Cache the result if applicable
        if query_optimizer.should_cache(operation):
            cache_ttl = query_optimizer.get_cache_ttl(operation)
            await cache_service.set(cache_key, result, ttl=cache_ttl)
            logger.debug(f"Cached result for {operation} on {model} (TTL: {cache_ttl}s)")

        # Handle write operations - invalidate cache and broadcast updates
        if operation in ['create', 'write', 'unlink', 'web_save']:
            # Invalidate cache
            invalidation_patterns = query_optimizer.get_invalidation_patterns(
                system_id=system_id,
                model=model,
                operation=operation
            )

            for pattern in invalidation_patterns:
                deleted_count = await cache_service.delete_pattern(pattern)
                if deleted_count > 0:
                    logger.info(
                        f"Invalidated {deleted_count} cache entries "
                        f"matching pattern: {pattern}"
                    )

            # Broadcast updates via WebSocket
            if operation == 'create' and isinstance(result, int):
                # New record created
                await ws_manager.broadcast_model_update(
                    system_id=system_id,
                    model=model,
                    record_id=result,
                    operation='create',
                    data=request_data.get('values', {})
                )

            elif operation == 'write':
                # Records updated
                record_ids = request_data.get('ids', [])
                for record_id in record_ids:
                    await ws_manager.broadcast_model_update(
                        system_id=system_id,
                        model=model,
                        record_id=record_id,
                        operation='write',
                        data=request_data.get('values', {})
                    )

            elif operation == 'unlink':
                # Records deleted
                record_ids = request_data.get('ids', [])
                for record_id in record_ids:
                    await ws_manager.broadcast_model_update(
                        system_id=system_id,
                        model=model,
                        record_id=record_id,
                        operation='unlink',
                        data={}
                    )

        # Record metrics
        duration = time.time() - start_time
        record_api_operation("odoo", model, operation, duration, True)

        response = {"result": result}
        if cached:
            response["cached"] = True
        if optimized:
            response["optimized"] = True

        return response

    except ValueError as e:
        logger.error(f"Validation error in {operation}: {str(e)}")
        duration = time.time() - start_time
        record_api_operation("odoo", model, operation, duration, False)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Operation {operation} failed: {str(e)}")
        duration = time.time() - start_time
        record_api_operation("odoo", model, operation, duration, False)

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


@router.get("/{system_id}/cache/stats")
async def get_cache_stats(
    system_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get cache statistics for a system

    Args:
        system_id: System identifier
        current_user: Current authenticated user

    Returns:
        Cache statistics including hit rate, total keys, etc.
    """
    try:
        # Get Redis info
        redis_client = cache_service.redis_client

        # Get info stats
        info = await redis_client.info("stats")
        keyspace = await redis_client.info("keyspace")

        # Calculate hit rate
        hits = int(info.get("keyspace_hits", 0))
        misses = int(info.get("keyspace_misses", 0))
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0

        # Count keys for this system
        pattern = f"odoo:{system_id}:*"
        keys = await redis_client.keys(pattern)
        system_keys_count = len(keys) if keys else 0

        return {
            "system_id": system_id,
            "cache_stats": {
                "total_keys": system_keys_count,
                "hit_rate_percent": round(hit_rate, 2),
                "total_hits": hits,
                "total_misses": misses,
                "total_commands": int(info.get("total_commands_processed", 0)),
                "total_connections": int(info.get("total_connections_received", 0)),
                "keyspace_info": keyspace
            }
        }

    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )


@router.delete("/{system_id}/cache/clear")
async def clear_cache(
    system_id: str,
    model: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Clear cache for a system or specific model

    Args:
        system_id: System identifier
        model: Optional model name to clear cache for
        current_user: Current authenticated user

    Returns:
        Number of keys deleted
    """
    try:
        if model:
            # Clear cache for specific model
            pattern = f"odoo:{system_id}:*:{model}:*"
        else:
            # Clear all cache for system
            pattern = f"odoo:{system_id}:*"

        deleted_count = await cache_service.delete_pattern(pattern)

        logger.info(
            f"User {current_user.username} cleared {deleted_count} cache entries "
            f"for system {system_id}" + (f" model {model}" if model else "")
        )

        return {
            "system_id": system_id,
            "model": model,
            "deleted_keys": deleted_count,
            "message": f"Cleared {deleted_count} cache entries"
        }

    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )
