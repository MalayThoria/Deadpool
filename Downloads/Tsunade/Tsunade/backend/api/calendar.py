from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4
from enum import Enum
import json

from database.config import get_sync_db
from database.models import User, CalendarEvent
from auth.auth import current_active_user

router = APIRouter()

# Enums
class EventType(str, Enum):
    APPOINTMENT = "appointment"
    MEDICATION = "medication"
    EXERCISE = "exercise"
    CHECKUP = "checkup"
    REMINDER = "reminder"
    THERAPY = "therapy"
    VACCINATION = "vaccination"
    LAB_TEST = "lab_test"
    FOLLOW_UP = "follow_up"
    PERSONAL = "personal"

class EventPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class RecurrenceType(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

# Pydantic models
class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    event_type: EventType
    start_datetime: datetime
    end_datetime: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=200)
    priority: EventPriority = EventPriority.MEDIUM
    is_all_day: bool = False
    reminder_minutes: Optional[int] = Field(None, ge=0, le=10080)  # Max 1 week
    recurrence_type: RecurrenceType = RecurrenceType.NONE
    recurrence_end_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)
    attendees: Optional[List[str]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
    
    @validator('end_datetime')
    def validate_end_datetime(cls, v, values):
        if v and 'start_datetime' in values and v <= values['start_datetime']:
            raise ValueError('End datetime must be after start datetime')
        return v
    
    @validator('recurrence_end_date')
    def validate_recurrence_end_date(cls, v, values):
        if v and 'start_datetime' in values and v <= values['start_datetime'].date():
            raise ValueError('Recurrence end date must be after start date')
        return v

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    event_type: Optional[EventType] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=200)
    priority: Optional[EventPriority] = None
    is_all_day: Optional[bool] = None
    reminder_minutes: Optional[int] = Field(None, ge=0, le=10080)
    recurrence_type: Optional[RecurrenceType] = None
    recurrence_end_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=500)
    attendees: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_completed: Optional[bool] = None

class EventResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    event_type: EventType
    start_datetime: datetime
    end_datetime: Optional[datetime]
    location: Optional[str]
    priority: EventPriority
    is_all_day: bool
    reminder_minutes: Optional[int]
    recurrence_type: RecurrenceType
    recurrence_end_date: Optional[date]
    notes: Optional[str]
    attendees: List[str]
    tags: List[str]
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class CalendarView(BaseModel):
    date: date
    events: List[EventResponse]
    event_count: int
    has_urgent_events: bool
    has_appointments: bool

class MonthlyCalendar(BaseModel):
    year: int
    month: int
    days: List[CalendarView]
    total_events: int
    event_types_summary: Dict[str, int]
    upcoming_important_events: List[EventResponse]

class EventStats(BaseModel):
    total_events: int
    completed_events: int
    upcoming_events: int
    overdue_events: int
    events_by_type: Dict[str, int]
    events_by_priority: Dict[str, int]
    completion_rate: float
    most_common_event_type: Optional[str]
    busiest_day_of_week: Optional[str]

class ReminderSettings(BaseModel):
    default_reminder_minutes: int = Field(15, ge=0, le=10080)
    email_reminders: bool = True
    push_reminders: bool = True
    sms_reminders: bool = False
    reminder_sound: Optional[str] = "default"

# Helper functions
def generate_recurring_events(event: CalendarEvent, end_date: date) -> List[Dict]:
    """Generate recurring event instances."""
    events = []
    current_date = event.start_datetime.date()
    
    while current_date <= end_date:
        if event.recurrence_type == RecurrenceType.DAILY:
            current_date += timedelta(days=1)
        elif event.recurrence_type == RecurrenceType.WEEKLY:
            current_date += timedelta(weeks=1)
        elif event.recurrence_type == RecurrenceType.MONTHLY:
            # Simple monthly increment (same day of month)
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        elif event.recurrence_type == RecurrenceType.YEARLY:
            current_date = current_date.replace(year=current_date.year + 1)
        else:
            break
        
        if current_date <= end_date:
            # Calculate time difference
            time_diff = event.end_datetime - event.start_datetime if event.end_datetime else timedelta(hours=1)
            start_datetime = datetime.combine(current_date, event.start_datetime.time())
            end_datetime = start_datetime + time_diff if event.end_datetime else None
            
            events.append({
                "id": str(uuid4()),
                "title": event.title,
                "description": event.description,
                "event_type": event.event_type,
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
                "location": event.location,
                "priority": event.priority,
                "is_all_day": event.is_all_day,
                "reminder_minutes": event.reminder_minutes,
                "notes": event.notes,
                "attendees": event.attendees or [],
                "tags": event.tags or [],
                "is_completed": False,
                "is_recurring_instance": True,
                "parent_event_id": str(event.id)
            })
    
    return events

