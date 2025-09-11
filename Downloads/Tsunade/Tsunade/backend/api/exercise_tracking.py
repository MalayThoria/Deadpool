from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from pydantic import BaseModel, Field
from uuid import UUID
import uuid
import json

from database.config import get_sync_db
from database.models import User, ExerciseLog, UserProfile
from auth.auth import current_active_user

router = APIRouter()

# Pydantic models
class ExerciseCreate(BaseModel):
    exercise_type: str = Field(..., min_length=1, max_length=100)
    duration_minutes: int = Field(..., ge=1, le=600)  # 1 minute to 10 hours
    intensity: str = Field(..., pattern="^(low|moderate|high|very_high)$")
    calories_burned: Optional[int] = Field(None, ge=0, le=2000)
    notes: Optional[str] = Field(None, max_length=500)
    date_performed: Optional[date] = None
    heart_rate_avg: Optional[int] = Field(None, ge=40, le=220)
    heart_rate_max: Optional[int] = Field(None, ge=40, le=220)
    distance_km: Optional[float] = Field(None, ge=0, le=1000)
    steps: Optional[int] = Field(None, ge=0, le=100000)
    sets: Optional[int] = Field(None, ge=1, le=50)
    reps: Optional[int] = Field(None, ge=1, le=1000)
    weight_kg: Optional[float] = Field(None, ge=0, le=500)
    equipment_used: Optional[List[str]] = None
    location: Optional[str] = Field(None, max_length=100)
    weather_conditions: Optional[str] = Field(None, max_length=100)
    mood_before: Optional[str] = Field(None, pattern="^(very_poor|poor|fair|good|excellent)$")
    mood_after: Optional[str] = Field(None, pattern="^(very_poor|poor|fair|good|excellent)$")
    difficulty_level: Optional[int] = Field(None, ge=1, le=10)
    enjoyment_level: Optional[int] = Field(None, ge=1, le=10)

class ExerciseUpdate(BaseModel):
    exercise_type: Optional[str] = Field(None, min_length=1, max_length=100)
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    intensity: Optional[str] = Field(None, pattern="^(low|moderate|high|very_high)$")
    calories_burned: Optional[int] = Field(None, ge=0, le=2000)
    notes: Optional[str] = Field(None, max_length=500)
    heart_rate_avg: Optional[int] = Field(None, ge=40, le=220)
    heart_rate_max: Optional[int] = Field(None, ge=40, le=220)
    distance_km: Optional[float] = Field(None, ge=0, le=1000)
    steps: Optional[int] = Field(None, ge=0, le=100000)
    sets: Optional[int] = Field(None, ge=1, le=50)
    reps: Optional[int] = Field(None, ge=1, le=1000)
    weight_kg: Optional[float] = Field(None, ge=0, le=500)
    equipment_used: Optional[List[str]] = None
    location: Optional[str] = Field(None, max_length=100)
    weather_conditions: Optional[str] = Field(None, max_length=100)
    mood_before: Optional[str] = Field(None, pattern="^(very_poor|poor|fair|good|excellent)$")
    mood_after: Optional[str] = Field(None, pattern="^(very_poor|poor|fair|good|excellent)$")
    difficulty_level: Optional[int] = Field(None, ge=1, le=10)
    enjoyment_level: Optional[int] = Field(None, ge=1, le=10)

class ExerciseResponse(BaseModel):
    id: UUID
    exercise_type: str
    duration_minutes: int
    intensity: str
    calories_burned: Optional[int]
    notes: Optional[str]
    date_performed: date
    heart_rate_avg: Optional[int]
    heart_rate_max: Optional[int]
    distance_km: Optional[float]
    steps: Optional[int]
    sets: Optional[int]
    reps: Optional[int]
    weight_kg: Optional[float]
    equipment_used: Optional[List[str]]
    location: Optional[str]
    weather_conditions: Optional[str]
    mood_before: Optional[str]
    mood_after: Optional[str]
    difficulty_level: Optional[int]
    enjoyment_level: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExerciseStats(BaseModel):
    total_exercises: int
    total_duration_minutes: int
    total_calories_burned: int
    average_duration: float
    average_calories_per_session: float
    most_common_exercise: str
    most_common_intensity: str
    total_distance_km: float
    total_steps: int
    streak_days: int
    exercises_this_week: int
    exercises_this_month: int

