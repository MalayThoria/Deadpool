from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass

from database.models import User, UserProfile, MedicineHistory, DiseaseHistory
from database.prescription_models import (
    PrescriptionRecord, HealthRecommendation, 
    ConditionRecord, IntegrationSyncLog, PrescriptionStatus, 
    RecommendationType, SyncStatus
)
from services.websocket_service import sync_service
from utils.gpt import GPTProcessor
from security.data_protection import (
    DataValidator, SecureStorage, AccessControl, 
    initialize_security_services, get_security_config
)
from database.config import get_db

logger = logging.getLogger(__name__)

@dataclass
class PrescriptionData:
    """Data structure for prescription information"""
    original_text: str
    medications: List[Dict[str, Any]]
    conditions: List[str]
    doctor_info: Optional[Dict[str, Any]] = None
    prescription_date: Optional[datetime] = None
    confidence_score: float = 0.0

@dataclass
class IntegrationResult:
    """Result of prescription integration process"""
    success: bool
    prescription_id: Optional[int] = None
    recommendations_created: int = 0
    conditions_detected: int = 0
    error_message: Optional[str] = None

class PrescriptionIntegrationService:
    """Service for integrating prescription data with health recommendations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.gpt_processor = GPTProcessor()
        
        # Initialize security services
        self.security_services = initialize_security_services()
        self.secure_storage = self.security_services['secure_storage']
        self.validator = self.security_services['validator']
        self.access_control = self.security_services['access_control']
        
        # Supported image formats
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp'}
        
        # Confidence thresholds
        self.min_confidence = 0.7
        self.high_confidence = 0.9
        
    async def process_prescription_upload(
        self, 
        user_id: int, 
        prescription_text: str, 
        image_reference: Optional[str] = None
    ) -> IntegrationResult:
        """
        Main entry point for processing prescription uploads and generating health recommendations
        """
        sync_log = self._create_sync_log(user_id, "prescription_upload", "prescription", 0)
        start_time = datetime.now()
        
        try:
            # Validate user ID
            user_id = self.validator.validate_user_id(user_id)
            
            # Log data access
            self.access_control.log_data_access(
                user_id=user_id,
                action="prescription_upload_start",
                data_type="prescription_text",
                additional_info={"has_image": image_reference is not None}
            )
            
            # Step 1: Extract structured data from prescription text
            prescription_data = await self._extract_prescription_data(prescription_text)
            
            # Validate and sanitize extracted data
            validated_data = self.validator.validate_prescription_data(prescription_data)
            
            # Store prescription data securely
            secure_data = self.secure_storage.store_prescription_securely(validated_data)
            
            # Step 2: Create prescription record
            prescription_record = self._create_prescription_record(
                user_id, secure_data, image_reference
            )
            
            # Step 3: Generate health recommendations
            recommendations = await self._generate_health_recommendations(
                user_id, prescription_record
            )
            
            # Step 4: Update user health profile
            await self._update_user_health_profile(user_id, validated_data)
            
            # Step 5: Mark as successfully integrated
            prescription_record.processing_status = PrescriptionStatus.INTEGRATED
            prescription_record.processed_at = datetime.now()
            
            self.db.commit()
            
            # Update sync log
            self._complete_sync_log(sync_log, SyncStatus.SYNCED, start_time)
            
            # Send real-time notifications
            await self._send_realtime_notifications(user_id, prescription_record, recommendations)
            
            # Log successful processing
            self.access_control.log_data_access(
                user_id=user_id,
                action="prescription_upload_complete",
                data_type="prescription_record",
                resource_id=prescription_record.id,
                additional_info={
                    "medications_count": len(validated_data.medications),
                    "conditions_count": len(validated_data.conditions),
                    "confidence_score": validated_data.confidence_score
                }
            )
            
            return IntegrationResult(
                success=True,
                prescription_id=prescription_record.id,
                recommendations_created=len(recommendations),
                conditions_detected=len(validated_data.conditions)
            )
            
        except Exception as e:
            logger.error(f"Prescription integration failed for user {user_id}: {str(e)}")
            self.db.rollback()
            
            # Log error
            self.access_control.log_data_access(
                user_id=user_id,
                action="prescription_upload_error",
                data_type="prescription_text",
                additional_info={"error": str(e)}
            )
            
            # Update sync log with error
            self._complete_sync_log(sync_log, SyncStatus.FAILED, start_time, str(e))
            
            return IntegrationResult(
                success=False,
                error_message=str(e)
            )
    
    async def _extract_prescription_data(self, prescription_text: str) -> PrescriptionData:
        """Extract structured data from prescription text using AI"""
        
        if self.gpt_processor.client is None:
            # Fallback extraction when OpenAI is not available
            return self._fallback_extraction(prescription_text)
        
        try:
            extraction_prompt = f"""
            Analyze this prescription text and extract medical information in JSON format:
            
            {prescription_text}
            
            Return valid JSON with this structure:
            {{
                "medications": [
                    {{
                        "name": "medication name",
                        "dosage": "dosage with units",
                        "frequency": "how often to take",
                        "duration": "treatment duration",
                        "instructions": "special instructions"
                    }}
                ],
                "conditions": ["condition1", "condition2"],
                "doctor_info": {{
                    "name": "doctor name",
                    "specialty": "medical specialty",
                    "contact": "contact info if available"
                }},
                "prescription_date": "YYYY-MM-DD or null",
                "confidence_score": 0.95
            }}
            """
            
            response = self.gpt_processor.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical data extraction specialist. Extract information accurately and return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": extraction_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                extracted_data = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from response if it's wrapped in text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse JSON from AI response")
            
            # Convert to PrescriptionData
            prescription_date = None
            if extracted_data.get("prescription_date"):
                try:
                    prescription_date = datetime.strptime(
                        extracted_data["prescription_date"], "%Y-%m-%d"
                    )
                except ValueError:
                    pass
            
            return PrescriptionData(
                original_text=prescription_text,
                medications=extracted_data.get("medications", []),
                conditions=extracted_data.get("conditions", []),
                doctor_info=extracted_data.get("doctor_info"),
                prescription_date=prescription_date,
                confidence_score=extracted_data.get("confidence_score", 0.0)
            )
            
        except Exception as e:
            logger.error(f"AI extraction failed: {str(e)}")
            return self._fallback_extraction(prescription_text)
    
    def _fallback_extraction(self, prescription_text: str) -> PrescriptionData:
        """Fallback extraction using simple pattern matching"""
        import re
        
        # Simple medication pattern matching
        medication_patterns = [
            r'([A-Z][a-z]+(?:cillin|mycin|prazole|statin|metformin|insulin))\s*(\d+\s*mg)',
            r'([A-Z][a-z]+)\s*(\d+\s*mg)',
            r'([A-Z][a-z]+)\s*tablet',
        ]
        
        medications = []
        for pattern in medication_patterns:
            matches = re.findall(pattern, prescription_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    name, dosage = match if len(match) == 2 else (match[0], "")
                else:
                    name, dosage = match, ""
                
                medications.append({
                    "name": name.title(),
                    "dosage": dosage,
                    "frequency": "As prescribed",
                    "duration": "As prescribed",
                    "instructions": "Follow doctor's instructions"
                })
        
        # Simple condition detection
        condition_keywords = [
            "diabetes", "hypertension", "infection", "pain", "inflammation",
            "depression", "anxiety", "asthma", "arthritis", "migraine"
        ]
        
        conditions = []
        for keyword in condition_keywords:
            if keyword.lower() in prescription_text.lower():
                conditions.append(keyword.title())
        
        return PrescriptionData(
            original_text=prescription_text,
            medications=medications,
            conditions=conditions,
            confidence_score=0.6  # Lower confidence for fallback
        )
    
    def _create_prescription_record(
        self, 
        user_id: int, 
        prescription_data: PrescriptionData, 
        image_reference: Optional[str]
    ) -> PrescriptionRecord:
        """Create a new prescription record in the database"""
        
        prescription_record = PrescriptionRecord(
            user_id=user_id,
            original_text=prescription_data.original_text,
            image_reference=image_reference,
            medications=prescription_data.medications,
            conditions=prescription_data.conditions,
            doctor_info=prescription_data.doctor_info,
            prescription_date=prescription_data.prescription_date,
            extraction_confidence=prescription_data.confidence_score,
            processing_status=PrescriptionStatus.PROCESSED
        )
        
        self.db.add(prescription_record)
        self.db.flush()  # Get the ID without committing
        
        return prescription_record
    
    async def _generate_health_recommendations(
        self, 
        user_id: int, 
        prescription_record: PrescriptionRecord
    ) -> List[HealthRecommendation]:
        """Generate personalized health recommendations based on prescription"""
        
        recommendations = []
        
        # Get user profile for personalized recommendations
        user_profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        # Generate medication reminders
        for medication in prescription_record.medications:
            reminder = HealthRecommendation(
                user_id=user_id,
                prescription_id=prescription_record.id,
                title=f"Take {medication['name']}",
                description=f"Remember to take {medication['name']} {medication.get('dosage', '')} {medication.get('frequency', '')}",
                recommendation_type=RecommendationType.MEDICATION_REMINDER,
                priority="high",
                based_on_medications=[medication],
                reasoning=f"Medication reminder based on prescription for {medication['name']}",
                action_items=[
                    f"Take {medication['name']} as prescribed",
                    "Set up medication reminders",
                    "Monitor for side effects"
                ],
                timeline="immediately"
            )
            recommendations.append(reminder)
        
        # Generate condition-based recommendations
        for condition in prescription_record.conditions:
            condition_rec = await self._generate_condition_recommendation(
                user_id, prescription_record.id, condition, user_profile
            )
            if condition_rec:
                recommendations.append(condition_rec)
        
        # Add all recommendations to database
        for rec in recommendations:
            self.db.add(rec)
        
        self.db.flush()
        return recommendations
    
    async def _generate_condition_recommendation(
        self, 
        user_id: int, 
        prescription_id: int, 
        condition: str, 
        user_profile: Optional[UserProfile]
    ) -> Optional[HealthRecommendation]:
        """Generate specific recommendations for a medical condition"""
        
        # Condition-specific recommendation templates
        condition_templates = {
            "diabetes": {
                "title": "Diabetes Management",
                "description": "Monitor blood sugar levels and maintain a healthy diet",
                "type": RecommendationType.LIFESTYLE_CHANGE,
                "actions": [
                    "Monitor blood glucose regularly",
                    "Follow diabetic diet plan",
                    "Exercise regularly as approved by doctor",
                    "Take medications as prescribed"
                ]
            },
            "hypertension": {
                "title": "Blood Pressure Management",
                "description": "Monitor blood pressure and reduce sodium intake",
                "type": RecommendationType.DIETARY_ADVICE,
                "actions": [
                    "Monitor blood pressure daily",
                    "Reduce sodium intake",
                    "Maintain healthy weight",
                    "Exercise regularly"
                ]
            },
            "infection": {
                "title": "Infection Treatment",
                "description": "Complete antibiotic course and monitor symptoms",
                "type": RecommendationType.FOLLOW_UP_CARE,
                "actions": [
                    "Complete full antibiotic course",
                    "Monitor symptoms",
                    "Rest and stay hydrated",
                    "Follow up with doctor if symptoms worsen"
                ]
            }
        }
        
        condition_lower = condition.lower()
        template = None
        
        for key, tmpl in condition_templates.items():
            if key in condition_lower:
                template = tmpl
                break
        
        if not template:
            # Generic recommendation
            template = {
                "title": f"{condition} Management",
                "description": f"Follow treatment plan for {condition}",
                "type": RecommendationType.FOLLOW_UP_CARE,
                "actions": [
                    "Follow prescribed treatment",
                    "Monitor symptoms",
                    "Schedule follow-up appointments"
                ]
            }
        
        return HealthRecommendation(
            user_id=user_id,
            prescription_id=prescription_id,
            title=template["title"],
            description=template["description"],
            recommendation_type=template["type"],
            priority="medium",
            based_on_conditions=[condition],
            reasoning=f"Recommendation generated for {condition} management",
            action_items=template["actions"],
            timeline="within 1 week"
        )
    
    async def _update_user_health_profile(
        self, 
        user_id: int, 
        prescription_data: PrescriptionData
    ) -> None:
        """Update user's health profile with new information from prescription"""
        
        user_profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not user_profile:
            return
        
        # Update medical conditions
        existing_conditions = user_profile.medical_conditions or []
        new_conditions = []
        
        for condition in prescription_data.conditions:
            if condition not in existing_conditions:
                new_conditions.append(condition)
                existing_conditions.append(condition)
        
        if new_conditions:
            user_profile.medical_conditions = existing_conditions
            user_profile.updated_at = datetime.now()
        
        # Create condition records for tracking
        for condition in prescription_data.conditions:
            existing_condition = self.db.query(ConditionRecord).filter(
                ConditionRecord.user_id == user_id,
                ConditionRecord.condition_name == condition
            ).first()
            
            if not existing_condition:
                condition_record = ConditionRecord(
                    user_id=user_id,
                    prescription_id=prescription_data.prescription_id if hasattr(prescription_data, 'prescription_id') else None,
                    condition_name=condition,
                    source="prescription",
                    confidence_score=prescription_data.confidence_score,
                    diagnosed_date=prescription_data.prescription_date or datetime.now()
                )
                self.db.add(condition_record)
    
    def _create_sync_log(
        self, 
        user_id: int, 
        sync_type: str, 
        entity_type: str, 
        entity_id: int
    ) -> IntegrationSyncLog:
        """Create a sync log entry for tracking"""
        
        sync_log = IntegrationSyncLog(
            user_id=user_id,
            sync_type=sync_type,
            entity_type=entity_type,
            entity_id=entity_id,
            status=SyncStatus.PENDING
        )
        
        self.db.add(sync_log)
        self.db.flush()
        return sync_log
    
    def _complete_sync_log(
        self, 
        sync_log: IntegrationSyncLog, 
        status: SyncStatus, 
        start_time: datetime, 
        error_message: Optional[str] = None
    ) -> None:
        """Complete a sync log entry"""
        
        sync_log.status = status
        sync_log.completed_at = datetime.now()
        sync_log.processing_time_ms = int(
            (sync_log.completed_at - start_time).total_seconds() * 1000
        )
        
        if error_message:
            sync_log.error_message = error_message
    
    async def _send_realtime_notifications(self, user_id: str, prescription_record: PrescriptionRecord, 
                                         recommendations: List[HealthRecommendation]):
        """Send real-time notifications via WebSocket"""
        try:
            # Notify about prescription upload
            prescription_data = {
                "id": prescription_record.id,
                "medications": [med.dict() for med in prescription_record.medications],
                "conditions": [cond.dict() for cond in prescription_record.conditions]
            }
            await sync_service.notify_prescription_uploaded(user_id, prescription_data)
            
            # Notify about new recommendations
            for recommendation in recommendations:
                await sync_service.notify_recommendation_added(user_id, recommendation.dict())
            
            # Update sync status
            await sync_service.notify_sync_status(user_id, "completed", {
                "prescription_id": prescription_record.id,
                "processed_at": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logging.error(f"Failed to send real-time notifications: {e}")
            await sync_service.notify_sync_status(user_id, "notification_failed", {
                "error": str(e)
            })