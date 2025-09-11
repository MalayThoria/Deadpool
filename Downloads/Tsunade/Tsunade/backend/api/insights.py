from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field
from uuid import UUID
import statistics
import json

from database.config import get_sync_db, get_mongodb
from database.models import User, UserProfile, ExerciseLog, MedicineHistory, DiseaseHistory
from auth.auth import current_active_user

router = APIRouter()

# Pydantic models
class HealthMetrics(BaseModel):
    bmi: Optional[float] = None
    bmi_category: Optional[str] = None
    ideal_weight_range: Optional[Dict[str, float]] = None
    daily_calorie_needs: Optional[int] = None
    daily_water_intake: Optional[float] = None
    fitness_score: Optional[int] = None

class ExerciseInsights(BaseModel):
    total_exercises_this_month: int
    completion_rate: float
    average_duration: float
    total_calories_burned: int
    most_frequent_exercise_type: Optional[str]
    weekly_trend: List[Dict[str, Any]]
    recommendations: List[str]

class HealthRisks(BaseModel):
    risk_level: str  # low, moderate, high
    risk_factors: List[str]
    recommendations: List[str]
    chronic_conditions: List[str]
    medication_interactions: List[str]

class PersonalizedRecommendations(BaseModel):
    exercise_recommendations: List[str]
    nutrition_tips: List[str]
    lifestyle_suggestions: List[str]
    health_goals: List[str]
    next_checkup_reminder: Optional[str]

class ComprehensiveHealthInsights(BaseModel):
    user_id: UUID
    generated_at: datetime
    health_metrics: HealthMetrics
    exercise_insights: ExerciseInsights
    health_risks: HealthRisks
    recommendations: PersonalizedRecommendations
    overall_health_score: int  # 0-100
    insights_summary: List[str]

class ProgressTracking(BaseModel):
    metric: str
    current_value: float
    previous_value: Optional[float]
    change_percentage: Optional[float]
    trend: str  # improving, declining, stable
    target_value: Optional[float]
    days_to_target: Optional[int]

class WeeklyHealthReport(BaseModel):
    week_start: date
    week_end: date
    exercise_summary: Dict[str, Any]
    health_metrics_changes: List[ProgressTracking]
    achievements: List[str]
    areas_for_improvement: List[str]
    next_week_goals: List[str]

# Helper functions
def calculate_bmi(height_cm: float, weight_kg: float) -> float:
    """Calculate BMI."""
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)

def get_bmi_category(bmi: float) -> str:
    """Get BMI category."""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"

def calculate_ideal_weight_range(height_cm: float) -> Dict[str, float]:
    """Calculate ideal weight range using BMI 18.5-24.9."""
    height_m = height_cm / 100
    min_weight = 18.5 * (height_m ** 2)
    max_weight = 24.9 * (height_m ** 2)
    return {"min": round(min_weight, 1), "max": round(max_weight, 1)}

def calculate_daily_calories(weight_kg: float, height_cm: float, age: int, gender: str, activity_level: str = "moderate") -> int:
    """Calculate daily calorie needs using Mifflin-St Jeor equation."""
    if gender.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    
    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }
    
    return int(bmr * activity_multipliers.get(activity_level, 1.55))

def calculate_fitness_score(exercises: List[ExerciseLog], profile: UserProfile) -> int:
    """Calculate fitness score based on exercise consistency and intensity."""
    if not exercises:
        return 0
    
    # Base score factors
    completion_rate = len([e for e in exercises if e.completed]) / len(exercises)
    consistency_score = min(len(exercises) / 20, 1)  # Max score at 20+ exercises
    
    # Intensity scoring
    intensity_scores = {"low": 1, "moderate": 2, "high": 3, "very_high": 4}
    avg_intensity = statistics.mean([
        intensity_scores.get(e.intensity, 1) for e in exercises if e.intensity
    ]) if exercises else 1
    
    # Duration scoring
    avg_duration = statistics.mean([
        e.duration_minutes for e in exercises if e.duration_minutes
    ]) if exercises else 0
    duration_score = min(avg_duration / 60, 1)  # Max score at 60+ minutes
    
    # Calculate final score
    score = (completion_rate * 40 + consistency_score * 30 + 
             (avg_intensity / 4) * 20 + duration_score * 10)
    
    return min(int(score), 100)

