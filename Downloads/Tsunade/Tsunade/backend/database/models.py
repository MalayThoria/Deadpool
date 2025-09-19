from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from cryptography.fernet import Fernet
import os
from .health_analysis_models import (
    DiseaseCondition, HealthExercise, PersonalizedExerciseRecommendation,
    ExerciseSchedule, UserHealthAnalysisProfile, ExerciseCategory,
    DifficultyLevel, ScheduleFrequency, exercise_disease_association
)
from database.config import Base

# Encryption setup for GDPR/HIPAA compliance
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

# Enums for structured data
class FitnessLevel(enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    ATHLETE = "athlete"

class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

class DiseaseSeverity(enum.Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"

class ExerciseIntensity(enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class EventFrequency(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

class UserRole(enum.Enum):
    PATIENT = "patient"
    ADMIN = "admin"
    HEALTHCARE_PROVIDER = "healthcare_provider"

# Helper functions for encryption
def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data for GDPR/HIPAA compliance"""
    if not data:
        return data
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data"""
    if not encrypted_data:
        return encrypted_data
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PATIENT)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # OAuth fields
    google_id = Column(String(255), unique=True, nullable=True)
    facebook_id = Column(String(255), unique=True, nullable=True)
    
    # GDPR compliance
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime(timezone=True))
    data_retention_date = Column(DateTime(timezone=True))
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    medicine_history = relationship("MedicineHistory", back_populates="user", cascade="all, delete-orphan")
    disease_history = relationship("DiseaseHistory", back_populates="user", cascade="all, delete-orphan")
    exercise_logs = relationship("ExerciseLog", back_populates="user", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Basic demographics
    first_name = Column(String(100))
    last_name = Column(String(100))
    age = Column(Integer)
    gender = Column(Enum(Gender))
    
    # Physical attributes
    weight = Column(Float)  # in kg
    height = Column(Float)  # in cm
    bmi = Column(Float, nullable=True)  # calculated field
    
    # Fitness information
    fitness_level = Column(Enum(FitnessLevel), default=FitnessLevel.BEGINNER)
    activity_goals = Column(JSON)  # {"weekly_minutes": 150, "sessions_per_week": 3}
    
    # Medical information (encrypted)
    medical_conditions = Column(JSON)  # List of conditions (stored as JSON for SQLite compatibility)
    allergies = Column(Text)  # Encrypted
    medications = Column(Text)  # Encrypted
    emergency_contact = Column(Text)  # Encrypted
    
    # Preferences
    preferences = Column(JSON)  # Exercise preferences, notification settings, etc.
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")

class MedicineHistory(Base):
    __tablename__ = "medicine_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Medicine information
    medicine_name = Column(String(255), nullable=False)
    dosage = Column(String(100))
    frequency = Column(String(100))
    duration = Column(String(100))
    
    # Additional details (encrypted for sensitive info)
    side_effects = Column(JSON)  # List of reported side effects
    interactions = Column(JSON)  # Drug interactions
    prescription_text = Column(Text)  # Original OCR text (encrypted)
    prescription_image_ref = Column(String(255))  # Reference to image in MongoDB
    
    # Metadata
    prescribed_by = Column(String(255))  # Doctor name (encrypted)
    prescribed_date = Column(DateTime(timezone=True))
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="medicine_history")

class DiseaseHistory(Base):
    __tablename__ = "disease_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Disease information
    disease_name = Column(String(255), nullable=False)
    severity = Column(Enum(DiseaseSeverity), default=DiseaseSeverity.MILD)
    diagnosis_date = Column(DateTime(timezone=True))
    
    # Additional details
    symptoms = Column(JSON)  # List of symptoms
    notes = Column(Text)  # Doctor notes (encrypted)
    treatment_plan = Column(Text)  # Treatment details (encrypted)
    
    # Status
    is_chronic = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    resolved_date = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="disease_history")

class ExerciseLog(Base):
    __tablename__ = "exercise_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Exercise details
    exercise_name = Column(String(255), nullable=False)
    exercise_type = Column(String(100))  # cardio, strength, flexibility, etc.
    duration_minutes = Column(Integer)
    intensity = Column(Enum(ExerciseIntensity))
    calories_burned = Column(Integer)
    
    # Progress tracking
    completed = Column(Boolean, default=False)
    completion_percentage = Column(Integer, default=0)
    user_feedback = Column(Text)  # User notes about the exercise
    difficulty_rating = Column(Integer)  # 1-5 scale
    
    # Scheduling
    scheduled_date = Column(DateTime(timezone=True))
    completed_date = Column(DateTime(timezone=True))
    
    # Metadata
    exercise_plan_id = Column(String(100))  # Reference to exercise plan
    recommended_by_ai = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="exercise_logs")

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Google Calendar integration
    google_event_id = Column(String(255), unique=True)
    calendar_id = Column(String(255))  # Google Calendar ID
    
    # Event details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    start_datetime = Column(DateTime(timezone=True), nullable=False)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    
    # Exercise reference
    exercise_log_id = Column(Integer, ForeignKey("exercise_logs.id"))
    exercise_type = Column(String(100))
    
    # Recurrence
    frequency = Column(Enum(EventFrequency), default=EventFrequency.DAILY)
    recurrence_rule = Column(String(255))  # RRULE format
    
    # Status
    is_active = Column(Boolean, default=True)
    is_synced = Column(Boolean, default=False)
    last_sync = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="calendar_events")
    exercise_log = relationship("ExerciseLog")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Audit information
    action = Column(String(100), nullable=False)  # CREATE, READ, UPDATE, DELETE
    resource = Column(String(100), nullable=False)  # table/resource name
    resource_id = Column(String(100))  # ID of the affected resource
    
    # Details
    old_values = Column(JSON)  # Previous values (for updates/deletes)
    new_values = Column(JSON)  # New values (for creates/updates)
    ip_address = Column(String(45))  # IPv4/IPv6
    user_agent = Column(String(500))
    
    # GDPR compliance
    data_classification = Column(String(50))  # personal, sensitive, public
    retention_date = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Notification channels
    email_enabled = Column(Boolean, default=True)
    push_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    
    # Notification types
    exercise_reminders = Column(Boolean, default=True)
    medicine_reminders = Column(Boolean, default=True)
    health_insights = Column(Boolean, default=True)
    weekly_reports = Column(Boolean, default=True)
    
    # Timing preferences
    preferred_time = Column(String(10))  # HH:MM format
    timezone = Column(String(50), default="UTC")
    
    # Firebase Cloud Messaging
    fcm_token = Column(String(255))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")

