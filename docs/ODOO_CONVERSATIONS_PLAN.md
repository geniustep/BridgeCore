# خطة دعم المحادثات في BridgeCore - Odoo Conversations Support Plan

## 📋 نظرة عامة

هذه الخطة توضح كيفية إضافة دعم كامل لجميع أنواع المحادثات التي يستخدمها Odoo 18.0 في BridgeCore بناءً على Odoo Official Documentation:

### أنواع المحادثات المدعومة:

1. **mail.message** - الرسائل
   - Direct Messages (model='mail.channel', channel_type='chat')
   - Chatter Messages (على sale.order, res.partner, etc.)
   - Channel Messages (في قنوات عامة)
   - Notifications (message_type='notification')

2. **mail.channel** - القنوات
   - Public Channels (public='public')
   - Private Channels (public='private')
   - Direct Message Channels (channel_type='chat')
   - Group-based Channels (public='groups')

3. **mail.thread** - Chatter Mixin
   - Abstract mixin لإضافة messaging capabilities لأي model
   - يدعم followers, message history, tracking

4. **mail.followers** - المتابعون
   - إدارة المتابعين للسجلات
   - تحديد من يحصل على إشعارات

### المميزات الرئيسية:

- ✅ **Webhook Integration**: تتبع جميع الرسائل والقنوات عبر auto-webhook-odoo
- ✅ **Real-time Messaging**: WebSocket support للرسائل الفورية
- ✅ **API Methods**: استخدام Odoo official methods (message_post, message_subscribe)
- ✅ **Sync Support**: دعم sync للمحادثات في التطبيقات المحمولة
- ✅ **Security**: التحقق من permissions قبل الوصول للمحادثات

---

## ⚠️ تصحيحات مهمة تم تطبيقها (بناءً على مراجعة أمنية)

قبل التنفيذ، تم تطبيق **4 تصحيحات حرجة**:

### A) Inheritance الصحيح في auto-webhook-odoo
- ❌ **خطأ:** `_name = 'mail.message'` + `_inherit`
- ✅ **صحيح:** `_inherit = ['mail.message', 'webhook.mixin']` فقط (Extension pattern)

### B) استخدام partner_id بدل user_id
- ❌ **خطأ:** `channel_member_ids` مع `user_id`
- ✅ **صحيح:** `channel_partner_ids` مع `partner_id` (Odoo messaging مبني على res.partner)

### C) Security: منع user_id/author_id من العميل
- ❌ **خطأ:** قبول `user_id` و `author_id` من request parameters
- ✅ **صحيح:** استخراج user/partner من JWT فقط

### D) message_post: author يأتي من session
- ❌ **خطأ:** إرسال `author_id` في message_post
- ✅ **صحيح:** Odoo يستخرج author تلقائياً من session user

---

## 📌 ملاحظات تنفيذية

1. **Partner vs User**: جميع queries تستخدم `partner_id` (res.partner)
2. **Authentication**: جميع endpoints تستخرج user/partner من JWT
3. **WebSocket Security**: لا user_id في path، authentication عبر token
4. **Routing**: نظام routing keys للأحداث (channel:{id}, thread:{model}:{id}, inbox:{partner_id})

---

## 🎯 الأهداف

1. ✅ تتبع جميع الرسائل والمحادثات في Odoo عبر webhooks
2. ✅ دعم Real-time messaging عبر WebSocket
3. ✅ Sync المحادثات للمستخدمين في التطبيقات المحمولة
4. ✅ دعم جميع أنواع المحادثات: Channels, DMs, Chatter
5. ✅ إدارة المتابعين والإشعارات

---

## 📊 أنواع المحادثات في Odoo (بناءً على Odoo 18.0 Documentation)

### 1. **mail.message** - الرسائل

**الأنواع:**
- **Direct Messages**: رسائل مباشرة بين المستخدمين (model='mail.channel', channel_type='chat')
- **Chatter Messages**: رسائل على سجلات (model='sale.order', 'res.partner', etc.)
- **Channel Messages**: رسائل في القنوات العامة (model='mail.channel')
- **Notifications**: إشعارات النظام (message_type='notification')

**الحقول الأساسية (Odoo 18.0 API):**
```python
{
    'id': int,                          # Message ID
    'model': str,                       # Related model (sale.order, mail.channel, etc.)
    'res_id': int,                      # Related record ID
    'message_type': str,                # 'comment', 'notification', 'email'
    'subtype_id': int,                  # Message subtype ID
    'subject': str,                     # Message subject
    'body': str,                        # Message body (HTML format)
    'author_id': int,                   # Author (res.partner) ID
    'author_name': str,                 # Author display name
    'partner_ids': List[int],           # Recipient partners
    'channel_ids': List[int],           # Associated channels
    'date': datetime,                   # Message date
    'parent_id': int,                   # Parent message ID (for replies)
    'attachment_ids': List[int],        # Attachments
    'is_internal': bool                 # Internal note flag
}
```

**Methods الرئيسية:**
- `message_post()`: إرسال رسالة جديدة في thread
- `message_post_with_template()`: إرسال رسالة باستخدام template
- `message_update()`: تحديث رسالة موجودة

### 2. **mail.channel** - القنوات

**الأنواع:**
- **Public Channels**: قنوات عامة (public='public')
- **Private Channels**: قنوات خاصة (public='private' أو groups-based)
- **Direct Message Channels**: قنوات الرسائل المباشرة (channel_type='chat')

**الحقول الأساسية:**
```python
{
    'id': int,
    'name': str,                        # Channel name
    'channel_type': str,                # 'chat', 'channel'
    'public': str,                      # 'public', 'private', 'groups'
    'description': str,                 # Channel description
    'channel_member_ids': List[int],    # Channel members (res.partner)
    'channel_partner_ids': List[int],   # Partner members
    'group_ids': List[int],             # Security groups (if public='groups')
    'message_ids': List[int],           # Related messages (One2many)
    'uuid': str                         # Unique ID (for DM channels)
}
```

**Methods الرئيسية:**
- `message_subscribe()`: إضافة members للقناة
- `message_unsubscribe()`: إزالة members من القناة

### 3. **mail.thread** - Mixin للـ Chatter