def generate_exercise_recommendations(profile: UserProfile, exercises: List[ExerciseLog]) -> List[str]:
    """Generate personalized exercise recommendations."""
    recommendations = []
    
    if not exercises:
        recommendations.append("Start with 15-20 minutes of light exercise daily")
        recommendations.append("Try walking, stretching, or beginner yoga")
        return recommendations
    
    # Analyze current exercise patterns
    exercise_types = [e.exercise_type for e in exercises if e.exercise_type]
    type_counts = {t: exercise_types.count(t) for t in set(exercise_types)}
    
    # Check for balance
    if "cardio" not in type_counts or type_counts.get("cardio", 0) < 2:
        recommendations.append("Add more cardiovascular exercises like walking, cycling, or swimming")
    
    if "strength" not in type_counts or type_counts.get("strength", 0) < 2:
        recommendations.append("Include strength training exercises 2-3 times per week")
    
    if "flexibility" not in type_counts:
        recommendations.append("Add flexibility exercises like yoga or stretching")
    
    # Check completion rate
    completion_rate = len([e for e in exercises if e.completed]) / len(exercises)
    if completion_rate < 0.7:
        recommendations.append("Try shorter, more manageable exercise sessions to improve consistency")
    
    # Fitness level specific recommendations
    if profile.fitness_level == "beginner":
        recommendations.append("Focus on building a consistent routine with low-impact exercises")
    elif profile.fitness_level == "intermediate":
        recommendations.append("Challenge yourself with varied intensity levels and new exercise types")
    elif profile.fitness_level == "advanced":
        recommendations.append("Consider high-intensity interval training and specialized workouts")
    
    return recommendations[:5]  # Limit to 5 recommendations

def assess_health_risks(profile: UserProfile, diseases: List[DiseaseHistory], medicines: List[MedicineHistory]) -> HealthRisks:
    """Assess health risks based on profile and medical history."""
    risk_factors = []
    recommendations = []
    chronic_conditions = []
    medication_interactions = []
    
    # BMI-based risks
    if profile.height_cm and profile.weight_kg:
        bmi = calculate_bmi(profile.height_cm, profile.weight_kg)
        if bmi >= 30:
            risk_factors.append("Obesity (BMI ≥ 30)")
            recommendations.append("Consider weight management program")
        elif bmi >= 25:
            risk_factors.append("Overweight (BMI 25-29.9)")
            recommendations.append("Focus on healthy weight loss through diet and exercise")
        elif bmi < 18.5:
            risk_factors.append("Underweight (BMI < 18.5)")
            recommendations.append("Consult healthcare provider about healthy weight gain")
    
    # Age-based risks
    if profile.date_of_birth:
        age = (date.today() - profile.date_of_birth).days // 365
        if age >= 65:
            risk_factors.append("Advanced age (≥65 years)")
            recommendations.append("Regular health screenings and preventive care")
        elif age >= 50:
            risk_factors.append("Middle age (50-64 years)")
            recommendations.append("Increased focus on preventive health measures")
    
    # Disease-based risks
    for disease in diseases:
        if disease.status in ["active", "chronic"]:
            chronic_conditions.append(disease.disease_name)
            if disease.severity in ["severe", "critical"]:
                risk_factors.append(f"Severe {disease.disease_name}")
    
    # Medication interactions (simplified)
    medicine_names = [m.medicine_name.lower() for m in medicines]
    if len(medicine_names) >= 5:
        risk_factors.append("Polypharmacy (5+ medications)")
        recommendations.append("Regular medication review with healthcare provider")
    
    # Determine overall risk level
    risk_score = len(risk_factors)
    if risk_score >= 4:
        risk_level = "high"
    elif risk_score >= 2:
        risk_level = "moderate"
    else:
        risk_level = "low"
    
    return HealthRisks(
        risk_level=risk_level,
        risk_factors=risk_factors,
        recommendations=recommendations,
        chronic_conditions=chronic_conditions,
        medication_interactions=medication_interactions
    )

