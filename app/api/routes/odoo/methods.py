"""
Custom method routes for Odoo API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.services.odoo import CustomOperations
from app.schemas.odoo.custom import (
    CallMethodRequest,
    CallMethodResponse,
    ActionRequest,
    ActionResponse,
    MessagePostRequest,
    MessagePostResponse,
)
from app.core.exceptions import OdooConnectionException
from app.services.odoo.base import OdooExecutionError
from .deps import get_custom_service

router = APIRouter()


@router.post("/call_method", response_model=CallMethodResponse)
async def call_method(
    request: CallMethodRequest,
    service: CustomOperations = Depends(get_custom_service)
):
    """
    Call any public method on a model

    **Example Request:**
    ```json
    {
      "model": "sale.order",
      "method": "action_confirm",
      "args": [[1, 2, 3]],
      "kwargs": {}
    }
    ```
    """
    try:
        result = await service.call_method(
            model=request.model,
            method=request.method,
            args=request.args,
            kwargs=request.kwargs,
            context=request.context
        )

        return CallMethodResponse(
            success=True,
            result=result
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
        logger.error(f"Call method error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/action", response_model=ActionResponse)
async def execute_action(
    request: ActionRequest,
    service: CustomOperations = Depends(get_custom_service)
):
    """
    Execute a workflow action on records

    **Example Request:**
    ```json
    {
      "model": "sale.order",
      "ids": [1],
      "action": "action_confirm"
    }
    ```
    """
    try:
        result = await service.call_method(
            model=request.model,
            method=request.action,
            args=[request.ids],
            context=request.context
        )

        return ActionResponse(
            success=True,
            result=result
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
        logger.error(f"Action error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/action_confirm", response_model=ActionResponse)
async def action_confirm(
    model: str,
    ids: list[int],
    service: CustomOperations = Depends(get_custom_service)
):
    """
    Confirm records (shortcut for action_confirm)
    """
    try:
        result = await service.action_confirm(
            model=model,
            ids=ids
        )

        return ActionResponse(success=True, result=result)

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
        logger.error(f"Action confirm error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/action_cancel", response_model=ActionResponse)
async def action_cancel(
    model: str,
    ids: list[int],
    service: CustomOperations = Depends(get_custom_service)
):
    """
    Cancel records (shortcut for action_cancel)
    """
    try:
        result = await service.action_cancel(
            model=model,
            ids=ids
        )

        return ActionResponse(success=True, result=result)

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
        logger.error(f"Action cancel error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/message_post", response_model=MessagePostResponse)
async def message_post(
    request: MessagePostRequest,
    service: CustomOperations = Depends(get_custom_service)
):
    """
    Post a message on records

    **Example Request:**
    ```json
    {
      "model": "sale.order",
      "ids": [1],
      "body": "<p>Order has been processed!</p>",
      "message_type": "comment"
    }
    ```
    """
    try:
        result = await service.message_post(
            model=request.model,
            ids=request.ids,
            body=request.body,
            message_type=request.message_type,
            subtype_xmlid=request.subtype_xmlid,
            context=request.context
        )

        return MessagePostResponse(
            success=True,
            message_id=result if isinstance(result, int) else None
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
        logger.error(f"Message post error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()
