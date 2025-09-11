from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.ocr import ocr_processor

router = APIRouter()

class OCRResponse(BaseModel):
    text: str
    success: bool
    message: str

@router.post("/ocr", response_model=OCRResponse)
async def extract_text_from_image(file: UploadFile = File(...)):
    """
    Extract text from uploaded prescription image using OCR
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400, 
                detail="File must be an image (JPEG, PNG, etc.)"
            )
        
        # Read file content
        image_data = await file.read()
        
        # Extract text using OCR
        extracted_text = ocr_processor.extract_text_from_image(image_data)
        
        if not extracted_text.strip():
            return OCRResponse(
                text="",
                success=False,
                message="No text could be extracted from the image. Please ensure the image is clear and contains readable text."
            )
        
        return OCRResponse(
            text=extracted_text,
            success=True,
            message="Text extracted successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(e)}"
        )

@router.post("/ocr/base64", response_model=OCRResponse)
async def extract_text_from_base64(request: dict):
    """
    Extract text from base64 encoded image
    """
    try:
        base64_string = request.get("image")
        if not base64_string:
            raise HTTPException(
                status_code=400,
                detail="Base64 image string is required"
            )
        
        # Extract text using OCR
        extracted_text = ocr_processor.extract_text_from_base64(base64_string)
        
        if not extracted_text.strip():
            return OCRResponse(
                text="",
                success=False,
                message="No text could be extracted from the image. Please ensure the image is clear and contains readable text."
            )
        
        return OCRResponse(
            text=extracted_text,
            success=True,
            message="Text extracted successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(e)}"
        ) 