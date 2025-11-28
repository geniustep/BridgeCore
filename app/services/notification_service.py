"""
Notification service for managing user notifications
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, update
from loguru import logger

from app.models.notification import (
    Notification, NotificationPreference, DeviceToken,
    NotificationType, NotificationPriority, NotificationChannel
)
from app.schemas.notification_schemas import (
    NotificationCreate, NotificationBulkCreate,
    NotificationPreferenceUpdate, DeviceTokenRegister
)


class NotificationService:
    """Service for managing notifications"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # Notification CRUD
    # ========================================================================

    async def create_notification(
        self,
        tenant_id: UUID,
        notification_data: NotificationCreate
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            tenant_id=tenant_id,
            user_id=notification_data.user_id,
            title=notification_data.title,
            message=notification_data.message,
            type=notification_data.type,
            priority=notification_data.priority,
            channels=[ch.value for ch in notification_data.channels],
            action_type=notification_data.action_type,
            action_data=notification_data.action_data,
            related_model=notification_data.related_model,
            related_id=notification_data.related_id,
            metadata=notification_data.metadata,
            expires_at=notification_data.expires_at,
            source="api"
        )

        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)

        # Send push notification if enabled
        if NotificationChannel.PUSH in notification_data.channels:
            await self._send_push_notification(notification)

        logger.info(f"Created notification for user {notification_data.user_id}")
        return notification

    async def create_bulk_notifications(
        self,
        tenant_id: UUID,
        bulk_data: NotificationBulkCreate
    ) -> List[Notification]:
        """Create notifications for multiple users"""
        notifications = []

        for user_id in bulk_data.user_ids:
            notification = Notification(
                tenant_id=tenant_id,
                user_id=user_id,
                title=bulk_data.title,
                message=bulk_data.message,
                type=bulk_data.type,
                priority=bulk_data.priority,
                channels=[ch.value for ch in bulk_data.channels],
                action_type=bulk_data.action_type,
                action_data=bulk_data.action_data,
                expires_at=bulk_data.expires_at,
                source="bulk_api"
            )
            self.db.add(notification)
            notifications.append(notification)

        await self.db.commit()

        # Refresh all notifications
        for notification in notifications:
            await self.db.refresh(notification)

        logger.info(f"Created {len(notifications)} bulk notifications")
        return notifications

    async def get_notification(
        self,
        notification_id: UUID,
        user_id: UUID
    ) -> Optional[Notification]:
        """Get a notification by ID"""
        query = select(Notification).where(
            and_(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_notifications(
        self,
        user_id: UUID,
        tenant_id: UUID,
        is_read: Optional[bool] = None,
        notification_type: Optional[NotificationType] = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Notification], int, int]:
        """List notifications for a user"""
        base_query = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.tenant_id == tenant_id,
                or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at > datetime.utcnow()
                )
            )
        )

        if is_read is not None:
            base_query = base_query.where(Notification.is_read == is_read)
        if notification_type:
            base_query = base_query.where(Notification.type == notification_type)

        # Count total
        count_query = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == user_id,
                Notification.tenant_id == tenant_id
            )
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Count unread
        unread_query = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == user_id,
                Notification.tenant_id == tenant_id,
                Notification.is_read == False
            )
        )
        unread_result = await self.db.execute(unread_query)
        unread_count = unread_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(
            Notification.is_read,
            Notification.priority.desc(),
            Notification.created_at.desc()
        )
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        notifications = list(result.scalars().all())

        return notifications, total, unread_count

    async def mark_as_read(
        self,
        notification_ids: List[UUID],
        user_id: UUID
    ) -> int:
        """Mark notifications as read"""
        stmt = update(Notification).where(
            and_(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        ).values(
            is_read=True,
            read_at=datetime.utcnow()
        )

        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount

    async def mark_all_as_read(self, user_id: UUID, tenant_id: UUID) -> int:
        """Mark all notifications as read for a user"""
        stmt = update(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.tenant_id == tenant_id,
                Notification.is_read == False
            )
        ).values(
            is_read=True,
            read_at=datetime.utcnow()
        )

        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount

    async def delete_notification(
        self,
        notification_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a notification"""
        notification = await self.get_notification(notification_id, user_id)
        if not notification:
            return False

        await self.db.delete(notification)
        await self.db.commit()

        return True

    async def delete_old_notifications(
        self,
        tenant_id: UUID,
        days: int = 30
    ) -> int:
        """Delete notifications older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get notifications to delete
        query = select(Notification).where(
            and_(
                Notification.tenant_id == tenant_id,
                Notification.created_at < cutoff_date,
                Notification.is_read == True
            )
        )
        result = await self.db.execute(query)
        notifications = list(result.scalars().all())

        for notification in notifications:
            await self.db.delete(notification)

        await self.db.commit()

        logger.info(f"Deleted {len(notifications)} old notifications for tenant {tenant_id}")
        return len(notifications)

    # ========================================================================
    # Notification Preferences
    # ========================================================================

    async def get_preferences(
        self,
        user_id: UUID,
        tenant_id: UUID
    ) -> NotificationPreference:
        """Get or create notification preferences for a user"""
        query = select(NotificationPreference).where(
            and_(
                NotificationPreference.user_id == user_id,
                NotificationPreference.tenant_id == tenant_id
            )
        )
        result = await self.db.execute(query)
        preferences = result.scalar_one_or_none()

        if not preferences:
            # Create default preferences
            preferences = NotificationPreference(
                user_id=user_id,
                tenant_id=tenant_id
            )
            self.db.add(preferences)
            await self.db.commit()
            await self.db.refresh(preferences)

        return preferences

    async def update_preferences(
        self,
        user_id: UUID,
        tenant_id: UUID,
        preference_data: NotificationPreferenceUpdate
    ) -> NotificationPreference:
        """Update notification preferences"""
        preferences = await self.get_preferences(user_id, tenant_id)

        update_data = preference_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(preferences, field, value)

        await self.db.commit()
        await self.db.refresh(preferences)

        return preferences

    # ========================================================================
    # Device Tokens
    # ========================================================================

    async def register_device(
        self,
        user_id: UUID,
        tenant_id: UUID,
        device_data: DeviceTokenRegister
    ) -> DeviceToken:
        """Register a device for push notifications"""
        # Check if device already registered
        query = select(DeviceToken).where(
            and_(
                DeviceToken.user_id == user_id,
                DeviceToken.device_id == device_data.device_id
            )
        )
        result = await self.db.execute(query)
        existing_device = result.scalar_one_or_none()

        if existing_device:
            # Update existing device
            existing_device.token = device_data.token
            existing_device.device_name = device_data.device_name
            existing_device.app_version = device_data.app_version
            existing_device.os_version = device_data.os_version
            existing_device.is_active = True
            existing_device.last_used_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(existing_device)
            return existing_device

        # Create new device
        device = DeviceToken(
            user_id=user_id,
            tenant_id=tenant_id,
            device_id=device_data.device_id,
            device_name=device_data.device_name,
            device_type=device_data.device_type,
            token=device_data.token,
            token_type=device_data.token_type,
            app_version=device_data.app_version,
            os_version=device_data.os_version,
            is_active=True
        )

        self.db.add(device)
        await self.db.commit()
        await self.db.refresh(device)

        logger.info(f"Registered device {device_data.device_id} for user {user_id}")
        return device

    async def unregister_device(
        self,
        user_id: UUID,
        device_id: str
    ) -> bool:
        """Unregister a device"""
        query = select(DeviceToken).where(
            and_(
                DeviceToken.user_id == user_id,
                DeviceToken.device_id == device_id
            )
        )
        result = await self.db.execute(query)
        device = result.scalar_one_or_none()

        if not device:
            return False

        device.is_active = False
        await self.db.commit()

        logger.info(f"Unregistered device {device_id} for user {user_id}")
        return True

    async def list_devices(
        self,
        user_id: UUID,
        tenant_id: UUID
    ) -> List[DeviceToken]:
        """List registered devices for a user"""
        query = select(DeviceToken).where(
            and_(
                DeviceToken.user_id == user_id,
                DeviceToken.tenant_id == tenant_id,
                DeviceToken.is_active == True
            )
        ).order_by(DeviceToken.last_used_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ========================================================================
    # Statistics
    # ========================================================================

    async def get_stats(
        self,
        user_id: UUID,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Get notification statistics for a user"""
        # Total and unread counts
        total_query = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == user_id,
                Notification.tenant_id == tenant_id
            )
        )
        unread_query = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == user_id,
                Notification.tenant_id == tenant_id,
                Notification.is_read == False
            )
        )

        # Today's and this week's counts
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=7)

        today_query = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == user_id,
                Notification.tenant_id == tenant_id,
                Notification.created_at >= today
            )
        )
        week_query = select(func.count(Notification.id)).where(
            and_(
                Notification.user_id == user_id,
                Notification.tenant_id == tenant_id,
                Notification.created_at >= week_ago
            )
        )

        total_result = await self.db.execute(total_query)
        unread_result = await self.db.execute(unread_query)
        today_result = await self.db.execute(today_query)
        week_result = await self.db.execute(week_query)

        # Count by type
        type_counts = {}
        for ntype in NotificationType:
            type_query = select(func.count(Notification.id)).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.tenant_id == tenant_id,
                    Notification.type == ntype
                )
            )
            type_result = await self.db.execute(type_query)
            type_counts[ntype.value] = type_result.scalar() or 0

        # Count by priority
        priority_counts = {}
        for priority in NotificationPriority:
            priority_query = select(func.count(Notification.id)).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.tenant_id == tenant_id,
                    Notification.priority == priority
                )
            )
            priority_result = await self.db.execute(priority_query)
            priority_counts[priority.value] = priority_result.scalar() or 0

        total = total_result.scalar() or 0
        unread = unread_result.scalar() or 0

        return {
            "total_notifications": total,
            "unread_count": unread,
            "read_count": total - unread,
            "notifications_today": today_result.scalar() or 0,
            "notifications_this_week": week_result.scalar() or 0,
            "by_type": type_counts,
            "by_priority": priority_counts
        }

    # ========================================================================
    # Push Notifications
    # ========================================================================

    async def _send_push_notification(self, notification: Notification):
        """Send push notification to user's devices"""
        # Get user's active devices
        devices = await self.list_devices(notification.user_id, notification.tenant_id)

        if not devices:
            return

        # Check user preferences
        preferences = await self.get_preferences(notification.user_id, notification.tenant_id)
        if not preferences.enable_push:
            return

        # Check quiet hours
        if preferences.quiet_hours_enabled:
            if self._is_quiet_hours(preferences):
                return

        # TODO: Implement actual push notification sending
        # This would integrate with FCM, APNS, etc.
        for device in devices:
            await self._send_to_device(device, notification)

    async def _send_to_device(self, device: DeviceToken, notification: Notification):
        """Send push notification to a specific device"""
        # TODO: Implement actual push notification sending
        # Example with FCM:
        # 
        # import firebase_admin
        # from firebase_admin import messaging
        # 
        # message = messaging.Message(
        #     notification=messaging.Notification(
        #         title=notification.title,
        #         body=notification.message,
        #     ),
        #     token=device.token,
        #     data={
        #         "notification_id": str(notification.id),
        #         "action_type": notification.action_type or "",
        #     }
        # )
        # response = messaging.send(message)

        logger.debug(f"Would send push to device {device.device_id}: {notification.title}")

    def _is_quiet_hours(self, preferences: NotificationPreference) -> bool:
        """Check if current time is within quiet hours"""
        if not preferences.quiet_hours_start or not preferences.quiet_hours_end:
            return False

        from datetime import time
        import pytz

        tz = pytz.timezone(preferences.quiet_hours_timezone)
        now = datetime.now(tz).time()

        start_parts = preferences.quiet_hours_start.split(":")
        end_parts = preferences.quiet_hours_end.split(":")

        start_time = time(int(start_parts[0]), int(start_parts[1]))
        end_time = time(int(end_parts[0]), int(end_parts[1]))

        if start_time <= end_time:
            return start_time <= now <= end_time
        else:
            # Quiet hours span midnight
            return now >= start_time or now <= end_time

