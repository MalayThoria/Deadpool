from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.gpt import gpt_processor
from backend.utils.medicine_db import medicine_db

router = APIRouter()

class MedicineInfo(BaseModel):
    name: str
    description: str
    dosage: str
    precautions: str
    side_effects: str
    category: str
    interactions: str = ""
    pregnancy_safety: str = ""
    storage: str = ""
    missed_dose: str = ""
    verified: bool = False
    verification_sources: List[str] = []

class MedInfoRequest(BaseModel):
    medicines: List[str]

class MedInfoResponse(BaseModel):
    medicines_info: List[MedicineInfo]
    success: bool
    message: str
    count: int

@router.post("/med-info", response_model=MedInfoResponse)
async def get_medicine_information(request: MedInfoRequest):
    """
    Get detailed information about medicines using GPT-4
    """
    try:
        if not request.medicines:
            raise HTTPException(
                status_code=400,
                detail="List of medicines is required"
            )
        
        # Get medicine information using GPT
        medicines_info = gpt_processor.get_medicine_info(request.medicines)
        
        if not medicines_info:
            return MedInfoResponse(
                medicines_info=[],
                success=False,
                message="Could not retrieve information for the provided medicines.",
                count=0
            )
        
        # Cross-verify with FDA and RxNav databases
        verified_medicines_info = []
        for info in medicines_info:
            medicine_name = info.get("name", "Unknown")
            verified_info = medicine_db.cross_verify_medicine(medicine_name, info)
            verified_medicines_info.append(verified_info)
        
        # Convert to MedicineInfo objects
        medicine_info_objects = []
        for info in verified_medicines_info:
            medicine_info_objects.append(MedicineInfo(
                name=info.get("name", "Unknown"),
                description=info.get("description", "No description available"),
                dosage=info.get("dosage", "Consult your healthcare provider"),
                precautions=info.get("precautions", "Always consult with a healthcare professional"),
                side_effects=info.get("side_effects", "Side effects may vary"),
                category=info.get("category", "General medication"),
                interactions=info.get("interactions", ""),
                pregnancy_safety=info.get("pregnancy_safety", ""),
                storage=info.get("storage", ""),
                missed_dose=info.get("missed_dose", ""),
                verified=info.get("verified", False),
                verification_sources=info.get("verification_sources", [])
            ))
        
        return MedInfoResponse(
            medicines_info=medicine_info_objects,
            success=True,
            message=f"Successfully retrieved information for {len(medicine_info_objects)} medicine(s)",
            count=len(medicine_info_objects)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Medicine information retrieval failed: {str(e)}"
        )

@router.get("/med-info/test")
async def test_medicine_information():
    """
    Test endpoint with sample medicines
    """
    try:
        sample_medicines = ["Amoxicillin", "Ibuprofen", "Omeprazole"]
        
        medicines_info = gpt_processor.get_medicine_info(sample_medicines)
        
        # Convert to MedicineInfo objects
        medicine_info_objects = []
        for info in medicines_info:
            medicine_info_objects.append(MedicineInfo(
                name=info.get("name", "Unknown"),
                description=info.get("description", "No description available"),
                dosage=info.get("dosage", "Consult your healthcare provider"),
                precautions=info.get("precautions", "Always consult with a healthcare professional"),
                side_effects=info.get("side_effects", "Side effects may vary"),
                category=info.get("category", "General medication")
            ))
        
        return MedInfoResponse(
            medicines_info=medicine_info_objects,
            success=True,
            message=f"Test successful - retrieved information for {len(medicine_info_objects)} medicine(s)",
            count=len(medicine_info_objects)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test failed: {str(e)}"
        )

@router.get("/med-info/{medicine_name}")
async def get_single_medicine_info(medicine_name: str):
    """
    Get information for a single medicine
    """
    try:
        if not medicine_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Medicine name is required"
            )
        
        medicines_info = gpt_processor.get_medicine_info([medicine_name])
        
        if not medicines_info:
            raise HTTPException(
                status_code=404,
                detail=f"Information not found for {medicine_name}"
            )
        
        info = medicines_info[0]
        medicine_info = MedicineInfo(
            name=info.get("name", medicine_name),
            description=info.get("description", "No description available"),
            dosage=info.get("dosage", "Consult your healthcare provider"),
            precautions=info.get("precautions", "Always consult with a healthcare professional"),
            side_effects=info.get("side_effects", "Side effects may vary"),
            category=info.get("category", "General medication")
        )
        
        return {
            "medicine_info": medicine_info,
            "success": True,
            "message": f"Successfully retrieved information for {medicine_name}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Medicine information retrieval failed: {str(e)}"
        ) 