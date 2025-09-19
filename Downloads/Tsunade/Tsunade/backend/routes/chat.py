from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.gpt import gpt_processor

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    context: str = ""  # Optional context about medicines

class ChatResponse(BaseModel):
    response: str
    success: bool
    message: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest):
    """
    Chat with RX Assistant about medicines and health
    """
    try:
        if not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message is required"
            )
        
        # Create context-aware prompt
        context_prompt = ""
        if request.context:
            context_prompt = f"\n\nContext about your medicines: {request.context}"
        
        prompt = f"""
        You are RX Assistant, a certified healthcare AI assistant. A user is asking about their medicines or health.
        
        User question: {request.message}
        {context_prompt}
        
        Please provide a helpful, accurate, and friendly response. Remember:
        - Be professional but warm
        - Provide accurate medical information
        - Always recommend consulting a healthcare provider for specific medical advice
        - Include relevant safety warnings when appropriate
        - If you're not sure about something, say so and suggest consulting a doctor
        
        Respond in a conversational, helpful tone.
        """
        
        # Check if OpenAI client is available
        if gpt_processor.client is None:
            return ChatResponse(
                response="I'm sorry, but I'm currently unable to process your question due to a configuration issue. Please try again later or consult with your healthcare provider for immediate assistance.",
                success=False,
                message="OpenAI client not available"
            )
        
        # Get response from GPT
        response = gpt_processor.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are RX Assistant, a helpful healthcare AI that provides accurate medical information while always encouraging users to consult healthcare professionals for specific advice."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        assistant_response = response.choices[0].message.content.strip()
        
        return ChatResponse(
            response=assistant_response,
            success=True,
            message="Response generated successfully"
        )
        
    except Exception as e:
        return ChatResponse(
            response="I apologize, but I encountered an error while processing your question. Please try again or consult with your healthcare provider for assistance.",
            success=False,
            message=f"Chat processing failed: {str(e)}"
        )

@router.get("/chat/suggestions")
async def get_chat_suggestions():
    """
    Get suggested questions for the chat
    """
    suggestions = [
        "What are the common side effects of antibiotics?",
        "Can I take pain relievers with my other medicines?",
        "What should I do if I miss a dose?",
        "Are there any foods I should avoid with my medicine?",
        "How long does it take for medicine to work?",
        "What are the signs of an allergic reaction?",
        "Can I drink alcohol with my medicine?",
        "What should I do if I experience side effects?",
        "How should I store my medicines?",
        "When should I call my doctor?"
    ]
    
    return {
        "suggestions": suggestions,
        "success": True
    }