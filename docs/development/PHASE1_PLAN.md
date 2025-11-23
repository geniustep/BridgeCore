# 🚀 خطة تطوير BridgeCore - Phase 1

**التاريخ:** نوفمبر 2024  
**الهدف:** تطوير BridgeCore ليغطي جميع عمليات Odoo API (26 عملية)  
**المدة:** 4-6 أسابيع

---

## 📋 الوضع الحالي في BridgeCore

### ✅ العمليات الموجودة حالياً
من خلال مراجعة الـ README:

1. ✅ `create` - POST `/systems/{system_id}/create`
2. ✅ `read` - GET `/systems/{system_id}/read`
3. ✅ `update` - PUT `/systems/{system_id}/update/{id}`
4. ✅ `delete` - DELETE `/systems/{system_id}/delete/{id}`
5. ✅ `batch` - POST `/batch` (create, update, read)

**الملاحظات:**
- الـ endpoints الحالية تستخدم REST style مختلط
- لا يوجد توحيد واضح في الـ body structure
- معظم العمليات المتقدمة ناقصة

### ❌ العمليات الناقصة (21 عملية)

#### 🔴 أولوية عالية (Phase 1A)
1. ❌ `search` - البحث يرجع IDs
2. ❌ `search_read` - بحث وقراءة
3. ❌ `search_count` - عد السجلات
4. ❌ `onchange` - الحسابات التلقائية

#### 🟡 أولوية متوسطة (Phase 1B)
5. ❌ `name_search` - بحث للـ autocomplete
6. ❌ `name_get` - اسم العرض
7. ❌ `read_group` - تقارير مجمعة
8. ❌ `fields_get` - معلومات الحقول
9. ❌ `default_get` - القيم الافتراضية
10. ❌ `copy` - نسخ سجل
11. ❌ `check_access_rights` - الصلاحيات

#### 🟢 أولوية منخفضة (Phase 1C)
12. ❌ `name_create` - إنشاء بالاسم
13. ❌ `fields_view_get` - تعريف view
14. ❌ `load_views` - تحميل views
15. ❌ `get_views` - Odoo 17+
16. ❌ `exists` - فحص الوجود
17. ❌ `write` - (ربما موجود كـ update)

#### Web Operations (اختياري)
18. ❌ `web_save`
19. ❌ `web_read`
20. ❌ `web_search_read`

#### Custom Methods
21. ❌ `call_method` - استدعاء methods مخصصة

---

## 🎯 الخطة الجديدة

### 1. توحيد الـ API Structure

#### الهيكل المقترح الموحد

**بدلاً من:**
```
POST /systems/{system_id}/create?model=res.partner
GET  /systems/{system_id}/read?model=res.partner
PUT  /systems/{system_id}/update/{id}?model=res.partner
```

**الهيكل الجديد الموحد:**
```
POST /api/v1/odoo/create
POST /api/v1/odoo/read
POST /api/v1/odoo/write
POST /api/v1/odoo/unlink
POST /api/v1/odoo/search
POST /api/v1/odoo/search_read
... (كل العمليات)
```

**مع Body موحد:**
```json
{
  "system_id": "odoo-prod",          // من الـ tenant
  "model": "res.partner",
  "method": "search_read",           // optional (للتوضيح)
  "domain": [["is_company", "=", true]],
  "fields": ["name", "email"],
  "limit": 50,
  "offset": 0,
  "order": "name ASC",
  "context": {
    "lang": "ar_001",
    "tz": "Asia/Riyadh"
  }
}
```

---

## 📁 البنية المقترحة

