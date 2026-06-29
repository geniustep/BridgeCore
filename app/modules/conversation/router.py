"""
Conversation Router - API endpoints for conversations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.modules.conversation.schemas import (
    ChannelListResponse,
    MessageListResponse,
    SendMessageRequest,
    SendMessageResponse,
    MailChannelData,
    MailMessageData,
)
from app.modules.conversation.service import ConversationService
from app.core.dependencies import get_current_tenant_user, get_cache_service, get_db, get_odoo_adapter
from app.models.tenant_user import TenantUser
from app.services.cache_service import CacheService
from app.services.tenant_service import TenantService
from app.utils.odoo_client import OdooClient
from app.adapters.odoo_adapter import OdooAdapter
from loguru import logger

router = APIRouter(prefix="/conversations", tags=["conversations"])


async def get_conversation_service(
    adapter: OdooAdapter = Depends(get_odoo_adapter),
    current_user: TenantUser = Depends(get_current_tenant_user),
    cache_service: CacheService = Depends(get_cache_service)
) -> ConversationService:
    """
    Get ConversationService with OdooClient initialized from tenant
    
    ⚠️ تصحيح أمني: user/partner يأتي من JWT فقط
    
    Uses same pattern as Moodle router - gets Odoo adapter via Depends
    """
    try:
        # adapter is already resolved by FastAPI's dependency injection
        
        # Get session_id from adapter (OdooAdapter stores it in session_id attribute)
        session_id = getattr(adapter, 'session_id', None)
        
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Odoo session not available. Please ensure Odoo is connected."
            )
        
        # Get base_url from adapter's url attribute
        if not adapter.url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Odoo URL not configured"
            )
        
        base_url = adapter.url.rstrip('/')
        if base_url.endswith('/odoo'):
            base_url = base_url[:-5].rstrip('/')
        
        # Create OdooClient with session
        odoo_client = OdooClient(
            base_url=base_url,
            session_id=session_id,
            timeout=30
        )
        
        return ConversationService(odoo_client, cache_service)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ConversationService: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize conversation service: {str(e)}"
        )


async def get_partner_id_from_user(
    current_user: TenantUser,
    odoo_client: OdooClient
) -> int:
    """
    Get partner_id from current user's Odoo user record
    
    ⚠️ مهم: partner_id يأتي من Odoo res.users.partner_id
    """
    if not current_user.odoo_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have Odoo user ID"
        )
    
    try:
        # Get user data from Odoo
        user_data = odoo_client.read(
            "res.users",
            [current_user.odoo_user_id],
            fields=["partner_id"]
        )
    except Exception as e:
        logger.error(f"Failed to read Odoo user {current_user.odoo_user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user data from Odoo: {str(e)}"
        )
    
    if not user_data or len(user_data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Odoo user not found"
        )
    
    partner_id_data = user_data[0].get("partner_id")
    if not partner_id_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Partner ID not found for user"
        )
    
    # partner_id is usually a tuple (id, name)
    if isinstance(partner_id_data, (list, tuple)) and len(partner_id_data) > 0:
        return partner_id_data[0]
    elif isinstance(partner_id_data, int):
        return partner_id_data
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Invalid partner_id format"
    )


@router.get("/channels", response_model=ChannelListResponse)
async def get_channels(
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: TenantUser = Depends(get_current_tenant_user),
):
    """
    Get all channels for current user
    
    ⚠️ تصحيح أمني مهم: user_id/partner_id يأتي من JWT فقط، ليس من query params
    """
    try:
        # Get partner_id from user's Odoo record
        odoo_client = conversation_service.odoo
        partner_id = await get_partner_id_from_user(current_user, odoo_client)
        
        channels = await conversation_service.get_user_channels(partner_id)
        
        # Transform to MailChannelData
        channel_data = []
        for ch in channels:
            # Extract partner_ids from channel_partner_ids
            partner_ids = ch.get("channel_partner_ids", [])
            if isinstance(partner_ids, list) and len(partner_ids) > 0 and isinstance(partner_ids[0], (list, tuple)):
                partner_ids = [p[0] if isinstance(p, (list, tuple)) else p for p in partner_ids]
            
            # Normalize channel_type (Odoo 18 may return 'group', map to 'channel')
            channel_type = ch.get("channel_type", "channel")
            if channel_type not in ("chat", "channel", "group"):
                channel_type = "channel"
            
            channel_data.append(MailChannelData(
                id=ch["id"],
                name=ch["name"],
                channel_type=channel_type,
                public=ch.get("public", "private"),
                description=ch.get("description") if ch.get("description") and isinstance(ch.get("description"), str) else None,
                members_partner_ids=partner_ids,
                channel_partner_ids=partner_ids,
            ))
        
        return ChannelListResponse(channels=channel_data, total=len(channel_data))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_channels endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/channels/{channel_id}/messages", response_model=MessageListResponse)
async def get_channel_messages(
    channel_id: int,
    limit: int = 50,
    offset: int = 0,
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Get messages in a channel"""
    messages = await conversation_service.get_channel_messages(channel_id, limit, offset)
    
    # Transform to MailMessageData
    message_data = []
    for msg in messages:
        # Handle date field - convert string to datetime if needed
        date_value = msg.get("date")
        if isinstance(date_value, str):
            try:
                date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except:
                try:
                    date_value = datetime.fromisoformat(date_value)
                except:
                    date_value = datetime.utcnow()  # Fallback
        
        message_data.append(MailMessageData(
            id=msg["id"],
            model="mail.channel",
            res_id=channel_id,
            message_type=msg.get("message_type", "comment"),
            body=msg.get("body"),
            subject=msg.get("subject"),
            author_id=msg.get("author_id"),
            author_name=msg.get("author_name"),
            partner_ids=msg.get("partner_ids", []),
            channel_ids=msg.get("channel_ids", []),
            date=date_value or datetime.utcnow(),
            parent_id=msg.get("parent_id"),
        ))
    
    return MessageListResponse(
        messages=message_data,
        total=len(message_data),
        limit=limit,
        offset=offset
    )


