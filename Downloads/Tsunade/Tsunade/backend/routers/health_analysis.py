"""
Health Analysis API Router
Provides endpoints for personalized exercise recommendations based on health conditions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from database.config import get_db
from services.health_analysis_service import HealthAnalysisService
from auth.auth import current_active_user
from database.models import User

router = APIRouter(prefix="/health-analysis", tags=["Health Analysis"])

# Pydantic models for request/response
class DiseaseConditionResponse(BaseModel):
    id: int
    name: str
    category: str
    description: str
    severity_levels: List[str]
    requires_medical_clearance: bool
    is_chronic: bool

class UserHealthProfileRequest(BaseModel):
    current_conditions: List[str] = Field(..., description="List of current health conditions")
    fitness_level: str = Field(..., description="User's fitness level: beginner, intermediate, advanced")
    exercise_preferences: List[str] = Field(default=[], description="Preferred exercise categories")
    exercise_restrictions: List[str] = Field(default=[], description="Any exercise restrictions")
    primary_goals: List[str] = Field(..., description="Primary fitness/health goals")
    available_time_per_session: int = Field(..., description="Available time per session in minutes")
    preferred_schedule: Dict = Field(default={}, description="Preferred days and times")
    equipment_available: List[str] = Field(default=[], description="Available equipment")
    medical_clearance_date: Optional[datetime] = Field(default=None, description="Date of medical clearance")
    healthcare_provider_notes: Optional[str] = Field(default=None, description="Notes from healthcare provider")

class ExerciseRecommendationRequest(BaseModel):
    condition_ids: List[int] = Field(..., description="List of disease condition IDs")
    user_preferences: Optional[Dict] = Field(default=None, description="Additional user preferences")

class ExerciseRecommendationResponse(BaseModel):
    id: int
    exercise: Dict
    condition: Dict
    personalization: Dict
    reasoning: str
    priority_score: float
    status: str
    created_at: Optional[str]

class RecommendationFeedbackRequest(BaseModel):
    user_rating: Optional[int] = Field(default=None, ge=1, le=5, description="User rating 1-5")
    user_feedback: Optional[str] = Field(default=None, description="User's text feedback")
    difficulty_feedback: Optional[str] = Field(default=None, description="too_easy, just_right, too_hard")
    status: Optional[str] = Field(default=None, description="active, completed, paused, discontinued")

class ScheduleExerciseRequest(BaseModel):
    recommendation_id: int = Field(..., description="Exercise recommendation ID")
    scheduled_date: datetime = Field(..., description="When to schedule the exercise")
    scheduled_duration: Optional[int] = Field(default=None, description="Planned duration in minutes")
    scheduled_intensity: Optional[str] = Field(default=None, description="Planned intensity level")

class ExerciseCompletionRequest(BaseModel):
    schedule_id: int = Field(..., description="Exercise schedule ID")
    actual_duration: Optional[int] = Field(default=None, description="Actual time spent in minutes")
    actual_intensity: Optional[str] = Field(default=None, description="Actual intensity level")
    completion_rating: Optional[int] = Field(default=None, ge=1, le=5, description="How did it go? 1-5")
    energy_level_before: Optional[int] = Field(default=None, ge=1, le=10, description="Energy before 1-10")
    energy_level_after: Optional[int] = Field(default=None, ge=1, le=10, description="Energy after 1-10")
    pain_level_before: Optional[int] = Field(default=None, ge=1, le=10, description="Pain before 1-10")
    pain_level_after: Optional[int] = Field(default=None, ge=1, le=10, description="Pain after 1-10")
    notes: Optional[str] = Field(default=None, description="User's notes about the session")

@router.get("/conditions", response_model=List[DiseaseConditionResponse])
async def get_disease_conditions(
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all available disease conditions or search by query"""
    service = HealthAnalysisService(db)
    
    if search:
        conditions = service.search_disease_conditions(search)
    else:
        conditions = service.get_all_disease_conditions()
    
    return conditions

