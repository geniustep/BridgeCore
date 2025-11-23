"""
Name operation schemas for Odoo
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Tuple


class NameSearchRequest(BaseModel):
    """Request schema for name_search operation"""
    model: str = Field(..., description="Model name", min_length=1)
    name: str = Field(default="", description="Name to search for")
    args: Optional[List] = Field(default=None, description="Additional domain conditions")
    operator: str = Field(default="ilike", description="Search operator")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum results")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "res.partner",
                "name": "Ahmed",
                "args": [["is_company", "=", True]],
                "operator": "ilike",
                "limit": 10
            }
        }


class NameSearchResponse(BaseModel):
    """Response schema for name_search operation"""
    success: bool = True
    results: List[List] = Field(
        default=[],
        description="List of [id, display_name] pairs"
    )
    count: int = Field(default=0, description="Number of results")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "results": [
                    [1, "Ahmed Company"],
                    [5, "Ahmed Trading LLC"]
                ],
                "count": 2
            }
        }


class NameGetRequest(BaseModel):
    """Request schema for name_get operation"""
    model: str = Field(..., description="Model name", min_length=1)
    ids: List[int] = Field(..., description="Record IDs", min_length=1)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "res.partner",
                "ids": [1, 2, 3]
            }
        }


class NameGetResponse(BaseModel):
    """Response schema for name_get operation"""
    success: bool = True
    names: List[List] = Field(
        default=[],
        description="List of [id, display_name] pairs"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "names": [
                    [1, "Company A"],
                    [2, "John Doe"],
                    [3, "Jane Smith"]
                ]
            }
        }


class NameCreateRequest(BaseModel):
    """Request schema for name_create operation"""
    model: str = Field(..., description="Model name", min_length=1)
    name: str = Field(..., description="Name for new record", min_length=1)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "res.partner.category",
                "name": "New Category"
            }
        }


class NameCreateResponse(BaseModel):
    """Response schema for name_create operation"""
    success: bool = True
    id: int = Field(..., description="Created record ID")
    display_name: str = Field(..., description="Display name of created record")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "id": 10,
                "display_name": "New Category"
            }
        }