```python
BridgeCore/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py              # موجود
│   │       ├── health.py            # موجود
│   │       ├── odoo/                # NEW - مجلد منفصل لـ Odoo
│   │       │   ├── __init__.py
│   │       │   ├── crud.py          # create, read, write, unlink
│   │       │   ├── search.py        # search, search_read, search_count
│   │       │   ├── advanced.py      # onchange, read_group, copy
│   │       │   ├── names.py         # name_search, name_get, name_create
│   │       │   ├── metadata.py      # fields_get, default_get
│   │       │   ├── views.py         # fields_view_get, load_views, get_views
│   │       │   ├── permissions.py   # check_access_rights
│   │       │   ├── web.py           # web_save, web_read, web_search_read
│   │       │   └── custom.py        # call_method
│   │       ├── batch.py             # موجود - نحسنه
│   │       └── systems.py           # نعيد تنظيمه
│   ├── services/
│   │   ├── odoo/                    # NEW
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # OdooOperationsService (Base)
│   │   │   ├── crud_ops.py          # CRUD operations
│   │   │   ├── search_ops.py        # Search operations
│   │   │   ├── advanced_ops.py      # Advanced operations
│   │   │   ├── name_ops.py          # Name operations
│   │   │   ├── metadata_ops.py      # Metadata operations
│   │   │   ├── view_ops.py          # View operations
│   │   │   ├── permission_ops.py    # Permission operations
│   │   │   └── web_ops.py           # Web operations
│   │   ├── odoo_client.py           # موجود - نحسنه
│   │   └── ...
│   ├── schemas/
│   │   ├── odoo/                    # NEW
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # BaseOdooRequest, BaseOdooResponse
│   │   │   ├── crud.py              # CreateRequest, ReadRequest, etc.
│   │   │   ├── search.py            # SearchRequest, SearchReadRequest
│   │   │   ├── advanced.py          # OnchangeRequest, ReadGroupRequest
│   │   │   └── ...
│   │   └── ...
│   └── ...
```

---

## 🔧 التنفيذ - Phase 1A (الأسبوع 1-2)

### Week 1: إعادة الهيكلة + العمليات الحرجة

#### Day 1-2: إعادة الهيكلة
**الهدف:** تجهيز البنية الأساسية

**Tasks:**
```python
# 1. إنشاء المجلدات الجديدة
mkdir -p app/api/routes/odoo
mkdir -p app/services/odoo
mkdir -p app/schemas/odoo

# 2. إنشاء Base Classes
```

**File: `app/services/odoo/base.py`**
```python
from abc import ABC
from typing import Any, Dict, List, Optional
import httpx
from loguru import logger

class OdooOperationsService(ABC):
    """
    طبقة أساسية لجميع عمليات Odoo
    تحتوي على المنطق المشترك:
    - استخراج credentials من tenant
    - إضافة context (lang, tz, company)
    - error handling
    - logging
    - caching
    """
    
    def __init__(
        self,
        odoo_url: str,
        database: str,
        username: str,
        password: str,
        context: Optional[Dict[str, Any]] = None
    ):
        self.odoo_url = odoo_url
        self.database = database
        self.username = username
        self.password = password
        self.base_context = context or {}
        self._uid: Optional[int] = None
        
    async def _authenticate(self) -> int:
        """مصادقة مع Odoo والحصول على UID"""
        if self._uid:
            return self._uid
            
        url = f"{self.odoo_url}/web/session/authenticate"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "db": self.database,
                        "login": self.username,
                        "password": self.password
                    }
                }
            )
            
            result = response.json()
            
            if "error" in result:
                raise Exception(f"Authentication failed: {result['error']}")
                
            self._uid = result["result"]["uid"]
            return self._uid
    
    async def _execute_kw(
        self,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """
        تنفيذ عملية Odoo عبر call_kw
        
        Args:
            model: اسم الـ model (مثل res.partner)
            method: اسم الـ method (مثل search_read)
            args: قائمة المعاملات الموضعية
            kwargs: معاملات مسماة (fields, limit, offset, etc.)
        """
        uid = await self._authenticate()
        
        # دمج الـ context
        merged_kwargs = kwargs or {}
        if "context" not in merged_kwargs:
            merged_kwargs["context"] = {}
        merged_kwargs["context"].update(self.base_context)
        
        url = f"{self.odoo_url}/web/dataset/call_kw"
        
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": model,
                "method": method,
                "args": args or [],
                "kwargs": merged_kwargs
            }
        }
        
        # Logging
        logger.info(f"Executing {model}.{method}", extra={
            "model": model,
            "method": method,
            "args_count": len(args) if args else 0
        })
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            result = response.json()
            
            if "error" in result:
                logger.error(f"Odoo error: {result['error']}")
                raise Exception(f"Odoo error: {result['error']}")
            
            return result.get("result")
    
    async def _execute_with_cache(
        self,
        cache_key: str,
        ttl: int,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """تنفيذ مع caching"""
        # TODO: Implement caching logic
        return await self._execute_kw(model, method, args, kwargs)
```

