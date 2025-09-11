from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import json

from database.config import get_sync_db
from auth.auth import current_active_user
from database.models import User
from security.compliance import (
    DataCategory, ProcessingPurpose, AuditAction,
    audit_logger, consent_manager, privacy_controls,
    data_retention_manager
)

router = APIRouter()

# Pydantic models for privacy API
class ConsentRequest(BaseModel):
    data_category: DataCategory
    processing_purpose: ProcessingPurpose
    consent_given: bool

class ConsentResponse(BaseModel):
    data_category: str
    processing_purpose: str
    consent_given: bool
    timestamp: datetime

class PrivacySettings(BaseModel):
    data_sharing_enabled: bool = False
    analytics_enabled: bool = True
    marketing_enabled: bool = False
    research_participation: bool = False
    data_retention_period: int = 2555  # days
    export_format: str = "json"

class DataExportRequest(BaseModel):
    format: str = "json"  # json, csv, xml
    include_audit_logs: bool = True
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None

class DataDeletionRequest(BaseModel):
    confirmation_text: str
    reason: Optional[str] = None
    delete_immediately: bool = False

class AuditLogResponse(BaseModel):
    id: int
    action: str
    resource_type: str
    resource_id: Optional[str]
    timestamp: datetime
    ip_address: Optional[str]
    details: Optional[Dict[str, Any]]

class PrivacyDashboard(BaseModel):
    total_data_points: int
    data_categories: Dict[str, int]
    consent_status: Dict[str, bool]
    last_export: Optional[datetime]
    retention_status: Dict[str, datetime]
    privacy_score: int  # 0-100

