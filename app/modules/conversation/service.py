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
        cache_key = f"conversation:channels:partner:{partner_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        domain = [
            ("channel_partner_ids", "in", [partner_id])
        ]
        channels = self.odoo.search_read(
            "mail.channel",
            domain,
            fields=["id", "name", "channel_type", "public", "description", "channel_partner_ids"],
            limit=100
        )
        
        # Transform channel_partner_ids to members_partner_ids for consistency
        for channel in channels:
            if "channel_partner_ids" in channel:
                channel["members_partner_ids"] = channel["channel_partner_ids"]
        
        # Cache for 60 seconds
        await self.cache.set(cache_key, channels, ttl=60)
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
        messages = self.odoo.call_kw(
            "mail.message",
            "search_read",
            [domain],
            {
                "fields": [
                    "id", "body", "author_id", "date", "subject", "partner_ids",
                    "channel_ids", "parent_id"
                ],
                "limit": limit,
                "offset": offset,
                "order": "date desc"
            }
        )
        
        # Transform author_id from tuple to dict
        for msg in messages:
            author_id_data = msg.get("author_id")
            if isinstance(author_id_data, (list, tuple)) and len(author_id_data) >= 2:
                msg["author_id"] = author_id_data[0]
                msg["author_name"] = author_id_data[1] if len(author_id_data) > 1 else None
            elif isinstance(author_id_data, (list, tuple)) and len(author_id_data) == 1:
                msg["author_id"] = author_id_data[0]
                msg["author_name"] = None
            # Ensure date is properly formatted
            if isinstance(msg.get("date"), str):
                # Date is already a string, will be parsed by validator
                pass
        
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
                "id", "body", "author_id", "date", "subject", "parent_id"
            ],
            limit=limit,
            order="date desc"
        )
        
        # Transform author_id
        for msg in messages:
            author_id_data = msg.get("author_id")
            if isinstance(author_id_data, (list, tuple)) and len(author_id_data) >= 2:
                msg["author_id"] = author_id_data[0]
                msg["author_name"] = author_id_data[1] if len(author_id_data) > 1 else None
            elif isinstance(author_id_data, (list, tuple)) and len(author_id_data) == 1:
                msg["author_id"] = author_id_data[0]
                msg["author_name"] = None
        
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
        3. partner_ids هي الـ recipients الرئيسية
        
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
        
        # Invalidate cache for this channel/record
        if model == "mail.channel":
            cache_key = f"conversation:messages:channel:{res_id}"
        else:
            cache_key = f"conversation:messages:{model}:{res_id}"
        await self.cache.delete(cache_key)
        
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
            [[res_id], template_id],
            kwargs
        )
        return {"id": message_id, "success": True}
    
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
            fields=["id", "name", "channel_partner_ids", "uuid"],
            limit=100
        )
        return channels
    
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
        kwargs = {}
        if partner_ids:
            kwargs["partner_ids"] = partner_ids
        if channel_ids:
            kwargs["channel_ids"] = channel_ids
        if subtype_ids:
            kwargs["subtype_ids"] = subtype_ids
        
        result = self.odoo.call_kw(
            model,
            "message_subscribe",
            [[res_id]],
            kwargs
        )
        return result
    
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
        kwargs = {}
        if partner_ids:
            kwargs["partner_ids"] = partner_ids
        if channel_ids:
            kwargs["channel_ids"] = channel_ids
        
        result = self.odoo.call_kw(
            model,
            "message_unsubscribe",
            [[res_id]],
            kwargs
        )
        return result
    
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
            fields=["partner_id"],
            limit=1000  # Reasonable limit for followers
        )
        # Extract partner_ids (filter None values)
        partner_ids = []
        for f in followers:
            partner_id = f.get("partner_id")
            if partner_id:
                if isinstance(partner_id, (list, tuple)) and len(partner_id) > 0:
                    partner_ids.append(partner_id[0])
                elif isinstance(partner_id, int):
                    partner_ids.append(partner_id)
        return partner_ids
