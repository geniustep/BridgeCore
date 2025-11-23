"""
Base schemas for Odoo operations

Provides foundational Pydantic models used across all Odoo operations.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union


class DomainItem(BaseModel):
    """Single domain condition"""
    field: str
    operator: str
    value: Any

    class Config:
        json_schema_extra = {
            "example": {
                "field": "is_company",
                "operator": "=",
                "value": True
            }
        }


class Context(BaseModel):
    """Odoo context dictionary"""
    lang: Optional[str] = Field(None, description="Language code (e.g., 'en_US', 'fr_FR')")
    tz: Optional[str] = Field(None, description="Timezone (e.g., 'UTC', 'America/New_York')")
    uid: Optional[int] = Field(None, description="User ID")
    company_id: Optional[int] = Field(None, description="Company ID")
    allowed_company_ids: Optional[List[int]] = Field(None, description="Allowed company IDs")

    class Config:
        extra = "allow"  # Allow additional context keys


class OdooBaseRequest(BaseModel):
    """Base request schema for all Odoo operations"""
    model: str = Field(..., description="Odoo model name (e.g., 'res.partner')", min_length=1)
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context values"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model": "res.partner",
                "context": {"lang": "en_US"}
            }
        }


class OdooBaseResponse(BaseModel):
    """Base response schema for all Odoo operations"""
    success: bool = Field(..., description="Whether the operation succeeded")
    message: Optional[str] = Field(None, description="Optional message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully"
            }
        }


class OdooErrorResponse(BaseModel):
    """Error response schema for Odoo operations"""
    success: bool = Field(default=False, description="Always False for errors")
    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "OdooExecutionError",
                "message": "Record does not exist",
                "details": {"model": "res.partner", "id": 999}
            }
        }


# Type alias for domain - can be list of lists or DomainItem
Domain = List[Union[List[Any], str]]  # Includes '&', '|', '!' operators