---

#### Day 3-4: Search Operations
**الهدف:** إضافة عمليات البحث الأساسية

**File: `app/services/odoo/search_ops.py`**
```python
from typing import List, Optional, Dict, Any
from .base import OdooOperationsService

class SearchOperations(OdooOperationsService):
    """عمليات البحث"""
    
    async def search(
        self,
        model: str,
        domain: Optional[List] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[int]:
        """
        بحث يرجع IDs فقط
        
        Args:
            model: اسم الـ model
            domain: شروط البحث
            limit: حد أقصى
            offset: الإزاحة
            order: الترتيب
            
        Returns:
            قائمة IDs
        """
        kwargs = {}
        if limit is not None:
            kwargs["limit"] = limit
        if offset is not None:
            kwargs["offset"] = offset
        if order:
            kwargs["order"] = order
            
        result = await self._execute_kw(
            model=model,
            method="search",
            args=[domain or []],
            kwargs=kwargs
        )
        
        return result
    
    async def search_read(
        self,
        model: str,
        domain: Optional[List] = None,
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        بحث وقراءة في عملية واحدة
        
        Returns:
            قائمة من السجلات
        """
        kwargs = {}
        if fields:
            kwargs["fields"] = fields
        if limit is not None:
            kwargs["limit"] = limit
        if offset is not None:
            kwargs["offset"] = offset
        if order:
            kwargs["order"] = order
            
        result = await self._execute_kw(
            model=model,
            method="search_read",
            args=[domain or []],
            kwargs=kwargs
        )
        
        return result
    
    async def search_count(
        self,
        model: str,
        domain: Optional[List] = None
    ) -> int:
        """
        عد السجلات المطابقة
        
        Returns:
            العدد
        """
        result = await self._execute_kw(
            model=model,
            method="search_count",
            args=[domain or []]
        )
        
        return result
```

**File: `app/api/routes/odoo/search.py`**
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from ....schemas.odoo.search import (
    SearchRequest,
    SearchResponse,
    SearchReadRequest,
    SearchReadResponse,
    SearchCountRequest,
    SearchCountResponse
)
from ....services.odoo.search_ops import SearchOperations
from ....core.deps import get_current_user, get_tenant_odoo_service

router = APIRouter()

