from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field
from uuid import UUID
import uuid

from database.config import get_sync_db
from database.models import ExerciseLog, User
from auth.auth import current_active_user

router = APIRouter()

# Pydantic models
class ExerciseCreate(BaseModel):
    exercise_name: str = Field(..., min_length=1, max_length=200)
    exercise_type: Optional[str] = Field(None, pattern="^(cardio|strength|flexibility|balance|sports|other)$")
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    intensity: Optional[str] = Field(None, pattern="^(low|moderate|high|very_high)$")
    calories_burned: Optional[int] = Field(None, ge=0, le=5000)
    date_performed: date
    feedback: Optional[str] = Field(None, max_length=1000)

class ExerciseUpdate(BaseModel):
    exercise_name: Optional[str] = Field(None, min_length=1, max_length=200)
    exercise_type: Optional[str] = Field(None, pattern="^(cardio|strength|flexibility|balance|sports|other)$")
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    intensity: Optional[str] = Field(None, pattern="^(low|moderate|high|very_high)$")
    calories_burned: Optional[int] = Field(None, ge=0, le=5000)
    completed: Optional[bool] = None
    feedback: Optional[str] = Field(None, max_length=1000)

class ExerciseResponse(BaseModel):
    id: UUID
    exercise_name: str
    exercise_type: Optional[str]
    duration_minutes: Optional[int]
    intensity: Optional[str]
    calories_burned: Optional[int]
    completed: bool
    feedback: Optional[str]
    date_performed: date
    created_at: datetime

    class Config:
        from_attributes = True

class ExerciseStats(BaseModel):
    total_exercises: int
    completed_exercises: int
    total_duration_minutes: int
    total_calories_burned: int
    completion_rate: float
    streak_days: int
    weekly_average: float

class WeeklyReport(BaseModel):
    week_start: date
    week_end: date
    total_exercises: int
    completed_exercises: int
    total_duration: int
    total_calories: int
    daily_breakdown: List[dict]
    insights: List[str]

@router.post("/exercises", response_model=ExerciseResponse)
async def create_exercise_log(
    exercise: ExerciseCreate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Create a new exercise log entry."""
    db_exercise = ExerciseLog(
        id=uuid.uuid4(),
        user_id=current_user.id,
        **exercise.dict()
    )
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise

@router.get("/exercises", response_model=List[ExerciseResponse])
async def get_exercise_logs(
    skip: int = 0,
    limit: int = 50,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    exercise_type: Optional[str] = None,
    completed: Optional[bool] = None,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get exercise logs for the current user with optional filters."""
    query = db.query(ExerciseLog).filter(ExerciseLog.user_id == current_user.id)
    
    if date_from:
        query = query.filter(ExerciseLog.date_performed >= date_from)
    if date_to:
        query = query.filter(ExerciseLog.date_performed <= date_to)
    if exercise_type:
        query = query.filter(ExerciseLog.exercise_type == exercise_type)
    if completed is not None:
        query = query.filter(ExerciseLog.completed == completed)
    
    exercises = query.order_by(desc(ExerciseLog.date_performed)).offset(skip).limit(limit).all()
    return exercises

@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise_log(
    exercise_id: UUID,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get a specific exercise log by ID."""
    exercise = db.query(ExerciseLog).filter(
        and_(ExerciseLog.id == exercise_id, ExerciseLog.user_id == current_user.id)
    ).first()
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise log not found"
        )
    
    return exercise

@router.put("/exercises/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise_log(
    exercise_id: UUID,
    exercise_update: ExerciseUpdate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Update an exercise log."""
    exercise = db.query(ExerciseLog).filter(
        and_(ExerciseLog.id == exercise_id, ExerciseLog.user_id == current_user.id)
    ).first()
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise log not found"
        )
    
    update_data = exercise_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exercise, field, value)
    
    db.commit()
    db.refresh(exercise)
    return exercise

