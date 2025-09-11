import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

class GoogleCalendarIntegration:
    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/calendar']
        self.client_config = {
            "web": {
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:3000/auth/google/callback"]
            }
        }
        
    def get_authorization_url(self, state: str = None) -> str:
        """
        Generate Google OAuth authorization URL
        
        Args:
            state: Optional state parameter for security
            
        Returns:
            Authorization URL for Google OAuth
        """
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                state=state
            )
            flow.redirect_uri = "http://localhost:3000/auth/google/callback"
            
            authorization_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            return authorization_url
            
        except Exception as e:
            print(f"Error generating authorization URL: {e}")
            return None
    
    def exchange_code_for_tokens(self, authorization_code: str, state: str = None) -> Dict[str, Any]:
        """
        Exchange authorization code for access tokens
        
        Args:
            authorization_code: Code received from Google OAuth callback
            state: State parameter for verification
            
        Returns:
            Dictionary containing token information
        """
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                state=state
            )
            flow.redirect_uri = "http://localhost:3000/auth/google/callback"
            
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            
            return {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
                "expiry": credentials.expiry.isoformat() if credentials.expiry else None
            }
            
        except Exception as e:
            print(f"Error exchanging code for tokens: {e}")
            return None
    
    def create_exercise_events(self, 
                             credentials_dict: Dict[str, Any], 
                             exercise_plan: Dict[str, Any],
                             start_date: datetime = None,
                             timezone: str = "UTC") -> List[Dict[str, Any]]:
        """
        Create calendar events for exercise recommendations
        
        Args:
            credentials_dict: Google OAuth credentials
            exercise_plan: Exercise plan with weekly schedule
            start_date: Start date for scheduling (defaults to tomorrow)
            timezone: Timezone for events
            
        Returns:
            List of created event details
        """
        try:
            # Reconstruct credentials
            credentials = Credentials(
                token=credentials_dict.get('access_token'),
                refresh_token=credentials_dict.get('refresh_token'),
                token_uri=credentials_dict.get('token_uri'),
                client_id=credentials_dict.get('client_id'),
                client_secret=credentials_dict.get('client_secret'),
                scopes=credentials_dict.get('scopes')
            )
            
            # Build the Calendar service
            service = build('calendar', 'v3', credentials=credentials)
            
            # Default start date to tomorrow
            if start_date is None:
                start_date = datetime.now() + timedelta(days=1)
            
            created_events = []
            weekly_plan = exercise_plan.get('weekly_plan', {})
            daily_exercises = exercise_plan.get('daily_exercises', [])
            
            # Create a mapping of exercise names to details
            exercise_details = {ex['name']: ex for ex in daily_exercises}
            
            # Days of the week mapping
            days_mapping = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            # Create events for the next 4 weeks
            for week in range(4):
                for day_name, exercises in weekly_plan.items():
                    if day_name.lower() in days_mapping:
                        day_offset = days_mapping[day_name.lower()]
                        event_date = start_date + timedelta(days=(week * 7) + day_offset)
                        
                        for exercise_name in exercises:
                            if exercise_name in exercise_details:
                                exercise = exercise_details[exercise_name]
                                
                                # Determine event time based on time_of_day
                                time_of_day = exercise.get('time_of_day', 'morning')
                                if time_of_day == 'morning':
                                    event_time = event_date.replace(hour=8, minute=0)
                                elif time_of_day == 'afternoon':
                                    event_time = event_date.replace(hour=14, minute=0)
                                else:  # evening
                                    event_time = event_date.replace(hour=18, minute=0)
                                
                                # Calculate end time based on duration
                                duration_str = exercise.get('duration', '15 minutes')
                                duration_minutes = self._parse_duration(duration_str)
                                end_time = event_time + timedelta(minutes=duration_minutes)
                                
                                # Create event
                                event = {
                                    'summary': f"Exercise: {exercise['name']}",
                                    'description': f"{exercise['description']}\n\nBenefits: {exercise['benefits']}\n\nPrecautions: {exercise['precautions']}",
                                    'start': {
                                        'dateTime': event_time.isoformat(),
                                        'timeZone': timezone,
                                    },
                                    'end': {
                                        'dateTime': end_time.isoformat(),
                                        'timeZone': timezone,
                                    },
                                    'reminders': {
                                        'useDefault': False,
                                        'overrides': [
                                            {'method': 'popup', 'minutes': 15},
                                            {'method': 'popup', 'minutes': 5},
                                        ],
                                    },
                                    'colorId': '4'  # Light green color for health events
                                }
                                
                                # Insert event
                                created_event = service.events().insert(
                                    calendarId='primary',
                                    body=event
                                ).execute()
                                
                                created_events.append({
                                    'event_id': created_event['id'],
                                    'event_link': created_event.get('htmlLink'),
                                    'exercise_name': exercise['name'],
                                    'date': event_time.date().isoformat(),
                                    'time': event_time.time().isoformat()
                                })
            
            return created_events
            
        except HttpError as error:
            print(f"Google Calendar API error: {error}")
            return []
        except Exception as e:
            print(f"Error creating exercise events: {e}")
            return []
    
    def _parse_duration(self, duration_str: str) -> int:
        """
        Parse duration string and return minutes
        
        Args:
            duration_str: Duration string like "10-15 minutes" or "30 minutes"
            
        Returns:
            Duration in minutes
        """
        try:
            # Extract numbers from duration string
            import re
            numbers = re.findall(r'\d+', duration_str)
            if numbers:
                # If range (e.g., "10-15 minutes"), take the average
                if len(numbers) >= 2:
                    return (int(numbers[0]) + int(numbers[1])) // 2
                else:
                    return int(numbers[0])
            return 15  # Default duration
        except:
            return 15
    
    def delete_exercise_events(self, credentials_dict: Dict[str, Any], event_ids: List[str]) -> bool:
        """
        Delete exercise events from calendar
        
        Args:
            credentials_dict: Google OAuth credentials
            event_ids: List of event IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            credentials = Credentials(
                token=credentials_dict.get('access_token'),
                refresh_token=credentials_dict.get('refresh_token'),
                token_uri=credentials_dict.get('token_uri'),
                client_id=credentials_dict.get('client_id'),
                client_secret=credentials_dict.get('client_secret'),
                scopes=credentials_dict.get('scopes')
            )
            
            service = build('calendar', 'v3', credentials=credentials)
            
            for event_id in event_ids:
                service.events().delete(
                    calendarId='primary',
                    eventId=event_id
                ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error deleting exercise events: {e}")
            return False

# Global instance
google_calendar = GoogleCalendarIntegration()