@router.post("/profile")
async def create_health_profile(
    profile_data: UserHealthProfileRequest,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Create or update user's health analysis profile"""
    service = HealthAnalysisService(db)
    
    try:
        profile = service.create_user_health_profile(
            user_id=current_user.id,
            profile_data=profile_data.dict()
        )
        return {
            "message": "Health profile created/updated successfully",
            "profile": profile
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating health profile: {str(e)}"
        )

@router.post("/recommendations", response_model=List[ExerciseRecommendationResponse])
async def generate_exercise_recommendations(
    request: ExerciseRecommendationRequest,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Generate personalized exercise recommendations based on health conditions"""
    service = HealthAnalysisService(db)
    
    try:
        recommendations = service.generate_exercise_recommendations(
            user_id=current_user.id,
            condition_ids=request.condition_ids,
            user_preferences=request.user_preferences
        )
        
        if not recommendations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No suitable exercises found for the specified conditions"
            )
        
        return recommendations
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )

@router.get("/recommendations", response_model=List[ExerciseRecommendationResponse])
async def get_user_recommendations(
    status_filter: Optional[str] = None,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's exercise recommendations"""
    service = HealthAnalysisService(db)
    
    try:
        recommendations = service.get_user_recommendations(
            user_id=current_user.id,
            status=status_filter
        )
        return recommendations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving recommendations: {str(e)}"
        )

@router.put("/recommendations/{recommendation_id}/feedback")
async def update_recommendation_feedback(
    recommendation_id: int,
    feedback: RecommendationFeedbackRequest,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Update recommendation with user feedback"""
    service = HealthAnalysisService(db)
    
    try:
        updated_recommendation = service.update_recommendation_feedback(
            recommendation_id=recommendation_id,
            feedback_data=feedback.dict(exclude_unset=True)
        )
        return {
            "message": "Feedback updated successfully",
            "recommendation": updated_recommendation
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating feedback: {str(e)}"
        )

@router.post("/schedule")
async def schedule_exercise(
    request: ScheduleExerciseRequest,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Schedule an exercise session"""
    from database.health_analysis_models import ExerciseSchedule, PersonalizedExerciseRecommendation
    
    # Verify recommendation belongs to user
    recommendation = db.query(PersonalizedExerciseRecommendation).filter(
        PersonalizedExerciseRecommendation.id == request.recommendation_id,
        PersonalizedExerciseRecommendation.user_id == current_user.id
    ).first()
    
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found"
        )
    
    try:
        # Create schedule entry
        schedule = ExerciseSchedule(
            user_id=current_user.id,
            recommendation_id=request.recommendation_id,
            scheduled_date=request.scheduled_date,
            scheduled_duration=request.scheduled_duration or recommendation.recommended_duration,
            scheduled_intensity=request.scheduled_intensity or recommendation.recommended_intensity
        )
        
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        
        return {
            "message": "Exercise scheduled successfully",
            "schedule": {
                "id": schedule.id,
                "scheduled_date": schedule.scheduled_date.isoformat(),
                "scheduled_duration": schedule.scheduled_duration,
                "scheduled_intensity": schedule.scheduled_intensity,
                "exercise_name": recommendation.exercise.name
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scheduling exercise: {str(e)}"
        )

@router.get("/schedule")
async def get_exercise_schedule(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's exercise schedule"""
    from database.health_analysis_models import ExerciseSchedule
    from sqlalchemy import and_
    
    query = db.query(ExerciseSchedule).filter(
        ExerciseSchedule.user_id == current_user.id
    )
    
    if start_date:
        query = query.filter(ExerciseSchedule.scheduled_date >= start_date)
    
    if end_date:
        query = query.filter(ExerciseSchedule.scheduled_date <= end_date)
    
    schedules = query.order_by(ExerciseSchedule.scheduled_date).all()
    
    return [
        {
            "id": schedule.id,
            "exercise_name": schedule.recommendation.exercise.name,
            "condition_name": schedule.recommendation.condition.name,
            "scheduled_date": schedule.scheduled_date.isoformat(),
            "scheduled_duration": schedule.scheduled_duration,
            "scheduled_intensity": schedule.scheduled_intensity,
            "is_completed": schedule.is_completed,
            "completed_at": schedule.completed_at.isoformat() if schedule.completed_at else None,
            "completion_rating": schedule.completion_rating
        }
        for schedule in schedules
    ]

@router.put("/schedule/{schedule_id}/complete")
async def complete_exercise_session(
    schedule_id: int,
    completion_data: ExerciseCompletionRequest,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Mark an exercise session as completed with feedback"""
    from database.health_analysis_models import ExerciseSchedule
    
    schedule = db.query(ExerciseSchedule).filter(
        ExerciseSchedule.id == schedule_id,
        ExerciseSchedule.user_id == current_user.id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise schedule not found"
        )
    
    try:
        # Update schedule with completion data
        schedule.is_completed = True
        schedule.completed_at = datetime.utcnow()
        
        completion_dict = completion_data.dict(exclude_unset=True, exclude={'schedule_id'})
        for key, value in completion_dict.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)
        
        # Update recommendation stats
        recommendation = schedule.recommendation
        recommendation.total_sessions_completed += 1
        if completion_data.actual_duration:
            recommendation.total_minutes_exercised += completion_data.actual_duration
        
        if completion_data.completion_rating:
            # Update average rating
            if recommendation.average_user_rating:
                total_ratings = recommendation.total_sessions_completed
                new_average = ((recommendation.average_user_rating * (total_ratings - 1)) + 
                             completion_data.completion_rating) / total_ratings
                recommendation.average_user_rating = new_average
            else:
                recommendation.average_user_rating = float(completion_data.completion_rating)
        
        recommendation.last_performed = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "Exercise session completed successfully",
            "completion": {
                "id": schedule.id,
                "completed_at": schedule.completed_at.isoformat(),
                "actual_duration": schedule.actual_duration,
                "completion_rating": schedule.completion_rating,
                "total_sessions": recommendation.total_sessions_completed
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error completing exercise session: {str(e)}"
        )

@router.get("/analytics")
async def get_user_analytics(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's exercise analytics and progress"""
    from database.health_analysis_models import PersonalizedExerciseRecommendation, ExerciseSchedule
    from sqlalchemy import func
    
    try:
        # Get recommendation stats
        recommendation_stats = db.query(
            func.count(PersonalizedExerciseRecommendation.id).label('total_recommendations'),
            func.sum(PersonalizedExerciseRecommendation.total_sessions_completed).label('total_sessions'),
            func.sum(PersonalizedExerciseRecommendation.total_minutes_exercised).label('total_minutes'),
            func.avg(PersonalizedExerciseRecommendation.average_user_rating).label('avg_rating')
        ).filter(
            PersonalizedExerciseRecommendation.user_id == current_user.id
        ).first()
        
        # Get recent activity
        recent_sessions = db.query(ExerciseSchedule).filter(
            ExerciseSchedule.user_id == current_user.id,
            ExerciseSchedule.is_completed == True
        ).order_by(ExerciseSchedule.completed_at.desc()).limit(10).all()
        
        # Get upcoming schedule
        upcoming_sessions = db.query(ExerciseSchedule).filter(
            ExerciseSchedule.user_id == current_user.id,
            ExerciseSchedule.is_completed == False,
            ExerciseSchedule.scheduled_date >= datetime.utcnow()
        ).order_by(ExerciseSchedule.scheduled_date).limit(5).all()
        
        return {
            "summary": {
                "total_recommendations": recommendation_stats.total_recommendations or 0,
                "total_sessions_completed": recommendation_stats.total_sessions or 0,
                "total_minutes_exercised": recommendation_stats.total_minutes or 0,
                "average_rating": round(recommendation_stats.avg_rating or 0, 2)
            },
            "recent_sessions": [
                {
                    "exercise_name": session.recommendation.exercise.name,
                    "completed_at": session.completed_at.isoformat(),
                    "duration": session.actual_duration,
                    "rating": session.completion_rating
                }
                for session in recent_sessions
            ],
            "upcoming_sessions": [
                {
                    "exercise_name": session.recommendation.exercise.name,
                    "scheduled_date": session.scheduled_date.isoformat(),
                    "duration": session.scheduled_duration
                }
                for session in upcoming_sessions
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving analytics: {str(e)}"
        )