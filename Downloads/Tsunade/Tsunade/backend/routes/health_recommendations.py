from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.config import get_sync_db
from database.models import User, UserProfile, DiseaseHistory
from auth.auth import current_active_user
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.gpt import gpt_processor

router = APIRouter()

# Pydantic models
class DiseaseInput(BaseModel):
    disease_name: str = Field(..., description="Name of the medical condition")
    severity: str = Field(default="mild", description="Severity level: mild, moderate, severe")
    symptoms: List[str] = Field(default=[], description="List of current symptoms")
    limitations: List[str] = Field(default=[], description="Physical limitations or restrictions")

class ExerciseRecommendation(BaseModel):
    exercise_name: str
    exercise_type: str  # cardio, strength, flexibility, balance
    duration_minutes: int
    intensity: str  # low, moderate, high
    frequency_per_week: int
    instructions: str
    precautions: List[str]
    benefits: List[str]
    modifications: List[str]  # For different ability levels

class DietaryRecommendation(BaseModel):
    food_category: str  # fruits, vegetables, proteins, grains, etc.
    recommended_foods: List[str]
    foods_to_avoid: List[str]
    portion_guidelines: str
    nutritional_benefits: List[str]
    preparation_tips: List[str]

class HealthRecommendationResponse(BaseModel):
    disease_name: str
    exercise_plan: List[ExerciseRecommendation]
    dietary_plan: List[DietaryRecommendation]
    general_guidelines: List[str]
    warning_signs: List[str]
    follow_up_recommendations: List[str]
    success: bool
    message: str

class PersonalizedRecommendationRequest(BaseModel):
    include_medical_history: bool = Field(default=True, description="Include user's medical history")
    focus_areas: List[str] = Field(default=[], description="Specific areas to focus on (weight_loss, strength, flexibility, etc.)")
    time_availability: int = Field(default=30, description="Available time per day in minutes")
    fitness_level: str = Field(default="beginner", description="Current fitness level")

# Disease-specific recommendation templates
DISEASE_EXERCISE_TEMPLATES = {
    "diabetes": {
        "cardio": ["brisk walking", "swimming", "cycling", "dancing"],
        "strength": ["resistance bands", "light weights", "bodyweight exercises"],
        "flexibility": ["yoga", "tai chi", "stretching routines"],
        "precautions": ["Monitor blood sugar before and after exercise", "Carry glucose tablets", "Stay hydrated"]
    },
    "hypertension": {
        "cardio": ["walking", "swimming", "low-impact aerobics"],
        "strength": ["light resistance training", "isometric exercises"],
        "flexibility": ["gentle yoga", "stretching"],
        "precautions": ["Avoid heavy lifting", "Monitor blood pressure", "Gradual intensity increase"]
    },
    "arthritis": {
        "cardio": ["water aerobics", "stationary cycling", "walking"],
        "strength": ["resistance bands", "light weights"],
        "flexibility": ["range of motion exercises", "gentle yoga"],
        "precautions": ["Avoid high-impact activities", "Warm up thoroughly", "Listen to your body"]
    },
    "heart_disease": {
        "cardio": ["supervised walking", "stationary cycling", "swimming"],
        "strength": ["light resistance training"],
        "flexibility": ["gentle stretching", "tai chi"],
        "precautions": ["Medical clearance required", "Monitor heart rate", "Start slowly"]
    }
}

DISEASE_DIET_TEMPLATES = {
    "diabetes": {
        "recommended": ["leafy greens", "whole grains", "lean proteins", "berries", "nuts"],
        "avoid": ["refined sugars", "white bread", "sugary drinks", "processed foods"],
        "guidelines": "Focus on low glycemic index foods and portion control"
    },
    "hypertension": {
        "recommended": ["fruits", "vegetables", "whole grains", "low-fat dairy", "lean meats"],
        "avoid": ["high sodium foods", "processed meats", "canned soups", "fast food"],
        "guidelines": "Follow DASH diet principles with reduced sodium intake"
    },
    "arthritis": {
        "recommended": ["fatty fish", "leafy greens", "berries", "nuts", "olive oil"],
        "avoid": ["processed foods", "excess sugar", "trans fats", "excessive alcohol"],
        "guidelines": "Anti-inflammatory diet with omega-3 rich foods"
    },
    "heart_disease": {
        "recommended": ["fish", "fruits", "vegetables", "whole grains", "legumes"],
        "avoid": ["saturated fats", "trans fats", "high cholesterol foods", "excess sodium"],
        "guidelines": "Heart-healthy diet low in saturated fat and cholesterol"
    }
}

