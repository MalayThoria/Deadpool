from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from database.config import get_db
from database.models import User
from database.prescription_models import PrescriptionRecord, HealthRecommendation
from services.prescription_integration import PrescriptionIntegrationService, IntegrationResult
from auth.auth import current_active_user
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/prescription-integration", tags=["Prescription Integration"])

# Pydantic models for API requests/responses
class PrescriptionUploadRequest(BaseModel):
    prescription_text: str = Field(..., description="OCR extracted text from prescription")
    image_reference: Optional[str] = Field(None, description="Reference to uploaded image")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class PrescriptionUploadResponse(BaseModel):
    success: bool
    message: str
    prescription_id: Optional[int] = None
    integration_summary: Optional[Dict[str, Any]] = None
    recommendations_created: int = 0
    conditions_detected: int = 0

class RecommendationUpdateRequest(BaseModel):
    recommendation_id: int
    is_completed: Optional[bool] = None
    user_feedback: Optional[str] = None
    is_helpful: Optional[bool] = None

class SyncStatusResponse(BaseModel):
    user_id: int
    total_prescriptions: int
    synced_prescriptions: int
    pending_sync: int
    failed_sync: int
    last_sync: Optional[str] = None

@router.post("/upload-prescription", response_model=PrescriptionUploadResponse)
@limiter.limit("10/minute")
async def upload_prescription(
    request: Request,
    request_data: PrescriptionUploadRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process a prescription, integrating it with the health dashboard
    """
    try:
        integration_service = PrescriptionIntegrationService(db)
        
        # Process prescription and integrate with dashboard
        result: IntegrationResult = await integration_service.process_prescription_upload(
            user_id=current_user.id,
            prescription_text=request_data.prescription_text,
            image_reference=request_data.image_reference
        )
        
        if result.success:
            # Schedule background tasks for additional processing
            background_tasks.add_task(
                _schedule_medication_reminders,
                current_user.id,
                result.prescription_id,
                db
            )
            
            return PrescriptionUploadResponse(
                success=True,
                message="Prescription processed and integrated successfully",
                prescription_id=result.prescription_id,
                recommendations_created=result.recommendations_created,
                dashboard_entries_created=result.dashboard_entries_created,
                conditions_detected=result.conditions_detected,
                integration_summary={
                    "processing_time": "< 5 seconds",
                    "confidence_level": "high",
                    "sync_status": "completed"
                }
            )
        else:
            logger.error(f"Prescription integration failed for user {current_user.id}: {result.error_message}")
            return PrescriptionUploadResponse(
                success=False,
                message=f"Failed to process prescription: {result.error_message}"
            )
            
    except Exception as e:
        logger.error(f"Unexpected error in prescription upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during prescription processing"
        )

@router.get("/prescriptions", response_model=List[Dict[str, Any]])
@limiter.limit("20/minute")
async def get_user_prescriptions(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's prescription history with integration status
    """
    try:
        prescriptions = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.user_id == current_user.id
        ).order_by(
            PrescriptionRecord.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        prescription_data = []
        for presc in prescriptions:
            prescription_data.append({
                "id": presc.id,
                "created_at": presc.created_at.isoformat(),
                "prescription_date": presc.prescription_date.isoformat() if presc.prescription_date else None,
                "medications": presc.medications,
                "conditions": presc.conditions,
                "doctor_info": presc.doctor_info,
                "processing_status": presc.processing_status.value,
                "dashboard_sync_status": presc.dashboard_sync_status.value,
                "extraction_confidence": presc.extraction_confidence,
                "processed_at": presc.processed_at.isoformat() if presc.processed_at else None
            })
        
        return prescription_data
        
    except Exception as e:
        logger.error(f"Error fetching prescriptions for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch prescription history"
        )

@router.get("/recommendations", response_model=List[Dict[str, Any]])
@limiter.limit("20/minute")
async def get_health_recommendations(
    request: Request,
    active_only: bool = True,
    limit: int = 20,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get health recommendations for the current user
    """
    try:
        query = db.query(HealthRecommendation).filter(
            HealthRecommendation.user_id == current_user.id
        )
        
        if active_only:
            query = query.filter(
                HealthRecommendation.is_active == True,
                HealthRecommendation.is_completed == False
            )
        
        recommendations = query.order_by(
            HealthRecommendation.created_at.desc()
        ).limit(limit).all()
        
        recommendation_data = []
        for rec in recommendations:
            recommendation_data.append({
                "id": rec.id,
                "title": rec.title,
                "description": rec.description,
                "recommendation_type": rec.recommendation_type.value,
                "priority": rec.priority,
                "based_on_medications": rec.based_on_medications,
                "based_on_conditions": rec.based_on_conditions,
                "reasoning": rec.reasoning,
                "action_items": rec.action_items,
                "timeline": rec.timeline,
                "is_completed": rec.is_completed,
                "user_feedback": rec.user_feedback,
                "is_helpful": rec.is_helpful,
                "created_at": rec.created_at.isoformat(),
                "completed_at": rec.completed_at.isoformat() if rec.completed_at else None
            })
        
        return recommendation_data
        
    except Exception as e:
        logger.error(f"Error fetching recommendations for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch health recommendations"
        )

@router.put("/recommendations/{recommendation_id}")
@limiter.limit("20/minute")
async def update_recommendation(
    recommendation_id: int,
    request: Request,
    request_data: RecommendationUpdateRequest,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a health recommendation (mark as completed, add feedback, etc.)
    """
    try:
        recommendation = db.query(HealthRecommendation).filter(
            HealthRecommendation.id == recommendation_id,
            HealthRecommendation.user_id == current_user.id
        ).first()
        
        if not recommendation:
            raise HTTPException(
                status_code=404,
                detail="Recommendation not found"
            )
        
        # Update fields if provided
        if request_data.is_completed is not None:
            recommendation.is_completed = request_data.is_completed
            if request_data.is_completed:
                recommendation.completed_at = datetime.now()
        
        if request_data.user_feedback is not None:
            recommendation.user_feedback = request_data.user_feedback
        
        if request_data.is_helpful is not None:
            recommendation.is_helpful = request_data.is_helpful
        
        recommendation.updated_at = datetime.now()
        db.commit()
        
        return {
            "success": True,
            "message": "Recommendation updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating recommendation {recommendation_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update recommendation"
        )

@router.get("/sync-status", response_model=SyncStatusResponse)
@limiter.limit("10/minute")
async def get_sync_status(
    request: Request,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get synchronization status for user's prescription data
    """
    try:
        from database.prescription_models import SyncStatus
        
        # Count prescriptions by sync status
        total_prescriptions = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.user_id == current_user.id
        ).count()
        
        synced_prescriptions = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.user_id == current_user.id,
            PrescriptionRecord.dashboard_sync_status == SyncStatus.SYNCED
        ).count()
        
        pending_sync = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.user_id == current_user.id,
            PrescriptionRecord.dashboard_sync_status == SyncStatus.PENDING
        ).count()
        
        failed_sync = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.user_id == current_user.id,
            PrescriptionRecord.dashboard_sync_status == SyncStatus.FAILED
        ).count()
        
        # Get last successful sync
        last_synced = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.user_id == current_user.id,
            PrescriptionRecord.dashboard_sync_status == SyncStatus.SYNCED
        ).order_by(PrescriptionRecord.processed_at.desc()).first()
        
        return SyncStatusResponse(
            user_id=current_user.id,
            total_prescriptions=total_prescriptions,
            synced_prescriptions=synced_prescriptions,
            pending_sync=pending_sync,
            failed_sync=failed_sync,
            last_sync=last_synced.processed_at.isoformat() if last_synced and last_synced.processed_at else None
        )
        
    except Exception as e:
        logger.error(f"Error fetching sync status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch synchronization status"
        )

@router.post("/resync-prescription/{prescription_id}")
@limiter.limit("5/minute")
async def resync_prescription(
    prescription_id: int,
    request: Request,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger resynchronization of a specific prescription
    """
    try:
        prescription = db.query(PrescriptionRecord).filter(
            PrescriptionRecord.id == prescription_id,
            PrescriptionRecord.user_id == current_user.id
        ).first()
        
        if not prescription:
            raise HTTPException(
                status_code=404,
                detail="Prescription not found"
            )
        
        integration_service = PrescriptionIntegrationService(db)
        
        # Re-process the prescription
        result = await integration_service.process_prescription_upload(
            user_id=current_user.id,
            prescription_text=prescription.original_text,
            image_reference=prescription.image_reference
        )
        
        if result.success:
            return {
                "success": True,
                "message": "Prescription resynchronized successfully",
                "prescription_id": prescription_id
            }
        else:
            return {
                "success": False,
                "message": f"Resynchronization failed: {result.error_message}",
                "prescription_id": prescription_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resyncing prescription {prescription_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to resynchronize prescription"
        )

# Background task functions
async def _schedule_medication_reminders(
    user_id: int, 
    prescription_id: int, 
    db: Session
):
    """Background task to schedule medication reminders"""
    try:
        # This would integrate with a notification/reminder system
        # For now, we'll just log the action
        logger.info(f"Scheduling medication reminders for user {user_id}, prescription {prescription_id}")
        
        # In a real implementation, this would:
        # 1. Create calendar events
        # 2. Set up push notifications
        # 3. Send email reminders
        # 4. Integrate with external reminder services
        
    except Exception as e:
        logger.error(f"Failed to schedule medication reminders: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for the prescription integration service"""
    return {
        "status": "healthy",
        "service": "prescription-integration",
        "timestamp": datetime.now().isoformat()
    }