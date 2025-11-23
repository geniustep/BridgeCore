"""
Utility schemas for Odoo operations
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ExistsRequest(BaseModel):
    """Request schema for exists operation"""
    model: str = Field(..., description="Model name", min_length=1)
    ids: List[int] = Field(..., description="Record IDs to check", min_length=1)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "res.partner",
                "ids": [1, 2, 3, 999]
            }
        }


class ExistsResponse(BaseModel):
    """Response schema for exists operation"""
    success: bool = True
    existing_ids: List[int] = Field(default=[], description="IDs that exist")
    missing_ids: List[int] = Field(default=[], description="IDs that don't exist")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "existing_ids": [1, 2, 3],
                "missing_ids": [999]
            }
        }


class ValidateReferencesRequest(BaseModel):
    """Request schema for validating multiple references"""
    references: List[Dict[str, Any]] = Field(
        ...,
        description="List of {'model': str, 'ids': List[int]}"
    )
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "references": [
                    {"model": "res.partner", "ids": [1, 2, 3]},
                    {"model": "product.product", "ids": [10, 20]}
                ]
            }
        }


class ValidateReferencesResponse(BaseModel):
    """Response schema for validating references"""
    success: bool = True
    valid: List[Dict[str, Any]] = Field(default=[], description="Valid references")
    invalid: List[Dict[str, Any]] = Field(default=[], description="Invalid references")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "valid": [
                    {"model": "res.partner", "requested": [1, 2], "existing": [1, 2], "missing": []}
                ],
                "invalid": [
                    {"model": "product.product", "requested": [10, 999], "existing": [10], "missing": [999]}
                ]
            }
        }