class WeeklyProgress(BaseModel):
    week_start: date
    week_end: date
    total_exercises: int
    total_duration: int
    total_calories: int
    average_intensity: str
    exercise_types: List[str]
    daily_breakdown: Dict[str, Dict[str, Any]]

class ExerciseGoal(BaseModel):
    goal_type: str  # 'duration', 'frequency', 'calories', 'distance'
    target_value: float
    period: str  # 'daily', 'weekly', 'monthly'
    current_progress: float
    percentage_complete: float
    is_achieved: bool

class ExerciseRecommendation(BaseModel):
    exercise_type: str
    recommended_duration: int
    recommended_intensity: str
    reason: str
    benefits: List[str]
    precautions: List[str]
    equipment_needed: List[str]
    difficulty_level: int

# Helper functions
def calculate_calories_burned(exercise_type: str, duration_minutes: int, intensity: str, user_weight_kg: float = 70) -> int:
    """Calculate estimated calories burned based on exercise parameters"""
    # MET (Metabolic Equivalent of Task) values for different exercises
    met_values = {
        'walking': {'low': 2.5, 'moderate': 3.5, 'high': 4.5, 'very_high': 5.0},
        'running': {'low': 6.0, 'moderate': 8.0, 'high': 10.0, 'very_high': 12.0},
        'cycling': {'low': 4.0, 'moderate': 6.0, 'high': 8.0, 'very_high': 10.0},
        'swimming': {'low': 4.0, 'moderate': 6.0, 'high': 8.0, 'very_high': 10.0},
        'strength_training': {'low': 3.0, 'moderate': 4.5, 'high': 6.0, 'very_high': 8.0},
        'yoga': {'low': 2.0, 'moderate': 3.0, 'high': 4.0, 'very_high': 4.5},
        'pilates': {'low': 2.5, 'moderate': 3.5, 'high': 4.5, 'very_high': 5.0},
        'dancing': {'low': 3.0, 'moderate': 4.5, 'high': 6.0, 'very_high': 7.5},
        'basketball': {'low': 4.0, 'moderate': 6.0, 'high': 8.0, 'very_high': 10.0},
        'tennis': {'low': 4.0, 'moderate': 6.0, 'high': 8.0, 'very_high': 9.0},
        'soccer': {'low': 5.0, 'moderate': 7.0, 'high': 9.0, 'very_high': 11.0},
        'hiking': {'low': 3.5, 'moderate': 5.0, 'high': 6.5, 'very_high': 8.0},
        'rowing': {'low': 4.0, 'moderate': 6.0, 'high': 8.5, 'very_high': 11.0},
        'boxing': {'low': 5.0, 'moderate': 7.0, 'high': 9.0, 'very_high': 12.0}
    }
    
    # Default MET value if exercise type not found
    default_met = {'low': 3.0, 'moderate': 4.5, 'high': 6.0, 'very_high': 8.0}
    
    exercise_met = met_values.get(exercise_type.lower(), default_met)
    met_value = exercise_met.get(intensity, exercise_met['moderate'])
    
    # Calories = MET × weight (kg) × time (hours)
    calories = met_value * user_weight_kg * (duration_minutes / 60)
    
    return int(round(calories))