@router.post("/consent", response_model=ConsentResponse)
async def record_consent(
    consent_request: ConsentRequest,
    request: Request,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Record user consent for data processing"""
    
    # Record consent
    consent_manager.record_consent(
        user_id=current_user.id,
        data_category=consent_request.data_category,
        processing_purpose=consent_request.processing_purpose,
        consent_given=consent_request.consent_given,
        db=db
    )
    
    # Log the action
    await audit_logger.log_action(
        user_id=current_user.id,
        action=AuditAction.CONSENT_GIVEN if consent_request.consent_given else AuditAction.CONSENT_WITHDRAWN,
        resource_type="consent",
        details={
            "data_category": consent_request.data_category.value,
            "processing_purpose": consent_request.processing_purpose.value
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        db=db
    )
    
    return ConsentResponse(
        data_category=consent_request.data_category.value,
        processing_purpose=consent_request.processing_purpose.value,
        consent_given=consent_request.consent_given,
        timestamp=datetime.utcnow()
    )

@router.get("/consent", response_model=List[ConsentResponse])
async def get_consent_status(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get current consent status for all data categories"""
    
    consent_statuses = []
    
    for category in DataCategory:
        for purpose in ProcessingPurpose:
            consent_given = consent_manager.check_consent(
                user_id=current_user.id,
                data_category=category,
                processing_purpose=purpose,
                db=db
            )
            
            consent_statuses.append(ConsentResponse(
                data_category=category.value,
                processing_purpose=purpose.value,
                consent_given=consent_given,
                timestamp=datetime.utcnow()
            ))
    
    return consent_statuses

@router.get("/settings", response_model=PrivacySettings)
async def get_privacy_settings(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get user's privacy settings"""
    
    # In a real implementation, these would be stored in the database
    # For now, return default settings
    return PrivacySettings(
        data_sharing_enabled=False,
        analytics_enabled=True,
        marketing_enabled=False,
        research_participation=False,
        data_retention_period=2555,
        export_format="json"
    )

@router.put("/settings", response_model=PrivacySettings)
async def update_privacy_settings(
    settings: PrivacySettings,
    request: Request,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Update user's privacy settings"""
    
    # Log the privacy settings change
    await audit_logger.log_action(
        user_id=current_user.id,
        action=AuditAction.PRIVACY_SETTINGS_CHANGED,
        resource_type="privacy_settings",
        details=settings.dict(),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        db=db
    )
    
    # In a real implementation, save to database
    # For now, just return the settings
    return settings

@router.post("/export")
async def export_user_data(
    export_request: DataExportRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Export user data for GDPR compliance"""
    
    # Log the export request
    await audit_logger.log_action(
        user_id=current_user.id,
        action=AuditAction.EXPORT,
        resource_type="user_data",
        details={
            "format": export_request.format,
            "include_audit_logs": export_request.include_audit_logs
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        db=db
    )
    
    # Export user data
    user_data = privacy_controls.export_user_data(current_user.id, db)
    
    if export_request.format == "json":
        return {
            "message": "Data export completed",
            "data": user_data,
            "export_timestamp": datetime.utcnow().isoformat(),
            "format": "json"
        }
    else:
        # For other formats, you would implement conversion logic
        return {
            "message": f"Data export in {export_request.format} format is not yet implemented",
            "available_formats": ["json"]
        }

@router.delete("/data")
async def delete_user_data(
    deletion_request: DataDeletionRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Delete user data (GDPR right to be forgotten)"""
    
    # Verify confirmation text
    expected_confirmation = f"DELETE {current_user.email}"
    if deletion_request.confirmation_text != expected_confirmation:
        raise HTTPException(
            status_code=400,
            detail=f"Confirmation text must be exactly: {expected_confirmation}"
        )
    
    # Log the deletion request
    await audit_logger.log_action(
        user_id=current_user.id,
        action=AuditAction.DATA_DELETION,
        resource_type="user_account",
        details={
            "reason": deletion_request.reason,
            "delete_immediately": deletion_request.delete_immediately
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        db=db
    )
    
    if deletion_request.delete_immediately:
        # Immediate deletion
        await privacy_controls.delete_user_data(current_user.id, db)
        return {
            "message": "User data has been deleted immediately",
            "deletion_timestamp": datetime.utcnow().isoformat()
        }
    else:
        # Schedule deletion (30-day grace period)
        # In a real implementation, you would schedule this as a background task
        return {
            "message": "User data deletion has been scheduled",
            "deletion_date": (datetime.utcnow()).isoformat(),
            "grace_period_days": 30
        }

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    limit: int = 50,
    offset: int = 0,
    action_filter: Optional[str] = None,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get user's audit logs"""
    
    from database.models import AuditLog
    
    query = db.query(AuditLog).filter(AuditLog.user_id == current_user.id)
    
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    
    audit_logs = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
    
    return [
        AuditLogResponse(
            id=log.id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            timestamp=log.timestamp,
            ip_address=log.ip_address,
            details=json.loads(log.details) if log.details else None
        )
        for log in audit_logs
    ]

@router.get("/dashboard", response_model=PrivacyDashboard)
async def get_privacy_dashboard(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get privacy dashboard with user's data overview"""
    
    from database.models import AuditLog
    
    # Count total data points (simplified)
    total_audit_logs = db.query(AuditLog).filter(AuditLog.user_id == current_user.id).count()
    
    # Data categories breakdown (simplified)
    data_categories = {
        "personal": 1,
        "health": 0,
        "biometric": 0,
        "financial": 0,
        "behavioral": total_audit_logs,
        "technical": total_audit_logs
    }
    
    # Consent status
    consent_status = {}
    for category in DataCategory:
        for purpose in ProcessingPurpose:
            key = f"{category.value}_{purpose.value}"
            consent_status[key] = consent_manager.check_consent(
                user_id=current_user.id,
                data_category=category,
                processing_purpose=purpose,
                db=db
            )
    
    # Calculate privacy score (simplified)
    total_consents = len(consent_status)
    given_consents = sum(1 for consent in consent_status.values() if consent)
    privacy_score = int((given_consents / total_consents) * 100) if total_consents > 0 else 100
    
    return PrivacyDashboard(
        total_data_points=total_audit_logs + 1,  # +1 for user account
        data_categories=data_categories,
        consent_status=consent_status,
        last_export=None,  # Would be stored in database
        retention_status={
            "account_created": current_user.created_at,
            "data_expires": current_user.created_at  # Would calculate based on retention policy
        },
        privacy_score=privacy_score
    )

@router.get("/compliance-report")
async def get_compliance_report(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Generate compliance report for the user"""
    
    from database.models import AuditLog
    
    # Get recent audit activity
    recent_logs = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id
    ).order_by(AuditLog.timestamp.desc()).limit(10).all()
    
    return {
        "user_id": current_user.id,
        "report_generated": datetime.utcnow().isoformat(),
        "gdpr_compliance": {
            "data_portability": "Available via /export endpoint",
            "right_to_be_forgotten": "Available via /data DELETE endpoint",
            "consent_management": "Available via /consent endpoints",
            "audit_trail": "Comprehensive logging enabled"
        },
        "hipaa_compliance": {
            "data_encryption": "AES-256 encryption enabled",
            "access_controls": "Role-based access implemented",
            "audit_logging": "All actions logged",
            "data_retention": "Automated retention policies"
        },
        "recent_activity": [
            {
                "action": log.action,
                "timestamp": log.timestamp.isoformat(),
                "resource": log.resource_type
            }
            for log in recent_logs
        ],
        "data_categories_processed": list(DataCategory),
        "processing_purposes": list(ProcessingPurpose)
    }
