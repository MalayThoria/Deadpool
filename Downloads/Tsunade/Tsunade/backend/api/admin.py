from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from typing import List, Optional, Dict, Any, Union
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from enum import Enum
import json
import asyncio
from collections import defaultdict

from database.config import get_sync_db, get_redis, get_mongodb
from database.models import (
    User, UserProfile, ExerciseLog, MedicineHistory, 
    DiseaseHistory, CalendarEvent, AuditLog
)
from auth.auth import current_active_user, current_superuser

router = APIRouter()

# Enums
class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class SystemMetric(str, Enum):
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    ACTIVE_USERS = "active_users"
    API_REQUESTS = "api_requests"
    ERROR_RATE = "error_rate"

# Pydantic models
class UserSummary(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime]
    profile_completed: bool
    total_exercises: int
    total_medications: int
    
    class Config:
        from_attributes = True

class UserDetails(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    profile: Optional[Dict[str, Any]]
    exercise_stats: Dict[str, Any]
    health_summary: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class SystemStats(BaseModel):
    total_users: int
    active_users_today: int
    new_users_this_week: int
    total_exercises_logged: int
    total_medications_tracked: int
    total_calendar_events: int
    system_uptime: str
    database_size: str
    api_requests_today: int
    error_rate_today: float

class UserAnalytics(BaseModel):
    registration_trend: List[Dict[str, Any]]
    user_activity_distribution: Dict[str, int]
    feature_usage_stats: Dict[str, int]
    retention_metrics: Dict[str, float]
    geographic_distribution: Dict[str, int]
    device_distribution: Dict[str, int]

class SystemHealth(BaseModel):
    status: str  # healthy, warning, critical
    database_status: str
    redis_status: str
    mongodb_status: str
    api_response_time: float
    memory_usage_percent: float
    disk_usage_percent: float
    active_connections: int
    last_backup: Optional[datetime]
    alerts: List[Dict[str, Any]]

class AuditLogEntry(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True

class UserAction(BaseModel):
    action: str  # suspend, activate, verify, make_admin, remove_admin
    reason: Optional[str] = None
    notify_user: bool = True

class SystemAlert(BaseModel):
    id: str
    level: str  # info, warning, error, critical
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    affected_users: Optional[int] = None

class BackupStatus(BaseModel):
    last_backup: Optional[datetime]
    backup_size: Optional[str]
    backup_location: Optional[str]
    next_scheduled: Optional[datetime]
    status: str  # success, failed, in_progress
    retention_days: int

# Helper functions
async def get_system_metrics(db: Session, redis_client, mongodb) -> Dict[str, Any]:
    """Collect various system metrics."""
    metrics = {}
    
    # Database metrics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    today = date.today()
    week_ago = today - timedelta(days=7)
    new_users_week = db.query(User).filter(
        User.created_at >= datetime.combine(week_ago, datetime.min.time())
    ).count()
    
    total_exercises = db.query(ExerciseLog).count()
    total_medications = db.query(MedicineHistory).count()
    total_events = db.query(CalendarEvent).count()
    
    # API metrics from Redis (if available)
    try:
        api_requests_today = await redis_client.get(f"api_requests:{today.isoformat()}")
        api_requests_today = int(api_requests_today) if api_requests_today else 0
        
        error_count = await redis_client.get(f"api_errors:{today.isoformat()}")
        error_count = int(error_count) if error_count else 0
        error_rate = (error_count / api_requests_today * 100) if api_requests_today > 0 else 0
    except:
        api_requests_today = 0
        error_rate = 0.0
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "new_users_week": new_users_week,
        "total_exercises": total_exercises,
        "total_medications": total_medications,
        "total_events": total_events,
        "api_requests_today": api_requests_today,
        "error_rate_today": round(error_rate, 2)
    }

async def check_system_health(db: Session, redis_client, mongodb) -> SystemHealth:
    """Check overall system health."""
    alerts = []
    
    # Database health
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = "error"
        alerts.append({
            "level": "critical",
            "message": f"Database connection error: {str(e)}",
            "timestamp": datetime.utcnow()
        })
    
    # Redis health
    try:
        await redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = "error"
        alerts.append({
            "level": "warning",
            "message": f"Redis connection error: {str(e)}",
            "timestamp": datetime.utcnow()
        })
    
    # MongoDB health
    try:
        await mongodb.admin.command('ping')
        mongodb_status = "healthy"
    except Exception as e:
        mongodb_status = "error"
        alerts.append({
            "level": "warning",
            "message": f"MongoDB connection error: {str(e)}",
            "timestamp": datetime.utcnow()
        })
    
    # Overall status
    if db_status == "error":
        overall_status = "critical"
    elif redis_status == "error" or mongodb_status == "error":
        overall_status = "warning"
    else:
        overall_status = "healthy"
    
    return SystemHealth(
        status=overall_status,
        database_status=db_status,
        redis_status=redis_status,
        mongodb_status=mongodb_status,
        api_response_time=0.0,  # Would need actual measurement
        memory_usage_percent=0.0,  # Would need system monitoring
        disk_usage_percent=0.0,  # Would need system monitoring
        active_connections=0,  # Would need connection pool monitoring
        last_backup=None,  # Would need backup system integration
        alerts=alerts
    )

# API endpoints
@router.get("/dashboard", response_model=SystemStats)
async def get_admin_dashboard(
    current_user: User = Depends(current_superuser),
    db: Session = Depends(get_sync_db),
    redis_client = Depends(get_redis),
    mongodb = Depends(get_mongodb)
):
    """Get admin dashboard statistics."""
    metrics = await get_system_metrics(db, redis_client, mongodb)
    
    return SystemStats(
        total_users=metrics["total_users"],
        active_users_today=metrics["active_users"],
        new_users_this_week=metrics["new_users_week"],
        total_exercises_logged=metrics["total_exercises"],
        total_medications_tracked=metrics["total_medications"],
        total_calendar_events=metrics["total_events"],
        system_uptime="N/A",  # Would need process monitoring
        database_size="N/A",  # Would need database size query
        api_requests_today=metrics["api_requests_today"],
        error_rate_today=metrics["error_rate_today"]
    )

@router.get("/users", response_model=List[UserSummary])
async def get_all_users(
    status: Optional[UserStatus] = Query(None, description="Filter by user status"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(current_superuser),
    db: Session = Depends(get_sync_db)
):
    """Get all users with filtering and pagination."""
    query = db.query(User)
    
    if status:
        if status == UserStatus.ACTIVE:
            query = query.filter(User.is_active == True)
        elif status == UserStatus.INACTIVE:
            query = query.filter(User.is_active == False)
        elif status == UserStatus.SUSPENDED:
            # Would need a suspended field in User model
            pass
    
    if search:
        query = query.filter(
            or_(
                User.email.ilike(f"%{search}%"),
                # Would need name fields in User model for full name search
            )
        )
    
    users = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()
    
    # Enhance with additional data
    user_summaries = []
    for user in users:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        exercise_count = db.query(ExerciseLog).filter(ExerciseLog.user_id == user.id).count()
        medication_count = db.query(MedicineHistory).filter(MedicineHistory.user_id == user.id).count()
        
        user_summaries.append(UserSummary(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            last_login=None,  # Would need last_login field
            profile_completed=profile is not None,
            total_exercises=exercise_count,
            total_medications=medication_count
        ))
    
    return user_summaries

@router.get("/users/{user_id}", response_model=UserDetails)
async def get_user_details(
    user_id: UUID,
    current_user: User = Depends(current_superuser),
    db: Session = Depends(get_sync_db)
):
    """Get detailed information about a specific user."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    profile_dict = {
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "date_of_birth": profile.date_of_birth,
        "gender": profile.gender,
        "fitness_level": profile.fitness_level,
        "health_goals": profile.health_goals
    } if profile else None
    
    # Exercise statistics
    exercises = db.query(ExerciseLog).filter(ExerciseLog.user_id == user_id).all()
    exercise_stats = {
        "total_exercises": len(exercises),
        "completed_exercises": len([e for e in exercises if e.completed]),
        "total_duration": sum([e.duration_minutes or 0 for e in exercises]),
        "total_calories": sum([e.calories_burned or 0 for e in exercises])
    }
    
    # Health summary
    medications = db.query(MedicineHistory).filter(MedicineHistory.user_id == user_id).count()
    diseases = db.query(DiseaseHistory).filter(DiseaseHistory.user_id == user_id).count()
    events = db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id).count()
    
    health_summary = {
        "total_medications": medications,
        "total_diseases": diseases,
        "total_calendar_events": events
    }
    
    # Recent activity (last 10 audit logs)
    recent_logs = db.query(AuditLog).filter(
        AuditLog.user_id == user_id
    ).order_by(desc(AuditLog.timestamp)).limit(10).all()
    
    recent_activity = [
        {
            "action": log.action,
            "resource_type": log.resource_type,
            "timestamp": log.timestamp,
            "details": log.details
        }
        for log in recent_logs
    ]
    
    return UserDetails(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login=None,  # Would need last_login field
        profile=profile_dict,
        exercise_stats=exercise_stats,
        health_summary=health_summary,
        recent_activity=recent_activity
    )

@router.post("/users/{user_id}/action")
async def perform_user_action(
    user_id: UUID,
    action_data: UserAction,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_superuser),
    db: Session = Depends(get_sync_db)
):
    """Perform administrative actions on a user."""
    target_user = db.query(User).filter(User.id == user_id).first()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-modification of admin status
    if target_user.id == current_user.id and action_data.action in ["make_admin", "remove_admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own admin status"
        )
    
    # Perform the action
    if action_data.action == "suspend":
        target_user.is_active = False
    elif action_data.action == "activate":
        target_user.is_active = True
    elif action_data.action == "verify":
        target_user.is_verified = True
    elif action_data.action == "make_admin":
        target_user.is_superuser = True
    elif action_data.action == "remove_admin":
        target_user.is_superuser = False
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action"
        )
    
    target_user.updated_at = datetime.utcnow()
    db.commit()
    
    # Log the action
    audit_log = AuditLog(
        user_id=current_user.id,
        action=f"admin_{action_data.action}",
        resource_type="user",
        resource_id=str(target_user.id),
        details={
            "target_user_email": target_user.email,
            "reason": action_data.reason,
            "admin_user_email": current_user.email
        }
    )
    db.add(audit_log)
    db.commit()
    
    # Send notification to user if requested
    if action_data.notify_user:
        # Would implement email notification here
        pass
    
    return {
        "message": f"Action '{action_data.action}' performed successfully on user {target_user.email}",
        "user_id": str(target_user.id)
    }

@router.get("/analytics", response_model=UserAnalytics)
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(current_superuser),
    db: Session = Depends(get_sync_db)
):
    """Get user analytics and trends."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Registration trend
    registration_trend = []
    for i in range(days):
        day = start_date + timedelta(days=i)
        count = db.query(User).filter(
            func.date(User.created_at) == day
        ).count()
        registration_trend.append({
            "date": day.isoformat(),
            "registrations": count
        })
    
    # User activity distribution (simplified)
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    
    activity_distribution = {
        "total": total_users,
        "active": active_users,
        "verified": verified_users,
        "inactive": total_users - active_users
    }
    
    # Feature usage stats
    users_with_profiles = db.query(UserProfile).count()
    users_with_exercises = db.query(func.count(func.distinct(ExerciseLog.user_id))).scalar()
    users_with_medications = db.query(func.count(func.distinct(MedicineHistory.user_id))).scalar()
    users_with_events = db.query(func.count(func.distinct(CalendarEvent.user_id))).scalar()
    
    feature_usage = {
        "profiles": users_with_profiles,
        "exercise_tracking": users_with_exercises,
        "medication_tracking": users_with_medications,
        "calendar": users_with_events
    }
    
    # Retention metrics (simplified)
    retention_metrics = {
        "day_1": 85.0,  # Would need actual calculation
        "day_7": 65.0,
        "day_30": 45.0,
        "day_90": 30.0
    }
    
    return UserAnalytics(
        registration_trend=registration_trend,
        user_activity_distribution=activity_distribution,
        feature_usage_stats=feature_usage,
        retention_metrics=retention_metrics,
        geographic_distribution={"Unknown": total_users},  # Would need geo data
        device_distribution={"Unknown": total_users}  # Would need device tracking
    )

@router.get("/system/health", response_model=SystemHealth)
async def get_system_health(
    current_user: User = Depends(current_superuser),
    db: Session = Depends(get_sync_db),
    redis_client = Depends(get_redis),
    mongodb = Depends(get_mongodb)
):
    """Get system health status."""
    return await check_system_health(db, redis_client, mongodb)

@router.get("/audit-logs", response_model=List[AuditLogEntry])
async def get_audit_logs(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(current_superuser),
    db: Session = Depends(get_sync_db)
):
    """Get audit logs with filtering."""
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    if start_date:
        query = query.filter(AuditLog.timestamp >= datetime.combine(start_date, datetime.min.time()))
    
    if end_date:
        query = query.filter(AuditLog.timestamp <= datetime.combine(end_date, datetime.max.time()))
    
    logs = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(limit).all()
    return logs

@router.post("/system/backup")
async def trigger_system_backup(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_superuser)
):
    """Trigger a system backup."""
    # Would implement actual backup logic here
    background_tasks.add_task(perform_backup)
    
    return {"message": "Backup initiated successfully"}

@router.get("/system/backup/status", response_model=BackupStatus)
async def get_backup_status(
    current_user: User = Depends(current_superuser)
):
    """Get backup system status."""
    # Would implement actual backup status checking
    return BackupStatus(
        last_backup=None,
        backup_size=None,
        backup_location=None,
        next_scheduled=None,
        status="unknown",
        retention_days=30
    )

@router.get("/alerts", response_model=List[SystemAlert])
async def get_system_alerts(
    level: Optional[str] = Query(None, description="Filter by alert level"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    current_user: User = Depends(current_superuser)
):
    """Get system alerts."""
    # Would implement actual alert system
    return []

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(current_superuser)
):
    """Mark an alert as resolved."""
    # Would implement alert resolution
    return {"message": f"Alert {alert_id} resolved successfully"}

# Background tasks
async def perform_backup():
    """Perform system backup (placeholder)."""
    # Would implement actual backup logic
    await asyncio.sleep(1)  # Simulate backup time
    print("Backup completed")
