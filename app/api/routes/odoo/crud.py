"""
CRUD operation routes for Odoo API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from loguru import logger

from app.services.odoo import CRUDOperations
from app.schemas.odoo.crud import (
    CreateRequest,
    CreateResponse,
    ReadRequest,
    ReadResponse,
    WriteRequest,
    WriteResponse,
    UnlinkRequest,
    UnlinkResponse,
)
from app.core.exceptions import (
    OdooConnectionException,
    OdooPermissionDeniedException,
    OdooModelNotFoundException,
    OdooRecordNotFoundException,
)
from app.services.odoo.base import OdooExecutionError
from app.core.rate_limiter import limiter, get_rate_limit
from .deps import get_crud_service

router = APIRouter()


@router.post("/create", response_model=CreateResponse)
@limiter.limit(get_rate_limit("odoo_create"))
async def create_record(
    request: Request,
    body: CreateRequest,
    service: CRUDOperations = Depends(get_crud_service)
):
    """
    Create new record(s)

    Supports single record or batch creation.

    **Single Record Example:**
    ```json
    {
      "model": "res.partner",
      "values": {"name": "New Customer", "email": "customer@example.com"}
    }
    ```

    **Batch Creation Example:**
    ```json
    {
      "model": "res.partner",
      "values": [
        {"name": "Customer 1", "email": "c1@example.com"},
        {"name": "Customer 2", "email": "c2@example.com"}
      ]
    }
    ```
    """
    try:
        result = await service.create(
            model=body.model,
            values=body.values,
            context=body.context
        )

        if isinstance(body.values, list):
            return CreateResponse(success=True, ids=result)
        else:
            return CreateResponse(success=True, id=result)

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
        logger.error(f"Create error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/read", response_model=ReadResponse)
@limiter.limit(get_rate_limit("odoo_read"))
async def read_records(
    request: Request,
    body: ReadRequest,
    service: CRUDOperations = Depends(get_crud_service)
):
    """
    Read records by ID

    More efficient than search_read when IDs are known.

    **Example Request:**
    ```json
    {
      "model": "res.partner",
      "ids": [1, 2, 3],
      "fields": ["name", "email", "phone"]
    }
    ```
    """
    try:
        records = await service.read(
            model=body.model,
            ids=body.ids,
            fields=body.fields,
            context=body.context
        )

        return ReadResponse(
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
        logger.error(f"Read error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/write", response_model=WriteResponse)
@limiter.limit(get_rate_limit("odoo_write"))
async def write_records(
    request: Request,
    body: WriteRequest,
    service: CRUDOperations = Depends(get_crud_service)
):
    """
    Update existing records

    **Example Request:**
    ```json
    {
      "model": "res.partner",
      "ids": [1],
      "values": {"name": "Updated Name", "phone": "+1234567890"}
    }
    ```
    """
    try:
        success = await service.write(
            model=body.model,
            ids=body.ids,
            values=body.values,
            context=body.context
        )

        return WriteResponse(success=True, updated=success)

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
        logger.error(f"Write error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/unlink", response_model=UnlinkResponse)
@limiter.limit(get_rate_limit("odoo_delete"))
async def unlink_records(
    request: Request,
    body: UnlinkRequest,
    service: CRUDOperations = Depends(get_crud_service)
):
    """
    Delete records

    **Warning:** This permanently removes records.

    **Example Request:**
    ```json
    {
      "model": "res.partner",
      "ids": [100, 101, 102]
    }
    ```
    """
    try:
        success = await service.unlink(
            model=body.model,
            ids=body.ids,
            context=body.context
        )

        return UnlinkResponse(success=True, deleted=success)

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
        logger.error(f"Unlink error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()
