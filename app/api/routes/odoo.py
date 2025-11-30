"""
Odoo Operations API routes - Tenant-Based

This file has been modified to use tenant information from JWT token.
Tenant credentials are automatically fetched from database, not passed in request.
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
from app.models.tenant import Tenant
from app.services.cache_service import CacheService
from app.services.query_optimizer import query_optimizer
from app.core.monitoring import record_cache_hit, record_cache_miss, record_api_operation
from app.core.config import settings
from app.api.routes.websocket import manager as ws_manager
from app.core.encryption import encryption_service
from app.adapters.odoo_adapter import OdooAdapter

router = APIRouter(prefix="/api/v1/odoo", tags=["Odoo Operations"])
security = HTTPBearer()

# Initialize cache service
cache_service = CacheService(settings.REDIS_URL)


class OdooOperationRequest(BaseModel):
    """Request model for Odoo operations - NO Odoo credentials needed!"""
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


def decrypt_password(encrypted_password: str) -> str:
    """
    Decrypt Odoo password from database using encryption_service
    
    Args:
        encrypted_password: Encrypted password from database
        
    Returns:
        Decrypted password string
    """
    try:
        return encryption_service.decrypt_value(encrypted_password)
    except Exception as e:
        logger.error(f"Failed to decrypt password: {str(e)}")
        # Fallback: try to use as-is (might be plain text from old records)
        logger.warning("Using password as-is (might be plain text or hash)")
        return encrypted_password


@router.post("/{operation}")
async def execute_odoo_operation(
    operation: str,
    request: Request,
    request_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Execute any Odoo operation - Tenant-based (NO credentials required in request!)

    🔐 SECURITY: This endpoint uses tenant info from JWT token automatically.
    User does NOT send Odoo credentials - they are fetched from tenant database.

    How it works:
    1. Middleware extracts tenant_id from JWT
    2. Middleware validates tenant status (active/suspended/deleted)
    3. Middleware attaches tenant object to request.state
    4. This endpoint uses tenant.odoo_url, tenant.odoo_database, etc.
    5. User only sends operation-specific data (model, domain, fields, etc.)

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
        operation: Operation name
        request: FastAPI request (contains tenant in state)
        request_data: Operation-specific data (NO Odoo credentials!)
        db: Database session

    Returns:
        {
            "result": [...] or {...} or int or bool,
            "cached": bool (optional),
            "optimized": bool (optional),
            "tenant_id": str (for debugging)
        }

    Example Request:
        POST /api/v1/odoo/search_read
        Authorization: Bearer <tenant_jwt>
        {
            "model": "res.partner",
            "domain": [["is_company", "=", true]],
            "fields": ["name", "email", "phone"],
            "limit": 10
        }

    Example Response:
        {
            "result": [
                {"id": 1, "name": "Company A", "email": "info@a.com", "phone": "+123"},
                {"id": 2, "name": "Company B", "email": "info@b.com", "phone": "+456"}
            ],
            "cached": false,
            "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
        }

    Raises:
        HTTPException: If operation fails or tenant not found
    """
    start_time = time.time()

    # 🔐 Get tenant from request state (set by middleware)
    tenant: Tenant = getattr(request.state, 'tenant', None)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant information not found. Are you using a valid tenant token?"
        )

    tenant_id = str(tenant.id)
    user_id = getattr(request.state, 'user_id', None)

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
        f"Tenant {tenant.name} (ID: {tenant_id}) executing {operation} "
        f"on model {model}"
    )

    try:
        cached = False
        optimized = False

        # Generate system_id for this tenant (for cache keys)
        system_id = f"tenant-{tenant_id}"

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
                logger.info(f"Cache HIT for {operation} on {model} (tenant: {tenant.name})")
                record_cache_hit(operation)

                # Record metrics
                duration = time.time() - start_time
                record_api_operation("odoo", model, operation, duration, True)

                return {
                    "result": cached_result,
                    "cached": True,
                    "tenant_id": tenant_id
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

        # 🔐 Execute operation with tenant's Odoo credentials
        result = await execute_operation_with_tenant(
            tenant=tenant,
            operation=operation,
            data=request_data,
            user_id=user_id
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

        response = {
            "result": result,
            "tenant_id": tenant_id
        }
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
        logger.error(f"Operation {operation} failed for tenant {tenant.name}: {str(e)}")
        duration = time.time() - start_time
        record_api_operation("odoo", model, operation, duration, False)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Operation failed: {str(e)}"
        )


async def execute_operation_with_tenant(
    tenant: Tenant,
    operation: str,
    data: Dict[str, Any],
    user_id: Optional[str] = None
) -> Any:
    """
    Execute Odoo operation using tenant's credentials

    This function connects to the tenant's Odoo instance using credentials
    stored in the tenant database record.

    Args:
        tenant: Tenant object with Odoo connection info
        operation: Operation name
        data: Operation data
        user_id: User ID for audit

    Returns:
        Operation result
    """
    
    # 🔐 Extract tenant's Odoo credentials
    odoo_url = tenant.odoo_url
    odoo_database = tenant.odoo_database
    odoo_username = tenant.odoo_username
    odoo_password = decrypt_password(tenant.odoo_password)
    
    logger.info(
        f"[ODOO OPERATION] Connecting to Odoo: {odoo_url}, DB: {odoo_database}, "
        f"User: {odoo_username}, Operation: {operation}"
    )

    # Create OdooAdapter with tenant credentials
    odoo_config = {
        "url": odoo_url,
        "database": odoo_database,
        "username": odoo_username,
        "password": odoo_password,
        "context": {}
    }
    
    adapter = OdooAdapter(odoo_config)
    
    # Authenticate with Odoo
    auth_result = await adapter.authenticate(odoo_username, odoo_password)
    if not auth_result.get("success"):
        error_msg = auth_result.get("error", "Authentication failed")
        logger.error(f"[ODOO OPERATION] Authentication failed: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Odoo authentication failed: {error_msg}"
        )
    
    logger.info(f"[ODOO OPERATION] Authenticated successfully - UID: {auth_result.get('uid')}")
    
    # Execute operation using OdooAdapter
    model = data.get("model")
    if not model and operation not in ["call_kw"]:
        raise ValueError("Model is required for this operation")

    try:
        # Execute operations using OdooAdapter
        if operation == "search_read":
            domain = data.get("domain", [])
            fields = data.get("fields")
            limit = data.get("limit", 80)
            offset = data.get("offset", 0)
            order = data.get("order")
            
            logger.info(
                f"🔍 [ENDPOINT] search_read request received\n"
                f"   Tenant: {tenant.name if tenant else 'unknown'}\n"
                f"   Model: {model}\n"
                f"   Domain: {domain}\n"
                f"   Fields: {fields}\n"
                f"   Limit: {limit}\n"
                f"   Offset: {offset}\n"
                f"   Order: {order}"
            )
            
            result = await adapter.search_read(
                model=model,
                domain=domain,
                fields=fields,
                limit=limit,
                offset=offset,
                order=order
            )
            
            logger.info(
                f"✅ [ENDPOINT] search_read completed\n"
                f"   Model: {model}\n"
                f"   Records returned: {len(result) if isinstance(result, list) else 'N/A'}"
            )
            
            return result

        elif operation == "read":
            ids = data.get("ids", [])
            if not ids:
                raise ValueError("ids are required for read operation")
            
            # Use search_read with domain to get specific records
            result = await adapter.search_read(
                model=model,
                domain=[["id", "in", ids]],
                fields=data.get("fields"),
                limit=len(ids)
            )
            return result

        elif operation == "create":
            values = data.get("values", {})
            if not values:
                raise ValueError("values are required for create operation")
            
            result = await adapter.create(
                model=model,
                values=values
            )
            return result

        elif operation == "write":
            ids = data.get("ids", [])
            values = data.get("values", {})
            
            if not ids:
                raise ValueError("ids are required for write operation")
            if not values:
                raise ValueError("values are required for write operation")
            
            # Write each record
            for record_id in ids:
                await adapter.write(
                    model=model,
                    record_id=record_id,
                    values=values
                )
            return True

        elif operation == "unlink":
            ids = data.get("ids", [])
            if not ids:
                raise ValueError("ids are required for unlink operation")
            
            result = await adapter.unlink(
                model=model,
                record_ids=ids
            )
            return result

        elif operation == "search_count":
            domain = data.get("domain", [])
            # Use search_read and count results
            result = await adapter.search_read(
                model=model,
                domain=domain,
                fields=["id"],
                limit=10000  # Large limit to get count
            )
            return len(result) if isinstance(result, list) else 0

        elif operation == "search":
            domain = data.get("domain", [])
            limit = data.get("limit", 80)
            offset = data.get("offset", 0)
            
            # Use search_read to get IDs
            result = await adapter.search_read(
                model=model,
                domain=domain,
                fields=["id"],
                limit=limit,
                offset=offset
            )
            # Extract IDs
            return [record.get("id") for record in result if record.get("id")]

        elif operation == "fields_get":
            fields = data.get("fields")
            result = await adapter.get_metadata(model=model)
            
            # Filter fields if specified
            if fields:
                result = {k: v for k, v in result.items() if k in fields}
            
            return result

        elif operation == "name_search":
            name = data.get("name", "")
            domain = data.get("domain", [])
            limit = data.get("limit", 100)
            
            result = await adapter.name_search(
                model=model,
                name=name,
                domain=domain,
                limit=limit
            )
            return result

        elif operation == "name_get":
            ids = data.get("ids", [])
            if not ids:
                raise ValueError("ids are required for name_get operation")
            
            # Use search_read to get names
            result = await adapter.search_read(
                model=model,
                domain=[["id", "in", ids]],
                fields=["id", "name", "display_name"],
                limit=len(ids)
            )
            # Format as (id, name) tuples
            return [
                (record.get("id"), record.get("display_name") or record.get("name", ""))
                for record in result
            ]

        elif operation in ["web_search_read", "web_read", "web_save"]:
            # These are Odoo 14+ web methods - use call_kw
            specification = data.get("specification", {})
            
            if operation == "web_search_read":
                result = await adapter.call_method(
                    model=model,
                    method="web_search_read",
                    kwargs=specification
                )
                return result
            elif operation == "web_read":
                result = await adapter.call_method(
                    model=model,
                    method="web_read",
                    kwargs=specification
                )
                return result
            else:  # web_save
                result = await adapter.call_method(
                    model=model,
                    method="web_save",
                    kwargs=specification
                )
                return result

        elif operation == "call_kw":
            method = data.get("method")
            args = data.get("args", [])
            kwargs = data.get("kwargs", {})
            
            if not method:
                raise ValueError("method is required for call_kw operation")
            
            logger.info(
                f"🔧 [ENDPOINT] call_kw request received\n"
                f"   Tenant: {tenant.name if tenant else 'unknown'}\n"
                f"   Model: {model}\n"
                f"   Method: {method}\n"
                f"   Args: {args}\n"
                f"   Kwargs keys: {list(kwargs.keys()) if kwargs else []}"
            )
            
            result = await adapter.call_method(
                model=model,
                method=method,
                args=args,
                kwargs=kwargs
            )
            
            logger.info(
                f"✅ [ENDPOINT] call_kw completed\n"
                f"   Model: {model}\n"
                f"   Method: {method}\n"
                f"   Result type: {type(result).__name__}"
            )
            
            return result

        else:
            raise ValueError(f"Operation {operation} not implemented")
    
    except Exception as e:
        logger.error(f"[ODOO OPERATION] Error executing {operation}: {str(e)}")
        raise
    
    finally:
        # Clean up adapter connection
        try:
            await adapter.disconnect()
        except Exception as e:
            logger.warning(f"Error disconnecting adapter: {str(e)}")


@router.get("/models")
async def list_odoo_models(
    request: Request
):
    """
    List available Odoo models for current tenant

    Args:
        request: FastAPI request (contains tenant in state)

    Returns:
        List of available models
    """
    tenant: Tenant = getattr(request.state, 'tenant', None)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant information not found"
        )

    # TODO: Get actual models from tenant's Odoo instance
    # This would typically call ir.model.search_read()

    return {
        "result": [
            {"model": "res.partner", "name": "Contact"},
            {"model": "product.product", "name": "Product"},
            {"model": "sale.order", "name": "Sales Order"},
            {"model": "account.move", "name": "Invoice"},
            {"model": "stock.picking", "name": "Transfer"},
        ],
        "tenant_id": str(tenant.id),
        "tenant_name": tenant.name
    }


@router.get("/cache/stats")
async def get_cache_stats(
    request: Request
):
    """
    Get cache statistics for current tenant

    Args:
        request: FastAPI request (contains tenant in state)

    Returns:
        Cache statistics
    """
    tenant: Tenant = getattr(request.state, 'tenant', None)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant information not found"
        )

    tenant_id = str(tenant.id)
    system_id = f"tenant-{tenant_id}"

    try:
        redis_client = cache_service.redis_client

        # Get info stats
        info = await redis_client.info("stats")
        keyspace = await redis_client.info("keyspace")

        # Calculate hit rate
        hits = int(info.get("keyspace_hits", 0))
        misses = int(info.get("keyspace_misses", 0))
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0

        # Count keys for this tenant
        pattern = f"odoo:{system_id}:*"
        keys = await redis_client.keys(pattern)
        tenant_keys_count = len(keys) if keys else 0

        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
            "cache_stats": {
                "total_keys": tenant_keys_count,
                "hit_rate_percent": round(hit_rate, 2),
                "total_hits": hits,
                "total_misses": misses,
            }
        }

    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )


@router.delete("/cache/clear")
async def clear_cache(
    request: Request,
    model: Optional[str] = None
):
    """
    Clear cache for current tenant or specific model

    Args:
        request: FastAPI request (contains tenant in state)
        model: Optional model name to clear cache for

    Returns:
        Number of keys deleted
    """
    tenant: Tenant = getattr(request.state, 'tenant', None)
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant information not found"
        )

    tenant_id = str(tenant.id)
    system_id = f"tenant-{tenant_id}"

    try:
        if model:
            pattern = f"odoo:{system_id}:*:{model}:*"
        else:
            pattern = f"odoo:{system_id}:*"

        deleted_count = await cache_service.delete_pattern(pattern)

        logger.info(
            f"Tenant {tenant.name} cleared {deleted_count} cache entries" +
            (f" for model {model}" if model else "")
        )

        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
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