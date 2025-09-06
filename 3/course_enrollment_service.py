"""
Course Enrollment Service with Waitlist Auto-Backfill
Handles course enrollment, waitlist management, and automatic backfilling
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from database import VolunteerDatabase
import uuid

logger = logging.getLogger(__name__)

class CourseEnrollmentService:
    def __init__(self, db: VolunteerDatabase):
        self.db = db
    
    async def enroll_user(self, user_id: str, course_id: str, 
                         waitlist_priority: int = 5) -> Dict[str, Any]:
        """
        Enroll user in course or add to waitlist with priority ranking
        Priority levels: 1=VIP/Staff, 2=Members, 3=Returning students, 4=Early bird, 5=Normal
        """
        try:
            # Get user and course information
            user = await self.db.get_user(user_id=user_id)
            course = await self.db.get_course(course_id)
            
            if not user or not course:
                return {'success': False, 'message': 'User or course not found'}
            
            # Check course eligibility and capacity
            eligibility_check = await self._check_enrollment_eligibility(user, course)
            if not eligibility_check['eligible']:
                return {'success': False, 'message': eligibility_check['reason']}
            
            # Determine priority based on user profile
            calculated_priority = await self._calculate_waitlist_priority(user, course)
            final_priority = min(waitlist_priority, calculated_priority)  # Use better priority
            
            # Attempt enrollment
            enrollment_result = await self.db.enroll_user_in_course(
                user_id, course_id, final_priority
            )
            
            if enrollment_result['success']:
                # If enrolled directly, send confirmation
                if enrollment_result['status'] == 'enrolled':
                    await self._send_enrollment_confirmation(user, course, enrollment_result['enrollment'])
                # If waitlisted, send waitlist notification
                elif enrollment_result['status'] == 'waitlisted':
                    await self._send_waitlist_notification(user, course, enrollment_result['enrollment'])
                
                return enrollment_result
            
            return enrollment_result
            
        except Exception as e:
            logger.error(f"❌ Error in enroll_user: {e}")
            return {'success': False, 'message': f'Enrollment error: {e}'}
    
    async def drop_user(self, user_id: str, course_id: str, 
                       reason: str = 'user_requested') -> Dict[str, Any]:
        """Drop user and trigger auto-backfill from waitlist"""
        try:
            # Get enrollment info
            enrollment = await self._get_user_enrollment(user_id, course_id)
            if not enrollment:
                return {'success': False, 'message': 'Enrollment not found'}
            
            if enrollment['enrollment_status'] not in ['enrolled', 'waitlisted']:
                return {'success': False, 'message': 'Cannot drop user with current status'}
            
            # Drop the user
            drop_success = await self.db.drop_user_from_course(user_id, course_id, reason)
            
            if drop_success and enrollment['enrollment_status'] == 'enrolled':
                # If enrolled student dropped, auto-backfill
                backfill_result = await self.auto_backfill_course(course_id, f'student_drop_{reason}')
                
                return {
                    'success': True,
                    'message': 'User dropped successfully',
                    'backfill_result': backfill_result
                }
            
            return {'success': drop_success, 'message': 'User dropped successfully'}
            
        except Exception as e:
            logger.error(f"❌ Error dropping user: {e}")
            return {'success': False, 'message': f'Drop error: {e}'}
    
    async def mark_no_show(self, user_id: str, course_id: str) -> Dict[str, Any]:
        """Mark user as no-show and auto-backfill"""
        try:
            no_show_success = await self.db.mark_no_show(user_id, course_id)
            
            if no_show_success:
                # Auto-backfill from waitlist
                backfill_result = await self.auto_backfill_course(course_id, 'no_show')
                
                return {
                    'success': True,
                    'message': 'User marked as no-show',
                    'backfill_result': backfill_result
                }
            
            return {'success': False, 'message': 'Failed to mark no-show'}
            
        except Exception as e:
            logger.error(f"❌ Error marking no-show: {e}")
            return {'success': False, 'message': f'No-show error: {e}'}
    
    async def auto_backfill_course(self, course_id: str, trigger_reason: str) -> Dict[str, Any]:
        """
        Intelligent auto-backfill from waitlist with priority ranking
        """
        try:
            # Get current course state
            course = await self.db.get_course(course_id)
            if not course:
                return {'success': False, 'message': 'Course not found'}
            
            available_spots = course['max_capacity'] - course['current_enrolled']
            if available_spots <= 0:
                return {'success': False, 'message': 'No available spots'}
            
            # Get ranked waitlist candidates
            candidates = await self._get_ranked_waitlist_candidates(course_id)
            if not candidates:
                return {'success': False, 'message': 'No waitlist candidates'}
            
            # Auto-enroll candidates based on ranking
            enrolled_users = []
            enrolled_count = 0
            
            for candidate in candidates:
                if enrolled_count >= available_spots:
                    break
                
                # Check if candidate is still eligible
                user = await self.db.get_user(user_id=candidate['user_id'])
                if not user:
                    continue
                
                eligibility_check = await self._check_enrollment_eligibility(user, course)
                if not eligibility_check['eligible']:
                    # Log skip reason
                    await self.db.log_waitlist_action(
                        course_id, candidate['user_id'], 'skipped_ineligible',
                        'waitlisted', 'waitlisted', eligibility_check['reason']
                    )
                    continue
                
                # Move to enrolled
                update_success = await self._promote_from_waitlist(candidate, course_id, trigger_reason)
                if update_success:
                    enrolled_count += 1
                    enrolled_users.append({
                        'user_id': candidate['user_id'],
                        'user_name': f"{user['first_name']} {user['last_name']}",
                        'email': user['email'],
                        'priority': candidate['waitlist_priority'],
                        'waitlist_position': candidate['waitlist_position']
                    })
                    
                    # Send enrollment notification
                    await self._send_auto_enrollment_notification(user, course, candidate)
            
            # Reorder remaining waitlist
            if enrolled_count > 0:
                await self.db.reorder_waitlist_positions(course_id)
            
            logger.info(f"✅ Auto-enrolled {enrolled_count} users from waitlist for course {course_id}")
            
            return {
                'success': True,
                'enrolled_count': enrolled_count,
                'enrolled_users': enrolled_users,
                'available_spots': available_spots,
                'message': f'Successfully auto-enrolled {enrolled_count} candidate(s) from waitlist'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in auto-backfill: {e}")
            return {'success': False, 'message': f'Auto-backfill error: {e}'}
    
    async def process_scheduled_auto_backfill(self) -> Dict[str, Any]:
        """Process scheduled auto-backfill for all courses (run periodically)"""
        try:
            # Get courses that need auto-backfill checking
            courses_needing_check = await self._get_courses_needing_backfill_check()
            
            results = []
            for course in courses_needing_check:
                result = await self.auto_backfill_course(course['id'], 'scheduled_check')
                results.append({
                    'course_id': course['id'],
                    'course_name': course['course_name'],
                    'result': result
                })
            
            return {
                'success': True,
                'courses_processed': len(courses_needing_check),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Error in scheduled auto-backfill: {e}")
            return {'success': False, 'message': f'Scheduled backfill error: {e}'}
    
    # Private helper methods
    
    async def _check_enrollment_eligibility(self, user: Dict, course: Dict) -> Dict[str, Any]:
        """Check if user is eligible to enroll in course"""
        try:
            # Check course status
            if course['status'] != 'open':
                return {'eligible': False, 'reason': 'Course is not open for enrollment'}
            
            # Check if course has started
            if course['start_date']:
                start_date = datetime.fromisoformat(course['start_date'].replace('Z', '+00:00'))
                if start_date <= datetime.now().astimezone():
                    return {'eligible': False, 'reason': 'Course has already started'}
            
            # Check age requirements if any
            if course.get('requirements'):
                # Parse age requirements from course requirements
                # This could be extended based on specific business rules
                pass
            
            return {'eligible': True, 'reason': 'User is eligible'}
            
        except Exception as e:
            logger.error(f"❌ Error checking eligibility: {e}")
            return {'eligible': False, 'reason': f'Eligibility check error: {e}'}
    
    async def _calculate_waitlist_priority(self, user: Dict, course: Dict) -> int:
        """Calculate waitlist priority based on user profile"""
        try:
            priority = 5  # Default normal priority
            
            # VIP priority for staff/volunteers
            if user.get('is_staff') or user.get('is_volunteer'):
                priority = 1
            
            # Member priority
            elif user.get('is_ymca_member'):
                priority = 2
            
            # Returning student priority (check if user has completed courses before)
            user_enrollments = await self.db.supabase.table('course_enrollments')\
                .select('*')\
                .eq('user_id', user['id'])\
                .eq('enrollment_status', 'completed')\
                .execute()
            
            if user_enrollments.data and len(user_enrollments.data) > 0:
                priority = min(priority, 3)  # Returning student priority
            
            return priority
            
        except Exception as e:
            logger.error(f"❌ Error calculating priority: {e}")
            return 5  # Default to normal priority on error
    
    async def _get_ranked_waitlist_candidates(self, course_id: str) -> List[Dict[str, Any]]:
        """Get waitlist candidates ranked by priority and enrollment date"""
        try:
            result = self.db.supabase.table('course_enrollments')\
                .select('*, users(*)')\
                .eq('course_id', course_id)\
                .eq('enrollment_status', 'waitlisted')\
                .order('waitlist_priority')\
                .order('enrollment_date')\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"❌ Error getting ranked candidates: {e}")
            return []
    
    async def _promote_from_waitlist(self, candidate: Dict, course_id: str, 
                                   trigger_reason: str) -> bool:
        """Promote a candidate from waitlist to enrolled"""
        try:
            result = self.db.supabase.table('course_enrollments')\
                .update({
                    'enrollment_status': 'enrolled',
                    'waitlist_position': None,
                    'notification_sent': False,
                    'updated_at': datetime.now().isoformat()
                })\
                .eq('id', candidate['id'])\
                .execute()
            
            if result.data:
                # Log the promotion
                await self.db.log_waitlist_action(
                    course_id, candidate['user_id'], 'auto_enrolled',
                    'waitlisted', 'enrolled',
                    f'Auto-promoted from waitlist due to {trigger_reason}',
                    'system'
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error promoting from waitlist: {e}")
            return False
    
    async def _get_user_enrollment(self, user_id: str, course_id: str) -> Optional[Dict]:
        """Get user's enrollment record for a course"""
        try:
            result = self.db.supabase.table('course_enrollments')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('course_id', course_id)\
                .execute()
            
            return result.data[0] if result.data else None
            
        except Exception as e:
            logger.error(f"❌ Error getting user enrollment: {e}")
            return None
    
    async def _get_courses_needing_backfill_check(self) -> List[Dict[str, Any]]:
        """Get courses that might need auto-backfill checking"""
        try:
            # Get open courses that have waitlists and available capacity
            result = self.db.supabase.rpc('get_courses_with_waitlist_and_capacity').execute()
            
            # Fallback to manual query if RPC not available
            if not hasattr(result, 'data') or not result.data:
                courses_result = self.db.supabase.table('courses')\
                    .select('*')\
                    .eq('status', 'open')\
                    .lt('current_enrolled', 'max_capacity')\
                    .execute()
                
                courses_with_waitlist = []
                for course in courses_result.data or []:
                    waitlist_count = self.db.supabase.table('course_enrollments')\
                        .select('*', count='exact')\
                        .eq('course_id', course['id'])\
                        .eq('enrollment_status', 'waitlisted')\
                        .execute()
                    
                    if waitlist_count.count and waitlist_count.count > 0:
                        courses_with_waitlist.append(course)
                
                return courses_with_waitlist
            
            return result.data
            
        except Exception as e:
            logger.error(f"❌ Error getting courses needing backfill: {e}")
            return []
    
    # Notification methods (placeholders - implement based on your notification system)
    
    async def _send_enrollment_confirmation(self, user: Dict, course: Dict, enrollment: Dict):
        """Send enrollment confirmation notification"""
        try:
            # This would integrate with your notification system (email, SMS, etc.)
            logger.info(f"📧 Sending enrollment confirmation to {user['email']} for {course['course_name']}")
            
            # Mark notification as sent
            await self.db.mark_notification_sent(enrollment['id'])
            
        except Exception as e:
            logger.error(f"❌ Error sending enrollment confirmation: {e}")
    
    async def _send_waitlist_notification(self, user: Dict, course: Dict, enrollment: Dict):
        """Send waitlist notification"""
        try:
            logger.info(f"📧 Sending waitlist notification to {user['email']} for {course['course_name']}")
            
        except Exception as e:
            logger.error(f"❌ Error sending waitlist notification: {e}")
    
    async def _send_auto_enrollment_notification(self, user: Dict, course: Dict, enrollment: Dict):
        """Send auto-enrollment notification"""
        try:
            logger.info(f"📧 Sending auto-enrollment notification to {user['email']} for {course['course_name']}")
            
            # Mark notification as sent
            await self.db.mark_notification_sent(enrollment['id'])
            
        except Exception as e:
            logger.error(f"❌ Error sending auto-enrollment notification: {e}")

