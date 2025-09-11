import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from database.models import AuditLog, User
from database.config import get_sync_db
from fastapi import Request, Depends
import logging
from enum import Enum

# GDPR/HIPAA Compliance Module

class DataCategory(str, Enum):
    """Data categories for GDPR compliance"""
    PERSONAL = "personal"
    HEALTH = "health"
    BIOMETRIC = "biometric"
    FINANCIAL = "financial"
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"

class ProcessingPurpose(str, Enum):
    """Data processing purposes for GDPR compliance"""
    HEALTHCARE_DELIVERY = "healthcare_delivery"
    TREATMENT_PLANNING = "treatment_planning"
    HEALTH_MONITORING = "health_monitoring"
    RESEARCH = "research"
    ANALYTICS = "analytics"
    SYSTEM_ADMINISTRATION = "system_administration"
    LEGAL_COMPLIANCE = "legal_compliance"

class AuditAction(str, Enum):
    """Audit log action types"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    SHARE = "share"
    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    DATA_DELETION = "data_deletion"
    PRIVACY_SETTINGS_CHANGED = "privacy_settings_changed"

class DataEncryption:
    """Handle data encryption for HIPAA compliance"""
    
    def __init__(self):
        self.key = os.getenv("ENCRYPTION_KEY").encode()
        self.fernet = Fernet(self.key)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return data
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        return self.fernet.decrypt(encrypted_data.encode()).decode()
    
    def encrypt_dict(self, data: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
        """Encrypt specific fields in a dictionary"""
        encrypted_data = data.copy()
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt_data(str(encrypted_data[field]))
        return encrypted_data
    
    def decrypt_dict(self, data: Dict[str, Any], sensitive_fields: List[str]) -> Dict[str, Any]:
        """Decrypt specific fields in a dictionary"""
        decrypted_data = data.copy()
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = self.decrypt_data(decrypted_data[field])
        return decrypted_data

class AuditLogger:
    """Comprehensive audit logging for compliance"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler for audit logs
        handler = logging.FileHandler("logs/audit.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    async def log_action(
        self,
        user_id: Optional[int],
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        db: Session = Depends(get_sync_db)
    ):
        """Log user actions for audit trail"""
        
        audit_entry = AuditLog(
            user_id=user_id,
            action=action.value,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )
        
        db.add(audit_entry)
        db.commit()
        
        # Also log to file
        log_message = f"User {user_id} performed {action.value} on {resource_type}"
        if resource_id:
            log_message += f" (ID: {resource_id})"
        if ip_address:
            log_message += f" from {ip_address}"
        
        self.logger.info(log_message)

class ConsentManager:
    """Manage user consent for GDPR compliance"""
    
    @staticmethod
    def record_consent(
        user_id: int,
        data_category: DataCategory,
        processing_purpose: ProcessingPurpose,
        consent_given: bool,
        db: Session
    ):
        """Record user consent for data processing"""
        # This would typically be stored in a separate consent table
        # For now, we'll use the audit log
        audit_logger = AuditLogger()
        
        details = {
            "data_category": data_category.value,
            "processing_purpose": processing_purpose.value,
            "consent_given": consent_given
        }
        
        action = AuditAction.CONSENT_GIVEN if consent_given else AuditAction.CONSENT_WITHDRAWN
        
        audit_logger.log_action(
            user_id=user_id,
            action=action,
            resource_type="consent",
            details=details,
            db=db
        )
    
    @staticmethod
    def check_consent(
        user_id: int,
        data_category: DataCategory,
        processing_purpose: ProcessingPurpose,
        db: Session
    ) -> bool:
        """Check if user has given consent for specific data processing"""
        # Query the most recent consent record
        latest_consent = db.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.action.in_([AuditAction.CONSENT_GIVEN.value, AuditAction.CONSENT_WITHDRAWN.value]),
            AuditLog.resource_type == "consent"
        ).order_by(AuditLog.timestamp.desc()).first()
        
        if not latest_consent:
            return False
        
        details = json.loads(latest_consent.details) if latest_consent.details else {}
        
        if (details.get("data_category") == data_category.value and 
            details.get("processing_purpose") == processing_purpose.value):
            return details.get("consent_given", False)
        
        return False

