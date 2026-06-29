"""
Conversation Module - Odoo Conversations Support
"""
from .service import ConversationService
from .router import router
from .schemas import (
    MailMessageData,
    MailChannelData,
    MailFollowerData,
    ConversationEventData,
    SendMessageRequest,
    ChannelListResponse,
    MessageListResponse,
    SendMessageResponse,
)

__all__ = [
    "router",
    "ConversationService",
    "MailMessageData",
    "MailChannelData",
    "MailFollowerData",
    "ConversationEventData",
    "SendMessageRequest",
    "ChannelListResponse",
    "MessageListResponse",
    "SendMessageResponse",
]
