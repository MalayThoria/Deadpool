from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import numpy as np
from database.config import get_sync_db
from auth.auth import current_active_user
from database.models import User, UserProfile, MedicineHistory, ExerciseLog
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic Models
class HealthMetric(BaseModel):
    name: str
    value: float
    unit: str
    trend: str  # "improving", "stable", "declining"
    change_percentage: float

class HealthInsight(BaseModel):
    id: str
    title: str
    description: str
    category: str  # "exercise", "nutrition", "medication", "general"
    priority: str  # "high", "medium", "low"
    actionable: bool
    recommendations: List[str]
    created_at: datetime

class HealthTrend(BaseModel):
    metric: str
    period: str  # "week", "month", "quarter", "year"
    data_points: List[Dict[str, Any]]
    trend_direction: str
    correlation_factors: List[str]

class RiskAssessment(BaseModel):
    risk_level: str  # "low", "moderate", "high"
    risk_factors: List[str]
    protective_factors: List[str]
    recommendations: List[str]
    next_checkup_date: Optional[datetime]

class HealthScore(BaseModel):
    overall_score: int  # 0-100
    category_scores: Dict[str, int]
    factors_affecting_score: List[str]
    improvement_suggestions: List[str]

class PersonalizedRecommendation(BaseModel):
    id: str
    type: str  # "exercise", "nutrition", "lifestyle", "medical"
    title: str
    description: str
    difficulty: str  # "easy", "moderate", "challenging"
    estimated_impact: str  # "low", "medium", "high"
    timeframe: str
    steps: List[str]

class HealthInsightsResponse(BaseModel):
    health_score: HealthScore
    key_metrics: List[HealthMetric]
    insights: List[HealthInsight]
    trends: List[HealthTrend]
    risk_assessment: RiskAssessment
    recommendations: List[PersonalizedRecommendation]
    last_updated: datetime

# Helper Functions
def calculate_bmi_trend(profile: UserProfile, exercise_logs: List[ExerciseLog]) -> HealthMetric:
    """Calculate BMI trend based on weight changes"""
    current_bmi = profile.weight / ((profile.height / 100) ** 2) if profile.weight and profile.height else 0
    
    # Simulate trend calculation (in real app, would use historical data)
    trend = "stable"
    change_percentage = 0.0
    
    if len(exercise_logs) > 10:  # Active user
        trend = "improving"
        change_percentage = -2.5
    elif len(exercise_logs) < 3:  # Inactive user
        trend = "declining"
        change_percentage = 1.2
    
    return HealthMetric(
        name="BMI",
        value=round(current_bmi, 1),
        unit="kg/m²",
        trend=trend,
        change_percentage=change_percentage
    )

def calculate_activity_level(exercise_logs: List[ExerciseLog]) -> HealthMetric:
    """Calculate activity level based on recent exercise logs"""
    recent_logs = [log for log in exercise_logs if log.date >= datetime.now().date() - timedelta(days=30)]
    weekly_sessions = len(recent_logs) / 4.3  # Approximate weeks in a month
    
    trend = "stable"
    change_percentage = 0.0
    
    if weekly_sessions >= 4:
        trend = "improving"
        change_percentage = 15.0
    elif weekly_sessions < 2:
        trend = "declining"
        change_percentage = -10.0
    
    return HealthMetric(
        name="Weekly Exercise Sessions",
        value=round(weekly_sessions, 1),
        unit="sessions/week",
        trend=trend,
        change_percentage=change_percentage
    )

def generate_health_insights(user: User, profile: UserProfile, exercise_logs: List[ExerciseLog], med_history: List[MedicineHistory]) -> List[HealthInsight]:
    """Generate personalized health insights"""
    insights = []
    
    # Exercise insights
    recent_exercises = len([log for log in exercise_logs if log.date >= datetime.now().date() - timedelta(days=7)])
    if recent_exercises < 3:
        insights.append(HealthInsight(
            id="low_activity",
            title="Increase Physical Activity",
            description="You've had fewer exercise sessions this week. Regular physical activity is crucial for maintaining good health.",
            category="exercise",
            priority="medium",
            actionable=True,
            recommendations=[
                "Aim for at least 150 minutes of moderate exercise per week",
                "Start with 20-minute walks daily",
                "Try bodyweight exercises at home"
            ],
            created_at=datetime.now()
        ))
    
    # Medication adherence insights
    if len(med_history) > 0:
        insights.append(HealthInsight(
            id="medication_review",
            title="Medication Review Recommended",
            description="Regular medication reviews help ensure optimal treatment effectiveness and safety.",
            category="medication",
            priority="high",
            actionable=True,
            recommendations=[
                "Schedule a medication review with your healthcare provider",
                "Keep a medication diary to track effectiveness",
                "Report any side effects promptly"
            ],
            created_at=datetime.now()
        ))
    
    # BMI insights
    if profile.weight and profile.height:
        bmi = profile.weight / ((profile.height / 100) ** 2)
        if bmi > 25:
            insights.append(HealthInsight(
                id="weight_management",
                title="Weight Management Opportunity",
                description="Your BMI indicates you might benefit from weight management strategies.",
                category="nutrition",
                priority="medium",
                actionable=True,
                recommendations=[
                    "Consult with a nutritionist for personalized meal planning",
                    "Focus on portion control and balanced meals",
                    "Increase daily physical activity gradually"
                ],
                created_at=datetime.now()
            ))
    
    return insights