@router.get("/chatter/{model}/{record_id}", response_model=MessageListResponse)
async def get_record_chatter(
    model: str,
    record_id: int,
    limit: int = 50,
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """Get chatter messages for a record"""
    messages = await conversation_service.get_record_chatter(model, record_id, limit)
    
    # Transform to MailMessageData
    message_data = []
    for msg in messages:
        # Handle date field
        date_value = msg.get("date")
        if isinstance(date_value, str):
            try:
                date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except:
                try:
                    date_value = datetime.fromisoformat(date_value)
                except:
                    date_value = datetime.utcnow()
        
        message_data.append(MailMessageData(
            id=msg["id"],
            model=model,
            res_id=record_id,
            message_type=msg.get("message_type", "comment"),
            body=msg.get("body"),
            subject=msg.get("subject"),
            author_id=msg.get("author_id"),
            author_name=msg.get("author_name"),
            date=date_value or datetime.utcnow(),
            parent_id=msg.get("parent_id"),
        ))
    
    return MessageListResponse(
        messages=message_data,
        total=len(message_data),
        limit=limit,
        offset=0
    )


@router.post("/messages/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: TenantUser = Depends(get_current_tenant_user),
):
    """
    Send a new message
    
    ⚠️ تصحيح أمني مهم: author يأتي من JWT session، ليس من request
    """
    result = await conversation_service.send_message(
        model=request.model,
        res_id=request.res_id,
        body=request.body,
        partner_ids=request.partner_ids,
        subject=request.subject,
        parent_id=request.parent_id
    )
    return SendMessageResponse(**result)


@router.get("/direct-messages", response_model=ChannelListResponse)
async def get_direct_messages(
    conversation_service: ConversationService = Depends(get_conversation_service),
    current_user: TenantUser = Depends(get_current_tenant_user),
):
    """
    Get direct message channels for current user
    
    ⚠️ تصحيح أمني: partner_id يأتي من JWT/Odoo user
    """
    odoo_client = conversation_service.odoo
    partner_id = await get_partner_id_from_user(current_user, odoo_client)
    
    channels = await conversation_service.get_direct_messages(partner_id)
    
    # Transform to MailChannelData
    channel_data = []
    for ch in channels:
        partner_ids = ch.get("channel_partner_ids", [])
        if isinstance(partner_ids, list) and len(partner_ids) > 0 and isinstance(partner_ids[0], (list, tuple)):
            partner_ids = [p[0] if isinstance(p, (list, tuple)) else p for p in partner_ids]
        
        channel_data.append(MailChannelData(
            id=ch["id"],
            name=ch.get("name", ""),
            channel_type="chat",
            public="private",
            uuid=ch.get("uuid"),
            members_partner_ids=partner_ids,
            channel_partner_ids=partner_ids,
        ))
    
    return ChannelListResponse(channels=channel_data, total=len(channel_data))


@router.post("/channels/get-or-create-dm", response_model=dict)
async def get_or_create_dm_channel(
    partner_ids: List[int],
    conversation_service: ConversationService = Depends(get_conversation_service),
):
    """
    Get or create a direct message channel with specified partners
    
    ⚠️ مهم: يستخدم channel_get method من Odoo (نفس ما يستخدمه Discuss app)
    
    This endpoint is equivalent to Odoo's:
    - discuss.channel.channel_get(partners_to=[196], force_open=True)
    - أو mail.channel.channel_get(partners_to=[196], force_open=True)
    
    Args:
        partner_ids: List of partner IDs to include in DM channel
        
    Returns:
        Dict with channel information in Odoo's format:
        {
            "discuss.channel": [...],
            "discuss.channel.member": [...],
            "res.partner": [...]
        }
        
    Example Request:
        POST /api/v1/conversations/channels/get-or-create-dm
        {
            "partner_ids": [196]
        }
        
    Example Response:
        {
            "discuss.channel": [{"id": 5, "name": "...", ...}],
            "discuss.channel.member": [...],
            "res.partner": [...]
        }
    """
    channel_data = await conversation_service.get_or_create_dm_channel(partner_ids)
    return channel_data