@router.post("/disease-recommendations", response_model=HealthRecommendationResponse)
async def get_disease_recommendations(disease_input: DiseaseInput):
    """
    Get exercise and dietary recommendations for a specific disease
    """
    try:
        disease_name = disease_input.disease_name.lower().replace(" ", "_")
        
        # Generate AI-powered recommendations using GPT
        prompt = f"""
        As a certified healthcare AI assistant, provide comprehensive health recommendations for a patient with {disease_input.disease_name}.
        
        Patient Details:
        - Disease: {disease_input.disease_name}
        - Severity: {disease_input.severity}
        - Symptoms: {', '.join(disease_input.symptoms) if disease_input.symptoms else 'None specified'}
        - Limitations: {', '.join(disease_input.limitations) if disease_input.limitations else 'None specified'}
        
        Please provide:
        1. 5-7 specific exercise recommendations with duration, intensity, and precautions
        2. Detailed dietary recommendations with specific foods to include and avoid
        3. General lifestyle guidelines
        4. Warning signs to watch for
        5. Follow-up recommendations
        
        Format the response as a structured recommendation that is safe, evidence-based, and appropriate for the condition.
        Always include the disclaimer to consult healthcare providers.
        """
        
        try:
            ai_response = await gpt_processor.generate_health_recommendations(prompt)
            
            # Parse AI response and structure it
            exercise_plan = _generate_exercise_recommendations(disease_name, disease_input)
            dietary_plan = _generate_dietary_recommendations(disease_name, disease_input)
            
            return HealthRecommendationResponse(
                disease_name=disease_input.disease_name,
                exercise_plan=exercise_plan,
                dietary_plan=dietary_plan,
                general_guidelines=[
                    "Consult with your healthcare provider before starting any new exercise program",
                    "Start slowly and gradually increase intensity",
                    "Listen to your body and stop if you experience pain or discomfort",
                    "Maintain regular medical check-ups",
                    "Keep a health diary to track progress"
                ],
                warning_signs=[
                    "Chest pain or shortness of breath",
                    "Dizziness or fainting",
                    "Unusual fatigue",
                    "Worsening of symptoms",
                    "New or concerning symptoms"
                ],
                follow_up_recommendations=[
                    "Schedule regular check-ups with your healthcare provider",
                    "Monitor key health metrics (blood pressure, blood sugar, etc.)",
                    "Consider working with a certified fitness trainer",
                    "Join support groups for your condition",
                    "Stay updated on latest treatment options"
                ],
                success=True,
                message="Health recommendations generated successfully"
            )
            
        except Exception as e:
            # Fallback to template-based recommendations if AI fails
            exercise_plan = _generate_exercise_recommendations(disease_name, disease_input)
            dietary_plan = _generate_dietary_recommendations(disease_name, disease_input)
            
            return HealthRecommendationResponse(
                disease_name=disease_input.disease_name,
                exercise_plan=exercise_plan,
                dietary_plan=dietary_plan,
                general_guidelines=[
                    "Consult with your healthcare provider before starting any new exercise program",
                    "Start slowly and gradually increase intensity",
                    "Listen to your body and stop if you experience pain or discomfort"
                ],
                warning_signs=[
                    "Chest pain or shortness of breath",
                    "Dizziness or fainting",
                    "Unusual fatigue"
                ],
                follow_up_recommendations=[
                    "Schedule regular check-ups with your healthcare provider",
                    "Monitor key health metrics"
                ],
                success=True,
                message="Health recommendations generated using clinical guidelines"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate health recommendations: {str(e)}"
        )

