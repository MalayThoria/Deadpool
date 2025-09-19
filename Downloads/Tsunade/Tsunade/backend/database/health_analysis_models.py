from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, Table, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base
import enum

# Enums for health analysis
class ExerciseCategory(enum.Enum):
    CARDIO = "cardio"
    STRENGTH = "strength"
    FLEXIBILITY = "flexibility"
    BALANCE = "balance"
    REHABILITATION = "rehabilitation"
    LOW_IMPACT = "low_impact"
    BREATHING = "breathing"
    YOGA = "yoga"
    PILATES = "pilates"
    WATER_THERAPY = "water_therapy"

class DifficultyLevel(enum.Enum):
    BEGINNER = "beginner"
    EASY = "easy"
    MODERATE = "moderate"
    CHALLENGING = "challenging"
    ADVANCED = "advanced"

class RecommendationStatus(enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    DISCONTINUED = "discontinued"

class ScheduleFrequency(enum.Enum):
    DAILY = "daily"
    EVERY_OTHER_DAY = "every_other_day"
    THREE_TIMES_WEEK = "three_times_week"
    TWICE_WEEK = "twice_week"
    WEEKLY = "weekly"
    CUSTOM = "custom"

# Association table for many-to-many relationship between exercises and diseases
exercise_disease_association = Table(
    'exercise_disease_mappings',
    Base.metadata,
    Column('exercise_id', Integer, ForeignKey('health_exercises.id'), primary_key=True),
    Column('disease_condition_id', Integer, ForeignKey('disease_conditions.id'), primary_key=True),
    Column('effectiveness_score', Float, default=0.8),  # 0.0 to 1.0
    Column('safety_score', Float, default=0.9),  # 0.0 to 1.0
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

# Disease/Condition Master Database
class DiseaseCondition(Base):
    __tablename__ = "disease_conditions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(String(100), nullable=False)  # cardiovascular, musculoskeletal, etc.
    description = Column(Text)
    severity_levels = Column(JSON)  # ["mild", "moderate", "severe"]
    
    # Exercise considerations
    exercise_restrictions = Column(JSON)  # List of restricted exercise types
    recommended_intensity = Column(String(50))  # low, moderate, high
    special_considerations = Column(Text)  # Medical notes for exercise planning
    
    # Metadata
    is_chronic = Column(Boolean, default=False)
    requires_medical_clearance = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exercises = relationship("HealthExercise", secondary=exercise_disease_association, back_populates="conditions")
    user_recommendations = relationship("PersonalizedExerciseRecommendation", back_populates="condition")

# Exercise Database
class HealthExercise(Base):
    __tablename__ = "health_exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(SQLEnum(ExerciseCategory), nullable=False)
    difficulty_level = Column(SQLEnum(DifficultyLevel), nullable=False)
    
    # Exercise details
    description = Column(Text, nullable=False)
    instructions = Column(JSON)  # Step-by-step instructions
    duration_minutes = Column(Integer)  # Recommended duration
    repetitions = Column(Integer)  # For strength exercises
    sets = Column(Integer)  # For strength exercises
    
    # Equipment and setup
    equipment_needed = Column(JSON)  # List of required equipment
    space_requirements = Column(String(100))  # indoor, outdoor, gym, etc.
    
    # Health benefits and targets
    primary_benefits = Column(JSON)  # List of primary health benefits
    muscle_groups_targeted = Column(JSON)  # List of muscle groups
    calories_per_minute = Column(Float)  # Estimated calories burned per minute
    
    # Safety and contraindications
    contraindications = Column(JSON)  # Conditions where this exercise should be avoided
    modifications = Column(JSON)  # Exercise modifications for different abilities
    safety_tips = Column(JSON)  # Important safety considerations
    
    # Media and resources
    video_url = Column(String(500))  # Link to demonstration video
    image_url = Column(String(500))  # Link to exercise image
    reference_links = Column(JSON)  # Additional educational resources
    
    # Metadata
    is_active = Column(Boolean, default=True)
    medical_approval_required = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    conditions = relationship("DiseaseCondition", secondary=exercise_disease_association, back_populates="exercises")
    recommendations = relationship("PersonalizedExerciseRecommendation", back_populates="exercise")

# Personalized Exercise Recommendations
class PersonalizedExerciseRecommendation(Base):
    __tablename__ = "personalized_exercise_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("health_exercises.id"), nullable=False)
    condition_id = Column(Integer, ForeignKey("disease_conditions.id"), nullable=False)
    
    # Personalization details
    recommended_duration = Column(Integer)  # Personalized duration in minutes
    recommended_frequency = Column(SQLEnum(ScheduleFrequency))
    recommended_intensity = Column(String(50))  # low, moderate, high
    
    # AI-generated insights
    reasoning = Column(Text)  # Why this exercise was recommended
    expected_benefits = Column(JSON)  # Expected benefits for this user
    progress_markers = Column(JSON)  # What to track for progress
    
    # Customizations
    modifications_applied = Column(JSON)  # Any modifications for user's condition
    equipment_alternatives = Column(JSON)  # Alternative equipment options
    
    # Status and tracking
    status = Column(SQLEnum(RecommendationStatus), default=RecommendationStatus.ACTIVE)
    priority_score = Column(Float, default=0.5)  # 0.0 to 1.0, higher = more important
    
    # User interaction
    user_rating = Column(Integer)  # 1-5 star rating from user
    user_feedback = Column(Text)  # User's comments about the exercise
    difficulty_feedback = Column(String(50))  # too_easy, just_right, too_hard
    
    # Scheduling
    start_date = Column(DateTime(timezone=True))
    target_end_date = Column(DateTime(timezone=True))
    last_performed = Column(DateTime(timezone=True))
    next_scheduled = Column(DateTime(timezone=True))
    
    # Progress tracking
    total_sessions_completed = Column(Integer, default=0)
    total_minutes_exercised = Column(Integer, default=0)
    average_user_rating = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    exercise = relationship("HealthExercise", back_populates="recommendations")
    condition = relationship("DiseaseCondition", back_populates="user_recommendations")
    schedules = relationship("ExerciseSchedule", back_populates="recommendation")

# Exercise Schedule and Planning
class ExerciseSchedule(Base):
    __tablename__ = "exercise_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recommendation_id = Column(Integer, ForeignKey("personalized_exercise_recommendations.id"), nullable=False)
    
    # Schedule details
    scheduled_date = Column(DateTime(timezone=True), nullable=False)
    scheduled_duration = Column(Integer)  # Duration in minutes
    scheduled_intensity = Column(String(50))
    
    # Completion tracking
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))
    actual_duration = Column(Integer)  # Actual time spent
    actual_intensity = Column(String(50))  # User-reported intensity
    
    # User feedback
    completion_rating = Column(Integer)  # 1-5 how did it go
    energy_level_before = Column(Integer)  # 1-10 energy before exercise
    energy_level_after = Column(Integer)  # 1-10 energy after exercise
    pain_level_before = Column(Integer)  # 1-10 pain before exercise
    pain_level_after = Column(Integer)  # 1-10 pain after exercise
    notes = Column(Text)  # User's notes about the session
    
    # Reminders and notifications
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    recommendation = relationship("PersonalizedExerciseRecommendation", back_populates="schedules")

