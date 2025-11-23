"""
Search operation routes for Odoo API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.services.odoo import SearchOperations
from app.schemas.odoo.search import (
    SearchRequest,
    SearchResponse,
    SearchReadRequest,
    SearchReadResponse,
    SearchCountRequest,
    SearchCountResponse,
    PaginatedSearchReadRequest,
    PaginatedSearchReadResponse,
)
from app.core.exceptions import (
    OdooConnectionException,
    OdooPermissionDeniedException,
    OdooModelNotFoundException,
)
from app.services.odoo.base import OdooExecutionError
from .deps import get_search_service

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search_records(
    request: SearchRequest,
    service: SearchOperations = Depends(get_search_service)
):
    """
    Search for records, returns IDs only

    This is the most efficient way to get record IDs matching criteria.
    Use for pagination or when you need IDs for batch operations.

    **Example Request:**
    ```json
    {
      "model": "res.partner",
      "domain": [["is_company", "=", true]],
      "limit": 100,
      "order": "name ASC"
    }
    ```
    """
    try:
        ids = await service.search(
            model=request.model,
            domain=request.domain,
            limit=request.limit,
            offset=request.offset,
            order=request.order,
            context=request.context
        )

        return SearchResponse(
            success=True,
            ids=ids,
            count=len(ids)
        )

    except OdooConnectionException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Odoo connection error: {str(e)}"
        )
    except OdooPermissionDeniedException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except OdooModelNotFoundException as e:
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
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/search_read", response_model=SearchReadResponse)
async def search_read_records(
    request: SearchReadRequest,
    service: SearchOperations = Depends(get_search_service)
):
    """
    Search and read records in one operation

    Most commonly used operation for fetching data with filtering.

    **Example Request:**
    ```json
    {
      "model": "product.product",
      "domain": [["sale_ok", "=", true]],
      "fields": ["name", "list_price", "qty_available"],
      "limit": 50,
      "order": "name ASC"
    }
    ```
    """
    try:
        records = await service.search_read(
            model=request.model,
            domain=request.domain,
            fields=request.fields,
            limit=request.limit,
            offset=request.offset,
            order=request.order,
            context=request.context
        )

        return SearchReadResponse(
            success=True,
            records=records,
            count=len(records)
        )

    except OdooConnectionException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Odoo connection error: {str(e)}"
        )
    except OdooPermissionDeniedException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except OdooModelNotFoundException as e:
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
        logger.error(f"Search read error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/search_count", response_model=SearchCountResponse)
async def count_records(
    request: SearchCountRequest,
    service: SearchOperations = Depends(get_search_service)
):
    """
    Count records matching the domain

    Useful for pagination metadata or dashboard statistics.

    **Example Request:**
    ```json
    {
      "model": "sale.order",
      "domain": [["state", "in", ["sale", "done"]]]
    }
    ```
    """
    try:
        count = await service.search_count(
            model=request.model,
            domain=request.domain,
            context=request.context
        )

        return SearchCountResponse(
            success=True,
            count=count
        )

    except OdooConnectionException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Odoo connection error: {str(e)}"
        )
    except OdooPermissionDeniedException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except OdooModelNotFoundException as e:
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
        logger.error(f"Search count error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/paginated_search_read", response_model=PaginatedSearchReadResponse)
async def paginated_search_read(
    request: PaginatedSearchReadRequest,
    service: SearchOperations = Depends(get_search_service)
):
    """
    Search with pagination metadata

    Returns records with pagination information (total, pages, has_next, etc.)

    **Example Request:**
    ```json
    {
      "model": "res.partner",
      "domain": [["customer_rank", ">", 0]],
      "fields": ["name", "email"],
      "page": 1,
      "page_size": 25
    }
    ```
    """
    try:
        result = await service.paginated_search_read(
            model=request.model,
            domain=request.domain,
            fields=request.fields,
            page=request.page,
            page_size=request.page_size,
            order=request.order,
            context=request.context
        )

        return PaginatedSearchReadResponse(
            success=True,
            **result
        )

    except OdooConnectionException as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Odoo connection error: {str(e)}"
        )
    except OdooPermissionDeniedException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except OdooModelNotFoundException as e:
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
        logger.error(f"Paginated search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()
