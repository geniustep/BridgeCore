"""
Custom method routes for Odoo API
"""
import time
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.services.odoo import CustomOperations
from app.schemas.odoo.custom import (
    CallMethodRequest,
    CallMethodResponse,
    CallKwRequest,
    CallKwResponse,
    ActionRequest,
    ActionResponse,
    MessagePostRequest,
    MessagePostResponse,
)
from app.core.exceptions import OdooConnectionException
from app.services.odoo.base import OdooExecutionError
from .deps import get_custom_service

router = APIRouter()


@router.post("/call_kw", response_model=CallKwResponse)
async def call_kw(
    request: CallKwRequest,
    service: CustomOperations = Depends(get_custom_service)
):
    """
    Call any Odoo method with keyword arguments (execute_kw)

    This is the most flexible endpoint for calling any Odoo model method.
    Use this for custom methods not covered by standard CRUD operations.

    **Example Request:**
    ```json
    {
      "model": "shuttlebee.trip",
      "method": "get_manager_analytics",
      "args": [],
      "kwargs": {}
    }
    ```

    **Another Example:**
    ```json
    {
      "model": "sale.order",
      "method": "action_confirm",
      "args": [[1, 2, 3]],
      "kwargs": {}
    }
    ```
    """
    start_time = time.time()
    
    try:
        # Escape curly braces in args for .format()
        args_safe = str(request.args).replace('{', '{{').replace('}', '}}')
        logger.info(
            "🔧 [ENDPOINT] /call_kw request received\n"
            "   Model: {}\n"
            "   Method: {}\n"
            "   Args: {}\n"
            "   Kwargs keys: {}".format(
                str(request.model),
                str(request.method),
                args_safe,
                list(request.kwargs.keys()) if request.kwargs else []
            )
        )
        
        result = await service.call_method(
            model=request.model,
            method=request.method,
            args=request.args,
            kwargs=request.kwargs,
            context=request.context
        )

        duration = (time.time() - start_time) * 1000
        logger.info(
            "✅ [ENDPOINT] /call_kw completed successfully\n"
            "   Model: {}\n"
            "   Method: {}\n"
            "   Result type: {}\n"
            "   Duration: {:.2f}ms".format(
                str(request.model),
                str(request.method),
                type(result).__name__,
                duration
            )
        )

        return CallKwResponse(
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
        duration = (time.time() - start_time) * 1000
        error_msg = str(e).replace('{', '{{').replace('}', '}}')
        logger.error(
            "❌ [ENDPOINT] /call_kw error: {}\n"
            "   Model: {}\n"
            "   Method: {}\n"
            "   Duration: {:.2f}ms".format(
                error_msg,
                str(request.model),
                str(request.method),
                duration
            ),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error: {str(e)}"
        )
    finally:
        await service.close()


@router.post("/call_method", response_model=CallMethodResponse)
async def call_method(
    request: CallMethodRequest,
    service: CustomOperations = Depends(get_custom_service)
):
    """
    Call any public method on a model (alias for call_kw)

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
