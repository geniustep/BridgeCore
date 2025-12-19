"""
Conversation Module - Odoo Conversations Support
"""
from .service import ConversationService
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
