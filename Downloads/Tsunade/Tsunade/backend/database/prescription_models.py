from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from database.config import Base

# Enums for prescription integration
class PrescriptionStatus(enum.Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    INTEGRATED = "integrated"
    FAILED = "failed"

class RecommendationType(enum.Enum):
    MEDICATION_REMINDER = "medication_reminder"
    LIFESTYLE_CHANGE = "lifestyle_change"
    DIETARY_ADVICE = "dietary_advice"
    EXERCISE_RECOMMENDATION = "exercise_recommendation"
    FOLLOW_UP_CARE = "follow_up_care"
    DRUG_INTERACTION_WARNING = "drug_interaction_warning"

class SyncStatus(enum.Enum):
    PENDING = "pending"
    SYNCED = "synced"
    FAILED = "failed"
    PARTIAL = "partial"

# Enhanced Prescription Model for Integration
class PrescriptionRecord(Base):
    __tablename__ = "prescription_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Original prescription data
    original_text = Column(Text, nullable=False)  # OCR extracted text
    image_reference = Column(String(255))  # Reference to stored image
    
    # Extracted structured data
    medications = Column(JSON, nullable=False)  # Structured medication data
    conditions = Column(JSON, nullable=False)  # Extracted conditions/diseases
    doctor_info = Column(JSON)  # Doctor name, contact, etc.
    prescription_date = Column(DateTime(timezone=True))
    
    # Processing metadata
    extraction_confidence = Column(Float, default=0.0)
    processing_status = Column(Enum(PrescriptionStatus), default=PrescriptionStatus.PENDING)
    error_details = Column(Text)  # Error information if processing failed
    
    # Integration tracking
    last_sync_attempt = Column(DateTime(timezone=True))
    sync_error_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")
    health_recommendations = relationship("HealthRecommendation", back_populates="prescription", cascade="all, delete-orphan")

# Health Recommendations Model
class HealthRecommendation(Base):
    __tablename__ = "health_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prescription_id = Column(Integer, ForeignKey("prescription_records.id"), nullable=True)
    
    # Recommendation details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    recommendation_type = Column(Enum(RecommendationType), nullable=False)
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    
    # Context and reasoning
    based_on_conditions = Column(JSON)  # Conditions that triggered this recommendation
    based_on_medications = Column(JSON)  # Medications that triggered this recommendation
    reasoning = Column(Text)  # AI-generated reasoning for the recommendation
    
    # Implementation details
    action_items = Column(JSON)  # Specific steps user should take
    timeline = Column(String(100))  # When to implement (e.g., "immediately", "within 1 week")
    expected_outcome = Column(Text)  # What user can expect
    
    # Status tracking
    is_active = Column(Boolean, default=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime(timezone=True))
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    
    # Dashboard integration
    display_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    prescription = relationship("PrescriptionRecord", back_populates="health_recommendations")

# Dashboard Entry Model for Real-time Updates
# Condition Tracking Model
class ConditionRecord(Base):
    __tablename__ = "condition_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    prescription_id = Column(Integer, ForeignKey("prescription_records.id"), nullable=True)
    
    # Condition details
    condition_name = Column(String(255), nullable=False)
    condition_code = Column(String(50))  # ICD-10 or similar medical code
    severity = Column(String(20))  # mild, moderate, severe
    
    # Source and validation
    source = Column(String(50), default="prescription")  # prescription, manual, doctor_input
    confidence_score = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100))  # Healthcare provider who verified
    
    # Timeline
    diagnosed_date = Column(DateTime(timezone=True))
    first_detected = Column(DateTime(timezone=True), server_default=func.now())
    
    # Dashboard integration
    is_displayed = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    prescription = relationship("PrescriptionRecord")

# Sync Log for Tracking Integration Events
class IntegrationSyncLog(Base):
    __tablename__ = "integration_sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Sync details
    sync_type = Column(String(50), nullable=False)  # "prescription_upload", "dashboard_update", etc.
    entity_type = Column(String(50), nullable=False)  # "prescription", "recommendation", "condition"
    entity_id = Column(Integer, nullable=False)
    
    # Status and results
    status = Column(Enum(SyncStatus), nullable=False)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Performance metrics
    processing_time_ms = Column(Integer)
    data_size_bytes = Column(Integer)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")