# Background service runner
class WaitlistBackgroundService:
    def __init__(self, enrollment_service: CourseEnrollmentService):
        self.enrollment_service = enrollment_service
        self.running = False
        self.check_interval = 300  # 5 minutes
    
    async def start(self):
        """Start the background service"""
        self.running = True
        logger.info("🚀 Starting waitlist background service")
        
        while self.running:
            try:
                await self.enrollment_service.process_scheduled_auto_backfill()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"❌ Error in background service: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def stop(self):
        """Stop the background service"""
        self.running = False
        logger.info("🛑 Stopping waitlist background service")

# Usage example
async def example_usage():
    """Example of how to use the course enrollment service"""
    # Initialize database and service
    db = VolunteerDatabase()
    enrollment_service = CourseEnrollmentService(db)
    
    # Example course data
    course_data = {
        'course_name': 'Youth Basketball Skills',
        'course_description': 'Basketball fundamentals for kids aged 8-12',
        'instructor': 'Coach Mike Johnson',
        'branch': 'Blue Ash',
        'category': 'Youth Sports',
        'max_capacity': 15,
        'start_date': '2025-10-01T18:00:00Z',
        'end_date': '2025-12-01T19:00:00Z',
        'schedule_days': ['Monday', 'Wednesday'],
        'schedule_time': '18:00:00',
        'price': 50.00,
        'requirements': 'Ages 8-12, no experience required'
    }
    
    # Create course
    course = await db.create_course(course_data)
    if course:
        print(f"✅ Created course: {course['course_name']} (ID: {course['id']})")
        
        # Example enrollments
        user_ids = ['user1', 'user2', 'user3']  # Replace with real user IDs
        
        for user_id in user_ids:
            result = await enrollment_service.enroll_user(user_id, course['id'])
            print(f"📝 Enrollment result for {user_id}: {result}")

if __name__ == "__main__":
    asyncio.run(example_usage())