"""
Advanced operation routes for Odoo API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.services.odoo import AdvancedOperations
from app.schemas.odoo.advanced import (
    OnchangeRequest,
    OnchangeResponse,
    ReadGroupRequest,
    ReadGroupResponse,
    DefaultGetRequest,
    DefaultGetResponse,
    CopyRequest,
    CopyResponse,
)
from app.core.exceptions import (
    OdooConnectionException,
    OdooPermissionDeniedException,
    OdooModelNotFoundException,
    OdooRecordNotFoundException,
)
from app.services.odoo.base import OdooExecutionError
from .deps import get_advanced_service

router = APIRouter()


@router.post("/onchange", response_model=OnchangeResponse)
async def execute_onchange(
    request: OnchangeRequest,
    service: AdvancedOperations = Depends(get_advanced_service)
):
    """
    Execute onchange to calculate field values

    **Critical for:** Price calculations, discounts, taxes, form field dependencies

    **Example Request:**
    ```json
    {
      "model": "sale.order.line",
      "ids": [],
      "values": {"order_id": 100, "product_id": 50, "product_uom_qty": 5.0},
      "field_name": "product_id",
      "field_onchange": {"product_id": "1", "price_unit": "1", "discount": "1"}
    }
    ```
    """
    try:
        result = await service.onchange(
            model=request.model,
            ids=request.ids,
            values=request.values,
            field_name=request.field_name,
            field_onchange=request.field_onchange,
            context=request.context
        )

        return OnchangeResponse(
            success=True,
            value=result.get("value", {}),
            warning=result.get("warning"),
            domain=result.get("domain")
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
        logger.error(f"Onchange error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/read_group", response_model=ReadGroupResponse)
async def read_group(
    request: ReadGroupRequest,
    service: AdvancedOperations = Depends(get_advanced_service)
):
    """
    Read grouped/aggregated data

    **Use for:** Reports, dashboards, analytics

    **Example Request:**
    ```json
    {
      "model": "sale.order",
      "domain": [["state", "=", "sale"]],
      "fields": ["amount_total:sum"],
      "groupby": ["partner_id"],
      "orderby": "amount_total desc",
      "limit": 10
    }
    ```
    """
    try:
        groups = await service.read_group(
            model=request.model,
            domain=request.domain,
            fields=request.fields,
            groupby=request.groupby,
            offset=request.offset,
            limit=request.limit,
            orderby=request.orderby,
            lazy=request.lazy,
            context=request.context
        )

        return ReadGroupResponse(
            success=True,
            groups=groups,
            count=len(groups)
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
        logger.error(f"Read group error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/default_get", response_model=DefaultGetResponse)
async def get_defaults(
    request: DefaultGetRequest,
    service: AdvancedOperations = Depends(get_advanced_service)
):
    """
    Get default values for new record

    **Example Request:**
    ```json
    {
      "model": "sale.order",
      "fields": ["partner_id", "date_order", "pricelist_id"]
    }
    ```
    """
    try:
        defaults = await service.default_get(
            model=request.model,
            fields=request.fields,
            context=request.context
        )

        return DefaultGetResponse(
            success=True,
            defaults=defaults
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
        logger.error(f"Default get error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/copy", response_model=CopyResponse)
async def copy_record(
    request: CopyRequest,
    service: AdvancedOperations = Depends(get_advanced_service)
):
    """
    Duplicate a record

    **Example Request:**
    ```json
    {
      "model": "sale.order",
      "id": 100,
      "default": {"date_order": "2024-12-01", "client_order_ref": "COPY-001"}
    }
    ```
    """
    try:
        new_id = await service.copy(
            model=request.model,
            record_id=request.id,
            default=request.default,
            context=request.context
        )

        return CopyResponse(success=True, id=new_id)

    except OdooConnectionException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Odoo connection error: {str(e)}"
        )
    except OdooRecordNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except OdooExecutionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Odoo error: {e.message}"
        )
    except Exception as e:
        logger.error(f"Copy error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()
