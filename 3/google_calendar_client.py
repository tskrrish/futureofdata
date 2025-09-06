"""
Google Calendar API client for YMCA volunteer shift synchronization
Handles OAuth2 authentication and calendar operations
"""
import os
import pickle
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

class GoogleCalendarClient:
    """Google Calendar API client with OAuth2 authentication"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self, credentials_file: str = None):
        # Use config if available, otherwise use default
        try:
            from config import settings
            self.credentials_file = credentials_file or settings.GOOGLE_CREDENTIALS_PATH
        except ImportError:
            self.credentials_file = credentials_file or "google_credentials.json"
        
        self.token_dir = "tokens"
        self.service = None
        
        # Create tokens directory if it doesn't exist
        if not os.path.exists(self.token_dir):
            os.makedirs(self.token_dir)
    
    def get_authorization_url(self, user_id: str, redirect_uri: str) -> str:
        """Get OAuth2 authorization URL for a user"""
        try:
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )
            flow.state = user_id  # Use user_id as state for security
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'  # Force consent to get refresh token
            )
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {e}")
            raise
    
    def exchange_code_for_tokens(self, user_id: str, authorization_code: str, redirect_uri: str) -> Dict:
        """Exchange authorization code for access/refresh tokens"""
        try:
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )
            
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Save credentials for this user
            self._save_credentials(user_id, credentials)
            
            return {
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'expires_at': credentials.expiry.isoformat() if credentials.expiry else None,
                'scopes': credentials.scopes
            }
            
        except Exception as e:
            logger.error(f"Error exchanging authorization code: {e}")
            raise
    
    def _save_credentials(self, user_id: str, credentials: Credentials):
        """Save user credentials to disk"""
        token_file = os.path.join(self.token_dir, f"token_{user_id}.pickle")
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)
    
    def _load_credentials(self, user_id: str) -> Optional[Credentials]:
        """Load user credentials from disk"""
        token_file = os.path.join(self.token_dir, f"token_{user_id}.pickle")
        
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                credentials = pickle.load(token)
                
                # Refresh token if expired
                if credentials and credentials.expired and credentials.refresh_token:
                    try:
                        credentials.refresh(Request())
                        self._save_credentials(user_id, credentials)
                    except Exception as e:
                        logger.error(f"Error refreshing credentials for user {user_id}: {e}")
                        return None
                
                return credentials
        
        return None
    
    def get_service(self, user_id: str):
        """Get authenticated Google Calendar service for a user"""
        credentials = self._load_credentials(user_id)
        
        if not credentials or not credentials.valid:
            raise Exception(f"No valid credentials found for user {user_id}")
        
        return build('calendar', 'v3', credentials=credentials)
    
    def list_calendars(self, user_id: str) -> List[Dict]:
        """List all calendars for a user"""
        try:
            service = self.get_service(user_id)
            calendar_list = service.calendarList().list().execute()
            
            calendars = []
            for calendar_item in calendar_list.get('items', []):
                calendars.append({
                    'id': calendar_item['id'],
                    'summary': calendar_item['summary'],
                    'primary': calendar_item.get('primary', False),
                    'access_role': calendar_item.get('accessRole', 'reader')
                })
            
            return calendars
            
        except HttpError as e:
            logger.error(f"Error listing calendars for user {user_id}: {e}")
            raise
    
    def create_event(self, user_id: str, calendar_id: str, event_data: Dict) -> Dict:
        """Create a calendar event"""
        try:
            service = self.get_service(user_id)
            
            event = {
                'summary': event_data.get('title', 'Volunteer Shift'),
                'description': event_data.get('description', ''),
                'location': event_data.get('location', ''),
                'start': {
                    'dateTime': event_data['start_time'],
                    'timeZone': event_data.get('timezone', 'America/New_York'),
                },
                'end': {
                    'dateTime': event_data['end_time'],
                    'timeZone': event_data.get('timezone', 'America/New_York'),
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours before
                        {'method': 'popup', 'minutes': 30},      # 30 minutes before
                    ],
                },
            }
            
            # Add attendees if provided
            if 'attendees' in event_data:
                event['attendees'] = [{'email': email} for email in event_data['attendees']]
            
            # Add source metadata
            event['extendedProperties'] = {
                'private': {
                    'ymca_volunteer_shift': 'true',
                    'ymca_project_id': str(event_data.get('project_id', '')),
                    'ymca_shift_id': str(event_data.get('shift_id', '')),
                    'ymca_branch': event_data.get('branch', '')
                }
            }
            
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=event,
                sendUpdates='all'
            ).execute()
            
            return {
                'event_id': created_event['id'],
                'html_link': created_event.get('htmlLink'),
                'created': created_event.get('created'),
                'updated': created_event.get('updated')
            }
            
        except HttpError as e:
            logger.error(f"Error creating event for user {user_id}: {e}")
            raise
    
    def update_event(self, user_id: str, calendar_id: str, event_id: str, event_data: Dict) -> Dict:
        """Update an existing calendar event"""
        try:
            service = self.get_service(user_id)
            
            # Get existing event first
            existing_event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Update fields
            existing_event.update({
                'summary': event_data.get('title', existing_event.get('summary')),
                'description': event_data.get('description', existing_event.get('description')),
                'location': event_data.get('location', existing_event.get('location')),
            })
            
            if 'start_time' in event_data:
                existing_event['start'] = {
                    'dateTime': event_data['start_time'],
                    'timeZone': event_data.get('timezone', 'America/New_York'),
                }
            
            if 'end_time' in event_data:
                existing_event['end'] = {
                    'dateTime': event_data['end_time'],
                    'timeZone': event_data.get('timezone', 'America/New_York'),
                }
            
            updated_event = service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=existing_event,
                sendUpdates='all'
            ).execute()
            
            return {
                'event_id': updated_event['id'],
                'html_link': updated_event.get('htmlLink'),
                'updated': updated_event.get('updated')
            }
            
        except HttpError as e:
            logger.error(f"Error updating event {event_id} for user {user_id}: {e}")
            raise
    
    def delete_event(self, user_id: str, calendar_id: str, event_id: str) -> bool:
        """Delete a calendar event"""
        try:
            service = self.get_service(user_id)
            
            service.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendUpdates='all'
            ).execute()
            
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Event {event_id} not found for deletion")
                return True  # Event already doesn't exist
            logger.error(f"Error deleting event {event_id} for user {user_id}: {e}")
            raise
    
    def list_events(self, user_id: str, calendar_id: str, 
                   time_min: Optional[datetime] = None,
                   time_max: Optional[datetime] = None,
                   query: Optional[str] = None) -> List[Dict]:
        """List calendar events with optional filters"""
        try:
            service = self.get_service(user_id)
            
            # Default to next 30 days if no time range specified
            if time_min is None:
                time_min = datetime.utcnow()
            if time_max is None:
                time_max = time_min + timedelta(days=30)
            
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime',
                q=query
            ).execute()
            
            events = []
            for event in events_result.get('items', []):
                # Check if this is a YMCA volunteer shift
                extended_props = event.get('extendedProperties', {}).get('private', {})
                is_ymca_shift = extended_props.get('ymca_volunteer_shift') == 'true'
                
                event_data = {
                    'event_id': event['id'],
                    'title': event.get('summary', ''),
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'html_link': event.get('htmlLink'),
                    'created': event.get('created'),
                    'updated': event.get('updated'),
                    'is_ymca_shift': is_ymca_shift
                }
                
                # Parse start/end times
                start = event.get('start', {})
                end = event.get('end', {})
                
                if 'dateTime' in start:
                    event_data['start_time'] = start['dateTime']
                    event_data['start_timezone'] = start.get('timeZone')
                elif 'date' in start:
                    event_data['start_date'] = start['date']
                    event_data['all_day'] = True
                
                if 'dateTime' in end:
                    event_data['end_time'] = end['dateTime']
                    event_data['end_timezone'] = end.get('timeZone')
                elif 'date' in end:
                    event_data['end_date'] = end['date']
                
                # Add YMCA-specific metadata if present
                if is_ymca_shift:
                    event_data.update({
                        'project_id': extended_props.get('ymca_project_id'),
                        'shift_id': extended_props.get('ymca_shift_id'),
                        'branch': extended_props.get('ymca_branch')
                    })
                
                events.append(event_data)
            
            return events
            
        except HttpError as e:
            logger.error(f"Error listing events for user {user_id}: {e}")
            raise
    
    def is_user_authenticated(self, user_id: str) -> bool:
        """Check if user has valid Google Calendar authentication"""
        try:
            credentials = self._load_credentials(user_id)
            return credentials is not None and credentials.valid
        except Exception:
            return False
    
    def revoke_user_access(self, user_id: str) -> bool:
        """Revoke user's Google Calendar access and delete stored tokens"""
        try:
            credentials = self._load_credentials(user_id)
            
            if credentials and credentials.token:
                # Revoke the token
                revoke_request = Request()
                credentials.revoke(revoke_request)
            
            # Delete stored token file
            token_file = os.path.join(self.token_dir, f"token_{user_id}.pickle")
            if os.path.exists(token_file):
                os.remove(token_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Error revoking access for user {user_id}: {e}")
            return False