**الوصف:**
Abstract mixin model يضيف messaging capabilities لأي model آخر. جميع السجلات التي ترث `mail.thread` تدعم:
- **Chatter**: نافذة المحادثات في form view
- **Followers**: نظام المتابعين
- **Message History**: سجل الرسائل الكامل

**الحقول المضافة (عند الـ inherit):**
```python
{
    'message_ids': List[int],           # One2many to mail.message
    'message_follower_ids': List[int],  # Followers (mail.followers)
    'message_partner_ids': List[int],   # Partner followers
    'message_channel_ids': List[int],   # Channel followers
    'message_unread': bool,             # Unread messages flag
    'message_unread_counter': int,      # Unread messages count
    'message_needaction': bool,         # Messages requiring action
    'message_needaction_counter': int   # Needaction messages count
}
```

**Implementation Example:**
```python
class BusinessTrip(models.Model):
    _name = 'business.trip'
    _inherit = ['mail.thread']  # Enables chatter
    
    name = fields.Char(tracking=True)  # Track changes in chatter
    partner_id = fields.Many2one('res.partner', tracking=True)
```

**XML Integration:**
```xml
<form>
    <sheet>
        <!-- Form fields -->
    </sheet>
    <chatter open_attachments="True"/>
</form>
```

### 4. **mail.followers** - المتابعون

**الوصف:**
يحدد من يتابع السجلات ويحصل على إشعارات عند التغييرات.

**الحقول:**
```python
{
    'res_model': str,                   # Model name (e.g., 'sale.order')
    'res_id': int,                      # Record ID
    'partner_id': int,                  # Follower partner
    'channel_id': int,                  # Follower channel (optional)
    'subtype_ids': List[int]            # Notification subtypes
}
```

**Methods الرئيسية (في mail.thread):**
- `message_subscribe(partner_ids, channel_ids, subtype_ids)`: إضافة متابعين
- `message_unsubscribe(partner_ids, channel_ids)`: إزالة متابعين
- `message_unsubscribe_users(user_ids)`: إزالة متابعين من users

---

## 🏗️ البنية المعمارية

```
┌─────────────────────────────────────────────────────────┐
│                    Odoo System                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │mail.message │  │mail.channel │  │mail.thread  │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
│         │                 │                 │          │
│         └─────────────────┴─────────────────┘          │
│                    │                                    │
│              webhook.mixin                              │
│                    │                                    │
└────────────────────┼────────────────────────────────────┘
                     │
                     │ Webhook Events
                     ▼
┌─────────────────────────────────────────────────────────┐
│              auto-webhook-odoo                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Webhook Events (mail.message, mail.channel)   │    │
│  └────────────────────────────────────────────────┘    │
│                    │                                    │
└────────────────────┼────────────────────────────────────┘
                     │
                     │ Pull/Push Webhooks
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  BridgeCore                             │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Conversation Service                            │  │
│  │  - Sync conversations                            │  │
│  │  - Real-time messaging                           │  │
│  │  - Channel management                            │  │
│  └──────────────────────────────────────────────────┘  │
│                    │                                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │  WebSocket Manager                               │  │
│  │  - Real-time message delivery                    │  │
│  │  - Channel subscriptions                         │  │
│  └──────────────────────────────────────────────────┘  │
│                    │                                    │
└────────────────────┼────────────────────────────────────┘
                     │
                     │ API + WebSocket
                     ▼
┌─────────────────────────────────────────────────────────┐
│            Mobile/Web Applications                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Conversation UI                                 │  │
│  │  - Channels List                                 │  │
│  │  - Direct Messages                               │  │
│  │  - Chatter on Records                            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 المراحل التنفيذية

### المرحلة 1: إضافة Models في auto-webhook-odoo

#### 1.1 إضافة mail.message support ⚠️ تصحيح مهم

**الملف:** `/opt/auto-webhook-odoo/models/list_model.py`

```python
from odoo import models

class MailMessage(models.Model):
    """رسائل Odoo (Direct Messages, Chatter, Channel Messages)"""
    _inherit = ['mail.message', 'webhook.mixin']
```

**تصحيح مهم:**
- ❌ **خطأ:** لا تستعمل `_name` عند تمديد model موجود
- ✅ **صحيح:** استعمل `_inherit` فقط (Extension pattern في Odoo)
- Priority: **high** (رسائل مهمة يجب أن تصل فوراً)
- Instant send: **True** (للرسائل المباشرة)

#### 1.2 إضافة mail.channel support ⚠️ تصحيح مهم

```python
from odoo import models

class MailChannel(models.Model):
    """قنوات المحادثات (Public/Private Channels, DMs)"""
    _inherit = ['mail.channel', 'webhook.mixin']
```

**تصحيح مهم:**
- ❌ **خطأ:** لا تستعمل `_name` عند تمديد model موجود
- ✅ **صحيح:** استعمل `_inherit` فقط
- Priority: **high** (تغييرات القنوات مهمة)
- Instant send: **True** (للرسائل في القنوات)

#### 1.3 إضافة mail.followers support (اختياري) ⚠️ تصحيح مهم

```python
from odoo import models

class MailFollowers(models.Model):
    """متابعي السجلات"""
    _inherit = ['mail.followers', 'webhook.mixin']
```

**تصحيح مهم:**
- ❌ **خطأ:** لا تستعمل `_name` عند تمديد model موجود
- ✅ **صحيح:** استعمل `_inherit` فقط
- Priority: **medium** (تغييرات المتابعين أقل أهمية)
- Instant send: **False**

---

### المرحلة 2: إعدادات Webhook في Odoo

**الملف:** `/opt/auto-webhook-odoo/data/webhook_data.xml`

#### 2.1 إضافة webhook.config لـ mail.message

```xml
<!-- Mail Messages -->
<record id="webhook_config_mail_message" model="webhook.config">
    <field name="name">Mail Messages</field>
    <field name="model_id" ref="mail.model_mail_message"/>
    <field name="enabled" eval="True"/>
    <field name="active" eval="True"/>
    <field name="priority">high</field>
    <field name="category">notification</field>
    <field name="events">create</field>
    <field name="instant_send" eval="True"/>
    <field name="subscribers" eval="[(4, ref('auto_webhook.webhook_subscriber_bridgecore'))]"/>
    <field name="notes">High priority webhook for mail messages (DMs, Chatter, Channel messages). Push-based for instant delivery.</field>
