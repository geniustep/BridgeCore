"""
Pydantic schemas for conversation module
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime


# ===== Conversation Data Schemas =====

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
    
    @validator('date', pre=True)
    def parse_date(cls, v):
        """Parse date from string if needed"""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except:
                try:
                    return datetime.fromisoformat(v)
                except:
                    # Fallback to current time if parsing fails
                    return datetime.utcnow()
        return v
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
    channel_type: Literal["chat", "channel", "group"] = Field(..., description="Channel type")
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
    
    class Config:
        from_attributes = True


# ===== Request/Response Schemas =====

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


# ===== Extended Event Data =====

class ConversationEventData(BaseModel):
    """Extended event data for conversations"""
    message_data: Optional[MailMessageData] = None
    channel_data: Optional[MailChannelData] = None
    follower_data: Optional[MailFollowerData] = None
    conversation_type: Optional[Literal["channel", "dm", "chatter"]] = Field(
        None, description="Conversation type classification"
    )
