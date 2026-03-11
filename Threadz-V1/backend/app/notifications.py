"""
Advanced Notification System for Threadz Application
"""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_, or_
from fastapi import HTTPException, status
from pydantic import BaseModel
from enum import Enum

from . import models, auth
from .database import get_db
from .email import email_service
from .sentry_config import sentry_manager

class NotificationType(str, Enum):
    """Notification types"""
    ORDER_CONFIRMATION = "order_confirmation"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    DESIGN_APPROVED = "design_approved"
    DESIGN_REJECTED = "design_rejected"
    AI_GENERATION_COMPLETE = "ai_generation_complete"
    AI_GENERATION_FAILED = "ai_generation_failed"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_CHANGE = "password_change"
    NEW_FEATURE = "new_feature"
    PROMOTION = "promotion"
    SYSTEM_MAINTENANCE = "system_maintenance"

class NotificationChannel(str, Enum):
    """Notification channels"""
    EMAIL = "email"
    IN_APP = "in_app"
    PUSH = "push"
    SMS = "sms"

class NotificationPriority(str, Enum):
    """Notification priorities"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# Pydantic models
class NotificationCreate(BaseModel):
    title: str
    message: str
    notification_type: NotificationType
    channels: List[NotificationChannel] = [NotificationChannel.IN_APP]
    priority: NotificationPriority = NotificationPriority.MEDIUM
    data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None

class NotificationResponse(BaseModel):
    notification_id: str
    title: str
    message: str
    notification_type: NotificationType
    channels: List[NotificationChannel]
    priority: NotificationPriority
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]

class NotificationService:
    """Advanced notification service with multiple channels and scheduling"""
    
    def __init__(self):
        self.email_service = email_service
        self.channel_handlers = {
            NotificationChannel.EMAIL: self._send_email_notification,
            NotificationChannel.IN_APP: self._send_in_app_notification,
            NotificationChannel.PUSH: self._send_push_notification,
            NotificationChannel.SMS: self._send_sms_notification
        }
        
        # Notification templates
        self.templates = {
            NotificationType.ORDER_CONFIRMATION: {
                "title": "Order Confirmed!",
                "message": "Your order #{order_id} has been confirmed and is being processed.",
                "email_template": "order_confirmation"
            },
            NotificationType.ORDER_SHIPPED: {
                "title": "Order Shipped!",
                "message": "Your order #{order_id} has been shipped and will arrive soon.",
                "email_template": "order_shipped"
            },
            NotificationType.PAYMENT_SUCCESS: {
                "title": "Payment Successful",
                "message": "Your payment of ₹{amount} for order #{order_id} was successful.",
                "email_template": "payment_confirmation"
            },
            NotificationType.AI_GENERATION_COMPLETE: {
                "title": "Design Generated!",
                "message": "Your AI-generated design '{design_name}' is ready to view.",
                "email_template": "ai_generation_complete"
            },
            NotificationType.EMAIL_VERIFICATION: {
                "title": "Verify Your Email",
                "message": "Please verify your email address to activate your account.",
                "email_template": "email_verification"
            }
        }
    
    async def create_notification(
        self,
        user_id: str,
        notification_data: NotificationCreate,
        db: AsyncSession
    ) -> models.Notification:
        """Create a new notification"""
        try:
            # Create notification record
            notification = models.Notification(
                notification_id=str(uuid.uuid4()),
                user_id=user_id,
                title=notification_data.title,
                message=notification_data.message,
                notification_type=notification_data.notification_type,
                channels=notification_data.channels,
                priority=notification_data.priority,
                data=notification_data.data or {},
                is_read=False,
                scheduled_at=notification_data.scheduled_at,
                created_at=datetime.utcnow()
            )
            
            db.add(notification)
            await db.commit()
            await db.refresh(notification)
            
            # Send notification immediately if not scheduled
            if not notification_data.scheduled_at:
                await self._send_notification(notification, db)
            
            return notification
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "create_notification",
                "user_id": user_id,
                "notification_type": notification_data.notification_type
            })
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create notification"
            )
    
    async def create_system_notification(
        self,
        notification_type: NotificationType,
        data: Dict[str, Any],
        target_users: Optional[List[str]] = None,
        channels: List[NotificationChannel] = [NotificationChannel.IN_APP]
    ) -> int:
        """Create system-wide notifications"""
        try:
            # Get template
            template = self.templates.get(notification_type)
            if not template:
                return 0
            
            # Format message with data
            title = template["title"].format(**data)
            message = template["message"].format(**data)
            
            # Create notifications for target users
            notifications_created = 0
            
            async with get_db() as db:
                if target_users:
                    # Send to specific users
                    for user_id in target_users:
                        notification_data = NotificationCreate(
                            title=title,
                            message=message,
                            notification_type=notification_type,
                            channels=channels,
                            priority=NotificationPriority.HIGH,
                            data=data
                        )
                        
                        await self.create_notification(user_id, notification_data, db)
                        notifications_created += 1
                else:
                    # Send to all users (system-wide)
                    result = await db.execute(select(models.User.user_id))
                    all_users = result.scalars().all()
                    
                    for user in all_users:
                        notification_data = NotificationCreate(
                            title=title,
                            message=message,
                            notification_type=notification_type,
                            channels=channels,
                            priority=NotificationPriority.HIGH,
                            data=data
                        )
                        
                        await self.create_notification(user.user_id, notification_data, db)
                        notifications_created += 1
            
            return notifications_created
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "create_system_notification",
                "notification_type": notification_type
            })
            return 0
    
    async def get_user_notifications(
        self,
        user_id: str,
        db: AsyncSession,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[models.Notification]:
        """Get notifications for a user"""
        try:
            query = select(models.Notification).where(models.Notification.user_id == user_id)
            
            if unread_only:
                query = query.where(models.Notification.is_read == False)
            
            query = query.order_by(desc(models.Notification.created_at)).offset(offset).limit(limit)
            
            result = await db.execute(query)
            notifications = result.scalars().all()
            
            return notifications
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "get_user_notifications",
                "user_id": user_id
            })
            return []
    
    async def mark_notification_read(
        self,
        notification_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """Mark a notification as read"""
        try:
            result = await db.execute(
                select(models.Notification).where(
                    models.Notification.notification_id == notification_id,
                    models.Notification.user_id == user_id
                )
            )
            notification = result.scalars().first()
            
            if not notification:
                return False
            
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await db.commit()
            
            return True
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "mark_notification_read",
                "notification_id": notification_id,
                "user_id": user_id
            })
            return False
    
    async def mark_all_notifications_read(
        self,
        user_id: str,
        db: AsyncSession
    ) -> int:
        """Mark all notifications as read for a user"""
        try:
            result = await db.execute(
                select(models.Notification).where(
                    models.Notification.user_id == user_id,
                    models.Notification.is_read == False
                )
            )
            unread_notifications = result.scalars().all()
            
            for notification in unread_notifications:
                notification.is_read = True
                notification.read_at = datetime.utcnow()
            
            await db.commit()
            
            return len(unread_notifications)
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "mark_all_notifications_read",
                "user_id": user_id
            })
            return 0
    
    async def delete_notification(
        self,
        notification_id: str,
        user_id: str,
        db: AsyncSession
    ) -> bool:
        """Delete a notification"""
        try:
            result = await db.execute(
                select(models.Notification).where(
                    models.Notification.notification_id == notification_id,
                    models.Notification.user_id == user_id
                )
            )
            notification = result.scalars().first()
            
            if not notification:
                return False
            
            await db.delete(notification)
            await db.commit()
            
            return True
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "delete_notification",
                "notification_id": notification_id,
                "user_id": user_id
            })
            return False
    
    async def get_notification_stats(
        self,
        user_id: str,
        db: AsyncSession
    ) -> Dict[str, int]:
        """Get notification statistics for a user"""
        try:
            # Total notifications
            total_result = await db.execute(
                select(func.count(models.Notification.notification_id)).where(
                    models.Notification.user_id == user_id
                )
            )
            total = total_result.scalar() or 0
            
            # Unread notifications
            unread_result = await db.execute(
                select(func.count(models.Notification.notification_id)).where(
                    models.Notification.user_id == user_id,
                    models.Notification.is_read == False
                )
            )
            unread = unread_result.scalar() or 0
            
            # Notifications by type
            type_stats = {}
            for notification_type in NotificationType:
                type_result = await db.execute(
                    select(func.count(models.Notification.notification_id)).where(
                        models.Notification.user_id == user_id,
                        models.Notification.notification_type == notification_type
                    )
                )
                type_stats[notification_type.value] = type_result.scalar() or 0
            
            return {
                "total": total,
                "unread": unread,
                "read": total - unread,
                "by_type": type_stats
            }
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "get_notification_stats",
                "user_id": user_id
            })
            return {"total": 0, "unread": 0, "read": 0, "by_type": {}}
    
    async def _send_notification(
        self,
        notification: models.Notification,
        db: AsyncSession
    ) -> bool:
        """Send notification through specified channels"""
        try:
            success = True
            
            for channel in notification.channels:
                handler = self.channel_handlers.get(channel)
                if handler:
                    try:
                        await handler(notification, db)
                    except Exception as e:
                        sentry_manager.capture_exception(e, {
                            "action": "send_notification_channel",
                            "channel": channel,
                            "notification_id": notification.notification_id
                        })
                        success = False
            
            return success
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "send_notification",
                "notification_id": notification.notification_id
            })
            return False
    
    async def _send_email_notification(
        self,
        notification: models.Notification,
        db: AsyncSession
    ):
        """Send email notification"""
        try:
            # Get user email
            result = await db.execute(
                select(models.User.email).where(models.User.user_id == notification.user_id)
            )
            user_email = result.scalar()
            
            if not user_email:
                return
            
            # Send email based on notification type
            if notification.notification_type == NotificationType.ORDER_CONFIRMATION:
                await self.email_service.send_order_confirmation_email(
                    user_email, notification.data or {}
                )
            elif notification.notification_type == NotificationType.PAYMENT_SUCCESS:
                await self.email_service.send_payment_confirmation_email(
                    user_email, notification.data or {}
                )
            elif notification.notification_type == NotificationType.EMAIL_VERIFICATION:
                await self.email_service.send_verification_email(
                    user_email, notification.user_id
                )
            else:
                # Generic email (would need email template)
                pass
                
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "send_email_notification",
                "notification_id": notification.notification_id
            })
            raise
    
    async def _send_in_app_notification(
        self,
        notification: models.Notification,
        db: AsyncSession
    ):
        """Send in-app notification (already stored in database)"""
        # In-app notifications are stored in the database
        # This would trigger real-time updates via WebSocket in production
        pass
    
    async def _send_push_notification(
        self,
        notification: models.Notification,
        db: AsyncSession
    ):
        """Send push notification (would integrate with push service)"""
        # Placeholder for push notification service integration
        # Would use services like Firebase Cloud Messaging, OneSignal, etc.
        pass
    
    async def _send_sms_notification(
        self,
        notification: models.Notification,
        db: AsyncSession
    ):
        """Send SMS notification (would integrate with SMS service)"""
        # Placeholder for SMS service integration
        # Would use services like Twilio, AWS SNS, etc.
        pass
    
    async def process_scheduled_notifications(self, db: AsyncSession):
        """Process scheduled notifications"""
        try:
            # Get notifications scheduled for now or earlier
            result = await db.execute(
                select(models.Notification).where(
                    models.Notification.scheduled_at <= datetime.utcnow(),
                    models.Notification.scheduled_at.isnot(None)
                )
            )
            scheduled_notifications = result.scalars().all()
            
            for notification in scheduled_notifications:
                await self._send_notification(notification, db)
                
                # Clear scheduled_at to mark as processed
                notification.scheduled_at = None
                await db.commit()
            
        except Exception as e:
            sentry_manager.capture_exception(e, {
                "action": "process_scheduled_notifications"
            })

# Global notification service instance
notification_service = NotificationService()