@router.get("/health-metrics", response_model=HealthMetrics)
async def get_health_metrics(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get current health metrics for the user."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    metrics = HealthMetrics()
    
    if profile.height_cm and profile.weight_kg:
        bmi = calculate_bmi(profile.height_cm, profile.weight_kg)
        metrics.bmi = round(bmi, 1)
        metrics.bmi_category = get_bmi_category(bmi)
        metrics.ideal_weight_range = calculate_ideal_weight_range(profile.height_cm)
        
        if profile.date_of_birth and profile.gender:
            age = (date.today() - profile.date_of_birth).days // 365
            activity_level = profile.fitness_level or "moderate"
            metrics.daily_calorie_needs = calculate_daily_calories(
                profile.weight_kg, profile.height_cm, age, profile.gender, activity_level
            )
        
        # Water intake recommendation (35ml per kg body weight)
        metrics.daily_water_intake = round(profile.weight_kg * 0.035, 1)
    
    # Calculate fitness score
    exercises = db.query(ExerciseLog).filter(
        and_(
            ExerciseLog.user_id == current_user.id,
            ExerciseLog.date_performed >= date.today() - timedelta(days=30)
        )
    ).all()
    
    metrics.fitness_score = calculate_fitness_score(exercises, profile)
    
    return metrics

@router.get("/exercise-insights", response_model=ExerciseInsights)
async def get_exercise_insights(
    days: int = 30,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get exercise insights and analytics."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    exercises = db.query(ExerciseLog).filter(
        and_(
            ExerciseLog.user_id == current_user.id,
            ExerciseLog.date_performed >= start_date,
            ExerciseLog.date_performed <= end_date
        )
    ).all()
    
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    total_exercises = len(exercises)
    completed_exercises = len([e for e in exercises if e.completed])
    completion_rate = (completed_exercises / total_exercises * 100) if total_exercises > 0 else 0
    
    durations = [e.duration_minutes for e in exercises if e.duration_minutes]
    average_duration = statistics.mean(durations) if durations else 0
    
    calories = [e.calories_burned for e in exercises if e.calories_burned]
    total_calories = sum(calories)
    
    # Most frequent exercise type
    exercise_types = [e.exercise_type for e in exercises if e.exercise_type]
    most_frequent_type = max(set(exercise_types), key=exercise_types.count) if exercise_types else None
    
    # Weekly trend
    weekly_trend = []
    for i in range(4):  # Last 4 weeks
        week_end = end_date - timedelta(days=i*7)
        week_start = week_end - timedelta(days=6)
        week_exercises = [e for e in exercises if week_start <= e.date_performed <= week_end]
        
        weekly_trend.append({
            "week": f"Week {4-i}",
            "exercises": len(week_exercises),
            "completed": len([e for e in week_exercises if e.completed]),
            "total_duration": sum([e.duration_minutes or 0 for e in week_exercises]),
            "total_calories": sum([e.calories_burned or 0 for e in week_exercises])
        })
    
    # Generate recommendations
    recommendations = generate_exercise_recommendations(profile, exercises) if profile else []
    
    return ExerciseInsights(
        total_exercises_this_month=total_exercises,
        completion_rate=round(completion_rate, 1),
        average_duration=round(average_duration, 1),
        total_calories_burned=total_calories,
        most_frequent_exercise_type=most_frequent_type,
        weekly_trend=weekly_trend,
        recommendations=recommendations
    )

@router.get("/comprehensive", response_model=ComprehensiveHealthInsights)
async def get_comprehensive_insights(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get comprehensive health insights and recommendations."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Get health metrics
    health_metrics = await get_health_metrics(current_user, db)
    
    # Get exercise insights
    exercise_insights = await get_exercise_insights(30, current_user, db)
    
    # Get medical history
    diseases = db.query(DiseaseHistory).filter(DiseaseHistory.user_id == current_user.id).all()
    medicines = db.query(MedicineHistory).filter(MedicineHistory.user_id == current_user.id).all()
    
    # Assess health risks
    health_risks = assess_health_risks(profile, diseases, medicines)
    
    # Generate personalized recommendations
    exercise_recs = exercise_insights.recommendations
    nutrition_tips = [
        "Eat a balanced diet with plenty of fruits and vegetables",
        "Stay hydrated by drinking adequate water daily",
        "Limit processed foods and added sugars",
        "Include lean proteins in your meals"
    ]
    
    lifestyle_suggestions = [
        "Maintain a regular sleep schedule (7-9 hours per night)",
        "Practice stress management techniques",
        "Avoid smoking and limit alcohol consumption",
        "Stay socially connected and engaged"
    ]
    
    health_goals = [
        "Maintain consistent exercise routine",
        "Achieve and maintain healthy weight",
        "Regular health check-ups and screenings",
        "Manage chronic conditions effectively"
    ]
    
    recommendations = PersonalizedRecommendations(
        exercise_recommendations=exercise_recs,
        nutrition_tips=nutrition_tips,
        lifestyle_suggestions=lifestyle_suggestions,
        health_goals=health_goals,
        next_checkup_reminder="Schedule annual physical exam"
    )
    
    # Calculate overall health score
    fitness_score = health_metrics.fitness_score or 0
    bmi_score = 100 if health_metrics.bmi and 18.5 <= health_metrics.bmi <= 24.9 else 70
    risk_score = {"low": 100, "moderate": 70, "high": 40}.get(health_risks.risk_level, 70)
    exercise_score = min(exercise_insights.completion_rate, 100)
    
    overall_score = int((fitness_score + bmi_score + risk_score + exercise_score) / 4)
    
    # Generate insights summary
    insights_summary = [
        f"Your overall health score is {overall_score}/100",
        f"Exercise completion rate: {exercise_insights.completion_rate}%",
        f"Health risk level: {health_risks.risk_level}"
    ]
    
    if health_metrics.bmi:
        insights_summary.append(f"BMI: {health_metrics.bmi} ({health_metrics.bmi_category})")
    
    return ComprehensiveHealthInsights(
        user_id=current_user.id,
        generated_at=datetime.utcnow(),
        health_metrics=health_metrics,
        exercise_insights=exercise_insights,
        health_risks=health_risks,
        recommendations=recommendations,
        overall_health_score=overall_score,
        insights_summary=insights_summary
    )

@router.get("/weekly-report", response_model=WeeklyHealthReport)
async def get_weekly_health_report(
    week_offset: int = 0,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Generate a comprehensive weekly health report."""
    today = date.today()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday + (week_offset * 7))
    week_end = week_start + timedelta(days=6)
    
    # Get week's exercises
    exercises = db.query(ExerciseLog).filter(
        and_(
            ExerciseLog.user_id == current_user.id,
            ExerciseLog.date_performed >= week_start,
            ExerciseLog.date_performed <= week_end
        )
    ).all()
    
    exercise_summary = {
        "total_exercises": len(exercises),
        "completed_exercises": len([e for e in exercises if e.completed]),
        "total_duration": sum([e.duration_minutes or 0 for e in exercises]),
        "total_calories": sum([e.calories_burned or 0 for e in exercises]),
        "unique_exercise_types": len(set([e.exercise_type for e in exercises if e.exercise_type]))
    }
    
    # Health metrics changes (simplified - would need historical data)
    health_metrics_changes = [
        ProgressTracking(
            metric="Exercise Completion Rate",
            current_value=exercise_summary["completed_exercises"] / exercise_summary["total_exercises"] * 100 if exercise_summary["total_exercises"] > 0 else 0,
            previous_value=None,
            change_percentage=None,
            trend="stable",
            target_value=80.0,
            days_to_target=None
        )
    ]
    
    # Achievements
    achievements = []
    if exercise_summary["completed_exercises"] >= 5:
        achievements.append("Completed 5+ exercises this week!")
    if exercise_summary["total_duration"] >= 150:
        achievements.append("Met WHO recommended 150 minutes of exercise!")
    if exercise_summary["unique_exercise_types"] >= 3:
        achievements.append("Tried 3+ different types of exercises!")
    
    if not achievements:
        achievements.append("Keep building your exercise routine!")
    
    # Areas for improvement
    areas_for_improvement = []
    completion_rate = exercise_summary["completed_exercises"] / exercise_summary["total_exercises"] * 100 if exercise_summary["total_exercises"] > 0 else 0
    
    if completion_rate < 70:
        areas_for_improvement.append("Improve exercise completion rate")
    if exercise_summary["total_duration"] < 150:
        areas_for_improvement.append("Increase weekly exercise duration")
    if exercise_summary["unique_exercise_types"] < 2:
        areas_for_improvement.append("Add variety to exercise routine")
    
    # Next week goals
    next_week_goals = [
        "Complete at least 80% of planned exercises",
        "Try one new type of exercise",
        "Maintain consistent daily activity"
    ]
    
    return WeeklyHealthReport(
        week_start=week_start,
        week_end=week_end,
        exercise_summary=exercise_summary,
        health_metrics_changes=health_metrics_changes,
        achievements=achievements,
        areas_for_improvement=areas_for_improvement,
        next_week_goals=next_week_goals
    )

@router.post("/store-insights")
async def store_insights_to_mongodb(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db),
    mongodb = Depends(get_mongodb)
):
    """Store comprehensive insights to MongoDB for historical tracking."""
    insights = await get_comprehensive_insights(current_user, db)
    
    # Convert to dict and store in MongoDB
    insights_dict = insights.dict()
    insights_dict["_id"] = f"{current_user.id}_{datetime.utcnow().isoformat()}"
    
    collection = mongodb["health_insights"]
    result = await collection.insert_one(insights_dict)
    
    return {
        "message": "Insights stored successfully",
        "document_id": str(result.inserted_id)
    }