@router.delete("/exercises/{exercise_id}")
async def delete_exercise_log(
    exercise_id: UUID,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Delete an exercise log."""
    exercise = db.query(ExerciseLog).filter(
        and_(ExerciseLog.id == exercise_id, ExerciseLog.user_id == current_user.id)
    ).first()
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise log not found"
        )
    
    db.delete(exercise)
    db.commit()
    return {"message": "Exercise log deleted successfully"}

@router.post("/exercises/{exercise_id}/complete")
async def mark_exercise_complete(
    exercise_id: UUID,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Mark an exercise as completed."""
    exercise = db.query(ExerciseLog).filter(
        and_(ExerciseLog.id == exercise_id, ExerciseLog.user_id == current_user.id)
    ).first()
    
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise log not found"
        )
    
    exercise.completed = True
    db.commit()
    return {"message": "Exercise marked as completed"}

@router.get("/exercises/stats", response_model=ExerciseStats)
async def get_exercise_stats(
    days: int = 30,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get exercise statistics for the specified number of days."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    exercises = db.query(ExerciseLog).filter(
        and_(
            ExerciseLog.user_id == current_user.id,
            ExerciseLog.date_performed >= start_date,
            ExerciseLog.date_performed <= end_date
        )
    ).all()
    
    total_exercises = len(exercises)
    completed_exercises = len([e for e in exercises if e.completed])
    total_duration = sum([e.duration_minutes or 0 for e in exercises])
    total_calories = sum([e.calories_burned or 0 for e in exercises])
    completion_rate = (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0
    
    # Calculate streak
    streak_days = 0
    current_date = date.today()
    while True:
        day_exercises = [e for e in exercises if e.date_performed == current_date and e.completed]
        if day_exercises:
            streak_days += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    weekly_average = total_exercises / (days / 7) if days >= 7 else total_exercises
    
    return ExerciseStats(
        total_exercises=total_exercises,
        completed_exercises=completed_exercises,
        total_duration_minutes=total_duration,
        total_calories_burned=total_calories,
        completion_rate=round(completion_rate, 2),
        streak_days=streak_days,
        weekly_average=round(weekly_average, 2)
    )

@router.get("/exercises/report/weekly", response_model=WeeklyReport)
async def get_weekly_report(
    week_offset: int = 0,  # 0 = current week, 1 = last week, etc.
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get a detailed weekly exercise report."""
    today = date.today()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday + (week_offset * 7))
    week_end = week_start + timedelta(days=6)
    
    exercises = db.query(ExerciseLog).filter(
        and_(
            ExerciseLog.user_id == current_user.id,
            ExerciseLog.date_performed >= week_start,
            ExerciseLog.date_performed <= week_end
        )
    ).all()
    
    total_exercises = len(exercises)
    completed_exercises = len([e for e in exercises if e.completed])
    total_duration = sum([e.duration_minutes or 0 for e in exercises])
    total_calories = sum([e.calories_burned or 0 for e in exercises])
    
    # Daily breakdown
    daily_breakdown = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_exercises = [e for e in exercises if e.date_performed == day]
        daily_breakdown.append({
            "date": day.isoformat(),
            "day_name": day.strftime("%A"),
            "exercises": len(day_exercises),
            "completed": len([e for e in day_exercises if e.completed]),
            "duration": sum([e.duration_minutes or 0 for e in day_exercises]),
            "calories": sum([e.calories_burned or 0 for e in day_exercises])
        })
    
    # Generate insights
    insights = []
    if completed_exercises > 0:
        completion_rate = (completed_exercises / total_exercises) * 100
        insights.append(f"You completed {completion_rate:.1f}% of your planned exercises this week.")
        
        if total_duration > 0:
            avg_duration = total_duration / completed_exercises
            insights.append(f"Average exercise duration: {avg_duration:.1f} minutes.")
        
        if total_calories > 0:
            insights.append(f"You burned approximately {total_calories} calories through exercise.")
        
        # Find most active day
        most_active_day = max(daily_breakdown, key=lambda x: x["exercises"])
        if most_active_day["exercises"] > 0:
            insights.append(f"Your most active day was {most_active_day['day_name']} with {most_active_day['exercises']} exercises.")
    else:
        insights.append("No exercises completed this week. Consider setting small, achievable goals to get started.")
    
    return WeeklyReport(
        week_start=week_start,
        week_end=week_end,
        total_exercises=total_exercises,
        completed_exercises=completed_exercises,
        total_duration=total_duration,
        total_calories=total_calories,
        daily_breakdown=daily_breakdown,
        insights=insights
    )
