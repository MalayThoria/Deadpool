from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import json
from utils.ocr import ocr_processor
from utils.gpt import gpt_processor
from database.config import get_sync_db
from database.models import User, UserProfile
from auth.auth import current_active_user

router = APIRouter()

# Pydantic models for enhanced exercise recommendations
class DiseaseBasedExerciseRequest(BaseModel):
    detected_diseases: List[str] = Field(..., description="List of detected diseases from prescription")
    user_preferences: Dict[str, Any] = Field(default={}, description="User exercise preferences and limitations")
    fitness_level: str = Field(default="beginner", description="Current fitness level")
    available_time: int = Field(default=30, description="Available time per day in minutes")

class ExerciseDetail(BaseModel):
    name: str
    type: str  # cardio, strength, flexibility, balance
    duration_minutes: int
    intensity: str  # low, moderate, high
    frequency_per_week: int
    instructions: str
    precautions: List[str]
    benefits: List[str]
    modifications: List[str]

class WeeklyExercisePlan(BaseModel):
    day: int
    day_name: str
    exercises: List[ExerciseDetail]
    total_duration: int
    focus_area: str
    rest_day: bool

class DiseaseBasedExerciseResponse(BaseModel):
    detected_diseases: List[str]
    weekly_plan: List[WeeklyExercisePlan]
    general_guidelines: List[str]
    contraindications: List[str]
    progress_tracking: List[str]
    warning_signs: List[str] = []
    medical_disclaimer: str = "This exercise plan is generated for informational purposes only. Always consult with qualified healthcare providers before starting any exercise program, especially with existing medical conditions."
    success: bool
    message: str