# User Health Analysis Profile
class UserHealthAnalysisProfile(Base):
    __tablename__ = "user_health_analysis_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Current health status
    current_conditions = Column(JSON)  # List of current health conditions
    fitness_level = Column(String(50))  # beginner, intermediate, advanced
    exercise_preferences = Column(JSON)  # Preferred types of exercise
    exercise_restrictions = Column(JSON)  # Any exercise restrictions
    
    # Goals and preferences
    primary_goals = Column(JSON)  # weight_loss, strength, flexibility, etc.
    available_time_per_session = Column(Integer)  # Minutes available per session
    preferred_schedule = Column(JSON)  # Days and times preferred
    equipment_available = Column(JSON)  # Equipment user has access to
    
    # Medical considerations
    medical_clearance_date = Column(DateTime(timezone=True))
    healthcare_provider_notes = Column(Text)
    emergency_contact = Column(JSON)  # Emergency contact information
    
    # AI analysis results
    risk_assessment = Column(JSON)  # AI-generated risk assessment
    recommended_approach = Column(Text)  # Overall exercise approach recommendation
    last_analysis_date = Column(DateTime(timezone=True))
    
    # Progress tracking
    baseline_measurements = Column(JSON)  # Initial fitness measurements
    current_measurements = Column(JSON)  # Current fitness measurements
    progress_photos = Column(JSON)  # References to progress photos
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships