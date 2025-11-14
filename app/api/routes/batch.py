"""
Batch Operations API

Execute multiple operations in a single request
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from loguru import logger

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.system_service import SystemService
from app.api.routes.systems import get_system_service

router = APIRouter(prefix="/batch", tags=["Batch Operations"])


class BatchOperation(BaseModel):
    """Single batch operation"""
    action: str = Field(..., description="Operation type: create/read/update/delete")
    model: str = Field(..., description="Model name")
    data: Dict[str, Any] = Field(default={}, description="Operation data")
    record_id: int = Field(None, description="Record ID (for update/delete)")
    domain: List = Field(default=[], description="Search domain (for read)")
    fields: List[str] = Field(default=[], description="Fields to return (for read)")


class BatchRequest(BaseModel):
    """Batch operations request"""
    system_id: str = Field(..., description="System identifier")
    operations: List[BatchOperation] = Field(..., description="List of operations")
    stop_on_error: bool = Field(default=False, description="Stop execution on first error")
    use_universal_schema: bool = Field(default=False)
    system_version: str = Field(None)


class BatchOperationResult(BaseModel):
    """Single operation result"""
    success: bool
    action: str
    model: str
    data: Any = None
    error: str = None


class BatchResponse(BaseModel):
    """Batch operations response"""
    success: bool
    results: List[BatchOperationResult]
    total: int
    succeeded: int
    failed: int


@router.post("", response_model=BatchResponse)
async def execute_batch_operations(
    batch_request: BatchRequest,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    service: SystemService = Depends(get_system_service)
):
    """
    Execute multiple operations in a single request

    Features:
    - Multiple CRUD operations
    - Atomic or non-atomic execution
    - Detailed results for each operation

    Args:
        batch_request: Batch operations request

    Returns:
        Batch execution results

    Example:
        ```json
        POST /batch
        {
            "system_id": "odoo-prod",
            "operations": [
                {
                    "action": "create",
                    "model": "res.partner",
                    "data": {"name": "Ahmed", "email": "ahmed@example.com"}
                },
                {
                    "action": "update",
                    "model": "res.partner",
                    "record_id": 42,
                    "data": {"phone": "+966501234567"}
                },
                {
                    "action": "read",
                    "model": "product.product",
                    "domain": [["type", "=", "product"]],
                    "fields": ["name", "list_price"]
                }
            ],
            "stop_on_error": false
        }
        ```
    """
    results = []
    succeeded = 0
    failed = 0

    for operation in batch_request.operations:
        try:
            result = await _execute_single_operation(
                service=service,
                user_id=current_user.id,
                system_id=batch_request.system_id,
                operation=operation,
                use_universal_schema=batch_request.use_universal_schema,
                system_version=batch_request.system_version,
                request=request
            )

            results.append(BatchOperationResult(
                success=True,
                action=operation.action,
                model=operation.model,
                data=result
            ))
            succeeded += 1

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Batch operation error: {error_msg}")

            results.append(BatchOperationResult(
                success=False,
                action=operation.action,
                model=operation.model,
                error=error_msg
            ))
            failed += 1

            # Stop on error if requested
            if batch_request.stop_on_error:
                break

    return BatchResponse(
        success=failed == 0,
        results=results,
        total=len(results),
        succeeded=succeeded,
        failed=failed
    )


async def _execute_single_operation(
    service: SystemService,
    user_id: int,
    system_id: str,
    operation: BatchOperation,
    use_universal_schema: bool,
    system_version: str,
    request: Request
) -> Any:
    """
    Execute a single batch operation

    Args:
        service: System service
        user_id: User ID
        system_id: System identifier
        operation: Operation to execute
        use_universal_schema: Use universal schema
        system_version: System version
        request: HTTP request

    Returns:
        Operation result
    """
    from app.core.dependencies import get_client_ip, get_user_agent

    if operation.action == "create":
        result = await service.create_record(
            user_id=user_id,
            system_id=system_id,
            model=operation.model,
            data=operation.data,
            use_universal_schema=use_universal_schema,
            system_version=system_version,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        return result

    elif operation.action == "read":
        result = await service.read_records(
            user_id=user_id,
            system_id=system_id,
            model=operation.model,
            domain=operation.domain,
            fields=operation.fields,
            use_universal_schema=use_universal_schema,
            system_version=system_version,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        return result

    elif operation.action == "update":
        if not operation.record_id:
            raise ValueError("record_id is required for update operation")

        result = await service.update_record(
            user_id=user_id,
            system_id=system_id,
            model=operation.model,
            record_id=operation.record_id,
            data=operation.data,
            use_universal_schema=use_universal_schema,
            system_version=system_version,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        return result

    elif operation.action == "delete":
        if not operation.record_id:
            raise ValueError("record_id is required for delete operation")

        result = await service.delete_record(
            user_id=user_id,
            system_id=system_id,
            model=operation.model,
            record_id=operation.record_id,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        return result

    else:
        raise ValueError(f"Unsupported action: {operation.action}")
