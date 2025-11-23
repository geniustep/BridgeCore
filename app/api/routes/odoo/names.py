"""
Name operation routes for Odoo API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.services.odoo import NameOperations
from app.schemas.odoo.names import (
    NameSearchRequest,
    NameSearchResponse,
    NameGetRequest,
    NameGetResponse,
    NameCreateRequest,
    NameCreateResponse,
)
from app.core.exceptions import OdooConnectionException
from app.services.odoo.base import OdooExecutionError
from .deps import get_name_service

router = APIRouter()


@router.post("/name_search", response_model=NameSearchResponse)
async def name_search(
    request: NameSearchRequest,
    service: NameOperations = Depends(get_name_service)
):
    """
    Search records by name

    **Use for:** Autocomplete in Many2one fields

    **Example Request:**
    ```json
    {
      "model": "res.partner",
      "name": "Ahmed",
      "args": [["is_company", "=", true]],
      "operator": "ilike",
      "limit": 10
    }
    ```
    """
    try:
        results = await service.name_search(
            model=request.model,
            name=request.name,
            args=request.args,
            operator=request.operator,
            limit=request.limit,
            context=request.context
        )

        return NameSearchResponse(
            success=True,
            results=[list(r) for r in results],
            count=len(results)
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
        logger.error(f"Name search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/name_get", response_model=NameGetResponse)
async def name_get(
    request: NameGetRequest,
    service: NameOperations = Depends(get_name_service)
):
    """
    Get display names for records

    **Example Request:**
    ```json
    {
      "model": "res.partner",
      "ids": [1, 2, 3]
    }
    ```
    """
    try:
        results = await service.name_get(
            model=request.model,
            ids=request.ids,
            context=request.context
        )

        return NameGetResponse(
            success=True,
            names=[list(r) for r in results]
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
        logger.error(f"Name get error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/name_create", response_model=NameCreateResponse)
async def name_create(
    request: NameCreateRequest,
    service: NameOperations = Depends(get_name_service)
):
    """
    Create record with just a name

    **Use for:** Quick creation from Many2one dropdown

    **Example Request:**
    ```json
    {
      "model": "res.partner.category",
      "name": "New Category"
    }
    ```
    """
    try:
        result = await service.name_create(
            model=request.model,
            name=request.name,
            context=request.context
        )

        return NameCreateResponse(
            success=True,
            id=result[0],
            display_name=result[1]
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
        logger.error(f"Name create error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()