def get_events_for_date_range(db: Session, user_id: UUID, start_date: date, end_date: date) -> List[Dict]:
    """Get all events (including recurring instances) for a date range."""
    # Get base events
    events = db.query(CalendarEvent).filter(
        and_(
            CalendarEvent.user_id == user_id,
            or_(
                and_(
                    CalendarEvent.start_datetime >= datetime.combine(start_date, datetime.min.time()),
                    CalendarEvent.start_datetime <= datetime.combine(end_date, datetime.max.time())
                ),
                and_(
                    CalendarEvent.recurrence_type != RecurrenceType.NONE,
                    CalendarEvent.start_datetime <= datetime.combine(end_date, datetime.max.time()),
                    or_(
                        CalendarEvent.recurrence_end_date.is_(None),
                        CalendarEvent.recurrence_end_date >= start_date
                    )
                )
            )
        )
    ).all()
    
    all_events = []
    
    for event in events:
        # Add the original event if it falls in the range
        if start_date <= event.start_datetime.date() <= end_date:
            all_events.append({
                "id": str(event.id),
                "title": event.title,
                "description": event.description,
                "event_type": event.event_type,
                "start_datetime": event.start_datetime,
                "end_datetime": event.end_datetime,
                "location": event.location,
                "priority": event.priority,
                "is_all_day": event.is_all_day,
                "reminder_minutes": event.reminder_minutes,
                "notes": event.notes,
                "attendees": event.attendees or [],
                "tags": event.tags or [],
                "is_completed": event.is_completed,
                "is_recurring_instance": False,
                "parent_event_id": None
            })
        
        # Generate recurring instances
        if event.recurrence_type != RecurrenceType.NONE:
            recurring_end = event.recurrence_end_date or end_date
            recurring_events = generate_recurring_events(event, min(recurring_end, end_date))
            all_events.extend(recurring_events)
    
    return all_events

