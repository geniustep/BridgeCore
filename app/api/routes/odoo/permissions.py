"""
Permission operation routes for Odoo API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.services.odoo import PermissionOperations
from app.schemas.odoo.permissions import (
    CheckAccessRightsRequest,
    CheckAccessRightsResponse,
    CheckAllAccessRightsRequest,
    CheckAllAccessRightsResponse,
)
from app.core.exceptions import OdooConnectionException
from app.services.odoo.base import OdooExecutionError
from .deps import get_permission_service

router = APIRouter()


@router.post("/check_access_rights", response_model=CheckAccessRightsResponse)
async def check_access_rights(
    request: CheckAccessRightsRequest,
    service: PermissionOperations = Depends(get_permission_service)
):
    """
    Check if user has rights for an operation

    **Example Request:**
    ```json
    {
      "model": "sale.order",
      "operation": "write",
      "raise_exception": false
    }
    ```
    """
    try:
        has_access = await service.check_access_rights(
            model=request.model,
            operation=request.operation,
            raise_exception=request.raise_exception,
            context=request.context
        )

        return CheckAccessRightsResponse(
            success=True,
            has_access=has_access,
            operation=request.operation,
            model=request.model
        )

    except OdooConnectionException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Odoo connection error: {str(e)}"
        )
    except OdooExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Odoo error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Check access rights error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/check_all_access_rights", response_model=CheckAllAccessRightsResponse)
async def check_all_access_rights(
    request: CheckAllAccessRightsRequest,
    service: PermissionOperations = Depends(get_permission_service)
):
    """
    Check all CRUD operations for a model

    **Example Request:**
    ```json
    {
      "model": "sale.order"
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "model": "sale.order",
      "rights": {
        "create": true,
        "read": true,
        "write": true,
        "unlink": false
      }
    }
    ```
    """
    try:
        rights = await service.check_all_access_rights(
            model=request.model,
            context=request.context
        )

        return CheckAllAccessRightsResponse(
            success=True,
            model=request.model,
            rights=rights
        )

    except OdooConnectionException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Odoo connection error: {str(e)}"
        )
    except OdooExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Odoo error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Check all access rights error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()