class DataRetentionManager:
    """Manage data retention policies for compliance"""
    
    # Data retention periods (in days)
    RETENTION_POLICIES = {
        DataCategory.PERSONAL: 2555,  # 7 years
        DataCategory.HEALTH: 3650,   # 10 years
        DataCategory.BIOMETRIC: 1825, # 5 years
        DataCategory.FINANCIAL: 2555, # 7 years
        DataCategory.BEHAVIORAL: 1095, # 3 years
        DataCategory.TECHNICAL: 365,   # 1 year
    }
    
    @staticmethod
    def should_delete_data(data_category: DataCategory, created_date: datetime) -> bool:
        """Check if data should be deleted based on retention policy"""
        retention_days = DataRetentionManager.RETENTION_POLICIES.get(data_category, 365)
        expiry_date = created_date + timedelta(days=retention_days)
        return datetime.utcnow() > expiry_date
    
    @staticmethod
    async def cleanup_expired_data(db: Session):
        """Clean up expired data based on retention policies"""
        audit_logger = AuditLogger()
        
        # This is a simplified example - in practice, you'd have specific
        # cleanup procedures for each data type
        
        # Log the cleanup action
        await audit_logger.log_action(
            user_id=None,
            action=AuditAction.DATA_DELETION,
            resource_type="system",
            details={"reason": "automated_retention_policy"},
            db=db
        )

class PrivacyControls:
    """Privacy controls for user data"""
    
    @staticmethod
    def anonymize_user_data(user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize user data for analytics/research"""
        anonymized = user_data.copy()
        
        # Remove direct identifiers
        sensitive_fields = [
            'email', 'phone', 'name', 'address', 'ssn', 'date_of_birth'
        ]
        
        for field in sensitive_fields:
            if field in anonymized:
                # Replace with hashed version or remove entirely
                if field in ['email', 'phone']:
                    anonymized[field] = hashlib.sha256(
                        str(anonymized[field]).encode()
                    ).hexdigest()[:8]
                else:
                    del anonymized[field]
        
        return anonymized
    
    @staticmethod
    def export_user_data(user_id: int, db: Session) -> Dict[str, Any]:
        """Export all user data for GDPR data portability"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Collect all user data from various tables
        user_data = {
            "personal_info": {
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "role": user.role
            },
            # Add other data categories as needed
            "profile_data": {},
            "health_data": {},
            "exercise_data": {},
            "audit_logs": []
        }
        
        # Get audit logs for this user
        audit_logs = db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.timestamp.desc()).limit(100).all()
        
        user_data["audit_logs"] = [
            {
                "action": log.action,
                "resource_type": log.resource_type,
                "timestamp": log.timestamp.isoformat(),
                "details": json.loads(log.details) if log.details else None
            }
            for log in audit_logs
        ]
        
        return user_data
    
    @staticmethod
    async def delete_user_data(user_id: int, db: Session):
        """Delete all user data for GDPR right to be forgotten"""
        audit_logger = AuditLogger()
        
        # Log the deletion request
        await audit_logger.log_action(
            user_id=user_id,
            action=AuditAction.DATA_DELETION,
            resource_type="user_account",
            details={"reason": "user_request_gdpr"},
            db=db
        )
        
        # Delete user data from all tables
        # This should be implemented based on your specific data model
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Mark as deleted rather than hard delete to maintain audit trail
            user.is_active = False
            user.email = f"deleted_user_{user_id}@deleted.local"
            user.hashed_password = "DELETED"
            db.commit()

# Initialize global instances
data_encryption = DataEncryption()
audit_logger = AuditLogger()
consent_manager = ConsentManager()
data_retention_manager = DataRetentionManager()
privacy_controls = PrivacyControls()

# Middleware for automatic audit logging
async def audit_middleware(request: Request, call_next):
    """Middleware to automatically log API requests"""
    start_time = datetime.utcnow()
    
    # Get user info if available
    user_id = getattr(request.state, 'user_id', None)
    
    response = await call_next(request)
    
    # Log the request
    if user_id:
        await audit_logger.log_action(
            user_id=user_id,
            action=AuditAction.READ,  # Default action
            resource_type="api_endpoint",
            resource_id=str(request.url.path),
            details={
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
            },
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
    
    return response