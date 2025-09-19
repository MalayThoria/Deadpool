from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json
import re
from datetime import datetime

from database.config import get_sync_db
from auth.auth import current_active_user
from database.models import User, UserProfile, MedicineHistory, DiseaseHistory, FitnessLevel
from utils.gpt import GPTProcessor
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class PrescriptionAnalysisRequest(BaseModel):
    prescription_text: str = Field(..., description="OCR extracted text from prescription")
    auto_update_profile: bool = Field(default=True, description="Automatically update user profile with extracted conditions")

class ExtractedMedicalInfo(BaseModel):
    medical_conditions: List[str] = Field(default=[], description="Detected medical conditions")
    medications: List[Dict[str, Any]] = Field(default=[], description="Extracted medications with details")
    allergies: List[str] = Field(default=[], description="Detected allergies")
    doctor_name: Optional[str] = Field(None, description="Prescribing doctor name")
    prescription_date: Optional[str] = Field(None, description="Prescription date")
    confidence_score: float = Field(default=0.0, description="Confidence in extraction accuracy")

class PrescriptionAnalysisResponse(BaseModel):
    extracted_info: ExtractedMedicalInfo
    profile_updated: bool = Field(default=False, description="Whether user profile was updated")
    new_conditions_detected: List[str] = Field(default=[], description="New conditions not in user profile")
    message: str = Field(default="", description="Analysis result message")

@router.post("/analyze-prescription", response_model=PrescriptionAnalysisResponse)
async def analyze_prescription(
    request: PrescriptionAnalysisRequest,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """
    Analyze prescription text to extract medical conditions, medications, and other relevant information.
    Automatically update user profile if requested.
    """
    try:
        # Initialize GPT processor
        gpt_processor = GPTProcessor()
        
        # Create prompt for medical information extraction
        extraction_prompt = f"""
        Analyze the following prescription text and extract medical information in JSON format.
        
        Prescription Text:
        {request.prescription_text}
        
        Extract the following information and return as valid JSON:
        {{
            "medical_conditions": ["list of medical conditions/diagnoses mentioned"],
            "medications": [
                {{
                    "name": "medication name",
                    "dosage": "dosage information",
                    "frequency": "frequency of administration",
                    "duration": "treatment duration if mentioned"
                }}
            ],
            "allergies": ["list of allergies mentioned"],
            "doctor_name": "prescribing doctor name if mentioned",
            "prescription_date": "prescription date if mentioned (YYYY-MM-DD format)",
            "confidence_score": 0.95
        }}
        
        Guidelines:
        - Only extract information that is clearly mentioned in the text
        - Use standard medical terminology
        - For conditions, include both the condition name and any severity indicators
        - For medications, be precise with names and dosages
        - Set confidence_score between 0.0 and 1.0 based on text clarity
        - If information is unclear or missing, use empty arrays or null values
        """
        
        # Call OpenAI API using GPTProcessor
        if gpt_processor.client is None:
            # Use fallback extraction when OpenAI is not available
            print("OpenAI client not available, using fallback extraction")
            extracted_data = _fallback_extraction(request.prescription_text)
        else:
            try:
                response = gpt_processor.client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Use gpt-3.5-turbo instead of gpt-4 for better availability
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a medical information extraction specialist. Extract medical information from prescription text accurately and return valid JSON only."
                        },
                        {
                            "role": "user",
                            "content": extraction_prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=1000
                )
                
                # Parse the response
                extracted_text = response.choices[0].message.content.strip()
                
                # Clean the response to extract JSON
                json_start = extracted_text.find('{')
                json_end = extracted_text.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_text = extracted_text[json_start:json_end]
                else:
                    json_text = extracted_text
                
                try:
                    extracted_data = json.loads(json_text)
                except json.JSONDecodeError:
                    # Fallback: try to extract information using regex patterns
                    print("Failed to parse GPT response, using fallback extraction")
                    extracted_data = _fallback_extraction(request.prescription_text)
                    
            except Exception as e:
                print(f"OpenAI API call failed: {str(e)}, using fallback extraction")
                extracted_data = _fallback_extraction(request.prescription_text)
        
        # Create ExtractedMedicalInfo object
        extracted_info = ExtractedMedicalInfo(**extracted_data)
        
        # Get user profile, create one if missing
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not user_profile:
            # Create a basic profile for users who don't have one
             user_profile = UserProfile(
                 user_id=current_user.id,
                 fitness_level=FitnessLevel.BEGINNER,
                 timezone="UTC",
                 language="en"
             )
             db.add(user_profile)
             db.commit()
             db.refresh(user_profile)
        
        profile_updated = False
        new_conditions_detected = []
        
        if request.auto_update_profile and extracted_info.medical_conditions:
            # Get existing conditions from user profile
            existing_conditions = []
            if user_profile.medical_conditions:
                if isinstance(user_profile.medical_conditions, list):
                    existing_conditions = user_profile.medical_conditions
                elif isinstance(user_profile.medical_conditions, str):
                    existing_conditions = [user_profile.medical_conditions]
            
            # Find new conditions
            for condition in extracted_info.medical_conditions:
                condition_lower = condition.lower()
                if not any(condition_lower in existing.lower() for existing in existing_conditions):
                    new_conditions_detected.append(condition)
                    existing_conditions.append(condition)
            
            # Update user profile if new conditions found
            if new_conditions_detected:
                user_profile.medical_conditions = existing_conditions
                
                # Also create disease history entries
                for condition in new_conditions_detected:
                    disease_entry = DiseaseHistory(
                        user_id=current_user.id,
                        disease_name=condition,
                        diagnosis_date=datetime.now(),
                        is_active=True,
                        notes=f"Detected from prescription analysis on {datetime.now().strftime('%Y-%m-%d')}"
                    )
                    db.add(disease_entry)
                
                db.commit()
                profile_updated = True
        
        # Store medication history
        for medication in extracted_info.medications:
            medicine_entry = MedicineHistory(
                user_id=current_user.id,
                medicine_name=medication.get('name', ''),
                dosage=medication.get('dosage', ''),
                frequency=medication.get('frequency', ''),
                duration=medication.get('duration', ''),
                prescription_text=request.prescription_text,
                prescribed_date=datetime.now(),
                start_date=datetime.now(),
                is_active=True,
                is_verified=False
            )
            db.add(medicine_entry)
        
        if extracted_info.medications:
            db.commit()
        
        # Create response message
        message_parts = []
        if extracted_info.medical_conditions:
            message_parts.append(f"Detected {len(extracted_info.medical_conditions)} medical condition(s)")
        if extracted_info.medications:
            message_parts.append(f"Extracted {len(extracted_info.medications)} medication(s)")
        if new_conditions_detected:
            message_parts.append(f"Added {len(new_conditions_detected)} new condition(s) to your profile")
        
        message = "; ".join(message_parts) if message_parts else "Prescription analyzed successfully"
        
        return PrescriptionAnalysisResponse(
            extracted_info=extracted_info,
            profile_updated=profile_updated,
            new_conditions_detected=new_conditions_detected,
            message=message
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Error analyzing prescription: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        print(f"Error analyzing prescription: {str(e)}")
        print(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze prescription: {str(e)}"
        )

def _fallback_extraction(prescription_text: str) -> Dict[str, Any]:
    """
    Fallback method to extract basic information using regex patterns
    when OpenAI API fails or returns invalid JSON.
    """
    extracted_data = {
        "medical_conditions": [],
        "medications": [],
        "allergies": [],
        "doctor_name": None,
        "prescription_date": None,
        "confidence_score": 0.3  # Lower confidence for regex extraction
    }
    
    # Common medical condition patterns
    condition_patterns = [
        r'(?i)(?:diagnosis|condition|disease)\s*:?\s*([a-zA-Z\s]+)',
        r'(?i)(diabetes|hypertension|asthma|arthritis|depression|anxiety)',
        r'(?i)(high blood pressure|low blood pressure)',
        r'(?i)(heart disease|kidney disease|liver disease)'
    ]
    
    for pattern in condition_patterns:
        matches = re.findall(pattern, prescription_text)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0] if match[0] else match[1]
            condition = match.strip().title()
            if condition and len(condition) > 2:
                extracted_data["medical_conditions"].append(condition)
    
    # Basic medication extraction
    medication_patterns = [
        r'(?i)([a-zA-Z]+(?:cillin|mycin|prazole|olol|pine|ide|ine))\s*(\d+\s*mg)?',
        r'(?i)(aspirin|ibuprofen|acetaminophen|metformin|lisinopril)\s*(\d+\s*mg)?'
    ]
    
    for pattern in medication_patterns:
        matches = re.findall(pattern, prescription_text)
        for match in matches:
            if isinstance(match, tuple):
                name = match[0].strip().title()
                dosage = match[1].strip() if len(match) > 1 and match[1] else ""
            else:
                name = match.strip().title()
                dosage = ""
            
            if name and len(name) > 2:
                extracted_data["medications"].append({
                    "name": name,
                    "dosage": dosage,
                    "frequency": "",
                    "duration": ""
                })
    
    # Remove duplicates
    extracted_data["medical_conditions"] = list(set(extracted_data["medical_conditions"]))
    
    return extracted_data

