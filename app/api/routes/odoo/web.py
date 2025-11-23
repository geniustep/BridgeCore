"""
Web operation routes for Odoo API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.services.odoo import WebOperations
from app.schemas.odoo.web import (
    WebSaveRequest,
    WebSaveResponse,
    WebReadRequest,
    WebReadResponse,
    WebSearchReadRequest,
    WebSearchReadResponse,
)
from app.core.exceptions import OdooConnectionException
from app.services.odoo.base import OdooExecutionError
from .deps import get_web_service

router = APIRouter()


@router.post("/web_save", response_model=WebSaveResponse)
async def web_save(
    request: WebSaveRequest,
    service: WebOperations = Depends(get_web_service)
):
    """
    Save records with specification

    Optimized save that returns data according to specification.

    **Example Request:**
    ```json
    {
      "model": "sale.order",
      "ids": [1],
      "values": {"partner_id": 10},
      "specification": {
        "name": {},
        "amount_total": {},
        "order_line": {"fields": {"name": {}, "price_subtotal": {}}}
      }
    }
    ```
    """
    try:
        records = await service.web_save(
            model=request.model,
            ids=request.ids,
            values=request.values,
            specification=request.specification,
            context=request.context
        )

        return WebSaveResponse(
            success=True,
            records=records
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
        logger.error(f"Web save error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/web_read", response_model=WebReadResponse)
async def web_read(
    request: WebReadRequest,
    service: WebOperations = Depends(get_web_service)
):
    """
    Read records with specification

    Supports nested field reading and pagination of relations.

    **Example Request:**
    ```json
    {
      "model": "sale.order",
      "ids": [1, 2, 3],
      "specification": {
        "name": {},
        "partner_id": {"fields": {"name": {}, "email": {}}},
        "order_line": {
          "fields": {"product_id": {"fields": {"name": {}}}, "product_uom_qty": {}},
          "limit": 50
        }
      }
    }
    ```
    """
    try:
        records = await service.web_read(
            model=request.model,
            ids=request.ids,
            specification=request.specification,
            context=request.context
        )

        return WebReadResponse(
            success=True,
            records=records
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
        logger.error(f"Web read error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/web_search_read", response_model=WebSearchReadResponse)
async def web_search_read(
    request: WebSearchReadRequest,
    service: WebOperations = Depends(get_web_service)
):
    """
    Search and read with specification

    Combines search and read with specification support.

    **Example Request:**
    ```json
    {
      "model": "sale.order",
      "domain": [["state", "=", "sale"]],
      "specification": {"name": {}, "partner_id": {"fields": {"name": {}}}, "amount_total": {}},
      "limit": 20,
      "order": "date_order DESC"
    }
    ```
    """
    try:
        result = await service.web_search_read(
            model=request.model,
            domain=request.domain,
            specification=request.specification,
            limit=request.limit,
            offset=request.offset,
            order=request.order,
            count_limit=request.count_limit,
            context=request.context
        )

        return WebSearchReadResponse(
            success=True,
            records=result.get("records", []),
            length=result.get("length", 0)
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
        logger.error(f"Web search read error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()
