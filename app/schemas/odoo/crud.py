"""
CRUD schemas for Odoo operations
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union


class CreateRequest(BaseModel):
    """Request schema for create operation"""
    model: str = Field(..., description="Model name", min_length=1)
    values: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(
        ...,
        description="Values for new record(s)"
    )
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "res.partner",
                "values": {
                    "name": "New Customer",
                    "email": "customer@example.com",
                    "is_company": True
                }
            }
        }


class CreateResponse(BaseModel):
    """Response schema for create operation"""
    success: bool = True
    id: Optional[int] = Field(default=None, description="Created record ID (single)")
    ids: Optional[List[int]] = Field(default=None, description="Created record IDs (batch)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "id": 42
            }
        }


class ReadRequest(BaseModel):
    """Request schema for read operation"""
    model: str = Field(..., description="Model name", min_length=1)
    ids: List[int] = Field(..., description="Record IDs to read", min_length=1)
    fields: Optional[List[str]] = Field(default=None, description="Fields to read")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "res.partner",
                "ids": [1, 2, 3],
                "fields": ["name", "email", "phone"]
            }
        }


class ReadResponse(BaseModel):
    """Response schema for read operation"""
    success: bool = True
    records: List[Dict[str, Any]] = Field(default=[], description="List of records")
    count: int = Field(default=0, description="Number of records")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "records": [
                    {"id": 1, "name": "Partner A", "email": "a@example.com"}
                ],
                "count": 1
            }
        }


class WriteRequest(BaseModel):
    """Request schema for write (update) operation"""
    model: str = Field(..., description="Model name", min_length=1)
    ids: List[int] = Field(..., description="Record IDs to update", min_length=1)
    values: Dict[str, Any] = Field(..., description="Values to update")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "res.partner",
                "ids": [1],
                "values": {
                    "name": "Updated Name",
                    "phone": "+1234567890"
                }
            }
        }


class WriteResponse(BaseModel):
    """Response schema for write operation"""
    success: bool = True
    updated: bool = Field(default=True, description="Whether update succeeded")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "updated": True
            }
        }


class UnlinkRequest(BaseModel):
    """Request schema for unlink (delete) operation"""
    model: str = Field(..., description="Model name", min_length=1)
    ids: List[int] = Field(..., description="Record IDs to delete", min_length=1)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "res.partner",
                "ids": [100, 101, 102]
            }
        }


class UnlinkResponse(BaseModel):
    """Response schema for unlink operation"""
    success: bool = True
    deleted: bool = Field(default=True, description="Whether deletion succeeded")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "deleted": True
            }
        }
