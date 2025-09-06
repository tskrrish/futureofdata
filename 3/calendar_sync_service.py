"""
Google Calendar Two-Way Sync Service for Volunteer Shifts
Handles bidirectional synchronization between YMCA volunteer shifts and Google Calendar
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from google_calendar_client import GoogleCalendarClient
from database import VolunteerDatabase
import json

logger = logging.getLogger(__name__)

class CalendarSyncService:
    """Service for managing two-way calendar synchronization"""
    
    def __init__(self, database: VolunteerDatabase, calendar_client: GoogleCalendarClient):
        self.database = database
        self.calendar_client = calendar_client
        self.sync_in_progress = set()  # Track ongoing sync operations
        
    async def sync_volunteer_shifts(self, user_id: str, sync_direction: str = 'bidirectional') -> Dict[str, Any]:
        """
        Synchronize volunteer shifts for a user
        
        Args:
            user_id: User ID to sync
            sync_direction: 'push_to_google', 'pull_from_google', or 'bidirectional'
            
        Returns:
            Sync result summary
        """
        if user_id in self.sync_in_progress:
            return {'status': 'error', 'message': 'Sync already in progress for this user'}
        
        self.sync_in_progress.add(user_id)
        
        try:
            # Check if user has Google Calendar authentication
            auth_data = await self.database.get_google_calendar_auth(user_id)
            if not auth_data or not auth_data.get('sync_enabled'):
                return {'status': 'error', 'message': 'Google Calendar not connected or sync disabled'}
            
            # Check if user's Google Calendar credentials are valid
            if not self.calendar_client.is_user_authenticated(user_id):
                return {'status': 'error', 'message': 'Google Calendar authentication expired'}
            
            calendar_id = auth_data.get('calendar_id', 'primary')
            sync_result = {
                'status': 'success',
                'user_id': user_id,
                'sync_direction': sync_direction,
                'operations': [],
                'errors': [],
                'summary': {
                    'created': 0,
                    'updated': 0,
                    'deleted': 0,
                    'conflicts': 0
                }
            }
            
            if sync_direction in ['push_to_google', 'bidirectional']:
                push_result = await self._push_shifts_to_google(user_id, calendar_id)
                sync_result['operations'].extend(push_result['operations'])
                sync_result['errors'].extend(push_result['errors'])
                for key in sync_result['summary']:
                    sync_result['summary'][key] += push_result['summary'].get(key, 0)
            
            if sync_direction in ['pull_from_google', 'bidirectional']:
                pull_result = await self._pull_shifts_from_google(user_id, calendar_id)
                sync_result['operations'].extend(pull_result['operations'])
                sync_result['errors'].extend(pull_result['errors'])
                for key in sync_result['summary']:
                    sync_result['summary'][key] += pull_result['summary'].get(key, 0)
            
            # Log sync completion
            await self.database.log_calendar_sync({
                'user_id': user_id,
                'sync_type': sync_direction,
                'operation': 'sync_complete',
                'status': 'success' if not sync_result['errors'] else 'partial',
                'sync_details': sync_result['summary']
            })
            
            return sync_result
            
        except Exception as e:
            logger.error(f"Error syncing volunteer shifts for user {user_id}: {e}")
            await self.database.log_calendar_sync({
                'user_id': user_id,
                'sync_type': sync_direction,
                'operation': 'sync_complete',
                'status': 'error',
                'error_message': str(e)
            })
            return {'status': 'error', 'message': f'Sync failed: {str(e)}'}
        
        finally:
            self.sync_in_progress.discard(user_id)
    
    async def _push_shifts_to_google(self, user_id: str, calendar_id: str) -> Dict[str, Any]:
        """Push volunteer shifts from database to Google Calendar"""
        result = {
            'operations': [],
            'errors': [],
            'summary': {'created': 0, 'updated': 0, 'deleted': 0, 'conflicts': 0}
        }
        
        try:
            # Get shifts needing sync
            shifts = await self.database.get_volunteer_shifts(
                user_id, 
                start_date=datetime.now() - timedelta(days=7),  # Sync past week
                end_date=datetime.now() + timedelta(days=90)    # Sync next 3 months
            )
            
            for shift in shifts:
                try:
                    if shift.get('sync_status') in ['synced'] and shift.get('google_event_id'):
                        # Check if shift was updated since last sync
                        if shift.get('updated_at') <= shift.get('last_synced_at', ''):
                            continue  # No changes since last sync
                        
                        # Update existing event
                        await self._update_google_event(user_id, calendar_id, shift, result)
                    else:
                        # Create new event
                        await self._create_google_event(user_id, calendar_id, shift, result)
                        
                except Exception as e:
                    error_msg = f"Error syncing shift {shift.get('id')}: {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
                    
                    await self.database.log_calendar_sync({
                        'user_id': user_id,
                        'sync_type': 'push_to_google',
                        'shift_id': shift.get('id'),
                        'operation': 'error',
                        'status': 'error',
                        'error_message': error_msg
                    })
        
        except Exception as e:
            logger.error(f"Error pushing shifts to Google for user {user_id}: {e}")
            result['errors'].append(str(e))
        
        return result
    
    async def _pull_shifts_from_google(self, user_id: str, calendar_id: str) -> Dict[str, Any]:
        """Pull volunteer shifts from Google Calendar to database"""
        result = {
            'operations': [],
            'errors': [],
            'summary': {'created': 0, 'updated': 0, 'deleted': 0, 'conflicts': 0}
        }
        
        try:
            # Get Google Calendar events
            time_min = datetime.now() - timedelta(days=7)
            time_max = datetime.now() + timedelta(days=90)
            
            google_events = self.calendar_client.list_events(
                user_id, calendar_id, time_min, time_max, 
                query="YMCA volunteer"  # Look for YMCA-related events
            )
            
            # Filter for YMCA volunteer shifts
            ymca_events = [event for event in google_events if event.get('is_ymca_shift')]
            
            for event in ymca_events:
                try:
                    await self._sync_google_event_to_database(user_id, event, result)
                    
                except Exception as e:
                    error_msg = f"Error syncing event {event.get('event_id')}: {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
                    
                    await self.database.log_calendar_sync({
                        'user_id': user_id,
                        'sync_type': 'pull_from_google',
                        'google_event_id': event.get('event_id'),
                        'operation': 'error',
                        'status': 'error',
                        'error_message': error_msg
                    })
        
        except Exception as e:
            logger.error(f"Error pulling shifts from Google for user {user_id}: {e}")
            result['errors'].append(str(e))
        
        return result
    
    async def _create_google_event(self, user_id: str, calendar_id: str, 
                                  shift: Dict[str, Any], result: Dict[str, Any]):
        """Create a new Google Calendar event from a volunteer shift"""
        event_data = {
            'title': shift.get('shift_title') or f"Volunteer: {shift.get('project_name', 'YMCA Shift')}",
            'description': self._build_event_description(shift),
            'location': shift.get('location', ''),
            'start_time': shift['start_time'],
            'end_time': shift['end_time'],
            'project_id': shift.get('project_id'),
            'shift_id': shift['id'],
            'branch': shift.get('branch', '')
        }
        
        created_event = self.calendar_client.create_event(user_id, calendar_id, event_data)
        
        # Update shift with Google event info
        await self.database.update_volunteer_shift(shift['id'], {
            'google_event_id': created_event['event_id'],
            'google_calendar_id': calendar_id,
            'sync_status': 'synced',
            'last_synced_at': datetime.now().isoformat()
        })
        
        result['summary']['created'] += 1
        result['operations'].append({
            'type': 'created',
            'shift_id': shift['id'],
            'google_event_id': created_event['event_id']
        })
        
        await self.database.log_calendar_sync({
            'user_id': user_id,
            'sync_type': 'push_to_google',
            'shift_id': shift['id'],
            'google_event_id': created_event['event_id'],
            'operation': 'create',
            'status': 'success'
        })
    
    async def _update_google_event(self, user_id: str, calendar_id: str, 
                                  shift: Dict[str, Any], result: Dict[str, Any]):
        """Update an existing Google Calendar event"""
        event_data = {
            'title': shift.get('shift_title') or f"Volunteer: {shift.get('project_name', 'YMCA Shift')}",
            'description': self._build_event_description(shift),
            'location': shift.get('location', ''),
            'start_time': shift['start_time'],
            'end_time': shift['end_time']
        }
        
        updated_event = self.calendar_client.update_event(
            user_id, calendar_id, shift['google_event_id'], event_data
        )
        
        # Update shift sync status
        await self.database.update_volunteer_shift(shift['id'], {
            'sync_status': 'synced',
            'last_synced_at': datetime.now().isoformat()
        })
        
        result['summary']['updated'] += 1
        result['operations'].append({
            'type': 'updated',
            'shift_id': shift['id'],
            'google_event_id': shift['google_event_id']
        })
        
        await self.database.log_calendar_sync({
            'user_id': user_id,
            'sync_type': 'push_to_google',
            'shift_id': shift['id'],
            'google_event_id': shift['google_event_id'],
            'operation': 'update',
            'status': 'success'
        })
    
    async def _sync_google_event_to_database(self, user_id: str, 
                                           event: Dict[str, Any], result: Dict[str, Any]):
        """Sync a Google Calendar event to the database"""
        # Check if this event already exists in our database
        existing_shifts = await self.database.get_volunteer_shifts(user_id)
        existing_shift = None
        
        for shift in existing_shifts:
            if shift.get('google_event_id') == event['event_id']:
                existing_shift = shift
                break
        
        # Extract shift data from event
        shift_data = {
            'user_id': user_id,
            'shift_title': event.get('title', ''),
            'shift_description': event.get('description', ''),
            'start_time': event.get('start_time', ''),
            'end_time': event.get('end_time', ''),
            'location': event.get('location', ''),
            'google_event_id': event['event_id'],
            'google_calendar_id': event.get('calendar_id'),
            'sync_status': 'synced',
            'last_synced_at': datetime.now().isoformat()
        }
        
        # Add YMCA-specific data if present
        if event.get('project_id'):
            shift_data['project_id'] = int(event['project_id'])
        if event.get('branch'):
            shift_data['branch'] = event['branch']
        
        if existing_shift:
            # Update existing shift
            await self.database.update_volunteer_shift(existing_shift['id'], shift_data)
            result['summary']['updated'] += 1
            operation = 'update'
        else:
            # Create new shift
            shift_id = await self.database.create_volunteer_shift(shift_data)
            result['summary']['created'] += 1
            operation = 'create'
        
        result['operations'].append({
            'type': operation,
            'google_event_id': event['event_id'],
            'shift_id': existing_shift['id'] if existing_shift else shift_id
        })
        
        await self.database.log_calendar_sync({
            'user_id': user_id,
            'sync_type': 'pull_from_google',
            'google_event_id': event['event_id'],
            'operation': operation,
            'status': 'success'
        })
    
    def _build_event_description(self, shift: Dict[str, Any]) -> str:
        """Build a rich description for the calendar event"""
        description_parts = []
        
        if shift.get('shift_description'):
            description_parts.append(shift['shift_description'])
        
        if shift.get('project_name'):
            description_parts.append(f"Project: {shift['project_name']}")
        
        if shift.get('branch'):
            description_parts.append(f"Branch: {shift['branch']}")
        
        description_parts.append("\n🎯 This is a YMCA volunteer shift")
        description_parts.append("📱 Managed by YMCA Volunteer PathFinder")
        
        return "\n\n".join(description_parts)
    
    async def create_shift_with_calendar(self, shift_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new volunteer shift and sync to Google Calendar"""
        try:
            # Create shift in database
            shift_id = await self.database.create_volunteer_shift(shift_data)
            if not shift_id:
                return {'status': 'error', 'message': 'Failed to create shift'}
            
            user_id = shift_data['user_id']
            
            # Check if user has calendar sync enabled
            auth_data = await self.database.get_google_calendar_auth(user_id)
            if auth_data and auth_data.get('sync_enabled'):
                # Sync to Google Calendar
                try:
                    calendar_id = auth_data.get('calendar_id', 'primary')
                    shift_data['id'] = shift_id
                    
                    result = {'operations': [], 'errors': [], 'summary': {'created': 0, 'updated': 0, 'deleted': 0, 'conflicts': 0}}
                    await self._create_google_event(user_id, calendar_id, shift_data, result)
                    
                    return {
                        'status': 'success',
                        'shift_id': shift_id,
                        'calendar_synced': True,
                        'google_event_id': result['operations'][0]['google_event_id'] if result['operations'] else None
                    }
                    
                except Exception as e:
                    logger.error(f"Error syncing new shift to calendar: {e}")
                    return {
                        'status': 'partial',
                        'shift_id': shift_id,
                        'calendar_synced': False,
                        'message': f'Shift created but calendar sync failed: {str(e)}'
                    }
            
            return {
                'status': 'success',
                'shift_id': shift_id,
                'calendar_synced': False,
                'message': 'Shift created (calendar sync not enabled)'
            }
            
        except Exception as e:
            logger.error(f"Error creating shift with calendar: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def update_shift_with_calendar(self, shift_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a volunteer shift and sync changes to Google Calendar"""
        try:
            # Update shift in database
            success = await self.database.update_volunteer_shift(shift_id, updates)
            if not success:
                return {'status': 'error', 'message': 'Failed to update shift'}
            
            # Get updated shift data
            shifts = await self.database.get_volunteer_shifts(updates.get('user_id', ''))
            shift = next((s for s in shifts if s['id'] == shift_id), None)
            
            if not shift:
                return {'status': 'error', 'message': 'Updated shift not found'}
            
            user_id = shift['user_id']
            
            # Check if user has calendar sync enabled and shift is synced
            auth_data = await self.database.get_google_calendar_auth(user_id)
            if (auth_data and auth_data.get('sync_enabled') and 
                shift.get('google_event_id') and shift.get('sync_status') == 'synced'):
                
                try:
                    calendar_id = auth_data.get('calendar_id', 'primary')
                    result = {'operations': [], 'errors': [], 'summary': {'created': 0, 'updated': 0, 'deleted': 0, 'conflicts': 0}}
                    await self._update_google_event(user_id, calendar_id, shift, result)
                    
                    return {
                        'status': 'success',
                        'shift_id': shift_id,
                        'calendar_synced': True
                    }
                    
                except Exception as e:
                    logger.error(f"Error syncing shift update to calendar: {e}")
                    return {
                        'status': 'partial',
                        'shift_id': shift_id,
                        'calendar_synced': False,
                        'message': f'Shift updated but calendar sync failed: {str(e)}'
                    }
            
            return {
                'status': 'success',
                'shift_id': shift_id,
                'calendar_synced': False,
                'message': 'Shift updated (calendar sync not available)'
            }
            
        except Exception as e:
            logger.error(f"Error updating shift with calendar: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def delete_shift_with_calendar(self, shift_id: str, user_id: str) -> Dict[str, Any]:
        """Delete a volunteer shift and remove from Google Calendar"""
        try:
            # Get shift data before deletion
            shifts = await self.database.get_volunteer_shifts(user_id)
            shift = next((s for s in shifts if s['id'] == shift_id), None)
            
            if not shift:
                return {'status': 'error', 'message': 'Shift not found'}
            
            # Delete from Google Calendar if synced
            calendar_deleted = False
            if shift.get('google_event_id'):
                auth_data = await self.database.get_google_calendar_auth(user_id)
                if auth_data and auth_data.get('sync_enabled'):
                    try:
                        calendar_id = auth_data.get('calendar_id', 'primary')
                        self.calendar_client.delete_event(user_id, calendar_id, shift['google_event_id'])
                        calendar_deleted = True
                        
                        await self.database.log_calendar_sync({
                            'user_id': user_id,
                            'sync_type': 'push_to_google',
                            'shift_id': shift_id,
                            'google_event_id': shift['google_event_id'],
                            'operation': 'delete',
                            'status': 'success'
                        })
                        
                    except Exception as e:
                        logger.error(f"Error deleting Google Calendar event: {e}")
            
            # Delete shift from database (this should cascade to sync logs)
            # Note: We need to implement delete method in database
            # For now, we'll mark as cancelled
            await self.database.update_volunteer_shift(shift_id, {
                'status': 'cancelled',
                'sync_status': 'deleted'
            })
            
            return {
                'status': 'success',
                'shift_id': shift_id,
                'calendar_deleted': calendar_deleted
            }
            
        except Exception as e:
            logger.error(f"Error deleting shift with calendar: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def run_periodic_sync(self, max_users: int = 50):
        """Run periodic synchronization for all users with calendar sync enabled"""
        try:
            # Get users with calendar sync enabled
            # Note: This would need a database method to get all users with sync enabled
            # For now, we'll implement a simple version
            
            logger.info("Starting periodic calendar sync...")
            
            # This is a placeholder - in production, you'd get users from database
            # users_with_sync = await self.database.get_users_with_calendar_sync_enabled()
            
            logger.info("Periodic calendar sync completed")
            
        except Exception as e:
            logger.error(f"Error in periodic sync: {e}")