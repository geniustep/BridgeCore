"""
Search schemas for Odoo operations
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class SearchRequest(BaseModel):
    """Request schema for search operation"""
    model: str = Field(..., description="Model name", min_length=1)
    domain: Optional[List] = Field(default=[], description="Search domain")
    limit: Optional[int] = Field(default=None, ge=1, le=10000, description="Maximum records")
    offset: Optional[int] = Field(default=None, ge=0, description="Offset for pagination")
    order: Optional[str] = Field(default=None, description="Sort order (e.g., 'name ASC')")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "res.partner",
                "domain": [["is_company", "=", True]],
                "limit": 100,
                "order": "name ASC"
            }
        }


class SearchResponse(BaseModel):
    """Response schema for search operation"""
    success: bool = True
    ids: List[int] = Field(default=[], description="List of matching record IDs")
    count: int = Field(default=0, description="Number of IDs returned")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "ids": [1, 5, 10, 15, 20],
                "count": 5
            }
        }


class SearchReadRequest(BaseModel):
    """Request schema for search_read operation"""
    model: str = Field(..., description="Model name", min_length=1)
    domain: Optional[List] = Field(default=[], description="Search domain")
    fields: Optional[List[str]] = Field(default=None, description="Fields to read")
    limit: Optional[int] = Field(default=None, ge=1, le=10000, description="Maximum records")
    offset: Optional[int] = Field(default=None, ge=0, description="Offset for pagination")
    order: Optional[str] = Field(default=None, description="Sort order")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "product.product",
                "domain": [["sale_ok", "=", True]],
                "fields": ["name", "list_price", "qty_available"],
                "limit": 50,
                "order": "name ASC"
            }
        }


class SearchReadResponse(BaseModel):
    """Response schema for search_read operation"""
    success: bool = True
    records: List[Dict[str, Any]] = Field(default=[], description="List of records")
    count: int = Field(default=0, description="Number of records returned")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "records": [
                    {"id": 1, "name": "Product A", "list_price": 100.0},
                    {"id": 2, "name": "Product B", "list_price": 200.0}
                ],
                "count": 2
            }
        }


class SearchCountRequest(BaseModel):
    """Request schema for search_count operation"""
    model: str = Field(..., description="Model name", min_length=1)
    domain: Optional[List] = Field(default=[], description="Search domain")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order",
                "domain": [["state", "in", ["sale", "done"]]]
            }
        }


class SearchCountResponse(BaseModel):
    """Response schema for search_count operation"""
    success: bool = True
    count: int = Field(default=0, description="Count of matching records")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "count": 142
            }
        }


class PaginatedSearchReadRequest(BaseModel):
    """Request schema for paginated search_read"""
    model: str = Field(..., description="Model name", min_length=1)
    domain: Optional[List] = Field(default=[], description="Search domain")
    fields: Optional[List[str]] = Field(default=None, description="Fields to read")
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(default=50, ge=1, le=1000, description="Records per page")
    order: Optional[str] = Field(default=None, description="Sort order")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "res.partner",
                "domain": [["customer_rank", ">", 0]],
                "fields": ["name", "email", "phone"],
                "page": 1,
                "page_size": 25,
                "order": "name ASC"
            }
        }


class PaginatedSearchReadResponse(BaseModel):
    """Response schema for paginated search_read"""
    success: bool = True
    records: List[Dict[str, Any]] = Field(default=[], description="List of records")
    total: int = Field(default=0, description="Total number of matching records")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=50, description="Records per page")
    pages: int = Field(default=1, description="Total number of pages")
    has_next: bool = Field(default=False, description="Whether there are more pages")
    has_prev: bool = Field(default=False, description="Whether there are previous pages")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "records": [{"id": 1, "name": "Customer A"}],
                "total": 100,
                "page": 1,
                "page_size": 25,
                "pages": 4,
                "has_next": True,
                "has_prev": False
            }
        }
