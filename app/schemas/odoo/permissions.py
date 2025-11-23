"""
Permission schemas for Odoo operations
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class CheckAccessRightsRequest(BaseModel):
    """Request schema for check_access_rights operation"""
    model: str = Field(..., description="Model name", min_length=1)
    operation: str = Field(
        ...,
        description="Operation to check",
        pattern="^(create|read|write|unlink)$"
    )
    raise_exception: bool = Field(
        default=False,
        description="Raise exception if no access"
    )
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order",
                "operation": "write",
                "raise_exception": False
            }
        }


class CheckAccessRightsResponse(BaseModel):
    """Response schema for check_access_rights operation"""
    success: bool = True
    has_access: bool = Field(..., description="Whether user has access")
    operation: str = Field(..., description="Operation that was checked")
    model: str = Field(..., description="Model that was checked")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "has_access": True,
                "operation": "write",
                "model": "sale.order"
            }
        }


class CheckAllAccessRightsRequest(BaseModel):
    """Request schema for checking all CRUD rights"""
    model: str = Field(..., description="Model name", min_length=1)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order"
            }
        }


class CheckAllAccessRightsResponse(BaseModel):
    """Response schema for all access rights"""
    success: bool = True
    model: str = Field(..., description="Model that was checked")
    rights: Dict[str, bool] = Field(
        ...,
        description="Rights by operation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "model": "sale.order",
                "rights": {
                    "create": True,
                    "read": True,
                    "write": True,
                    "unlink": False
                }
            }
        }