def get_exercise_recommendations(user_profile: UserProfile, recent_exercises: List[ExerciseLog]) -> List[ExerciseRecommendation]:
    """Generate personalized exercise recommendations"""
    recommendations = []
    
    # Analyze recent exercise patterns
    recent_types = [ex.exercise_type for ex in recent_exercises[-10:]]  # Last 10 exercises
    type_counts = {}
    for ex_type in recent_types:
        type_counts[ex_type] = type_counts.get(ex_type, 0) + 1
    
    # Base recommendations based on fitness level and health conditions
    base_recommendations = [
        {
            'exercise_type': 'walking',
            'recommended_duration': 30,
            'recommended_intensity': 'moderate',
            'reason': 'Low-impact cardiovascular exercise suitable for all fitness levels',
            'benefits': ['Improves cardiovascular health', 'Low injury risk', 'Accessible anywhere'],
            'precautions': ['Wear proper footwear', 'Stay hydrated'],
            'equipment_needed': ['Comfortable shoes'],
            'difficulty_level': 2
        },
        {
            'exercise_type': 'strength_training',
            'recommended_duration': 45,
            'recommended_intensity': 'moderate',
            'reason': 'Build muscle strength and bone density',
            'benefits': ['Increases muscle mass', 'Improves bone density', 'Boosts metabolism'],
            'precautions': ['Use proper form', 'Start with lighter weights', 'Allow rest days'],
            'equipment_needed': ['Dumbbells or resistance bands'],
            'difficulty_level': 4
        },
        {
            'exercise_type': 'yoga',
            'recommended_duration': 30,
            'recommended_intensity': 'low',
            'reason': 'Improve flexibility, balance, and mental well-being',
            'benefits': ['Increases flexibility', 'Reduces stress', 'Improves balance'],
            'precautions': ['Listen to your body', 'Modify poses as needed'],
            'equipment_needed': ['Yoga mat'],
            'difficulty_level': 2
        }
    ]
    
    # Add variety recommendations (exercises not done recently)
    if 'swimming' not in recent_types:
        base_recommendations.append({
            'exercise_type': 'swimming',
            'recommended_duration': 30,
            'recommended_intensity': 'moderate',
            'reason': 'Full-body, low-impact exercise',
            'benefits': ['Works all muscle groups', 'Easy on joints', 'Great cardio'],
            'precautions': ['Ensure pool safety', 'Start slowly if new to swimming'],
            'equipment_needed': ['Swimwear', 'Access to pool'],
            'difficulty_level': 3
        })
    
    if 'cycling' not in recent_types:
        base_recommendations.append({
            'exercise_type': 'cycling',
            'recommended_duration': 45,
            'recommended_intensity': 'moderate',
            'reason': 'Low-impact cardiovascular exercise',
            'benefits': ['Improves leg strength', 'Great cardio workout', 'Environmentally friendly transport'],
            'precautions': ['Wear helmet', 'Check bike condition', 'Follow traffic rules'],
            'equipment_needed': ['Bicycle', 'Helmet'],
            'difficulty_level': 3
        })
    
    # Convert to Pydantic models
    for rec in base_recommendations[:5]:  # Limit to 5 recommendations
        recommendations.append(ExerciseRecommendation(**rec))
    
    return recommendations

# API Endpoints
@router.post("/exercises", response_model=ExerciseResponse)
async def create_exercise_log(
    exercise_data: ExerciseCreate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Create a new exercise log entry"""
    try:
        # Get user profile for calorie calculation
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        user_weight = user_profile.weight if user_profile and user_profile.weight else 70.0
        
        # Auto-calculate calories if not provided
        if not exercise_data.calories_burned:
            exercise_data.calories_burned = calculate_calories_burned(
                exercise_data.exercise_type,
                exercise_data.duration_minutes,
                exercise_data.intensity,
                user_weight
            )
        
        # Set date if not provided
        if not exercise_data.date_performed:
            exercise_data.date_performed = date.today()
        
        # Create exercise log
        exercise_log = ExerciseLog(
            id=uuid.uuid4(),
            user_id=current_user.id,
            **exercise_data.dict()
        )
        
        db.add(exercise_log)
        db.commit()
        db.refresh(exercise_log)
        
        return exercise_log
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create exercise log: {str(e)}"
        )

@router.get("/exercises", response_model=List[ExerciseResponse])
async def get_exercise_logs(
    skip: int = 0,
    limit: int = 50,
    exercise_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    intensity: Optional[str] = None,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get exercise logs with filtering options"""
    try:
        query = db.query(ExerciseLog).filter(ExerciseLog.user_id == current_user.id)
        
        # Apply filters
        if exercise_type:
            query = query.filter(ExerciseLog.exercise_type.ilike(f"%{exercise_type}%"))
        
        if start_date:
            query = query.filter(ExerciseLog.date_performed >= start_date)
        
        if end_date:
            query = query.filter(ExerciseLog.date_performed <= end_date)
        
        if intensity:
            query = query.filter(ExerciseLog.intensity == intensity)
        
        # Order by date descending
        query = query.order_by(desc(ExerciseLog.date_performed), desc(ExerciseLog.created_at))
        
        # Apply pagination
        exercises = query.offset(skip).limit(limit).all()
        
        return exercises
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch exercise logs: {str(e)}"
        )

