"""
Utility operation routes for Odoo API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.services.odoo import UtilityOperations
from app.schemas.odoo.utility import (
    ExistsRequest,
    ExistsResponse,
    ValidateReferencesRequest,
    ValidateReferencesResponse,
)
from app.core.exceptions import OdooConnectionException
from app.services.odoo.base import OdooExecutionError
from .deps import get_utility_service

router = APIRouter()


@router.post("/exists", response_model=ExistsResponse)
async def check_exists(
    request: ExistsRequest,
    service: UtilityOperations = Depends(get_utility_service)
):
    """
    Check which records exist

    **Example Request:**
    ```json
    {
      "model": "res.partner",
      "ids": [1, 2, 3, 999]
    }
    ```

    **Response:**
    ```json
    {
      "success": true,
      "existing_ids": [1, 2, 3],
      "missing_ids": [999]
    }
    ```
    """
    try:
        existing = await service.exists(
            model=request.model,
            ids=request.ids,
            context=request.context
        )

        missing = list(set(request.ids) - set(existing))

        return ExistsResponse(
            success=True,
            existing_ids=existing,
            missing_ids=missing
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
        logger.error(f"Exists error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/validate_references", response_model=ValidateReferencesResponse)
async def validate_references(
    request: ValidateReferencesRequest,
    service: UtilityOperations = Depends(get_utility_service)
):
    """
    Validate multiple model references

    **Example Request:**
    ```json
    {
      "references": [
        {"model": "res.partner", "ids": [1, 2, 3]},
        {"model": "product.product", "ids": [10, 20]}
      ]
    }
    ```
    """
    try:
        result = await service.validate_references(
            references=request.references,
            context=request.context
        )

        return ValidateReferencesResponse(
            success=True,
            valid=result.get("valid", []),
            invalid=result.get("invalid", [])
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
        logger.error(f"Validate references error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()