</record>
```

#### 2.2 إضافة webhook.config لـ mail.channel

```xml
<!-- Mail Channels -->
<record id="webhook_config_mail_channel" model="webhook.config">
    <field name="name">Mail Channels</field>
    <field name="model_id" ref="mail.model_mail_channel"/>
    <field name="enabled" eval="True"/>
    <field name="active" eval="True"/>
    <field name="priority">high</field>
    <field name="category">notification</field>
    <field name="events">create,write</field>
    <field name="instant_send" eval="True"/>
    <field name="subscribers" eval="[(4, ref('auto_webhook.webhook_subscriber_bridgecore'))]"/>
    <field name="notes">High priority webhook for mail channels (channel creation, member changes). Push-based for instant delivery.</field>
</record>
```

---

### المرحلة 3: تحديث BridgeCore Models Mapping

#### 3.1 تحديث APP_TYPE_MODELS في WebhookService

**الملف:** `/opt/BridgeCore/app/modules/webhook/service.py`

```python
APP_TYPE_MODELS = {
    "sales_app": [
        "sale.order",
        "sale.order.line",
        "res.partner",
        "product.template",
        "product.product",
        "product.category",
        # Conversations
        "mail.message",
        "mail.channel",
    ],
    "delivery_app": [
        "stock.picking",
        "stock.move",
        "stock.move.line",
        "res.partner",
        # Conversations
        "mail.message",
        "mail.channel",
    ],
    "warehouse_app": [
        "stock.picking",
        "stock.move",
        "stock.move.line",
        "stock.quant",
        "product.product",
        "stock.location",
        # Conversations
        "mail.message",
        "mail.channel",
    ],
    "manager_app": [
        "sale.order",
        "purchase.order",
        "account.move",
        "res.partner",
        "hr.expense",
        "project.project",
        # Conversations
        "mail.message",
        "mail.channel",
    ],
    "mobile_app": [
        "sale.order",
        "res.partner",
        "product.template",
        "product.product",
        # Conversations
        "mail.message",
        "mail.channel",
    ],
    # New app type for messaging
    "messaging_app": [
        "mail.message",
        "mail.channel",
        "res.partner",
        "res.users",
    ],
}
```

#### 3.2 تحديث APP_TYPE_MODELS في OdooSyncService

**الملف:** `/opt/BridgeCore/app/modules/odoo_sync/service.py`

```python
APP_TYPE_MODELS = {
    # ... existing models ...
    "messaging_app": [
        "mail.message",
        "mail.channel",
        "res.partner",
        "res.users",
    ],
}
```

#### 3.3 تحديث APP_TYPE_MODELS في OfflineSyncService

**الملف:** `/opt/BridgeCore/app/modules/offline_sync/service.py`

```python
APP_TYPE_MODELS = {
    # ... existing models ...
    "messaging_app": [
        "mail.message",
        "mail.channel",
        "res.partner",
        "res.users",
    ],
}
```

---

### المرحلة 4: Schemas للمحادثات

**الملف:** `/opt/BridgeCore/app/modules/webhook/schemas.py`

#### 4.1 Conversation-specific schemas (Odoo 18.0 Compatible)

```python
# ===== Conversation Schemas =====
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class MailMessageData(BaseModel):
    """Mail message data structure - Odoo 18.0 compatible"""
    id: int
    model: Optional[str] = Field(None, description="Related model: 'sale.order', 'mail.channel', etc.")
    res_id: Optional[int] = Field(None, description="Related record ID")
    message_type: Literal["comment", "notification", "email", "user_notification"] = Field(
        ..., description="Message type"
    )
    subtype_id: Optional[int] = Field(None, description="Message subtype ID")
    subject: Optional[str] = Field(None, description="Message subject")
    body: Optional[str] = Field(None, description="Message body (HTML format)")
    author_id: Optional[int] = Field(None, description="Author partner ID")
    author_name: Optional[str] = Field(None, description="Author display name")
    partner_ids: Optional[List[int]] = Field(default=[], description="Recipient partner IDs")
    channel_ids: Optional[List[int]] = Field(default=[], description="Associated channel IDs")
    date: datetime = Field(..., description="Message date")
    parent_id: Optional[int] = Field(None, description="Parent message ID (for replies)")
    attachment_ids: Optional[List[int]] = Field(default=[], description="Attachment IDs")
    is_internal: Optional[bool] = Field(False, description="Internal note flag")
    
    class Config:
        from_attributes = True


class MailChannelData(BaseModel):
    """
    Mail channel data structure - Odoo 18.0 compatible
    
    ⚠️ تصحيح مهم: channel_member_ids في Odoo هي records وليست List[int]
    نستخدم members_partner_ids (List[int]) للاستخدام في BridgeCore
    """
    id: int
    name: str = Field(..., description="Channel name")
    channel_type: Literal["chat", "channel"] = Field(..., description="Channel type")
    public: Literal["public", "private", "groups"] = Field(
        default="private", description="Channel visibility"
    )
    description: Optional[str] = Field(None, description="Channel description")
    members_partner_ids: List[int] = Field(
        default=[], description="Channel member partner IDs (res.partner IDs)"
    )
    channel_partner_ids: Optional[List[int]] = Field(
        default=[], description="Partner member IDs (alternative field name)"
    )
    group_ids: Optional[List[int]] = Field(
        default=[], description="Security groups (if public='groups')"
    )
    message_ids: Optional[List[int]] = Field(
        default=[], description="Related message IDs"
    )
    uuid: Optional[str] = Field(None, description="Unique ID (for DM channels)")
    
    class Config:
        from_attributes = True


class MailFollowerData(BaseModel):
    """Mail follower data structure"""
    id: int
    res_model: str = Field(..., description="Model name (e.g., 'sale.order')")
    res_id: int = Field(..., description="Record ID")
    partner_id: Optional[int] = Field(None, description="Follower partner ID")
    channel_id: Optional[int] = Field(None, description="Follower channel ID")
    subtype_ids: Optional[List[int]] = Field(default=[], description="Notification subtype IDs")


