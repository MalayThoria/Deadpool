from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Rx Assistant API",
    description="Healthcare chatbot API for prescription analysis",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes
from backend.routes import ocr, extract_meds, med_info, chat

app.include_router(ocr.router, prefix="/api/v1", tags=["OCR"])
app.include_router(extract_meds.router, prefix="/api/v1", tags=["Medicine Extraction"])
app.include_router(med_info.router, prefix="/api/v1", tags=["Medicine Information"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])

@app.get("/")
async def root():
    return {"message": "Rx Assistant API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Rx Assistant API"} 