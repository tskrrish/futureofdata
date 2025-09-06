"""
Resource and Equipment Assignment Management
Extends the database functionality for resource/equipment assignments linked to shifts
"""
from database import VolunteerDatabase
from typing import Dict, List, Optional, Any
import json
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ResourceManagement(VolunteerDatabase):
    """Extended database class for resource and equipment management"""
    
    # Shifts Management
    async def create_shift(self, shift_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new shift"""
        if not self._is_available():
            logger.warning("Database not available, skipping shift creation")
            return None
            
        try:
            # Add timestamp
            shift_data['created_at'] = datetime.now().isoformat()
            shift_data['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('shifts').insert(shift_data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Created shift: {shift_data.get('name', 'unknown')}")
                return response.data[0]
            else:
                logger.error(f"Failed to create shift: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating shift: {e}")
            return None

    async def get_shifts(self, branch: str = None, date_range: tuple = None, status: str = None) -> List[Dict[str, Any]]:
        """Get shifts with optional filtering"""
        if not self._is_available():
            return []
            
        try:
            query = self.supabase.table('shifts').select('*')
            
            if branch:
                query = query.eq('branch', branch)
            if status:
                query = query.eq('status', status)
            if date_range and len(date_range) == 2:
                query = query.gte('start_time', date_range[0]).lte('end_time', date_range[1])
            
            result = query.order('start_time').execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error getting shifts: {e}")
            return []

    async def update_shift(self, shift_id: str, updates: Dict[str, Any]) -> bool:
        """Update shift information"""
        if not self._is_available():
            return False
            
        try:
            updates['updated_at'] = datetime.now().isoformat()
            result = self.supabase.table('shifts').update(updates).eq('id', shift_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error updating shift: {e}")
            return False

    # Resources Management
    async def create_resource(self, resource_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new resource/equipment item"""
        if not self._is_available():
            logger.warning("Database not available, skipping resource creation")
            return None
            
        try:
            # Add timestamp
            resource_data['created_at'] = datetime.now().isoformat()
            resource_data['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('resources').insert(resource_data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Created resource: {resource_data.get('name', 'unknown')}")
                return response.data[0]
            else:
                logger.error(f"Failed to create resource: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating resource: {e}")
            return None

    async def get_resources(self, branch: str = None, resource_type: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Get resources with optional filtering"""
        if not self._is_available():
            return []
            
        try:
            query = self.supabase.table('resources').select('*')
            
            if branch:
                query = query.eq('branch', branch)
            if resource_type:
                query = query.eq('resource_type', resource_type)
            if status:
                query = query.eq('status', status)
            
            result = query.order('name').execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error getting resources: {e}")
            return []

    async def update_resource(self, resource_id: str, updates: Dict[str, Any]) -> bool:
        """Update resource information"""
        if not self._is_available():
            return False
            
        try:
            updates['updated_at'] = datetime.now().isoformat()
            result = self.supabase.table('resources').update(updates).eq('id', resource_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"❌ Error updating resource: {e}")
            return False

    # Resource Assignments
    async def create_resource_assignment(self, assignment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new resource assignment to a shift"""
        if not self._is_available():
            logger.warning("Database not available, skipping assignment creation")
            return None
            
        try:
            # Check resource availability first using the database function
            availability_check = self.supabase.rpc(
                'check_resource_availability',
                {
                    'p_resource_id': assignment_data['resource_id'],
                    'p_shift_start': assignment_data.get('shift_start_time'),
                    'p_shift_end': assignment_data.get('shift_end_time')
                }
            ).execute()
            
            if not availability_check.data:
                logger.warning("Resource not available for assignment")
                return None
            
            # Add timestamp
            assignment_data['created_at'] = datetime.now().isoformat()
            assignment_data['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('resource_assignments').insert(assignment_data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Created resource assignment: {assignment_data.get('resource_id', 'unknown')}")
                return response.data[0]
            else:
                logger.error(f"Failed to create resource assignment: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creating resource assignment: {e}")
            return None

    async def get_resource_assignments(self, shift_id: str = None, resource_id: str = None, 
                                     user_id: str = None, status: str = None) -> List[Dict[str, Any]]:
        """Get resource assignments with optional filtering"""
        if not self._is_available():
            return []
            
        try:
            query = self.supabase.table('resource_assignments').select('''
                *,
                shifts:shift_id(*),
                resources:resource_id(*),
                assigned_to_user:assigned_to_user_id(*),
                assigned_by_user:assigned_by_user_id(*)
            ''')
            
            if shift_id:
                query = query.eq('shift_id', shift_id)
            if resource_id:
                query = query.eq('resource_id', resource_id)
            if user_id:
                query = query.eq('assigned_to_user_id', user_id)
            if status:
                query = query.eq('status', status)
            
            result = query.order('created_at', desc=True).execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error getting resource assignments: {e}")
            return []

    async def update_assignment_status(self, assignment_id: str, status: str, 
                                     additional_data: Dict[str, Any] = None) -> bool:
        """Update resource assignment status and related fields"""
        if not self._is_available():
            return False
            
        try:
            updates = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            # Add status-specific updates
            if status == 'checked_out':
                updates['checked_out_at'] = datetime.now().isoformat()
                if additional_data and 'condition_at_checkout' in additional_data:
                    updates['condition_at_checkout'] = additional_data['condition_at_checkout']
            elif status == 'returned':
                updates['checked_in_at'] = datetime.now().isoformat()
                if additional_data:
                    if 'condition_at_return' in additional_data:
                        updates['condition_at_return'] = additional_data['condition_at_return']
                    if 'return_notes' in additional_data:
                        updates['return_notes'] = additional_data['return_notes']
            
            result = self.supabase.table('resource_assignments').update(updates).eq('id', assignment_id).execute()
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ Error updating assignment status: {e}")
            return False

    # Usage Tracking
    async def get_usage_logs(self, resource_id: str = None, user_id: str = None, 
                           shift_id: str = None, date_range: tuple = None) -> List[Dict[str, Any]]:
        """Get resource usage logs with optional filtering"""
        if not self._is_available():
            return []
            
        try:
            query = self.supabase.table('resource_usage_logs').select('''
                *,
                resources:resource_id(*),
                users:user_id(*),
                shifts:shift_id(*)
            ''')
            
            if resource_id:
                query = query.eq('resource_id', resource_id)
            if user_id:
                query = query.eq('user_id', user_id)
            if shift_id:
                query = query.eq('shift_id', shift_id)
            if date_range and len(date_range) == 2:
                query = query.gte('action_timestamp', date_range[0]).lte('action_timestamp', date_range[1])
            
            result = query.order('action_timestamp', desc=True).execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error getting usage logs: {e}")
            return []

    # Analytics and Reporting
    async def get_resource_utilization_stats(self, date_range: tuple = None) -> Dict[str, Any]:
        """Get resource utilization statistics"""
        if not self._is_available():
            return {}
            
        try:
            # Get basic stats
            query = self.supabase.table('resource_usage_logs').select('*')
            if date_range:
                query = query.gte('action_timestamp', date_range[0]).lte('action_timestamp', date_range[1])
            
            logs_result = query.execute()
            logs = logs_result.data if logs_result.data else []
            
            # Calculate utilization metrics
            total_assignments = len([log for log in logs if log['action'] == 'assigned'])
            total_checkouts = len([log for log in logs if log['action'] == 'checked_out'])
            total_returns = len([log for log in logs if log['action'] == 'returned'])
            
            # Calculate average usage duration
            usage_durations = [log['duration_minutes'] for log in logs 
                             if log['duration_minutes'] is not None and log['action'] == 'returned']
            avg_duration = sum(usage_durations) / len(usage_durations) if usage_durations else 0
            
            # Get resource-specific stats
            resource_stats = {}
            for log in logs:
                resource_id = log['resource_id']
                if resource_id not in resource_stats:
                    resource_stats[resource_id] = {
                        'assignments': 0,
                        'checkouts': 0,
                        'returns': 0,
                        'total_duration': 0
                    }
                
                if log['action'] == 'assigned':
                    resource_stats[resource_id]['assignments'] += 1
                elif log['action'] == 'checked_out':
                    resource_stats[resource_id]['checkouts'] += 1
                elif log['action'] == 'returned':
                    resource_stats[resource_id]['returns'] += 1
                    if log['duration_minutes']:
                        resource_stats[resource_id]['total_duration'] += log['duration_minutes']
            
            return {
                'total_assignments': total_assignments,
                'total_checkouts': total_checkouts,
                'total_returns': total_returns,
                'checkout_rate': (total_checkouts / total_assignments * 100) if total_assignments > 0 else 0,
                'return_rate': (total_returns / total_checkouts * 100) if total_checkouts > 0 else 0,
                'average_usage_duration_minutes': round(avg_duration, 2),
                'resource_specific_stats': resource_stats,
                'period_start': date_range[0] if date_range else None,
                'period_end': date_range[1] if date_range else None,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting utilization stats: {e}")
            return {}

    async def get_shift_resource_summary(self, shift_id: str) -> Dict[str, Any]:
        """Get a summary of all resources assigned to a shift"""
        if not self._is_available():
            return {}
            
        try:
            # Get shift details
            shift_result = self.supabase.table('shifts').select('*').eq('id', shift_id).execute()
            if not shift_result.data:
                return {}
            
            shift = shift_result.data[0]
            
            # Get assignments for this shift
            assignments = await self.get_resource_assignments(shift_id=shift_id)
            
            # Categorize resources by type and status
            resource_summary = {
                'shift': shift,
                'total_resources_assigned': len(assignments),
                'by_type': {},
                'by_status': {},
                'assignments': assignments
            }
            
            for assignment in assignments:
                resource = assignment.get('resources', {})
                resource_type = resource.get('resource_type', 'unknown')
                status = assignment.get('status', 'unknown')
                
                # Count by type
                if resource_type not in resource_summary['by_type']:
                    resource_summary['by_type'][resource_type] = 0
                resource_summary['by_type'][resource_type] += 1
                
                # Count by status
                if status not in resource_summary['by_status']:
                    resource_summary['by_status'][status] = 0
                resource_summary['by_status'][status] += 1
            
            return resource_summary
            
        except Exception as e:
            logger.error(f"❌ Error getting shift resource summary: {e}")
            return {}

    # Maintenance Management
    async def schedule_maintenance(self, maintenance_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Schedule maintenance for a resource"""
        if not self._is_available():
            logger.warning("Database not available, skipping maintenance scheduling")
            return None
            
        try:
            maintenance_data['created_at'] = datetime.now().isoformat()
            maintenance_data['updated_at'] = datetime.now().isoformat()
            
            response = self.supabase.table('resource_maintenance').insert(maintenance_data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"✅ Scheduled maintenance: {maintenance_data.get('description', 'unknown')}")
                return response.data[0]
            else:
                logger.error(f"Failed to schedule maintenance: {response}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error scheduling maintenance: {e}")
            return None

    async def get_maintenance_schedule(self, resource_id: str = None, 
                                     status: str = None, date_range: tuple = None) -> List[Dict[str, Any]]:
        """Get maintenance schedules with optional filtering"""
        if not self._is_available():
            return []
            
        try:
            query = self.supabase.table('resource_maintenance').select('''
                *,
                resources:resource_id(*)
            ''')
            
            if resource_id:
                query = query.eq('resource_id', resource_id)
            if status:
                query = query.eq('status', status)
            if date_range and len(date_range) == 2:
                query = query.gte('scheduled_date', date_range[0]).lte('scheduled_date', date_range[1])
            
            result = query.order('scheduled_date').execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"❌ Error getting maintenance schedule: {e}")
            return []


# Usage example and testing
async def test_resource_management():
    """Test resource management functionality"""
    rm = ResourceManagement()
    
    # Create a test shift
    shift_data = {
        'name': 'Pool Maintenance - Morning',
        'description': 'Daily pool cleaning and maintenance',
        'branch': 'Blue Ash',
        'category': 'Maintenance',
        'start_time': (datetime.now() + timedelta(days=1)).isoformat(),
        'end_time': (datetime.now() + timedelta(days=1, hours=2)).isoformat(),
        'max_volunteers': 2
    }
    
    shift = await rm.create_shift(shift_data)
    if shift:
        print(f"✅ Created test shift: {shift['id']}")
        
        # Get available resources
        resources = await rm.get_resources(branch='Blue Ash', status='available')
        print(f"✅ Found {len(resources)} available resources")
        
        if resources:
            # Create a resource assignment
            assignment_data = {
                'shift_id': shift['id'],
                'resource_id': resources[0]['id'],
                'assigned_to_user_id': None,  # Will be assigned later
                'quantity_assigned': 1,
                'assignment_notes': 'Test assignment for pool cleaning',
                'shift_start_time': shift['start_time'],
                'shift_end_time': shift['end_time']
            }
            
            assignment = await rm.create_resource_assignment(assignment_data)
            if assignment:
                print(f"✅ Created test assignment: {assignment['id']}")
                
                # Get shift summary
                summary = await rm.get_shift_resource_summary(shift['id'])
                print(f"✅ Shift summary: {summary.get('total_resources_assigned', 0)} resources assigned")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_resource_management())