@router.post("/search", response_model=SearchResponse)
async def search_records(
    request: SearchRequest,
    service: SearchOperations = Depends(get_tenant_odoo_service),
    current_user = Depends(get_current_user)
):
    """
    بحث عن سجلات يرجع IDs فقط
    
    Example:
    ```json
    {
      "model": "res.partner",
      "domain": [["is_company", "=", true]],
      "limit": 100,
      "order": "name ASC"
    }
    ```
    """
    try:
        ids = await service.search(
            model=request.model,
            domain=request.domain,
            limit=request.limit,
            offset=request.offset,
            order=request.order
        )
        
        return SearchResponse(
            success=True,
            ids=ids,
            count=len(ids)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search_read", response_model=SearchReadResponse)
async def search_read_records(
    request: SearchReadRequest,
    service: SearchOperations = Depends(get_tenant_odoo_service),
    current_user = Depends(get_current_user)
):
    """
    بحث وقراءة في عملية واحدة
    
    Example:
    ```json
    {
      "model": "res.partner",
      "domain": [["is_company", "=", true]],
      "fields": ["name", "email", "phone"],
      "limit": 50
    }
    ```
    """
    try:
        records = await service.search_read(
            model=request.model,
            domain=request.domain,
            fields=request.fields,
            limit=request.limit,
            offset=request.offset,
            order=request.order
        )
        
        return SearchReadResponse(
            success=True,
            records=records,
            count=len(records)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search_count", response_model=SearchCountResponse)
async def count_records(
    request: SearchCountRequest,
    service: SearchOperations = Depends(get_tenant_odoo_service),
    current_user = Depends(get_current_user)
):
    """
    عد السجلات المطابقة
    
    Example:
    ```json
    {
      "model": "res.partner",
      "domain": [["is_company", "=", true]]
    }
    ```
    """
    try:
        count = await service.search_count(
            model=request.model,
            domain=request.domain
        )
        
        return SearchCountResponse(
            success=True,
            count=count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**File: `app/schemas/odoo/search.py`**
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class SearchRequest(BaseModel):
    """طلب بحث"""
    model: str = Field(..., description="Model name (e.g., res.partner)")
    domain: Optional[List] = Field(default=[], description="Search domain")
    limit: Optional[int] = Field(default=None, ge=1, le=10000)
    offset: Optional[int] = Field(default=None, ge=0)
    order: Optional[str] = Field(default=None, description="Order by (e.g., 'name ASC')")
    
    class Config:
        schema_extra = {
            "example": {
                "model": "res.partner",
                "domain": [["is_company", "=", True]],
                "limit": 100,
                "order": "name ASC"
            }
        }

class SearchResponse(BaseModel):
    """نتيجة بحث"""
    success: bool
    ids: List[int]
    count: int

class SearchReadRequest(BaseModel):
    """طلب بحث وقراءة"""
    model: str
    domain: Optional[List] = Field(default=[])
    fields: Optional[List[str]] = Field(default=None)
    limit: Optional[int] = Field(default=None, ge=1, le=10000)
    offset: Optional[int] = Field(default=None, ge=0)
    order: Optional[str] = Field(default=None)
    
    class Config:
        schema_extra = {
            "example": {
                "model": "res.partner",
                "domain": [["is_company", "=", True]],
                "fields": ["name", "email", "phone"],
                "limit": 50
            }
        }

class SearchReadResponse(BaseModel):
    """نتيجة بحث وقراءة"""
    success: bool
    records: List[Dict[str, Any]]
    count: int

class SearchCountRequest(BaseModel):
    """طلب عد"""
    model: str
    domain: Optional[List] = Field(default=[])

class SearchCountResponse(BaseModel):
    """نتيجة عد"""
    success: bool
    count: int
```

---

#### Day 5-7: CRUD + Onchange
**الهدف:** إضافة `read` المنفصل و `onchange`

سأكمل باقي الملفات في الرد التالي...

---

## 📊 Progress Tracking

### Week 1
```
[██████████] Day 1-2: Restructure + Base
[██████████] Day 3-4: Search Operations
[░░░░░░░░░░] Day 5-7: CRUD + Onchange
```

### Week 2-6
```
[░░░░░░░░░░] Week 2: Phase 1B (7 operations)
[░░░░░░░░░░] Week 3: Phase 1B continued
[░░░░░░░░░░] Week 4: Phase 1C (4 operations)
[░░░░░░░░░░] Week 5: Web Operations
[░░░░░░░░░░] Week 6: Testing & Documentation
```

---

**Status:** 🟡 In Progress (Week 1 Day 3-4)  
**Next:** Complete Day 5-7 implementation

هل تريدني أن أكمل باقي الأيام والأسابيع؟