class ConversationEventData(EventData):
    """Extended event data for conversations"""
    message_data: Optional[MailMessageData] = None
    channel_data: Optional[MailChannelData] = None
    follower_data: Optional[MailFollowerData] = None
    conversation_type: Optional[Literal["channel", "dm", "chatter"]] = Field(
        None, description="Conversation type classification"
    )


# Request/Response Schemas
class SendMessageRequest(BaseModel):
    """
    Request schema for sending a message
    
    ⚠️ تصحيح أمني مهم: author_id غير مسموح - يستخرج من JWT
    """
    model: str = Field(..., description="Target model")
    res_id: int = Field(..., description="Target record ID")
    body: str = Field(..., description="Message body (HTML)")
    partner_ids: Optional[List[int]] = Field(default=[], description="Recipient partner IDs")
    subject: Optional[str] = None
    parent_id: Optional[int] = Field(None, description="Parent message ID (reply)")
    attachments: Optional[List[dict]] = Field(default=[], description="Attachments")


class ChannelListResponse(BaseModel):
    """Response schema for channel list"""
    channels: List[MailChannelData]
    total: int


class MessageListResponse(BaseModel):
    """Response schema for message list"""
    messages: List[MailMessageData]
    total: int
    limit: int
    offset: int


class SendMessageResponse(BaseModel):
    """Response schema for send message"""
    id: int
    success: bool
    message: Optional[str] = None
```

---

### المرحلة 5: Conversation Service

**الملف الجديد:** `/opt/BridgeCore/app/modules/conversation/service.py`

```python
"""
Conversation Service - Handle Odoo conversations
"""
from typing import List, Optional, Dict, Any
from loguru import logger
from app.utils.odoo_client import OdooClient
from app.services.cache_service import CacheService


