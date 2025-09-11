from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from utils.google_calendar import google_calendar
from pydantic import BaseModel

router = APIRouter()

class CalendarAuthRequest(BaseModel):
    state: Optional[str] = None

class CalendarTokenRequest(BaseModel):
    authorization_code: str
    state: Optional[str] = None

class CreateEventsRequest(BaseModel):
    credentials: Dict[str, Any]
    exercise_plan: Dict[str, Any]
    start_date: Optional[str] = None
    timezone: Optional[str] = "UTC"

class DeleteEventsRequest(BaseModel):
    credentials: Dict[str, Any]
    event_ids: List[str]

@router.post("/calendar/auth-url")
async def get_calendar_auth_url(request: CalendarAuthRequest):
    """
    Get Google Calendar authorization URL
    
    Returns:
        Authorization URL for Google OAuth
    """
    try:
        auth_url = google_calendar.get_authorization_url(request.state)
        
        if not auth_url:
            raise HTTPException(status_code=500, detail="Failed to generate authorization URL")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "authorization_url": auth_url
            }
        )
        
    except Exception as e:
        print(f"Error getting calendar auth URL: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/api/v1/calendar/exchange-token")
async def exchange_calendar_token(request: CalendarTokenRequest):
    """
    Exchange authorization code for access tokens
    
    Args:
        request: Contains authorization code and optional state
        
    Returns:
        Access tokens and credentials
    """
    try:
        tokens = google_calendar.exchange_code_for_tokens(
            request.authorization_code, 
            request.state
        )
        
        if not tokens:
            raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "credentials": tokens
            }
        )
        
    except Exception as e:
        print(f"Error exchanging calendar token: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/calendar/create-exercise-events")
async def create_exercise_events(request: CreateEventsRequest):
    """
    Create calendar events for exercise recommendations
    
    Args:
        request: Contains credentials, exercise plan, and scheduling options
        
    Returns:
        List of created calendar events
    """
    try:
        # Parse start date if provided
        start_date = None
        if request.start_date:
            try:
                start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
        
        # Create calendar events
        created_events = google_calendar.create_exercise_events(
            credentials_dict=request.credentials,
            exercise_plan=request.exercise_plan,
            start_date=start_date,
            timezone=request.timezone
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "created_events": created_events,
                "total_events": len(created_events)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating exercise events: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/calendar/delete-exercise-events")
async def delete_exercise_events(request: DeleteEventsRequest):
    """
    Delete exercise events from calendar
    
    Args:
        request: Contains credentials and event IDs to delete
        
    Returns:
        Success status
    """
    try:
        success = google_calendar.delete_exercise_events(
            credentials_dict=request.credentials,
            event_ids=request.event_ids
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete some or all events")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "deleted_events": len(request.event_ids)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting exercise events: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/calendar/callback")
async def calendar_callback(request: Request):
    """
    Handle Google OAuth callback (for web flow)
    
    This endpoint can be used for web-based OAuth flows
    """
    try:
        # Get query parameters
        code = request.query_params.get('code')
        state = request.query_params.get('state')
        error = request.query_params.get('error')
        
        if error:
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
        
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not provided")
        
        # Exchange code for tokens
        tokens = google_calendar.exchange_code_for_tokens(code, state)
        
        if not tokens:
            raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
        
        # In a real application, you might want to store these tokens securely
        # and redirect to a success page with the tokens or a success message
        
        # For now, return the tokens as JSON
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Calendar integration successful",
                "credentials": tokens
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in calendar callback: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/calendar/status")
async def calendar_integration_status():
    """
    Check if Google Calendar integration is properly configured
    
    Returns:
        Configuration status
    """
    try:
        import os
        
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        
        configured = bool(client_id and client_secret)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "configured": configured,
                "client_id_set": bool(client_id),
                "client_secret_set": bool(client_secret)
            }
        )
        
    except Exception as e:
        print(f"Error checking calendar status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")