@router.get("/medical-profile", response_model=Dict[str, Any])
async def get_medical_profile(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """
    Get user's complete medical profile including conditions detected from prescriptions.
    """
    try:
        # Get user profile
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not user_profile:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )
        
        # Get disease history
        disease_history = db.query(DiseaseHistory).filter(
            DiseaseHistory.user_id == current_user.id,
            DiseaseHistory.is_active == True
        ).all()
        
        # Get medicine history
        medicine_history = db.query(MedicineHistory).filter(
            MedicineHistory.user_id == current_user.id,
            MedicineHistory.is_active == True
        ).all()
        
        return {
            "profile": {
                "medical_conditions": user_profile.medical_conditions or [],
                "allergies": user_profile.allergies or "",
                "medications": user_profile.medications or "",
                "emergency_contact": user_profile.emergency_contact or ""
            },
            "disease_history": [
                {
                    "id": disease.id,
                    "disease_name": disease.disease_name,
                    "severity": disease.severity.value if disease.severity else "mild",
                    "diagnosis_date": disease.diagnosis_date.isoformat() if disease.diagnosis_date else None,
                    "is_chronic": disease.is_chronic,
                    "notes": disease.notes
                }
                for disease in disease_history
            ],
            "medicine_history": [
                {
                    "id": medicine.id,
                    "medicine_name": medicine.medicine_name,
                    "dosage": medicine.dosage,
                    "frequency": medicine.frequency,
                    "prescribed_date": medicine.prescribed_date.isoformat() if medicine.prescribed_date else None,
                    "is_verified": medicine.is_verified
                }
                for medicine in medicine_history
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting medical profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get medical profile: {str(e)}"
        )