def calculate_health_score(profile: UserProfile, exercise_logs: List[ExerciseLog], med_history: List[MedicineHistory]) -> HealthScore:
    """Calculate overall health score"""
    scores = {
        "physical_activity": 70,
        "nutrition": 75,
        "sleep": 80,
        "stress_management": 65,
        "preventive_care": 85
    }
    
    # Adjust based on exercise frequency
    recent_exercises = len([log for log in exercise_logs if log.date >= datetime.now().date() - timedelta(days=30)])
    if recent_exercises >= 12:  # 3+ times per week
        scores["physical_activity"] = 90
    elif recent_exercises >= 8:  # 2+ times per week
        scores["physical_activity"] = 80
    elif recent_exercises < 4:  # Less than once per week
        scores["physical_activity"] = 50
    
    overall_score = int(np.mean(list(scores.values())))
    
    factors = []
    suggestions = []
    
    if scores["physical_activity"] < 70:
        factors.append("Low physical activity levels")
        suggestions.append("Increase weekly exercise frequency")
    
    if len(med_history) > 3:
        factors.append("Multiple medications requiring monitoring")
        suggestions.append("Regular medication reviews with healthcare provider")
    
    return HealthScore(
        overall_score=overall_score,
        category_scores=scores,
        factors_affecting_score=factors,
        improvement_suggestions=suggestions
    )

def generate_risk_assessment(profile: UserProfile, med_history: List[MedicineHistory]) -> RiskAssessment:
    """Generate health risk assessment"""
    risk_factors = []
    protective_factors = []
    risk_level = "low"
    
    # Age-based risk
    if profile.age and profile.age > 65:
        risk_factors.append("Advanced age")
        risk_level = "moderate"
    
    # BMI-based risk
    if profile.weight and profile.height:
        bmi = profile.weight / ((profile.height / 100) ** 2)
        if bmi > 30:
            risk_factors.append("Obesity (BMI > 30)")
            risk_level = "moderate"
        elif bmi < 18.5:
            risk_factors.append("Underweight (BMI < 18.5)")
    
    # Medication-based risk
    if len(med_history) > 5:
        risk_factors.append("Multiple medications (polypharmacy)")
        if risk_level == "moderate":
            risk_level = "high"
    
    # Protective factors
    protective_factors.extend([
        "Regular health monitoring",
        "Active health management",
        "Technology-assisted care"
    ])
    
    recommendations = [
        "Maintain regular exercise routine",
        "Follow balanced nutrition plan",
        "Schedule regular health check-ups",
        "Monitor vital signs regularly"
    ]
    
    next_checkup = datetime.now() + timedelta(days=90)  # 3 months
    
    return RiskAssessment(
        risk_level=risk_level,
        risk_factors=risk_factors,
        protective_factors=protective_factors,
        recommendations=recommendations,
        next_checkup_date=next_checkup
    )

