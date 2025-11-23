"""
View operation schemas for Odoo
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Tuple, Union


class FieldsGetRequest(BaseModel):
    """Request schema for fields_get operation"""
    model: str = Field(..., description="Model name", min_length=1)
    fields: Optional[List[str]] = Field(default=None, description="Specific fields (None for all)")
    attributes: Optional[List[str]] = Field(
        default=None,
        description="Attributes to return (e.g., 'string', 'type', 'required')"
    )
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "res.partner",
                "fields": ["name", "email", "country_id"],
                "attributes": ["string", "type", "required", "relation"]
            }
        }


class FieldsGetResponse(BaseModel):
    """Response schema for fields_get operation"""
    success: bool = True
    fields: Dict[str, Dict[str, Any]] = Field(
        default={},
        description="Field definitions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "fields": {
                    "name": {"string": "Name", "type": "char", "required": True},
                    "email": {"string": "Email", "type": "char", "required": False},
                    "country_id": {"string": "Country", "type": "many2one", "relation": "res.country"}
                }
            }
        }


class FieldsViewGetRequest(BaseModel):
    """Request schema for fields_view_get operation (legacy)"""
    model: str = Field(..., description="Model name", min_length=1)
    view_id: Optional[int] = Field(default=None, description="Specific view ID")
    view_type: str = Field(default="form", description="View type")
    toolbar: bool = Field(default=False, description="Include toolbar actions")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "res.partner",
                "view_type": "form",
                "toolbar": True
            }
        }


class FieldsViewGetResponse(BaseModel):
    """Response schema for fields_view_get operation"""
    success: bool = True
    arch: str = Field(default="", description="XML view architecture")
    fields: Dict[str, Dict[str, Any]] = Field(default={}, description="Field definitions")
    name: Optional[str] = Field(default=None, description="View name")
    view_id: Optional[int] = Field(default=None, description="View ID")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "arch": "<form>...</form>",
                "fields": {"name": {"type": "char"}},
                "name": "res.partner.form",
                "view_id": 123
            }
        }


class GetViewRequest(BaseModel):
    """Request schema for get_view operation (Odoo 16+)"""
    model: str = Field(..., description="Model name", min_length=1)
    view_id: Optional[int] = Field(default=None, description="Specific view ID")
    view_type: str = Field(default="form", description="View type")
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="View options"
    )
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order",
                "view_type": "form",
                "options": {"toolbar": True}
            }
        }


class GetViewResponse(BaseModel):
    """Response schema for get_view operation"""
    success: bool = True
    view: Dict[str, Any] = Field(default={}, description="View definition")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "view": {
                    "arch": "<form>...</form>",
                    "fields": {},
                    "name": "sale.order.form"
                }
            }
        }


class GetViewsRequest(BaseModel):
    """Request schema for get_views operation (Odoo 16+)"""
    model: str = Field(..., description="Model name", min_length=1)
    views: List[List] = Field(
        ...,
        description="List of [view_id, view_type] pairs"
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="View options"
    )
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "sale.order",
                "views": [[False, "form"], [False, "list"]],
                "options": {"toolbar": True, "load_filters": True}
            }
        }


class GetViewsResponse(BaseModel):
    """Response schema for get_views operation"""
    success: bool = True
    views: Dict[str, Any] = Field(default={}, description="Views by type")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "views": {
                    "form": {"arch": "...", "fields": {}},
                    "list": {"arch": "...", "fields": {}}
                }
            }
        }
