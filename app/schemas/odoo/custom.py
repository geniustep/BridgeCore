"""
Custom method schemas for Odoo operations
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class CallMethodRequest(BaseModel):
    """Request schema for call_method operation"""
    model: str = Field(..., description="Model name", min_length=1)
    method: str = Field(..., description="Method name to call", min_length=1)
    args: Optional[List[Any]] = Field(default=[], description="Positional arguments")
    kwargs: Optional[Dict[str, Any]] = Field(default={}, description="Keyword arguments")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order",
                "method": "action_confirm",
                "args": [[1, 2, 3]],
                "kwargs": {}
            }
        }


class CallMethodResponse(BaseModel):
    """Response schema for call_method operation"""
    success: bool = True
    result: Any = Field(default=None, description="Method result")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "result": True
            }
        }


class ActionRequest(BaseModel):
    """Request schema for action methods (action_confirm, action_cancel, etc.)"""
    model: str = Field(..., description="Model name", min_length=1)
    ids: List[int] = Field(..., description="Record IDs", min_length=1)
    action: str = Field(..., description="Action method name", min_length=1)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order",
                "ids": [1],
                "action": "action_confirm"
            }
        }


class ActionResponse(BaseModel):
    """Response schema for action methods"""
    success: bool = True
    result: Any = Field(default=None, description="Action result")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "result": True
            }
        }


class MessagePostRequest(BaseModel):
    """Request schema for message_post operation"""
    model: str = Field(..., description="Model name", min_length=1)
    ids: List[int] = Field(..., description="Record IDs", min_length=1)
    body: str = Field(..., description="Message body (HTML)")
    message_type: str = Field(default="comment", description="Message type")
    subtype_xmlid: Optional[str] = Field(default=None, description="Subtype XML ID")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order",
                "ids": [1],
                "body": "<p>Order has been processed!</p>",
                "message_type": "comment"
            }
        }


class MessagePostResponse(BaseModel):
    """Response schema for message_post operation"""
    success: bool = True
    message_id: Optional[int] = Field(default=None, description="Created message ID")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message_id": 123
            }
        }
