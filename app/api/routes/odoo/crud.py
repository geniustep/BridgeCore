"""
CRUD operation routes for Odoo API
"""
from fastapi import APIRouter, Depends, HTTPException, status
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
from .deps import get_crud_service

router = APIRouter()


@router.post("/create", response_model=CreateResponse)
async def create_record(
    request: CreateRequest,
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
            model=request.model,
            values=request.values,
            context=request.context
        )

        if isinstance(request.values, list):
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
async def read_records(
    request: ReadRequest,
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
            model=request.model,
            ids=request.ids,
            fields=request.fields,
            context=request.context
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
async def write_records(
    request: WriteRequest,
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
            model=request.model,
            ids=request.ids,
            values=request.values,
            context=request.context
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
async def unlink_records(
    request: UnlinkRequest,
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
            model=request.model,
            ids=request.ids,
            context=request.context
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