# MongoDB document schemas (for reference)
"""
ChatSession Document Schema:
{
    "_id": ObjectId,
    "user_id": int,
    "session_id": str,
    "messages": [
        {
            "role": "user" | "assistant",
            "content": str,
            "timestamp": datetime,
            "message_id": str
        }
    ],
    "context": {
        "current_medicines": [str],
        "current_conditions": [str],
        "user_profile_summary": dict
    },
    "created_at": datetime,
    "updated_at": datetime,
    "is_active": bool
}

PrescriptionImage Document Schema:
{
    "_id": ObjectId,
    "user_id": int,
    "medicine_history_id": int,
    "image_data": str,  # base64 encoded
    "image_metadata": {
        "filename": str,
        "size": int,
        "format": str,
        "upload_timestamp": datetime
    },
    "ocr_results": {
        "extracted_text": str,
        "confidence_score": float,
        "processing_time": float
    },
    "created_at": datetime
}

ProgressLog Document Schema:
{
    "_id": ObjectId,
    "user_id": int,
    "date": datetime,
    "metrics": {
        "exercises_completed": int,
        "total_exercise_time": int,
        "calories_burned": int,
        "health_score": float,
        "medication_adherence": float
    },
    "achievements": [str],
    "insights": [str],
    "created_at": datetime
}
"""