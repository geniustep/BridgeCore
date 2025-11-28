"""
Notification API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from app.db.session import get_db
from app.core.security import decode_tenant_token
from app.services.notification_service import NotificationService
from app.models.notification import NotificationType
from app.schemas.notification_schemas import (
    NotificationCreate,
    NotificationBulkCreate,
    NotificationMarkRead,
    NotificationPreferenceUpdate,
    DeviceTokenRegister,
    DeviceTokenUnregister,
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    DeviceTokenResponse,
    DeviceTokenListResponse,
    NotificationStatsResponse,
    BulkNotificationResult,
)
from loguru import logger

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])
security = HTTPBearer()


async def get_tenant_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Extract tenant and user info from JWT token"""
    token = credentials.credentials
    payload = decode_tenant_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return {
        "user_id": UUID(payload.get("sub")),
        "tenant_id": UUID(payload.get("tenant_id")),
        "email": payload.get("email"),
        "role": payload.get("role")
    }


# ============================================================================
# Notification CRUD
# ============================================================================

@router.get("/list", response_model=NotificationListResponse)
async def list_notifications(
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's notifications

    Returns paginated list of notifications with unread count.
    Notifications are sorted by read status, priority, and creation date.
    """
    service = NotificationService(db)
    notifications, total, unread_count = await service.list_notifications(
        user_id=auth["user_id"],
        tenant_id=auth["tenant_id"],
        is_read=is_read,
        notification_type=notification_type,
        skip=skip,
        limit=limit
    )

    return NotificationListResponse(
        notifications=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        unread_count=unread_count,
        skip=skip,
        limit=limit
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notification details
    """
    service = NotificationService(db)
    notification = await service.get_notification(notification_id, auth["user_id"])

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return NotificationResponse.model_validate(notification)


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a notification as read
    """
    service = NotificationService(db)
    count = await service.mark_as_read([notification_id], auth["user_id"])

    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or already read"
        )

    return {"success": True, "message": "Notification marked as read"}


@router.post("/mark-read")
async def mark_notifications_read(
    body: NotificationMarkRead,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark multiple notifications as read
    """
    service = NotificationService(db)
    count = await service.mark_as_read(body.notification_ids, auth["user_id"])

    return {
        "success": True,
        "marked_count": count,
        "message": f"Marked {count} notifications as read"
    }


@router.post("/read-all")
async def mark_all_notifications_read(
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark all notifications as read
    """
    service = NotificationService(db)
    count = await service.mark_all_as_read(auth["user_id"], auth["tenant_id"])

    return {
        "success": True,
        "marked_count": count,
        "message": f"Marked {count} notifications as read"
    }


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a notification
    """
    service = NotificationService(db)
    success = await service.delete_notification(notification_id, auth["user_id"])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return {"success": True, "message": "Notification deleted"}


# ============================================================================
# Notification Preferences
# ============================================================================

@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notification preferences

    Returns current notification preferences including:
    - Channel preferences (in-app, push, email, SMS)
    - Type preferences (info, success, warning, error, system)
    - Quiet hours settings
    - Email digest settings
    """
    service = NotificationService(db)
    preferences = await service.get_preferences(auth["user_id"], auth["tenant_id"])
    return NotificationPreferenceResponse.model_validate(preferences)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    body: NotificationPreferenceUpdate,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Update notification preferences

    Update any combination of preferences. Only provided fields will be updated.
    """
    service = NotificationService(db)
    preferences = await service.update_preferences(
        user_id=auth["user_id"],
        tenant_id=auth["tenant_id"],
        preference_data=body
    )
    return NotificationPreferenceResponse.model_validate(preferences)


# ============================================================================
# Device Registration (Push Notifications)
# ============================================================================

@router.post("/register-device", response_model=DeviceTokenResponse)
async def register_device(
    body: DeviceTokenRegister,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Register a device for push notifications

    Register the device's push notification token. If the device is already
    registered, the token will be updated.

    **Device Types:**
    - `ios`: Apple iOS device
    - `android`: Android device
    - `web`: Web browser (Web Push)

    **Token Types:**
    - `fcm`: Firebase Cloud Messaging
    - `apns`: Apple Push Notification Service
    - `web_push`: Web Push API
    """
    service = NotificationService(db)
    device = await service.register_device(
        user_id=auth["user_id"],
        tenant_id=auth["tenant_id"],
        device_data=body
    )
    return DeviceTokenResponse.model_validate(device)


@router.post("/unregister-device")
async def unregister_device(
    body: DeviceTokenUnregister,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Unregister a device from push notifications
    """
    service = NotificationService(db)
    success = await service.unregister_device(
        user_id=auth["user_id"],
        device_id=body.device_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    return {"success": True, "message": "Device unregistered successfully"}


@router.get("/devices", response_model=DeviceTokenListResponse)
async def list_devices(
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    List registered devices for push notifications
    """
    service = NotificationService(db)
    devices = await service.list_devices(auth["user_id"], auth["tenant_id"])

    return DeviceTokenListResponse(
        devices=[DeviceTokenResponse.model_validate(d) for d in devices],
        total=len(devices)
    )


# ============================================================================
# Statistics
# ============================================================================

@router.get("/stats", response_model=NotificationStatsResponse)
async def get_stats(
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notification statistics

    Returns statistics about user's notifications including:
    - Total and unread counts
    - Today's and this week's notification counts
    - Breakdown by type and priority
    """
    service = NotificationService(db)
    stats = await service.get_stats(auth["user_id"], auth["tenant_id"])
    return NotificationStatsResponse(**stats)


# ============================================================================
# Admin/System Endpoints (for creating notifications from triggers/system)
# ============================================================================

@router.post("/create", response_model=NotificationResponse)
async def create_notification(
    body: NotificationCreate,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a notification for a user

    **Note:** This endpoint is typically used by system/admin for creating
    notifications programmatically. Regular users receive notifications
    through triggers or system events.
    """
    # Check if user has admin role
    if auth["role"] not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create notifications for other users"
        )

    service = NotificationService(db)
    notification = await service.create_notification(auth["tenant_id"], body)
    return NotificationResponse.model_validate(notification)


@router.post("/bulk-create", response_model=BulkNotificationResult)
async def create_bulk_notifications(
    body: NotificationBulkCreate,
    auth: dict = Depends(get_tenant_from_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Create notifications for multiple users

    **Note:** Admin only endpoint.
    """
    if auth["role"] not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create bulk notifications"
        )

    service = NotificationService(db)
    notifications = await service.create_bulk_notifications(auth["tenant_id"], body)

    return BulkNotificationResult(
        success=True,
        created_count=len(notifications),
        failed_count=0,
        notification_ids=[n.id for n in notifications]
    )

