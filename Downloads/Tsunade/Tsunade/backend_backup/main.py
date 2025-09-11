from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pytesseract
from PIL import Image
import io
import os
from typing import Optional
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Medical OCR and Chat API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configure Tesseract path if needed
if os.name == 'nt':  # Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

@app.get("/")
async def root():
    return {"message": "Medical OCR and Chat API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "medical-ocr-chat-api"}

@app.post("/api/v1/ocr")
async def extract_text_from_image(file: UploadFile = File(...)):
    """
    Extract text from uploaded prescription image using OCR
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image file
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Perform OCR
        extracted_text = pytesseract.image_to_string(image)
        
        if not extracted_text.strip():
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "extracted_text": "",
                    "message": "No text found in the image"
                }
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "extracted_text": extracted_text.strip(),
                "message": "Text extracted successfully"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@app.post("/api/v1/chat")
async def chat_with_ai(request: dict):
    """
    Chat with AI assistant about medical prescriptions
    """
    try:
        user_message = request.get('message', '')
        extracted_text = request.get('extracted_text', '')
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Prepare system prompt
        if extracted_text:
            system_prompt = f"""You are a helpful medical assistant. The user has uploaded a prescription image with the following extracted text:

{extracted_text}

Please help the user understand their prescription, including medication names, dosages, instructions, and any other relevant information. Always remind users to consult with their healthcare provider for medical advice."""
        else:
            system_prompt = "You are a helpful medical assistant. Please provide helpful information about medications, prescriptions, and general health topics. Always remind users to consult with their healthcare provider for medical advice."
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "response": ai_response,
                "message": "Chat response generated successfully"
            }
        )
        
    except Exception as e:
        if "No API key provided" in str(e):
            raise HTTPException(status_code=401, detail="OpenAI API key not configured")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)