def generate_personalized_recommendations(user: User, profile: UserProfile, exercise_logs: List[ExerciseLog]) -> List[PersonalizedRecommendation]:
    """Generate personalized health recommendations"""
    recommendations = []
    
    # Exercise recommendations
    recent_exercises = len([log for log in exercise_logs if log.date >= datetime.now().date() - timedelta(days=7)])
    if recent_exercises < 3:
        recommendations.append(PersonalizedRecommendation(
            id="increase_cardio",
            type="exercise",
            title="Boost Cardiovascular Health",
            description="Incorporate more cardio exercises to improve heart health and endurance.",
            difficulty="easy",
            estimated_impact="high",
            timeframe="2-4 weeks",
            steps=[
                "Start with 20-minute brisk walks daily",
                "Gradually increase to 30 minutes",
                "Add 2-3 jogging sessions per week",
                "Monitor heart rate during exercise"
            ]
        ))
    
    # Nutrition recommendations
    recommendations.append(PersonalizedRecommendation(
        id="hydration_boost",
        type="nutrition",
        title="Optimize Daily Hydration",
        description="Proper hydration supports all bodily functions and can improve energy levels.",
        difficulty="easy",
        estimated_impact="medium",
        timeframe="1 week",
        steps=[
            "Drink a glass of water upon waking",
            "Carry a water bottle throughout the day",
            "Set hourly hydration reminders",
            "Monitor urine color as hydration indicator"
        ]
    ))
    
    # Lifestyle recommendations
    recommendations.append(PersonalizedRecommendation(
        id="sleep_optimization",
        type="lifestyle",
        title="Improve Sleep Quality",
        description="Quality sleep is essential for recovery, mental health, and overall well-being.",
        difficulty="moderate",
        estimated_impact="high",
        timeframe="2-3 weeks",
        steps=[
            "Establish consistent bedtime routine",
            "Limit screen time 1 hour before bed",
            "Keep bedroom cool and dark",
            "Avoid caffeine after 2 PM"
        ]
    ))
    
    return recommendations

# API Endpoints
@router.get("/insights", response_model=HealthInsightsResponse)
async def get_health_insights(
    period: str = Query("month", description="Time period for analysis"),
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get comprehensive health insights for the user"""
    try:
        # Get user data
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        exercise_logs = db.query(ExerciseLog).filter(ExerciseLog.user_id == current_user.id).all()
        med_history = db.query(MedicineHistory).filter(MedicineHistory.user_id == current_user.id).all()
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Calculate metrics
        bmi_metric = calculate_bmi_trend(profile, exercise_logs)
        activity_metric = calculate_activity_level(exercise_logs)
        
        # Generate insights
        insights = generate_health_insights(current_user, profile, exercise_logs, med_history)
        health_score = calculate_health_score(profile, exercise_logs, med_history)
        risk_assessment = generate_risk_assessment(profile, med_history)
        recommendations = generate_personalized_recommendations(current_user, profile, exercise_logs)
        
        # Generate trends (mock data for demonstration)
        trends = [
            HealthTrend(
                metric="weight",
                period=period,
                data_points=[
                    {"date": "2024-01-01", "value": 70.5},
                    {"date": "2024-01-15", "value": 70.2},
                    {"date": "2024-02-01", "value": 69.8},
                    {"date": "2024-02-15", "value": 69.5}
                ],
                trend_direction="decreasing",
                correlation_factors=["increased exercise", "improved diet"]
            )
        ]
        
        return HealthInsightsResponse(
            health_score=health_score,
            key_metrics=[bmi_metric, activity_metric],
            insights=insights,
            trends=trends,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            last_updated=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error generating health insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate health insights")

@router.get("/metrics", response_model=List[HealthMetric])
async def get_health_metrics(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get current health metrics"""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        exercise_logs = db.query(ExerciseLog).filter(ExerciseLog.user_id == current_user.id).all()
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        metrics = [
            calculate_bmi_trend(profile, exercise_logs),
            calculate_activity_level(exercise_logs)
        ]
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error fetching health metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch health metrics")

@router.get("/score", response_model=HealthScore)
async def get_health_score(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get overall health score"""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        exercise_logs = db.query(ExerciseLog).filter(ExerciseLog.user_id == current_user.id).all()
        med_history = db.query(MedicineHistory).filter(MedicineHistory.user_id == current_user.id).all()
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        return calculate_health_score(profile, exercise_logs, med_history)
        
    except Exception as e:
        logger.error(f"Error calculating health score: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate health score")

@router.get("/recommendations", response_model=List[PersonalizedRecommendation])
async def get_recommendations(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get personalized health recommendations"""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        exercise_logs = db.query(ExerciseLog).filter(ExerciseLog.user_id == current_user.id).all()
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        return generate_personalized_recommendations(current_user, profile, exercise_logs)
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")

@router.get("/risk-assessment", response_model=RiskAssessment)
async def get_risk_assessment(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get health risk assessment"""
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        med_history = db.query(MedicineHistory).filter(MedicineHistory.user_id == current_user.id).all()
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        return generate_risk_assessment(profile, med_history)
        
    except Exception as e:
        logger.error(f"Error generating risk assessment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate risk assessment")