class ConversationService:
    """Service for handling Odoo conversations"""

    def __init__(
        self,
        odoo_client: OdooClient,
        cache_service: CacheService
    ):
        self.odoo = odoo_client
        self.cache = cache_service

    async def get_user_channels(self, partner_id: int) -> List[Dict]:
        """
        Get all channels for a partner
        
        ⚠️ تصحيح مهم: Odoo messaging مبني على res.partner وليس res.users
        - channel_partner_ids يحتوي على partner IDs
        - channel_member_ids هي records (ليست IDs مباشرة)
        """
        domain = [
            ("channel_partner_ids", "in", [partner_id])
        ]
        channels = self.odoo.search_read(
            "mail.channel",
            domain,
            fields=["id", "name", "channel_type", "public", "description", "channel_partner_ids"]
        )
        return channels

    async def get_channel_messages(
        self,
        channel_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """Get messages in a channel"""
        domain = [
            ("model", "=", "mail.channel"),
            ("res_id", "=", channel_id),
            ("message_type", "=", "comment")
        ]
        messages = self.odoo.search_read(
            "mail.message",
            domain,
            fields=[
                "id", "body", "author_id", "author_name",
                "date", "subject", "partner_ids"
            ],
            limit=limit,
            offset=offset,
            order="date desc"
        )
        return messages

    async def get_record_chatter(
        self,
        model: str,
        record_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """Get chatter messages for a record"""
        domain = [
            ("model", "=", model),
            ("res_id", "=", record_id),
            ("message_type", "=", "comment")
        ]
        messages = self.odoo.search_read(
            "mail.message",
            domain,
            fields=[
                "id", "body", "author_id", "author_name",
                "date", "subject"
            ],
            limit=limit,
            order="date desc"
        )
        return messages

    async def send_message(
        self,
        model: str,
        res_id: int,
        body: str,
        partner_ids: Optional[List[int]] = None,
        subject: Optional[str] = None,
        parent_id: Optional[int] = None,
        message_type: str = "comment"
    ) -> Dict:
        """
        Send a new message using message_post() method (Odoo 18.0 best practice)
        
        ⚠️ تصحيحات مهمة:
        1. author_id غير مطلوب - Odoo يستخرجه من session user تلقائياً
        2. message_post يعمل على model نفسه (mail.channel.message_post أو sale.order.message_post)
        3. partner_ids هي الـ recipients الرئيسية (channel_ids اختيارية)
        
        Uses message_post() which is the recommended way to send messages in Odoo
        as it properly handles notifications, followers, and message threading.
        """
        kwargs = {
            "body": body,
            "message_type": message_type,
        }
        
        if subject:
            kwargs["subject"] = subject
        if parent_id:
            kwargs["parent_id"] = parent_id
        if partner_ids:
            kwargs["partner_ids"] = partner_ids
        
        # message_post automatically uses current user as author
        # Works for both mail.channel and any mail.thread model
        message_id = self.odoo.call_kw(
            model,
            "message_post",
            [[res_id]],
            kwargs
        )
        return {"id": message_id, "success": True}
    
    async def send_message_with_template(
        self,
        model: str,
        res_id: int,
        template_id: int,
        **kwargs
    ) -> Dict:
        """
        Send message using email template (Odoo 18.0 message_post_with_template)
        
        Uses message_post_with_template() for template-based messages
        """
        message_id = self.odoo.call_kw(
            model,
            "message_post_with_template",
            [[res_id]],
            {
                "template_id": template_id,
                **kwargs
            }
        )
        return {"id": message_id, "success": True}
    
    async def subscribe_followers(
        self,
        model: str,
        res_id: int,
        partner_ids: Optional[List[int]] = None,
        channel_ids: Optional[List[int]] = None,
        subtype_ids: Optional[List[int]] = None
    ) -> bool:
        """
        Subscribe followers to a record (Odoo 18.0 message_subscribe)
        """
        return self.odoo.call_kw(
            model,
            "message_subscribe",
            [[res_id]],
            {
                "partner_ids": partner_ids or [],
                "channel_ids": channel_ids or [],
                "subtype_ids": subtype_ids or [],
            }
        )
    
    async def unsubscribe_followers(
        self,
        model: str,
        res_id: int,
        partner_ids: Optional[List[int]] = None,
        channel_ids: Optional[List[int]] = None
    ) -> bool:
        """
        Unsubscribe followers from a record (Odoo 18.0 message_unsubscribe)
        """
        return self.odoo.call_kw(
            model,
            "message_unsubscribe",
            [[res_id]],
            {
                "partner_ids": partner_ids or [],
                "channel_ids": channel_ids or [],
            }
        )
    
    async def _get_record_followers(
        self,
        model: str,
        res_id: int
    ) -> List[int]:
        """
        Get partner IDs of followers for a record
        
        ⚠️ مهم: نستخدم mail.followers للحصول على followers
        """
        domain = [
            ("res_model", "=", model),
            ("res_id", "=", res_id)
        ]
        followers = self.odoo.search_read(
            "mail.followers",
            domain,
            fields=["partner_id"]
        )
        # Extract partner_ids (filter None values)
        partner_ids = [
            f["partner_id"][0] if isinstance(f.get("partner_id"), list) else f.get("partner_id")
            for f in followers
            if f.get("partner_id")
        ]
        return partner_ids

    async def get_direct_messages(self, partner_id: int) -> List[Dict]:
        """
        Get direct message channels for a partner
        
        ⚠️ تصحيح مهم: استعمل partner_id بدل user_id
        """
        domain = [
            ("channel_type", "=", "chat"),
            ("channel_partner_ids", "in", [partner_id])
        ]
        channels = self.odoo.search_read(
            "mail.channel",
            domain,
            fields=["id", "name", "channel_partner_ids", "uuid"]
        )
        return channels
```

---

### المرحلة 6: Conversation Router

**الملف الجديد:** `/opt/BridgeCore/app/modules/conversation/router.py`

```python
"""
Conversation Router - API endpoints for conversations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.modules.conversation.schemas import (
    ChannelListResponse,
    MessageListResponse,
    SendMessageRequest,
    SendMessageResponse
)
from app.modules.conversation.service import ConversationService
from app.utils.odoo_client import get_odoo_client
from app.services.cache_service import get_cache_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/channels", response_model=ChannelListResponse)
async def get_channels(
    current_user = Depends(get_current_user),  # ⚠️ تصحيح أمني: من JWT
    odoo_client = Depends(get_odoo_client),
    cache_service = Depends(get_cache_service)
):
    """
    Get all channels for current user
    
    ⚠️ تصحيح أمني مهم: user_id/partner_id يأتي من JWT فقط، ليس من query params
    """
    # Extract partner_id from current_user
    partner_id = current_user.partner_id  # أو current_user.get_partner_id()
    service = ConversationService(odoo_client, cache_service)
    channels = await service.get_user_channels(partner_id)
    return ChannelListResponse(channels=channels)


@router.get("/channels/{channel_id}/messages", response_model=MessageListResponse)
async def get_channel_messages(
    channel_id: int,
    limit: int = 50,
    offset: int = 0,
    odoo_client = Depends(get_odoo_client),
    cache_service = Depends(get_cache_service)
):
    """Get messages in a channel"""
    service = ConversationService(odoo_client, cache_service)
    messages = await service.get_channel_messages(channel_id, limit, offset)
    return MessageListResponse(messages=messages)


@router.get("/chatter/{model}/{record_id}", response_model=MessageListResponse)
async def get_record_chatter(
    model: str,
    record_id: int,
    limit: int = 50,
    odoo_client = Depends(get_odoo_client),
    cache_service = Depends(get_cache_service)
):
    """Get chatter messages for a record"""
    service = ConversationService(odoo_client, cache_service)
    messages = await service.get_record_chatter(model, record_id, limit)
    return MessageListResponse(messages=messages)


@router.post("/messages/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    current_user = Depends(get_current_user),  # ⚠️ تصحيح أمني: من JWT
    odoo_client = Depends(get_odoo_client),
    cache_service = Depends(get_cache_service)
):
    """
    Send a new message
    
    ⚠️ تصحيح أمني مهم: author يأتي من JWT session، ليس من request
    """
    service = ConversationService(odoo_client, cache_service)
    result = await service.send_message(
        model=request.model,
        res_id=request.res_id,
        body=request.body,
        partner_ids=request.partner_ids,
        subject=request.subject,
        parent_id=request.parent_id
    )
    return SendMessageResponse(**result)
```

---

### المرحلة 7: WebSocket Support للمحادثات

**الملف:** `/opt/BridgeCore/app/api/routes/websocket.py`

#### 7.1 إضافة conversation subscriptions

```python
# في ConnectionManager class

async def subscribe_to_channel(
    self,
    websocket: WebSocket,
    user_id: int,
    partner_id: int,
    channel_id: int
):
    """
    Subscribe to a channel for real-time messages
    
    ⚠️ تصحيح: نستخدم connection-based subscriptions + routing keys
    """
    channel_key = f"channel:{channel_id}"
    if channel_key not in self.channel_subscriptions:
        self.channel_subscriptions[channel_key] = set()
    
    # Store connection reference, not just user_id
    connection_id = id(websocket)
    self.channel_subscriptions[channel_key].add(connection_id)
    
    # Also store connection mapping
    if user_id not in self.active_connections:
        self.active_connections[user_id] = {}
    self.active_connections[user_id][connection_id] = {
        "websocket": websocket,
        "partner_id": partner_id,
        "subscriptions": set([channel_key])
    }
    
    logger.info(f"Connection {connection_id} (user {user_id}, partner {partner_id}) subscribed to channel {channel_id}")


async def broadcast_to_routing(
    self,
    routing_key: str,
    message: dict
):
    """
    Broadcast message to subscribers of a routing key
    
    Routing keys:
    - channel:{channel_id} - Channel messages
    - thread:{model}:{res_id} - Chatter messages
    - inbox:{partner_id} - Personal inbox
    """
    if routing_key in self.channel_subscriptions:
        connection_ids = self.channel_subscriptions[routing_key].copy()
        for conn_id in connection_ids:
            # Find connection and send message
            for user_id, connections in self.active_connections.items():
                if conn_id in connections:
                    websocket = connections[conn_id]["websocket"]
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        logger.error(f"Failed to send to connection {conn_id}: {e}")
                        # Clean up dead connection
                        del connections[conn_id]
                        self.channel_subscriptions[routing_key].discard(conn_id)
```

#### 7.2 WebSocket endpoint للمحادثات

```python
@router.websocket("/ws/conversations")
async def websocket_conversations(
    websocket: WebSocket,
    token: Optional[str] = Query(None)  # ⚠️ تصحيح أمني: auth via token
):
    """
    WebSocket endpoint for real-time conversations
    
    ⚠️ تصحيح أمني مهم:
    1. لا نستخدم user_id في path (security risk)
    2. نستخرج user/partner من JWT token في query/header
    3. نستخدم connection-based subscriptions بدل user_id فقط
    """
    # Extract user/partner from JWT token
    user_id, partner_id = await authenticate_websocket_token(token)
    
    await manager.connect(websocket, user_id, partner_id)
    
    try:
        # Initial subscription message should include channel_id
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "subscribe_channel":
                channel_id = data.get("channel_id")
                await manager.subscribe_to_channel(websocket, user_id, partner_id, channel_id)
            elif action == "unsubscribe_channel":
                channel_id = data.get("channel_id")
                await manager.unsubscribe_from_channel(websocket, channel_id)
            
            await websocket.send_json({"status": "received"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
```

---

### المرحلة 8: معالجة Webhook Events للمحادثات

**الملف:** `/opt/BridgeCore/app/modules/webhook/service.py`

#### 8.1 تحديث receive_webhook method

```python
async def receive_webhook(
    self,
    payload: dict
) -> Dict[str, Any]:
    """Receive webhook event from Odoo"""
    # ... existing code ...
    
    model = payload.get("model")
    
    # Handle conversation webhooks
    if model == "mail.message":
        await self._handle_message_webhook(payload)
    elif model == "mail.channel":
        await self._handle_channel_webhook(payload)
    
    # ... rest of the code ...


async def _handle_message_webhook(self, payload: dict):
    """
    Handle mail.message webhook
    
    ⚠️ تصحيح مهم: تحديد المستلمين بدقة عبر:
    1. Channel messages → channel subscribers
    2. Chatter messages → record followers (mail.followers)
    3. Routing: channel:{id}, thread:{model}:{id}, inbox:{partner_id}
    """
    record_id = payload.get("record_id")
    event_type = payload.get("event")
    
    if event_type == "create":
        message_data = payload.get("data", {})
        model = message_data.get("model")  # mail.channel, sale.order, etc.
        res_id = message_data.get("res_id")
        partner_ids = message_data.get("partner_ids", [])
        
        if model == "mail.channel":
            # Channel message: broadcast to channel subscribers
            await manager.broadcast_to_routing(
                routing_key=f"channel:{res_id}",
                message={
                    "type": "channel_message",
                    "channel_id": res_id,
                    "message": message_data
                }
            )
        else:
            # Chatter message: notify record followers
            # Fetch followers from mail.followers
            followers = await self._get_record_followers(model, res_id)
            
            # Notify each follower via inbox routing
            for follower_partner_id in followers:
                await manager.broadcast_to_routing(
                    routing_key=f"inbox:{follower_partner_id}",
                    message={
                        "type": "chatter_message",
                        "model": model,
                        "res_id": res_id,
                        "message": message_data
                    }
                )
            
            # Also broadcast to thread subscribers
            await manager.broadcast_to_routing(
                routing_key=f"thread:{model}:{res_id}",
                message={
                    "type": "thread_message",
                    "model": model,
                    "res_id": res_id,
                    "message": message_data
                }
            )


async def _handle_channel_webhook(self, payload: dict):
    """
    Handle mail.channel webhook
    
    ⚠️ تصحيح: استخدام routing system للأحداث
    """
    record_id = payload.get("record_id")
    event_type = payload.get("event")
    channel_data = payload.get("data", {})
    
    if event_type == "write":
        # Channel updated (members added/removed, etc.)
        # Notify channel members of changes via routing
        await manager.broadcast_to_routing(
            routing_key=f"channel:{record_id}",
            message={
                "type": "channel_updated",
                "channel_id": record_id,
                "data": channel_data
            }
        )
```

---

## 🔄 خطة التنفيذ التدريجية

### الأسبوع 1: Foundation
- ✅ إضافة mail.message و mail.channel models في auto-webhook-odoo
- ✅ إضافة webhook.config للمحادثات
- ✅ اختبار webhooks من Odoo

### الأسبوع 2: BridgeCore Backend
- ✅ تحديث APP_TYPE_MODELS في جميع الخدمات
- ✅ إنشاء Conversation Schemas
- ✅ إنشاء Conversation Service
- ✅ إنشاء Conversation Router

### الأسبوع 3: Real-time Features
- ✅ WebSocket support للمحادثات
- ✅ Channel subscriptions
- ✅ Real-time message broadcasting
- ✅ Integration مع webhook service

### الأسبوع 4: Testing & Optimization
- ✅ اختبار جميع أنواع المحادثات
- ✅ اختبار Real-time messaging
- ✅ Optimize performance
- ✅ Documentation

---

## 📌 ملاحظات مهمة

1. **Performance**: 
   - mail.message قد يكون volume كبير جداً
   - نستخدم filtering حسب user_id و channel_id في queries
   - Caching للقنوات والرسائل

2. **Security**:
   - التحقق من permissions قبل إرسال/قراءة الرسائل
   - Channel members only can see channel messages
   - Record followers only can see chatter messages

3. **Filtering**:
   - Filter messages حسب user_id (messages relevant to user)
   - Exclude system notifications إذا لزم الأمر
   - Pagination للرسائل الكثيرة

4. **Real-time vs Sync**:
   - Real-time: WebSocket للرسائل الجديدة
   - Sync: Pull-based للرسائل القديمة

---

## 🔍 التحقق من الحقول والـ API (Verification & Testing)

قبل التنفيذ النهائي، يجب التحقق من الحقول الفعلية في Odoo 18.0 عبر ORM.

### 1) التحقق من حقول Models

**Script للتحقق من الحقول:**

```python
# verification_script.py
from app.utils.odoo_client import OdooClient

async def verify_odoo_fields():
    """Verify actual field names in Odoo 18.0"""
    
    odoo = OdooClient(base_url=settings.ODOO_URL, session_id=session_id)
    
    models_to_check = [
        'mail.message',
        'mail.channel',
        'mail.followers',
        'mail.thread'  # check available fields
    ]
    
    results = {}
    
    for model_name in models_to_check:
        try:
            # Get all fields metadata
            fields_metadata = odoo.call_kw(
                model_name,
                'fields_get',
                [],
                {'attributes': ['string', 'type', 'relation', 'help']}
            )
            
            results[model_name] = {
                'fields': fields_metadata,
                'key_fields': {}
            }
            
            # Extract key fields we need
            if model_name == 'mail.message':
                results[model_name]['key_fields'] = {
                    'author_id': fields_metadata.get('author_id'),
                    'partner_ids': fields_metadata.get('partner_ids'),
                    'channel_ids': fields_metadata.get('channel_ids'),
                    'model': fields_metadata.get('model'),
                    'res_id': fields_metadata.get('res_id'),
                    'message_type': fields_metadata.get('message_type'),
                }
            elif model_name == 'mail.channel':
                results[model_name]['key_fields'] = {
                    'channel_type': fields_metadata.get('channel_type'),
                    'public': fields_metadata.get('public'),
                    'channel_partner_ids': fields_metadata.get('channel_partner_ids'),
                    'channel_member_ids': fields_metadata.get('channel_member_ids'),
                }
            elif model_name == 'mail.followers':
                results[model_name]['key_fields'] = {
                    'res_model': fields_metadata.get('res_model'),
                    'res_id': fields_metadata.get('res_id'),
                    'partner_id': fields_metadata.get('partner_id'),
                    'channel_id': fields_metadata.get('channel_id'),
                }
                
            print(f"\n✅ {model_name} fields verified")
            
        except Exception as e:
            print(f"\n❌ Error checking {model_name}: {e}")
            results[model_name] = {'error': str(e)}
    
    # Save results to file for reference
    import json
    with open('odoo_18_fields_verification.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    return results

# Run verification
if __name__ == '__main__':
    results = await verify_odoo_fields()
```

**الاستخدام:**

```python
# في BridgeCore: app/modules/conversation/verification.py
from app.modules.conversation.verification import verify_odoo_fields

# Run once during setup
verification_results = await verify_odoo_fields()
```

---

### 2) اختبار message_post على Models مختلفة

**Script للاختبار:**

```python
# test_message_post.py
async def test_message_post():
    """Test message_post on different models"""
    
    odoo = OdooClient(base_url=settings.ODOO_URL, session_id=session_id)
    
    test_cases = [
        {
            'name': 'Channel message',
            'model': 'mail.channel',
            'res_id': 1,  # existing channel ID
            'body': 'Test channel message',
        },
        {
            'name': 'Chatter on sale.order',
            'model': 'sale.order',
            'res_id': 1,  # existing sale order ID
            'body': 'Test chatter message',
        },
        {
            'name': 'Chatter on res.partner',
            'model': 'res.partner',
            'res_id': 1,  # existing partner ID
            'body': 'Test partner chatter',
        },
    ]
    
    results = []
    
    for test_case in test_cases:
        try:
            # Call message_post
            message_id = odoo.call_kw(
                test_case['model'],
                'message_post',
                [[test_case['res_id']]],
                {
                    'body': test_case['body'],
                    'message_type': 'comment',
                }
            )
            
            # Verify message was created
            message = odoo.call_kw(
                'mail.message',
                'read',
                [[message_id]],
                {
                    'fields': ['id', 'model', 'res_id', 'author_id', 'body', 'message_type']
                }
            )
            
            results.append({
                'test': test_case['name'],
                'success': True,
                'message_id': message_id,
                'message_data': message[0] if message else None,
                'author_from_session': message[0]['author_id'][0] if message and message[0].get('author_id') else None,
            })
            
            print(f"✅ {test_case['name']}: Message ID {message_id}")
            
        except Exception as e:
            results.append({
                'test': test_case['name'],
                'success': False,
                'error': str(e)
            })
            print(f"❌ {test_case['name']}: {e}")
    
    return results

# Run tests
if __name__ == '__main__':
    results = await test_message_post()
```

---

### 3) التحقق من channel_partner_ids vs channel_member_ids

**Script للتحقق:**

```python
# verify_channel_fields.py
async def verify_channel_structure():
    """Verify channel partner/member fields structure"""
    
    odoo = OdooClient(base_url=settings.ODOO_URL, session_id=session_id)
    
    # Get a sample channel
    channel_ids = odoo.call_kw('mail.channel', 'search', [[('channel_type', '=', 'channel')]], {'limit': 1})
    
    if not channel_ids:
        print("No channels found for testing")
        return None
    
    channel_id = channel_ids[0]
    
    # Read channel with all relevant fields
    channel = odoo.call_kw(
        'mail.channel',
        'read',
        [[channel_id]],
        {
            'fields': [
                'id', 'name', 'channel_type', 'public',
                'channel_partner_ids', 'channel_member_ids',
            ]
        }
    )[0]
    
    print(f"\nChannel: {channel['name']} (ID: {channel_id})")
    print(f"channel_partner_ids type: {type(channel.get('channel_partner_ids'))}")
    print(f"channel_partner_ids value: {channel.get('channel_partner_ids')}")
    print(f"channel_member_ids type: {type(channel.get('channel_member_ids'))}")
    print(f"channel_member_ids value: {channel.get('channel_member_ids')}")
    
    # Test search with channel_partner_ids
    current_partner_id = odoo.call_kw('res.users', 'read', [[odoo.user_id]], {'fields': ['partner_id']})[0]['partner_id'][0]
    
    domain_with_partner_ids = [('channel_partner_ids', 'in', [current_partner_id])]
    channels_via_partner_ids = odoo.call_kw('mail.channel', 'search', [domain_with_partner_ids], {})
    
    print(f"\n✅ Search with channel_partner_ids: Found {len(channels_via_partner_ids)} channels")
    
    return {
        'channel_structure': channel,
        'search_test': {
            'domain': domain_with_partner_ids,
            'found_channels': channels_via_partner_ids,
        }
    }
```

---

### 4) Document الحقول الفعلية

بعد التحقق، أضف ملف مرجعي:

**الملف:** `/opt/BridgeCore/docs/ODOO_18_FIELDS_REFERENCE.md`

```markdown
# Odoo 18.0 Fields Reference - Verified

This document contains verified field names from Odoo 18.0 installation.

## mail.message

**Verified Fields:**
- `author_id`: Many2one → res.partner
- `partner_ids`: Many2many → res.partner (recipients)
- `channel_ids`: Many2many → mail.channel
- `model`: Char (related model name)
- `res_id`: Integer (related record ID)
- `message_type`: Selection (comment, notification, email)
- `body`: Html (message content)

**Notes:**
- author_id is automatically set from session user's partner
- message_post() does not require author_id parameter

## mail.channel

**Verified Fields:**
- `channel_type`: Selection (chat, channel)
- `public`: Selection (public, private, groups)
- `channel_partner_ids`: Many2many → res.partner ✅ (USE THIS for queries)
- `channel_member_ids`: One2many → mail.channel.member (records, not IDs)

**Notes:**
- Use `channel_partner_ids` for domain searches (List[int] of partner IDs)
- `channel_member_ids` are records with additional metadata

---

## 📝 ملخص التحقق مقابل الوثائق الرسمية

بناءً على مراجعة **Odoo 18.0 Official Documentation**:

### ✅ ما تم تأكيده رسمياً:

1. **Extension Pattern (A)**: ✅ مثبت - استخدام `_inherit` بدون `_name` للتمديد
2. **mail.thread + chatter**: ✅ مثبت - طريقة إضافة messaging لأي model
3. **Followers system**: ✅ مثبت - الرسائل تُرسل للمتابعين
4. **message_post API**: ✅ مثبت - لا يتطلب `author_id` كـ parameter

### ⚠️ ما يحتاج تحقق عملي (ORM/Code):

1. **تفاصيل الحقول**: `channel_partner_ids`, `channel_member_ids`, `public='groups'`
   - **الحل**: استخدام `fields_get()` كما في verification script

2. **partner_id كقاعدة عامة**: منطقي ومؤيد بالأمثلة، لكن تفاصيل الحقول تحتاج ORM
   - **الحل**: التحقق من structure الحقول الفعلية

### ✅ التصحيحات الأمنية (C, D):

- **C (JWT only)**: متوافق مع API + أفضل ممارسة أمنية
- **D (author from session)**: منطقي رغم عدم ذكره نصياً (API لا يتطلب author_id)

**الخلاصة**: الخطة صحيحة، لكن يجب التحقق من الحقول الفعلية قبل التنفيذ النهائي.

## mail.followers

**Verified Fields:**
- `res_model`: Char (model name)
- `res_id`: Integer (record ID)
- `partner_id`: Many2one → res.partner
- `channel_id`: Many2one → mail.channel (optional)

**Notes:**
- One follower record per (res_model, res_id, partner_id/channel_id)
```

---

## 📋 خطة التحقق قبل التنفيذ

### المرحلة 0: Pre-implementation Verification

1. [ ] تشغيل `verify_odoo_fields()` script
2. [ ] حفظ نتائج `fields_get()` في ملف JSON
3. [ ] تحديث Schemas بناءً على الحقول الفعلية
4. [ ] اختبار `test_message_post()` على models مختلفة
5. [ ] التحقق من `channel_partner_ids` structure
6. [ ] إنشاء `ODOO_18_FIELDS_REFERENCE.md` مع الحقول المؤكدة

### بعد التحقق:

7. [ ] تحديث ConversationService domains بناءً على الحقول الفعلية
8. [ ] تحديث Schemas إذا كان هناك اختلافات
9. [ ] اختبار integration كامل

---

## ✅ Checklist مصحّح (مع التصحيحات الأمنية والهيكلية)

### Pre-Implementation Verification (المرحلة 0)
- [ ] تشغيل `verification.py` script للتحقق من الحقول
- [ ] حفظ نتائج `fields_get()` في `odoo_18_verification_results.json`
- [ ] مراجعة `ODOO_18_FIELDS_REFERENCE.md` (إنشاءه بعد التحقق)
- [ ] تحديث Schemas بناءً على الحقول الفعلية المكتشفة
- [ ] اختبار `message_post()` على models مختلفة
- [ ] التحقق من `channel_partner_ids` structure والـ domains

### auto-webhook-odoo
- [ ] إضافة mail.message: `_inherit = ['mail.message', 'webhook.mixin']` (بدون `_name`)
- [ ] إضافة mail.channel: `_inherit = ['mail.channel', 'webhook.mixin']` (بدون `_name`)
- [ ] إضافة mail.followers: `_inherit = ['mail.followers', 'webhook.mixin']` (بدون `_name`)
- [ ] إضافة webhook.config للمحادثات

### BridgeCore Backend
- [ ] تحديث APP_TYPE_MODELS في WebhookService/OdooSyncService/OfflineSyncService
- [ ] إنشاء Conversation Schemas (بدون author_id في SendMessageRequest)
- [ ] إنشاء Conversation Service:
  - [ ] استخدام `partner_id` بدل `user_id` في جميع queries
  - [ ] استخدام `channel_partner_ids` في domains
  - [ ] `send_message()` بدون `author_id` parameter
  - [ ] helper method: `get_partner_id_from_jwt()`
- [ ] إنشاء Conversation Router:
  - [ ] إزالة `user_id` من query params
  - [ ] استخراج user/partner من JWT dependency (`get_current_user`)
  - [ ] إزالة `author_id` من SendMessageRequest

### Security & WebSocket
- [ ] WebSocket endpoint: `/ws/conversations` (بدون user_id في path)
- [ ] WebSocket authentication: JWT token في query/header
- [ ] Connection-based subscriptions (بدل user_id فقط)
- [ ] Routing keys: `channel:{id}`, `thread:{model}:{id}`, `inbox:{partner_id}`

### Webhook Handling
- [ ] `_handle_message_webhook()`: تحديد المستلمين بدقة
  - [ ] Channel messages → channel subscribers
  - [ ] Chatter messages → record followers (mail.followers)
  - [ ] Routing system للأحداث
- [ ] `_get_record_followers()`: helper method لجلب followers

### Performance & Optimization
- [ ] Pagination: cursor-based (date/id) بدل offset فقط
- [ ] Permission checks: membership في channel + access rules للسجل
- [ ] Caching: للقنوات والرسائل

### Testing
- [ ] اختبار inheritance الصحيح في auto-webhook-odoo
- [ ] اختبار partner_id vs user_id في queries
- [ ] اختبار security: عدم قبول user_id/author_id من العميل
- [ ] اختبار message_post على models مختلفة
- [ ] اختبار WebSocket authentication
- [ ] اختبار routing للأحداث
