from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from uuid import UUID
import uuid
import os
import json
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import firebase_admin
from firebase_admin import credentials, messaging

from database.config import get_sync_db, get_redis
from database.models import NotificationPreference, User, AuditLog
from auth.auth import current_active_user

router = APIRouter()

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    try:
        firebase_config = {
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token")
        }
        
        if all(firebase_config.values()):
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase initialization failed: {e}")

# Pydantic models
class NotificationPreferenceUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    exercise_reminders: Optional[bool] = None
    medicine_reminders: Optional[bool] = None
    health_tips: Optional[bool] = None
    weekly_reports: Optional[bool] = None
    fcm_token: Optional[str] = Field(None, max_length=500)

class NotificationPreferenceResponse(BaseModel):
    id: UUID
    email_notifications: bool
    push_notifications: bool
    exercise_reminders: bool
    medicine_reminders: bool
    health_tips: bool
    weekly_reports: bool
    fcm_token: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class NotificationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1, max_length=1000)
    notification_type: str = Field(..., pattern="^(exercise_reminder|medicine_reminder|health_tip|weekly_report|general)$")
    scheduled_for: Optional[datetime] = None
    data: Optional[dict] = None

class NotificationResponse(BaseModel):
    id: str
    title: str
    body: str
    notification_type: str
    sent: bool
    scheduled_for: Optional[datetime]
    sent_at: Optional[datetime]
    data: Optional[dict]

# Helper functions
async def send_email_notification(to_email: str, subject: str, content: str):
    """Send email notification using SendGrid."""
    try:
        sg = SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
        message = Mail(
            from_email=os.getenv("SENDGRID_FROM_EMAIL", "noreply@lp-assistant.app"),
            to_emails=to_email,
            subject=subject,
            html_content=content
        )
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

async def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None):
    """Send push notification using Firebase Cloud Messaging."""
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=data or {},
            token=fcm_token
        )
        response = messaging.send(message)
        return True
    except Exception as e:
        print(f"Push notification failed: {e}")
        return False

async def log_notification(db: Session, user_id: UUID, notification_data: dict):
    """Log notification to audit trail."""
    audit_log = AuditLog(
        id=uuid.uuid4(),
        user_id=user_id,
        action="notification_sent",
        resource_type="notification",
        details=notification_data,
        timestamp=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()

@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get user's notification preferences."""
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    if not preferences:
        # Create default preferences
        preferences = NotificationPreference(
            id=uuid.uuid4(),
            user_id=current_user.id
        )
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return preferences

@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    preferences_update: NotificationPreferenceUpdate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Update user's notification preferences."""
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    if not preferences:
        preferences = NotificationPreference(
            id=uuid.uuid4(),
            user_id=current_user.id
        )
        db.add(preferences)
    
    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)
    
    preferences.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(preferences)
    
    return preferences

@router.post("/send")
async def send_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db),
    redis_client = Depends(get_redis)
):
    """Send a notification to the current user."""
    # Get user preferences
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preferences not found"
        )
    
    notification_id = str(uuid.uuid4())
    notification_data = {
        "id": notification_id,
        "user_id": str(current_user.id),
        "title": notification.title,
        "body": notification.body,
        "notification_type": notification.notification_type,
        "scheduled_for": notification.scheduled_for.isoformat() if notification.scheduled_for else None,
        "data": notification.data,
        "sent": False,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Store notification in Redis
    await redis_client.setex(
        f"notification:{notification_id}",
        86400,  # 24 hours TTL
        json.dumps(notification_data)
    )
    
    # Check if notification should be sent immediately or scheduled
    if notification.scheduled_for and notification.scheduled_for > datetime.utcnow():
        # Schedule for later (in a real implementation, you'd use a task queue like Celery)
        return {"message": "Notification scheduled", "notification_id": notification_id}
    
    # Send immediately
    sent_email = False
    sent_push = False
    
    # Send email if enabled
    if preferences.email_notifications:
        background_tasks.add_task(
            send_email_notification,
            current_user.email,
            notification.title,
            f"<h2>{notification.title}</h2><p>{notification.body}</p>"
        )
        sent_email = True
    
    # Send push notification if enabled and FCM token available
    if preferences.push_notifications and preferences.fcm_token:
        background_tasks.add_task(
            send_push_notification,
            preferences.fcm_token,
            notification.title,
            notification.body,
            notification.data
        )
        sent_push = True
    
    # Update notification status
    notification_data["sent"] = sent_email or sent_push
    notification_data["sent_at"] = datetime.utcnow().isoformat()
    
    await redis_client.setex(
        f"notification:{notification_id}",
        86400,
        json.dumps(notification_data)
    )
    
    # Log notification
    background_tasks.add_task(
        log_notification,
        db,
        current_user.id,
        notification_data
    )
    
    return {
        "message": "Notification sent",
        "notification_id": notification_id,
        "sent_email": sent_email,
        "sent_push": sent_push
    }

@router.get("/history", response_model=List[NotificationResponse])
async def get_notification_history(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(current_active_user),
    redis_client = Depends(get_redis)
):
    """Get notification history for the current user."""
    # Get all notification keys for the user
    pattern = f"notification:*"
    keys = await redis_client.keys(pattern)
    
    notifications = []
    for key in keys:
        data = await redis_client.get(key)
        if data:
            notification_data = json.loads(data)
            if notification_data.get("user_id") == str(current_user.id):
                notifications.append(NotificationResponse(
                    id=notification_data["id"],
                    title=notification_data["title"],
                    body=notification_data["body"],
                    notification_type=notification_data["notification_type"],
                    sent=notification_data["sent"],
                    scheduled_for=datetime.fromisoformat(notification_data["scheduled_for"]) if notification_data.get("scheduled_for") else None,
                    sent_at=datetime.fromisoformat(notification_data["sent_at"]) if notification_data.get("sent_at") else None,
                    data=notification_data.get("data")
                ))
    
    # Sort by creation time (newest first)
    notifications.sort(key=lambda x: x.sent_at or datetime.min, reverse=True)
    
    return notifications[skip:skip + limit]

@router.post("/test")
async def test_notification(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Send a test notification to verify setup."""
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preferences not found"
        )
    
    test_results = {
        "email": False,
        "push": False
    }
    
    # Test email
    if preferences.email_notifications:
        test_results["email"] = await send_email_notification(
            current_user.email,
            "LP Assistant Test Notification",
            "<h2>Test Successful!</h2><p>Your email notifications are working correctly.</p>"
        )
    
    # Test push notification
    if preferences.push_notifications and preferences.fcm_token:
        test_results["push"] = await send_push_notification(
            preferences.fcm_token,
            "LP Assistant Test Notification",
            "Your push notifications are working correctly!",
            {"test": "true"}
        )
    
    return {
        "message": "Test notifications sent",
        "results": test_results
    }

@router.delete("/clear-history")
async def clear_notification_history(
    current_user: User = Depends(current_active_user),
    redis_client = Depends(get_redis)
):
    """Clear notification history for the current user."""
    pattern = f"notification:*"
    keys = await redis_client.keys(pattern)
    
    deleted_count = 0
    for key in keys:
        data = await redis_client.get(key)
        if data:
            notification_data = json.loads(data)
            if notification_data.get("user_id") == str(current_user.id):
                await redis_client.delete(key)
                deleted_count += 1
    
    return {
        "message": f"Cleared {deleted_count} notifications from history"
    }