@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise_log(
    exercise_id: UUID,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get a specific exercise log"""
    try:
        exercise = db.query(ExerciseLog).filter(
            and_(
                ExerciseLog.id == exercise_id,
                ExerciseLog.user_id == current_user.id
            )
        ).first()
        
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise log not found"
            )
        
        return exercise
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch exercise log: {str(e)}"
        )

@router.put("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise_log(
    exercise_id: UUID,
    exercise_update: ExerciseUpdate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Update an exercise log"""
    try:
        exercise = db.query(ExerciseLog).filter(
            and_(
                ExerciseLog.id == exercise_id,
                ExerciseLog.user_id == current_user.id
            )
        ).first()
        
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise log not found"
            )
        
        # Update fields
        update_data = exercise_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(exercise, field, value)
        
        exercise.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(exercise)
        
        return exercise
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update exercise log: {str(e)}"
        )

@router.delete("/exercises/{exercise_id}")
async def delete_exercise_log(
    exercise_id: UUID,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Delete an exercise log"""
    try:
        exercise = db.query(ExerciseLog).filter(
            and_(
                ExerciseLog.id == exercise_id,
                ExerciseLog.user_id == current_user.id
            )
        ).first()
        
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise log not found"
            )
        
        db.delete(exercise)
        db.commit()
        
        return {"message": "Exercise log deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete exercise log: {str(e)}"
        )

@router.get("/exercises/stats", response_model=ExerciseStats)
async def get_exercise_stats(
    days: int = 30,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get exercise statistics for the specified period"""
    try:
        start_date = date.today() - timedelta(days=days)
        
        exercises = db.query(ExerciseLog).filter(
            and_(
                ExerciseLog.user_id == current_user.id,
                ExerciseLog.date_performed >= start_date
            )
        ).all()
        
        if not exercises:
            return ExerciseStats(
                total_exercises=0,
                total_duration_minutes=0,
                total_calories_burned=0,
                average_duration=0,
                average_calories_per_session=0,
                most_common_exercise="None",
                most_common_intensity="None",
                total_distance_km=0,
                total_steps=0,
                streak_days=0,
                exercises_this_week=0,
                exercises_this_month=0
            )
        
        # Calculate statistics
        total_exercises = len(exercises)
        total_duration = sum(ex.duration_minutes for ex in exercises)
        total_calories = sum(ex.calories_burned or 0 for ex in exercises)
        total_distance = sum(ex.distance_km or 0 for ex in exercises)
        total_steps = sum(ex.steps or 0 for ex in exercises)
        
        # Most common exercise and intensity
        exercise_types = [ex.exercise_type for ex in exercises]
        intensities = [ex.intensity for ex in exercises]
        
        most_common_exercise = max(set(exercise_types), key=exercise_types.count) if exercise_types else "None"
        most_common_intensity = max(set(intensities), key=intensities.count) if intensities else "None"
        
        # Calculate streak
        exercise_dates = sorted(set(ex.date_performed for ex in exercises), reverse=True)
        streak_days = 0
        current_date = date.today()
        
        for exercise_date in exercise_dates:
            if exercise_date == current_date or exercise_date == current_date - timedelta(days=streak_days):
                streak_days += 1
                current_date = exercise_date
            else:
                break
        
        # This week and month counts
        week_start = date.today() - timedelta(days=date.today().weekday())
        month_start = date.today().replace(day=1)
        
        exercises_this_week = len([ex for ex in exercises if ex.date_performed >= week_start])
        exercises_this_month = len([ex for ex in exercises if ex.date_performed >= month_start])
        
        return ExerciseStats(
            total_exercises=total_exercises,
            total_duration_minutes=total_duration,
            total_calories_burned=total_calories,
            average_duration=total_duration / total_exercises if total_exercises > 0 else 0,
            average_calories_per_session=total_calories / total_exercises if total_exercises > 0 else 0,
            most_common_exercise=most_common_exercise,
            most_common_intensity=most_common_intensity,
            total_distance_km=total_distance,
            total_steps=total_steps,
            streak_days=streak_days,
            exercises_this_week=exercises_this_week,
            exercises_this_month=exercises_this_month
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate exercise stats: {str(e)}"
        )

@router.get("/exercises/recommendations", response_model=List[ExerciseRecommendation])
async def get_exercise_recommendations_endpoint(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get personalized exercise recommendations"""
    try:
        # Get user profile
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        # Get recent exercises (last 30 days)
        start_date = date.today() - timedelta(days=30)
        recent_exercises = db.query(ExerciseLog).filter(
            and_(
                ExerciseLog.user_id == current_user.id,
                ExerciseLog.date_performed >= start_date
            )
        ).order_by(desc(ExerciseLog.date_performed)).all()
        
        recommendations = get_exercise_recommendations(user_profile, recent_exercises)
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get exercise recommendations: {str(e)}"
        )

@router.get("/exercises/weekly-progress", response_model=List[WeeklyProgress])
async def get_weekly_progress(
    weeks: int = 4,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get weekly exercise progress for the specified number of weeks"""
    try:
        weekly_progress = []
        
        for week_offset in range(weeks):
            # Calculate week start and end
            week_start = date.today() - timedelta(days=date.today().weekday() + (week_offset * 7))
            week_end = week_start + timedelta(days=6)
            
            # Get exercises for this week
            week_exercises = db.query(ExerciseLog).filter(
                and_(
                    ExerciseLog.user_id == current_user.id,
                    ExerciseLog.date_performed >= week_start,
                    ExerciseLog.date_performed <= week_end
                )
            ).all()
            
            # Calculate weekly stats
            total_exercises = len(week_exercises)
            total_duration = sum(ex.duration_minutes for ex in week_exercises)
            total_calories = sum(ex.calories_burned or 0 for ex in week_exercises)
            exercise_types = list(set(ex.exercise_type for ex in week_exercises))
            
            # Calculate average intensity
            intensities = [ex.intensity for ex in week_exercises]
            intensity_weights = {'low': 1, 'moderate': 2, 'high': 3, 'very_high': 4}
            avg_intensity_weight = sum(intensity_weights.get(i, 2) for i in intensities) / len(intensities) if intensities else 0
            
            if avg_intensity_weight <= 1.5:
                average_intensity = 'low'
            elif avg_intensity_weight <= 2.5:
                average_intensity = 'moderate'
            elif avg_intensity_weight <= 3.5:
                average_intensity = 'high'
            else:
                average_intensity = 'very_high'
            
            # Daily breakdown
            daily_breakdown = {}
            for day_offset in range(7):
                day_date = week_start + timedelta(days=day_offset)
                day_name = day_date.strftime('%A')
                day_exercises = [ex for ex in week_exercises if ex.date_performed == day_date]
                
                daily_breakdown[day_name] = {
                    'date': day_date.isoformat(),
                    'exercises': len(day_exercises),
                    'duration': sum(ex.duration_minutes for ex in day_exercises),
                    'calories': sum(ex.calories_burned or 0 for ex in day_exercises),
                    'types': list(set(ex.exercise_type for ex in day_exercises))
                }
            
            weekly_progress.append(WeeklyProgress(
                week_start=week_start,
                week_end=week_end,
                total_exercises=total_exercises,
                total_duration=total_duration,
                total_calories=total_calories,
                average_intensity=average_intensity,
                exercise_types=exercise_types,
                daily_breakdown=daily_breakdown
            ))
        
        return weekly_progress
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get weekly progress: {str(e)}"
        )
