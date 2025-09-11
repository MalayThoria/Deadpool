from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import json
from utils.ocr import ocr_processor
from utils.gpt import gpt_processor

router = APIRouter()

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