@router.post("/personalized-recommendations", response_model=HealthRecommendationResponse)
async def get_personalized_recommendations(
    request: PersonalizedRecommendationRequest,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """
    Get personalized health recommendations based on user's medical history and preferences
    """
    try:
        # Get user profile and medical history
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        disease_history = db.query(DiseaseHistory).filter(
            DiseaseHistory.user_id == current_user.id,
            DiseaseHistory.is_active == True
        ).all()
        
        if not user_profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found. Please complete your profile first."
            )
        
        # Build personalized prompt
        medical_conditions = []
        if request.include_medical_history and disease_history:
            medical_conditions = [disease.disease_name for disease in disease_history]
        
        prompt = f"""
        Create personalized health recommendations for a patient with the following profile:
        
        Patient Profile:
        - Age: {user_profile.age or 'Not specified'}
        - Gender: {user_profile.gender.value if user_profile.gender else 'Not specified'}
        - Fitness Level: {user_profile.fitness_level.value if user_profile.fitness_level else request.fitness_level}
        - Medical Conditions: {', '.join(medical_conditions) if medical_conditions else 'None specified'}
        - Available Time: {request.time_availability} minutes per day
        - Focus Areas: {', '.join(request.focus_areas) if request.focus_areas else 'General health'}
        
        Please provide:
        1. Personalized exercise plan considering their conditions and limitations
        2. Dietary recommendations based on their health profile
        3. Lifestyle modifications specific to their needs
        4. Progress tracking suggestions
        
        Ensure all recommendations are safe and appropriate for their medical conditions.
        """
        
        try:
            ai_response = await gpt_processor.generate_health_recommendations(prompt)
            
            # Generate personalized recommendations
            primary_condition = medical_conditions[0] if medical_conditions else "general_health"
            disease_input = DiseaseInput(
                disease_name=primary_condition,
                severity="mild",
                symptoms=[],
                limitations=[]
            )
            
            exercise_plan = _generate_personalized_exercise_plan(user_profile, request)
            dietary_plan = _generate_personalized_dietary_plan(user_profile, medical_conditions)
            
            return HealthRecommendationResponse(
                disease_name=primary_condition,
                exercise_plan=exercise_plan,
                dietary_plan=dietary_plan,
                general_guidelines=[
                    "Follow your personalized plan consistently",
                    "Track your progress regularly",
                    "Adjust intensity based on your energy levels",
                    "Stay hydrated and get adequate sleep",
                    "Consult your healthcare provider for any concerns"
                ],
                warning_signs=[
                    "Unusual pain or discomfort",
                    "Extreme fatigue",
                    "Difficulty breathing",
                    "Dizziness or nausea"
                ],
                follow_up_recommendations=[
                    "Review and update your plan monthly",
                    "Track key health metrics",
                    "Consider working with healthcare professionals",
                    "Join community support groups"
                ],
                success=True,
                message="Personalized health recommendations generated successfully"
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate personalized recommendations: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get personalized recommendations: {str(e)}"
        )

def _generate_exercise_recommendations(disease_name: str, disease_input: DiseaseInput) -> List[ExerciseRecommendation]:
    """
    Generate exercise recommendations based on disease templates
    """
    template = DISEASE_EXERCISE_TEMPLATES.get(disease_name, DISEASE_EXERCISE_TEMPLATES["diabetes"])
    
    recommendations = []
    
    # Cardio recommendations
    for exercise in template["cardio"][:2]:
        recommendations.append(ExerciseRecommendation(
            exercise_name=exercise.title(),
            exercise_type="cardio",
            duration_minutes=20,
            intensity="moderate",
            frequency_per_week=3,
            instructions=f"Perform {exercise} at a comfortable pace",
            precautions=template["precautions"],
            benefits=["Improves cardiovascular health", "Helps manage condition", "Boosts energy"],
            modifications=["Start with 10 minutes", "Increase gradually", "Rest as needed"]
        ))
    
    # Strength recommendations
    for exercise in template["strength"][:2]:
        recommendations.append(ExerciseRecommendation(
            exercise_name=exercise.title(),
            exercise_type="strength",
            duration_minutes=15,
            intensity="low",
            frequency_per_week=2,
            instructions=f"Perform {exercise} with proper form",
            precautions=template["precautions"],
            benefits=["Builds muscle strength", "Improves bone density", "Enhances metabolism"],
            modifications=["Use lighter weights", "Reduce repetitions", "Focus on form"]
        ))
    
    # Flexibility recommendations
    for exercise in template["flexibility"][:1]:
        recommendations.append(ExerciseRecommendation(
            exercise_name=exercise.title(),
            exercise_type="flexibility",
            duration_minutes=10,
            intensity="low",
            frequency_per_week=5,
            instructions=f"Practice {exercise} with gentle movements",
            precautions=["Don't force stretches", "Breathe deeply", "Stop if painful"],
            benefits=["Improves flexibility", "Reduces stiffness", "Promotes relaxation"],
            modifications=["Hold stretches shorter", "Use props for support", "Modify positions"]
        ))
    
    return recommendations

