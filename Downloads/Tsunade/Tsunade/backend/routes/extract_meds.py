from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.gpt import gpt_processor

router = APIRouter()

class ExtractMedsRequest(BaseModel):
    prescription_text: str

class MedicineInfo(BaseModel):
    original: str
    corrected: str
    confidence: float
    method: str
    explanation: str
    is_valid: bool = True

class ExtractMedsResponse(BaseModel):
    medicines: List[MedicineInfo]
    success: bool
    message: str
    count: int
    correction_summary: str

@router.post("/extract-meds", response_model=ExtractMedsResponse)
async def extract_medicines(request: ExtractMedsRequest):
    """
    Extract medicine names from prescription text using GPT-4 with fallback to regex extraction
    """
    try:
        if not request.prescription_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Prescription text is required"
            )
        
        # Extract medicines using GPT (with fallback if OpenAI unavailable)
        raw_medicines = gpt_processor.extract_medicines(request.prescription_text)
        
        if not raw_medicines:
            return ExtractMedsResponse(
                medicines=[],
                success=False,
                message="No medicines could be identified in the prescription text.",
                count=0,
                correction_summary="No medicines found to correct."
            )
        
        # Use GPT-4 to verify and correct medicine names (with fallback if OpenAI unavailable)
        verification_result = gpt_processor.verify_and_correct_medicine_names(
            raw_medicines, 
            request.prescription_text
        )
        
        # Convert to MedicineInfo objects
        medicine_info_list = []
        corrections_made = []
        
        for medicine in verification_result.get('corrected_medicines', []):
            medicine_info = MedicineInfo(
                original=medicine['original'],
                corrected=medicine['corrected'],
                confidence=medicine['confidence'],
                method=medicine['method'],
                explanation=medicine['explanation'],
                is_valid=medicine['is_valid']
            )
            medicine_info_list.append(medicine_info)
            
            # Track corrections for summary
            if medicine['original'] != medicine['corrected']:
                corrections_made.append(f"{medicine['original']} → {medicine['corrected']}")
        
        # Create correction summary
        correction_summary = verification_result.get('summary', 'No corrections made.')
        
        return ExtractMedsResponse(
            medicines=medicine_info_list,
            success=True,
            message=f"Successfully extracted and verified {len(medicine_info_list)} medicine(s)",
            count=len(medicine_info_list),
            correction_summary=correction_summary
        )
        
    except Exception as e:
        print(f"Error in extract_medicines endpoint: {str(e)}")
        # Return a graceful error response instead of 500
        return ExtractMedsResponse(
            medicines=[],
            success=False,
            message=f"Failed to process prescription: {str(e)}",
            count=0,
            correction_summary="Processing failed - please try again"
        )

@router.get("/extract-meds/test")
async def test_extract_medicines():
    """
    Test endpoint with sample prescription text
    """
    try:
        sample_text = """
        Rx: Amoxicillin 500mg
        Take 1 capsule 3 times daily for 7 days
        
        Also: Ibuprofen 400mg
        Take 1 tablet as needed for pain
        
        And: Omeprazole 20mg
        Take 1 capsule daily before breakfast
        """
        
        medicines = gpt_processor.extract_medicines(sample_text)
        
        return ExtractMedsResponse(
            medicines=medicines,
            success=True,
            message=f"Test successful - extracted {len(medicines)} medicine(s)",
            count=len(medicines)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test failed: {str(e)}"
        )