# API endpoints
@router.post("/events", response_model=EventResponse)
async def create_event(
    event_data: EventCreate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Create a new calendar event."""
    event = CalendarEvent(
        user_id=current_user.id,
        title=event_data.title,
        description=event_data.description,
        event_type=event_data.event_type,
        start_datetime=event_data.start_datetime,
        end_datetime=event_data.end_datetime,
        location=event_data.location,
        priority=event_data.priority,
        is_all_day=event_data.is_all_day,
        reminder_minutes=event_data.reminder_minutes,
        recurrence_type=event_data.recurrence_type,
        recurrence_end_date=event_data.recurrence_end_date,
        notes=event_data.notes,
        attendees=event_data.attendees,
        tags=event_data.tags
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return event

# Simplified endpoint for prescription integration
class SimpleEventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_datetime: datetime
    duration_minutes: int = 60
    recurrence: Optional[str] = None

@router.post("/create-event")
async def create_simple_event(
    event_data: SimpleEventCreate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Create a simple calendar event for prescription integration."""
    end_datetime = event_data.start_datetime + timedelta(minutes=event_data.duration_minutes)
    
    # Map recurrence to RecurrenceType
    recurrence_type = RecurrenceType.NONE
    if event_data.recurrence:
        if event_data.recurrence.lower() == 'daily':
            recurrence_type = RecurrenceType.DAILY
        elif event_data.recurrence.lower() == 'weekly':
            recurrence_type = RecurrenceType.WEEKLY
    
    event = CalendarEvent(
        user_id=current_user.id,
        title=event_data.title,
        description=event_data.description,
        event_type=EventType.MEDICATION,
        start_datetime=event_data.start_datetime,
        end_datetime=end_datetime,
        priority=EventPriority.MEDIUM,
        is_all_day=False,
        reminder_minutes=15,
        recurrence_type=recurrence_type,
        notes="Auto-created from prescription analysis"
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return {
        "success": True,
        "event_id": event.id,
        "title": event.title,
        "start_datetime": event.start_datetime,
        "end_datetime": event.end_datetime
    }

@router.get("/events", response_model=List[EventResponse])
async def get_events(
    start_date: Optional[date] = Query(None, description="Start date for filtering events"),
    end_date: Optional[date] = Query(None, description="End date for filtering events"),
    event_type: Optional[EventType] = Query(None, description="Filter by event type"),
    priority: Optional[EventPriority] = Query(None, description="Filter by priority"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get user's calendar events with optional filtering."""
    query = db.query(CalendarEvent).filter(CalendarEvent.user_id == current_user.id)
    
    if start_date:
        query = query.filter(CalendarEvent.start_datetime >= datetime.combine(start_date, datetime.min.time()))
    
    if end_date:
        query = query.filter(CalendarEvent.start_datetime <= datetime.combine(end_date, datetime.max.time()))
    
    if event_type:
        query = query.filter(CalendarEvent.event_type == event_type)
    
    if priority:
        query = query.filter(CalendarEvent.priority == priority)
    
    if completed is not None:
        query = query.filter(CalendarEvent.is_completed == completed)
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        for tag in tag_list:
            query = query.filter(CalendarEvent.tags.contains([tag]))
    
    events = query.order_by(CalendarEvent.start_datetime).offset(offset).limit(limit).all()
    return events

@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get a specific calendar event."""
    event = db.query(CalendarEvent).filter(
        and_(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id
        )
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return event

@router.put("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    event_data: EventUpdate,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Update a calendar event."""
    event = db.query(CalendarEvent).filter(
        and_(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id
        )
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Update fields
    update_data = event_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    
    event.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(event)
    
    return event

@router.delete("/events/{event_id}")
async def delete_event(
    event_id: UUID,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Delete a calendar event."""
    event = db.query(CalendarEvent).filter(
        and_(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id
        )
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    db.delete(event)
    db.commit()
    
    return {"message": "Event deleted successfully"}

@router.post("/events/{event_id}/complete")
async def mark_event_complete(
    event_id: UUID,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Mark an event as completed."""
    event = db.query(CalendarEvent).filter(
        and_(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id
        )
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    event.is_completed = True
    event.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Event marked as completed"}

@router.get("/calendar/month/{year}/{month}", response_model=MonthlyCalendar)
async def get_monthly_calendar(
    year: int,
    month: int,
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get calendar view for a specific month."""
    if not (1 <= month <= 12):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12"
        )
    
    # Calculate month boundaries
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    # Get all events for the month
    all_events = get_events_for_date_range(db, current_user.id, start_date, end_date)
    
    # Group events by date
    events_by_date = {}
    for event in all_events:
        event_date = event["start_datetime"].date()
        if event_date not in events_by_date:
            events_by_date[event_date] = []
        events_by_date[event_date].append(event)
    
    # Create calendar days
    days = []
    current_date = start_date
    while current_date <= end_date:
        day_events = events_by_date.get(current_date, [])
        
        days.append(CalendarView(
            date=current_date,
            events=[EventResponse(**event) for event in day_events],
            event_count=len(day_events),
            has_urgent_events=any(event["priority"] == "urgent" for event in day_events),
            has_appointments=any(event["event_type"] == "appointment" for event in day_events)
        ))
        
        current_date += timedelta(days=1)
    
    # Calculate summary statistics
    total_events = len(all_events)
    event_types_summary = {}
    for event in all_events:
        event_type = event["event_type"]
        event_types_summary[event_type] = event_types_summary.get(event_type, 0) + 1
    
    # Get upcoming important events (next 7 days from end of month)
    upcoming_start = end_date + timedelta(days=1)
    upcoming_end = upcoming_start + timedelta(days=7)
    upcoming_events = get_events_for_date_range(db, current_user.id, upcoming_start, upcoming_end)
    important_upcoming = [
        EventResponse(**event) for event in upcoming_events
        if event["priority"] in ["high", "urgent"] or event["event_type"] == "appointment"
    ][:5]  # Limit to 5 events
    
    return MonthlyCalendar(
        year=year,
        month=month,
        days=days,
        total_events=total_events,
        event_types_summary=event_types_summary,
        upcoming_important_events=important_upcoming
    )

@router.get("/calendar/today", response_model=CalendarView)
async def get_today_events(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get today's calendar events."""
    today = date.today()
    events = get_events_for_date_range(db, current_user.id, today, today)
    
    return CalendarView(
        date=today,
        events=[EventResponse(**event) for event in events],
        event_count=len(events),
        has_urgent_events=any(event["priority"] == "urgent" for event in events),
        has_appointments=any(event["event_type"] == "appointment" for event in events)
    )

@router.get("/calendar/upcoming", response_model=List[EventResponse])
async def get_upcoming_events(
    days: int = Query(7, ge=1, le=30, description="Number of days to look ahead"),
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get upcoming events for the next N days."""
    start_date = date.today()
    end_date = start_date + timedelta(days=days)
    
    events = get_events_for_date_range(db, current_user.id, start_date, end_date)
    
    # Sort by start datetime and filter out completed events
    upcoming_events = [
        EventResponse(**event) for event in events
        if not event["is_completed"] and event["start_datetime"] >= datetime.now()
    ]
    
    return sorted(upcoming_events, key=lambda x: x.start_datetime)

@router.get("/calendar/stats", response_model=EventStats)
async def get_calendar_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get calendar statistics and analytics."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    events = get_events_for_date_range(db, current_user.id, start_date, end_date)
    
    total_events = len(events)
    completed_events = len([e for e in events if e["is_completed"]])
    upcoming_events = len([e for e in events if e["start_datetime"] > datetime.now() and not e["is_completed"]])
    overdue_events = len([e for e in events if e["start_datetime"] < datetime.now() and not e["is_completed"]])
    
    # Events by type
    events_by_type = {}
    for event in events:
        event_type = event["event_type"]
        events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
    
    # Events by priority
    events_by_priority = {}
    for event in events:
        priority = event["priority"]
        events_by_priority[priority] = events_by_priority.get(priority, 0) + 1
    
    # Completion rate
    completion_rate = (completed_events / total_events * 100) if total_events > 0 else 0
    
    # Most common event type
    most_common_type = max(events_by_type.items(), key=lambda x: x[1])[0] if events_by_type else None
    
    # Busiest day of week
    day_counts = {}
    for event in events:
        day_name = event["start_datetime"].strftime("%A")
        day_counts[day_name] = day_counts.get(day_name, 0) + 1
    
    busiest_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
    
    return EventStats(
        total_events=total_events,
        completed_events=completed_events,
        upcoming_events=upcoming_events,
        overdue_events=overdue_events,
        events_by_type=events_by_type,
        events_by_priority=events_by_priority,
        completion_rate=round(completion_rate, 1),
        most_common_event_type=most_common_type,
        busiest_day_of_week=busiest_day
    )

@router.get("/reminders/due", response_model=List[EventResponse])
async def get_due_reminders(
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Get events with due reminders."""
    now = datetime.utcnow()
    
    # Get events with reminders that are due
    events = db.query(CalendarEvent).filter(
        and_(
            CalendarEvent.user_id == current_user.id,
            CalendarEvent.reminder_minutes.isnot(None),
            CalendarEvent.is_completed == False,
            CalendarEvent.start_datetime > now,
            CalendarEvent.start_datetime <= now + timedelta(minutes=60)  # Next hour
        )
    ).all()
    
    due_reminders = []
    for event in events:
        reminder_time = event.start_datetime - timedelta(minutes=event.reminder_minutes)
        if reminder_time <= now:
            due_reminders.append(event)
    
    return due_reminders

@router.post("/events/bulk-create")
async def bulk_create_events(
    events_data: List[EventCreate],
    current_user: User = Depends(current_active_user),
    db: Session = Depends(get_sync_db)
):
    """Create multiple events at once."""
    if len(events_data) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create more than 50 events at once"
        )
    
    created_events = []
    for event_data in events_data:
        event = CalendarEvent(
            user_id=current_user.id,
            **event_data.dict()
        )
        db.add(event)
        created_events.append(event)
    
    db.commit()
    
    for event in created_events:
        db.refresh(event)
    
    return {
        "message": f"Successfully created {len(created_events)} events",
        "events": [EventResponse.from_orm(event) for event in created_events]
    }