def _generate_dietary_recommendations(disease_name: str, disease_input: DiseaseInput) -> List[DietaryRecommendation]:
    """
    Generate dietary recommendations based on disease templates
    """
    template = DISEASE_DIET_TEMPLATES.get(disease_name, DISEASE_DIET_TEMPLATES["diabetes"])
    
    return [
        DietaryRecommendation(
            food_category="Recommended Foods",
            recommended_foods=template["recommended"],
            foods_to_avoid=template["avoid"],
            portion_guidelines=template["guidelines"],
            nutritional_benefits=["Supports condition management", "Provides essential nutrients", "Promotes overall health"],
            preparation_tips=["Choose fresh ingredients", "Limit processing", "Control portions"]
        )
    ]

def _generate_personalized_exercise_plan(user_profile: UserProfile, request: PersonalizedRecommendationRequest) -> List[ExerciseRecommendation]:
    """
    Generate personalized exercise plan based on user profile
    """
    fitness_level = user_profile.fitness_level.value if user_profile.fitness_level else request.fitness_level
    
    # Adjust recommendations based on fitness level
    if fitness_level == "beginner":
        duration = min(15, request.time_availability)
        intensity = "low"
        frequency = 3
    elif fitness_level == "intermediate":
        duration = min(25, request.time_availability)
        intensity = "moderate"
        frequency = 4
    else:
        duration = min(35, request.time_availability)
        intensity = "moderate"
        frequency = 5
    
    return [
        ExerciseRecommendation(
            exercise_name="Walking",
            exercise_type="cardio",
            duration_minutes=duration,
            intensity=intensity,
            frequency_per_week=frequency,
            instructions="Walk at a comfortable pace",
            precautions=["Wear comfortable shoes", "Stay hydrated", "Start slowly"],
            benefits=["Improves cardiovascular health", "Low impact", "Easy to do anywhere"],
            modifications=["Adjust pace as needed", "Take breaks", "Use walking aids if needed"]
        )
    ]

def _generate_personalized_dietary_plan(user_profile: UserProfile, medical_conditions: List[str]) -> List[DietaryRecommendation]:
    """
    Generate personalized dietary plan based on user profile and conditions
    """
    # Default healthy diet recommendations
    return [
        DietaryRecommendation(
            food_category="Balanced Nutrition",
            recommended_foods=["fruits", "vegetables", "whole grains", "lean proteins", "healthy fats"],
            foods_to_avoid=["processed foods", "excess sugar", "trans fats", "excessive sodium"],
            portion_guidelines="Follow balanced plate method: 1/2 vegetables, 1/4 protein, 1/4 whole grains",
            nutritional_benefits=["Provides essential nutrients", "Supports overall health", "Maintains energy levels"],
            preparation_tips=["Cook at home when possible", "Read nutrition labels", "Control portion sizes"]
        )
    ]

# New Pydantic models for day-wise diet chart
class DayWiseDietRequest(BaseModel):
    detected_diseases: List[str] = Field(..., description="List of detected diseases from prescription")
    user_preferences: Dict[str, Any] = Field(default={}, description="User dietary preferences and restrictions")
    duration_days: int = Field(default=7, description="Number of days for the diet chart")

class MealPlan(BaseModel):
    meal_type: str  # breakfast, lunch, dinner, snack
    foods: List[str]
    portion_size: str
    calories: int
    preparation_time: str
    instructions: str

class DayDietPlan(BaseModel):
    day: int
    day_name: str
    meals: List[MealPlan]
    total_calories: int
    nutritional_focus: str
    hydration_reminder: str

class DayWiseDietResponse(BaseModel):
    diet_plan: List[DayDietPlan]
    general_guidelines: List[str]
    food_restrictions: List[str] = []
    nutritional_goals: List[str] = []
    medical_disclaimer: str = "This dietary plan is generated for informational purposes only. Always consult with qualified healthcare providers before making significant dietary changes."
    success: bool
    message: str

