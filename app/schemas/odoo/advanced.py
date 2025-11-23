"""
Advanced operation schemas for Odoo
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class OnchangeRequest(BaseModel):
    """Request schema for onchange operation"""
    model: str = Field(..., description="Model name", min_length=1)
    ids: List[int] = Field(default=[], description="Record IDs (empty for new record)")
    values: Dict[str, Any] = Field(..., description="Current field values")
    field_name: str = Field(..., description="Field that changed", min_length=1)
    field_onchange: Dict[str, Any] = Field(
        ...,
        description="Specification of fields with onchange"
    )
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order.line",
                "ids": [],
                "values": {
                    "order_id": 100,
                    "product_id": 50,
                    "product_uom_qty": 5.0
                },
                "field_name": "product_id",
                "field_onchange": {
                    "product_id": "1",
                    "price_unit": "1",
                    "discount": "1",
                    "tax_id": "1"
                }
            }
        }


class OnchangeResponse(BaseModel):
    """Response schema for onchange operation"""
    success: bool = True
    value: Dict[str, Any] = Field(default={}, description="Computed field values")
    warning: Optional[Dict[str, Any]] = Field(default=None, description="Warning message")
    domain: Optional[Dict[str, List]] = Field(default=None, description="Updated field domains")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "value": {
                    "price_unit": 150.0,
                    "discount": 10.0,
                    "name": "Product Description"
                },
                "warning": None,
                "domain": None
            }
        }


class ReadGroupRequest(BaseModel):
    """Request schema for read_group operation"""
    model: str = Field(..., description="Model name", min_length=1)
    domain: Optional[List] = Field(default=[], description="Filter domain")
    fields: Optional[List[str]] = Field(default=[], description="Fields to aggregate")
    groupby: Optional[List[str]] = Field(default=[], description="Fields to group by")
    offset: Optional[int] = Field(default=None, ge=0, description="Offset for pagination")
    limit: Optional[int] = Field(default=None, ge=1, description="Maximum groups")
    orderby: Optional[str] = Field(default=None, description="Sort order for groups")
    lazy: bool = Field(default=True, description="Lazy grouping")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order",
                "domain": [["state", "=", "sale"]],
                "fields": ["amount_total:sum"],
                "groupby": ["partner_id"],
                "orderby": "amount_total desc",
                "limit": 10
            }
        }


class ReadGroupResponse(BaseModel):
    """Response schema for read_group operation"""
    success: bool = True
    groups: List[Dict[str, Any]] = Field(default=[], description="Grouped data")
    count: int = Field(default=0, description="Number of groups")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "groups": [
                    {
                        "partner_id": [1, "Customer A"],
                        "amount_total": 5000.0,
                        "__domain": [["partner_id", "=", 1], ["state", "=", "sale"]],
                        "__count": 10
                    }
                ],
                "count": 1
            }
        }


class DefaultGetRequest(BaseModel):
    """Request schema for default_get operation"""
    model: str = Field(..., description="Model name", min_length=1)
    fields: List[str] = Field(..., description="Fields to get defaults for", min_length=1)
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order",
                "fields": ["partner_id", "date_order", "pricelist_id"]
            }
        }


class DefaultGetResponse(BaseModel):
    """Response schema for default_get operation"""
    success: bool = True
    defaults: Dict[str, Any] = Field(default={}, description="Default values")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "defaults": {
                    "date_order": "2024-11-23",
                    "pricelist_id": 1
                }
            }
        }


class CopyRequest(BaseModel):
    """Request schema for copy operation"""
    model: str = Field(..., description="Model name", min_length=1)
    id: int = Field(..., description="Record ID to copy", gt=0)
    default: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Override values for the copy"
    )
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order",
                "id": 100,
                "default": {
                    "date_order": "2024-12-01",
                    "client_order_ref": "COPY-001"
                }
            }
        }


class CopyResponse(BaseModel):
    """Response schema for copy operation"""
    success: bool = True
    id: int = Field(..., description="ID of the new record", gt=0)

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "id": 101
            }
        }
