"""
Web operation schemas for Odoo
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class WebSaveRequest(BaseModel):
    """Request schema for web_save operation"""
    model: str = Field(..., description="Model name", min_length=1)
    ids: List[int] = Field(default=[], description="Record IDs (empty for create)")
    values: Dict[str, Any] = Field(..., description="Values to save")
    specification: Dict[str, Any] = Field(..., description="Fields specification to return")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order",
                "ids": [1],
                "values": {"partner_id": 10},
                "specification": {
                    "name": {},
                    "amount_total": {},
                    "order_line": {
                        "fields": {"name": {}, "price_subtotal": {}}
                    }
                }
            }
        }


class WebSaveResponse(BaseModel):
    """Response schema for web_save operation"""
    success: bool = True
    records: List[Dict[str, Any]] = Field(default=[], description="Saved records")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "records": [{"id": 1, "name": "SO001", "amount_total": 1000.0}]
            }
        }


class WebReadRequest(BaseModel):
    """Request schema for web_read operation"""
    model: str = Field(..., description="Model name", min_length=1)
    ids: List[int] = Field(..., description="Record IDs to read", min_length=1)
    specification: Dict[str, Any] = Field(..., description="Fields specification")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order",
                "ids": [1, 2, 3],
                "specification": {
                    "name": {},
                    "partner_id": {"fields": {"name": {}, "email": {}}},
                    "order_line": {
                        "fields": {
                            "product_id": {"fields": {"name": {}}},
                            "product_uom_qty": {},
                            "price_unit": {}
                        },
                        "limit": 50
                    }
                }
            }
        }


class WebReadResponse(BaseModel):
    """Response schema for web_read operation"""
    success: bool = True
    records: List[Dict[str, Any]] = Field(default=[], description="Records with nested data")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "records": [
                    {
                        "id": 1,
                        "name": "SO001",
                        "partner_id": {"id": 10, "name": "Customer A", "email": "a@test.com"},
                        "order_line": [
                            {"product_id": {"id": 1, "name": "Product X"}, "product_uom_qty": 5}
                        ]
                    }
                ]
            }
        }


class WebSearchReadRequest(BaseModel):
    """Request schema for web_search_read operation"""
    model: str = Field(..., description="Model name", min_length=1)
    domain: Optional[List] = Field(default=[], description="Search domain")
    specification: Optional[Dict[str, Any]] = Field(default={}, description="Fields specification")
    limit: Optional[int] = Field(default=None, ge=1, le=10000, description="Maximum records")
    offset: Optional[int] = Field(default=None, ge=0, description="Offset for pagination")
    order: Optional[str] = Field(default=None, description="Sort order")
    count_limit: Optional[int] = Field(default=None, description="Limit for counting")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order",
                "domain": [["state", "=", "sale"]],
                "specification": {
                    "name": {},
                    "partner_id": {"fields": {"name": {}}},
                    "amount_total": {}
                },
                "limit": 20,
                "order": "date_order DESC"
            }
        }


class WebSearchReadResponse(BaseModel):
    """Response schema for web_search_read operation"""
    success: bool = True
    records: List[Dict[str, Any]] = Field(default=[], description="List of records")
    length: int = Field(default=0, description="Number of records returned")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "records": [{"id": 1, "name": "SO001", "amount_total": 1000.0}],
                "length": 1
            }
        }
