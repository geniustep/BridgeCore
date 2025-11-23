"""
View operation routes for Odoo API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.services.odoo import ViewOperations
from app.schemas.odoo.views import (
    FieldsGetRequest,
    FieldsGetResponse,
    FieldsViewGetRequest,
    FieldsViewGetResponse,
    GetViewRequest,
    GetViewResponse,
    GetViewsRequest,
    GetViewsResponse,
)
from app.core.exceptions import OdooConnectionException
from app.services.odoo.base import OdooExecutionError
from .deps import get_view_service

router = APIRouter()


@router.post("/fields_get", response_model=FieldsGetResponse)
async def fields_get(
    request: FieldsGetRequest,
    service: ViewOperations = Depends(get_view_service)
):
    """
    Get field definitions for a model

    **Example Request:**
    ```json
    {
      "model": "res.partner",
      "fields": ["name", "email", "country_id"],
      "attributes": ["string", "type", "required", "relation"]
    }
    ```
    """
    try:
        fields = await service.fields_get(
            model=request.model,
            fields=request.fields,
            attributes=request.attributes,
            context=request.context
        )

        return FieldsGetResponse(
            success=True,
            fields=fields
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
        logger.error(f"Fields get error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/fields_view_get", response_model=FieldsViewGetResponse)
async def fields_view_get(
    request: FieldsViewGetRequest,
    service: ViewOperations = Depends(get_view_service)
):
    """
    Get view definition (legacy method, Odoo <= 15)

    **Example Request:**
    ```json
    {
      "model": "res.partner",
      "view_type": "form",
      "toolbar": true
    }
    ```
    """
    try:
        result = await service.fields_view_get(
            model=request.model,
            view_id=request.view_id,
            view_type=request.view_type,
            toolbar=request.toolbar,
            context=request.context
        )

        return FieldsViewGetResponse(
            success=True,
            arch=result.get("arch", ""),
            fields=result.get("fields", {}),
            name=result.get("name"),
            view_id=result.get("view_id")
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
        logger.error(f"Fields view get error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/get_view", response_model=GetViewResponse)
async def get_view(
    request: GetViewRequest,
    service: ViewOperations = Depends(get_view_service)
):
    """
    Get view definition (Odoo 16+)

    **Example Request:**
    ```json
    {
      "model": "sale.order",
      "view_type": "form",
      "options": {"toolbar": true}
    }
    ```
    """
    try:
        result = await service.get_view(
            model=request.model,
            view_id=request.view_id,
            view_type=request.view_type,
            options=request.options,
            context=request.context
        )

        return GetViewResponse(
            success=True,
            view=result
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
        logger.error(f"Get view error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/get_views", response_model=GetViewsResponse)
async def get_views(
    request: GetViewsRequest,
    service: ViewOperations = Depends(get_view_service)
):
    """
    Load multiple views at once (Odoo 16+)

    **Example Request:**
    ```json
    {
      "model": "sale.order",
      "views": [[false, "form"], [false, "list"]],
      "options": {"toolbar": true, "load_filters": true}
    }
    ```
    """
    try:
        # Convert list to tuples
        views = [(v[0], v[1]) for v in request.views]

        result = await service.get_views(
            model=request.model,
            views=views,
            options=request.options,
            context=request.context
        )

        return GetViewsResponse(
            success=True,
            views=result
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
        logger.error(f"Get views error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()