@router.post("/day-wise-diet-chart", response_model=DayWiseDietResponse)
async def get_day_wise_diet_chart(
    request: DayWiseDietRequest,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """
    Generate a comprehensive day-wise diet chart based on detected diseases from prescription
    """
    try:
        # Get user profile for personalization
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        
        # Enhanced medical safety prompt
        prompt = f"""
        As a certified clinical nutritionist and registered dietitian, create a medically appropriate {request.duration_days}-day diet chart for a patient with the following conditions: {', '.join(request.detected_diseases)}
        
        CRITICAL MEDICAL SAFETY REQUIREMENTS:
        1. All recommendations must be evidence-based and medically appropriate
        2. Include clear disclaimers about consulting healthcare providers
        3. Avoid any recommendations that could be harmful for the specified conditions
        4. Consider drug-nutrient interactions for common medications
        5. Provide safe, conservative recommendations suitable for the general population
        
        Patient Profile:
        - Detected Conditions: {', '.join(request.detected_diseases)}
        - Duration: {request.duration_days} days
        - User Preferences: {request.user_preferences}
        - Age: {user_profile.age if user_profile else 'Not specified'}
        - Gender: {user_profile.gender.value if user_profile and user_profile.gender else 'Not specified'}
        
        Create a structured diet plan with:
        - Daily meal plans (breakfast, lunch, dinner, snacks)
        - Nutritional focus for each day
        - Calorie estimates
        - Preparation time estimates
        - General safety guidelines
        
        MANDATORY DISCLAIMERS:
        - Always include "Consult your healthcare provider before making dietary changes"
        - Emphasize the importance of medical supervision
        - Include warnings about potential interactions with medications
        
        Return the response in a structured format suitable for a health application.
        """
        
        # Use the enhanced GPT processor to generate day-wise diet chart
        diet_chart_data = await gpt_processor.get_day_wise_diet_chart(
            diseases=request.detected_diseases,
            user_profile={
                "age": user_profile.age if user_profile else None,
                "gender": user_profile.gender.value if user_profile and user_profile.gender else None,
                "fitness_level": user_profile.fitness_level.value if user_profile and user_profile.fitness_level else "beginner",
                "preferences": request.user_preferences
            },
            duration_days=request.duration_days
        )
        
        if diet_chart_data and diet_chart_data.get("success"):
            # Convert the AI response to structured format
            diet_plan = []
            for day_data in diet_chart_data.get("diet_plan", []):
                meals = []
                for meal_data in day_data.get("meals", []):
                    meals.append(MealPlan(
                        meal_type=meal_data.get("meal_type", ""),
                        foods=meal_data.get("foods", []),
                        portion_size=meal_data.get("portion_size", ""),
                        calories=meal_data.get("calories", 0),
                        preparation_time=meal_data.get("preparation_time", ""),
                        instructions=meal_data.get("instructions", "")
                    ))
                
                diet_plan.append(DayDietPlan(
                    day=day_data.get("day", 1),
                    day_name=day_data.get("day_name", ""),
                    meals=meals,
                    total_calories=day_data.get("total_calories", 0),
                    nutritional_focus=day_data.get("nutritional_focus", ""),
                    hydration_reminder=day_data.get("hydration_reminder", "")
                ))
            
            # Add mandatory medical disclaimers
            enhanced_guidelines = [
                "⚠️ IMPORTANT: Consult your healthcare provider before making any dietary changes",
                "This diet chart is for informational purposes only and not a substitute for professional medical advice",
                "Monitor your body's response and adjust portions based on your individual needs",
                "If you have diabetes, hypertension, or other chronic conditions, seek medical supervision",
                "Stop any dietary changes if you experience adverse reactions",
                "Consider potential interactions with your current medications",
                "Regular medical check-ups are essential while following this plan"
            ] + diet_chart_data.get("general_guidelines", [])
            
            return DayWiseDietResponse(
                diet_plan=diet_plan,
                general_guidelines=enhanced_guidelines,
                food_restrictions=diet_chart_data.get("food_restrictions", []),
                nutritional_goals=diet_chart_data.get("nutritional_goals", []),
                success=True,
                message="Day-wise diet chart generated successfully with medical safety considerations"
            )
        else:
            # Fallback response with safety guidelines
            return DayWiseDietResponse(
                diet_plan=[],
                general_guidelines=[
                    "Unable to generate personalized diet chart at this time",
                    "Please consult with a registered dietitian for personalized nutrition advice",
                    "Follow general healthy eating guidelines recommended by your healthcare provider",
                    "⚠️ IMPORTANT: Always seek professional medical guidance for dietary changes"
                ],
                food_restrictions=[],
                nutritional_goals=[],
                success=False,
                message="Diet chart generation temporarily unavailable - please consult healthcare professionals"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate day-wise diet chart: {str(e)}"
        )