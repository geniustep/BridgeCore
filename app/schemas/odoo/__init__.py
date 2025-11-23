"""
Odoo Schemas Module

This module provides Pydantic schemas for all Odoo API operations.
"""

from .base import (
    OdooBaseRequest,
    OdooBaseResponse,
    OdooErrorResponse,
    DomainItem,
    Context,
)
from .search import (
    SearchRequest,
    SearchResponse,
    SearchReadRequest,
    SearchReadResponse,
    SearchCountRequest,
    SearchCountResponse,
    PaginatedSearchReadRequest,
    PaginatedSearchReadResponse,
)
from .crud import (
    CreateRequest,
    CreateResponse,
    ReadRequest,
    ReadResponse,
    WriteRequest,
    WriteResponse,
    UnlinkRequest,
    UnlinkResponse,
)
from .advanced import (
    OnchangeRequest,
    OnchangeResponse,
    ReadGroupRequest,
    ReadGroupResponse,
    DefaultGetRequest,
    DefaultGetResponse,
    CopyRequest,
    CopyResponse,
)
from .names import (
    NameSearchRequest,
    NameSearchResponse,
    NameGetRequest,
    NameGetResponse,
    NameCreateRequest,
    NameCreateResponse,
)
from .views import (
    FieldsGetRequest,
    FieldsGetResponse,
    FieldsViewGetRequest,
    FieldsViewGetResponse,
    GetViewRequest,
    GetViewResponse,
    GetViewsRequest,
    GetViewsResponse,
)
from .web import (
    WebSaveRequest,
    WebSaveResponse,
    WebReadRequest,
    WebReadResponse,
    WebSearchReadRequest,
    WebSearchReadResponse,
)
from .permissions import (
    CheckAccessRightsRequest,
    CheckAccessRightsResponse,
)
from .utility import (
    ExistsRequest,
    ExistsResponse,
)
from .custom import (
    CallMethodRequest,
    CallMethodResponse,
    ActionRequest,
    ActionResponse,
)

__all__ = [
    # Base
    "OdooBaseRequest",
    "OdooBaseResponse",
    "OdooErrorResponse",
    "DomainItem",
    "Context",
    # Search
    "SearchRequest",
    "SearchResponse",
    "SearchReadRequest",
    "SearchReadResponse",
    "SearchCountRequest",
    "SearchCountResponse",
    "PaginatedSearchReadRequest",
    "PaginatedSearchReadResponse",
    # CRUD
    "CreateRequest",
    "CreateResponse",
    "ReadRequest",
    "ReadResponse",
    "WriteRequest",
    "WriteResponse",
    "UnlinkRequest",
    "UnlinkResponse",
    # Advanced
    "OnchangeRequest",
    "OnchangeResponse",
    "ReadGroupRequest",
    "ReadGroupResponse",
    "DefaultGetRequest",
    "DefaultGetResponse",
    "CopyRequest",
    "CopyResponse",
    # Names
    "NameSearchRequest",
    "NameSearchResponse",
    "NameGetRequest",
    "NameGetResponse",
    "NameCreateRequest",
    "NameCreateResponse",
    # Views
    "FieldsGetRequest",
    "FieldsGetResponse",
    "FieldsViewGetRequest",
    "FieldsViewGetResponse",
    "GetViewRequest",
    "GetViewResponse",
    "GetViewsRequest",
    "GetViewsResponse",
    # Web
    "WebSaveRequest",
    "WebSaveResponse",
    "WebReadRequest",
    "WebReadResponse",
    "WebSearchReadRequest",
    "WebSearchReadResponse",
    # Permissions
    "CheckAccessRightsRequest",
    "CheckAccessRightsResponse",
    # Utility
    "ExistsRequest",
    "ExistsResponse",
    # Custom
    "CallMethodRequest",
    "CallMethodResponse",
    "ActionRequest",
    "ActionResponse",
]