@router.post("/disease-based-exercise-plan", response_model=DiseaseBasedExerciseResponse)
async def get_disease_based_exercise_plan(request: DiseaseBasedExerciseRequest):
    """
    Generate a comprehensive disease-based exercise plan with medical safety considerations
    """
    try:
        # Enhanced medical safety prompt
        prompt = f"""
        As a certified exercise physiologist and medical fitness specialist, create a medically appropriate exercise plan for a patient with: {', '.join(request.detected_diseases)}
        
        CRITICAL MEDICAL SAFETY REQUIREMENTS:
        1. All exercise recommendations must be evidence-based and medically safe
        2. Include clear contraindications and precautions for each condition
        3. Provide modifications for different fitness levels and limitations
        4. Consider potential complications and warning signs
        5. Emphasize the importance of medical clearance before starting
        
        Patient Profile:
        - Medical Conditions: {', '.join(request.detected_diseases)}
        - Fitness Level: {request.fitness_level}
        - Available Time: {request.available_time} minutes per session
        - User Preferences: {request.user_preferences}
        
        Create a structured weekly exercise plan with:
        - Safe exercise recommendations for each condition
        - Proper progression guidelines
        - Contraindications and precautions
        - Warning signs to stop exercising
        - Modifications for different abilities
        
        MANDATORY SAFETY MEASURES:
        - Include "Obtain medical clearance before starting any exercise program"
        - List specific warning signs for each condition
        - Provide exercise modifications for safety
        - Emphasize gradual progression and listening to the body
        
        Return a structured response suitable for a health application.
        """
        
        try:
            # Get user profile for personalization
            user_profile = {}  # This would typically come from user authentication
            
            # Generate AI-powered exercise plan with enhanced safety measures
            ai_response = await gpt_processor.generate_exercise_plan(user_profile, request.detected_diseases)
            
            # Convert AI response to structured format with safety validations
            exercise_plan = gpt_processor.get_disease_based_exercise_plan(request.detected_diseases, user_profile)
            
            # Add mandatory medical disclaimers and safety guidelines
            enhanced_guidelines = [
                "🚨 MEDICAL CLEARANCE REQUIRED: Obtain approval from your healthcare provider before starting this exercise program",
                "This exercise plan is for informational purposes only and not a substitute for professional medical advice",
                "Stop exercising immediately if you experience chest pain, shortness of breath, dizziness, or unusual fatigue",
                "Start slowly and progress gradually - listen to your body at all times",
                "If you have heart disease, diabetes, or other chronic conditions, exercise under medical supervision",
                "Consider working with a certified medical fitness professional",
                "Regular medical monitoring is essential while following this exercise plan",
                "Modify exercises based on your current symptoms and energy levels"
            ]
            
            return DiseaseBasedExerciseResponse(
                detected_diseases=request.detected_diseases,
                weekly_plan=exercise_plan.get('weekly_plan', []),
                general_guidelines=enhanced_guidelines,
                contraindications=exercise_plan.get('contraindications', [
                    "Acute illness or fever",
                    "Uncontrolled high blood pressure",
                    "Recent cardiac events",
                    "Severe joint pain or inflammation",
                    "Dizziness or balance problems"
                ]),
                progress_tracking=exercise_plan.get('progress_tracking', []),
                success=True,
                message="Disease-based exercise plan generated with comprehensive safety considerations"
            )
            
        except Exception as e:
            print(f"Error generating exercise plan: {e}")
            return DiseaseBasedExerciseResponse(
                detected_diseases=request.detected_diseases,
                weekly_plan=[],
                general_guidelines=[
                    "Unable to generate personalized exercise plan at this time",
                    "Please consult with a certified exercise physiologist or physical therapist",
                    "Obtain medical clearance before starting any exercise program",
                    "Follow exercise guidelines provided by your healthcare team"
                ],
                contraindications=[
                    "Do not exercise without medical clearance",
                    "Avoid strenuous activity if experiencing symptoms"
                ],
                progress_tracking=[],
                success=False,
                message="Exercise plan generation temporarily unavailable - please consult healthcare professionals"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating exercise plan: {str(e)}")

@router.post("/exercise-recommendations")
async def get_exercise_recommendations(
    file: UploadFile = File(...),
    user_profile: Optional[str] = Form(None)
):
    """
    Extract diseases from prescription and provide personalized exercise recommendations
    
    Args:
        file: Prescription image file
        user_profile: Optional JSON string with user profile data
        
    Returns:
        JSON response with diseases, exercise recommendations, and weekly plan
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process the image
        image_data = await file.read()
        
        # Extract text using OCR
        extracted_text = ocr_processor.extract_text_from_image(image_data)
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Could not extract sufficient text from image")
        
        # Parse user profile if provided
        profile_data = None
        if user_profile:
            try:
                profile_data = json.loads(user_profile)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid user profile JSON format")
        
        # Extract diseases from prescription text
        diseases = gpt_processor.extract_diseases(extracted_text)
        
        # Get exercise recommendations based on diseases and user profile
        exercise_recommendations = gpt_processor.get_exercise_recommendations(diseases, profile_data)
        
        # Also extract medicines for comprehensive analysis
        medicines = gpt_processor.extract_medicines(extracted_text)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "extracted_text": extracted_text,
                "diseases": diseases,
                "medicines": medicines,
                "exercise_recommendations": exercise_recommendations,
                "user_profile": profile_data
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in exercise recommendations endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/api/v1/diseases-only")
async def extract_diseases_only(
    file: UploadFile = File(...)
):
    """
    Extract only diseases from prescription image
    
    Args:
        file: Prescription image file
        
    Returns:
        JSON response with extracted diseases
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process the image
        image_data = await file.read()
        
        # Extract text using OCR
        extracted_text = ocr_processor.extract_text_from_image(image_data)
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Could not extract sufficient text from image")
        
        # Extract diseases from prescription text
        diseases = gpt_processor.extract_diseases(extracted_text)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "extracted_text": extracted_text,
                "diseases": diseases
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in disease extraction endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/exercise-plan")
async def create_exercise_plan(
    diseases: list = [],
    user_profile: Optional[Dict[str, Any]] = None
):
    """
    Create exercise plan based on provided diseases and user profile
    
    Args:
        diseases: List of disease names
        user_profile: Optional user profile data
        
    Returns:
        JSON response with exercise recommendations
    """
    try:
        # Get exercise recommendations
        exercise_recommendations = gpt_processor.get_exercise_recommendations(diseases, user_profile)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "diseases": diseases,
                "exercise_recommendations": exercise_recommendations,
                "user_profile": user_profile
            }
        )
        
    except Exception as e:
        print(f"Error creating exercise plan: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")