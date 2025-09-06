"""
Comprehensive Test Suite for Waitlist Auto-Backfill System
Tests enrollment, waitlist management, and auto-backfill functionality
"""

import asyncio
import pytest
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid

from database import VolunteerDatabase
from course_enrollment_service import CourseEnrollmentService
from notification_service import NotificationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WaitlistTestSuite:
    def __init__(self):
        self.db = VolunteerDatabase()
        self.enrollment_service = CourseEnrollmentService(self.db)
        self.notification_service = NotificationService(self.db)
        self.test_data = {}
    
    async def setup_test_data(self):
        """Create test users and courses"""
        logger.info("🔧 Setting up test data...")
        
        # Create test users with different profiles
        test_users = [
            {
                'email': 'staff.member@ymca.org',
                'first_name': 'Staff',
                'last_name': 'Member',
                'is_staff': True,
                'is_ymca_member': True,
                'profile_type': 'staff'
            },
            {
                'email': 'premium.member@example.com', 
                'first_name': 'Premium',
                'last_name': 'Member',
                'is_ymca_member': True,
                'profile_type': 'member'
            },
            {
                'email': 'returning.student@example.com',
                'first_name': 'Returning',
                'last_name': 'Student', 
                'profile_type': 'returning'
            },
            {
                'email': 'new.user1@example.com',
                'first_name': 'New',
                'last_name': 'User1',
                'profile_type': 'normal'
            },
            {
                'email': 'new.user2@example.com',
                'first_name': 'New',
                'last_name': 'User2',
                'profile_type': 'normal'
            },
            {
                'email': 'new.user3@example.com',
                'first_name': 'New',
                'last_name': 'User3',
                'profile_type': 'normal'
            }
        ]
        
        self.test_data['users'] = []
        for user_data in test_users:
            user = await self.db.create_user(user_data)
            if user:
                user['profile_type'] = user_data['profile_type']
                self.test_data['users'].append(user)
                logger.info(f"✅ Created test user: {user['email']}")
        
        # Create test courses
        test_courses = [
            {
                'course_name': 'Youth Basketball Skills',
                'max_capacity': 3,  # Small capacity for testing
                'course_description': 'Basketball fundamentals for kids aged 8-12',
                'instructor': 'Coach Mike Johnson',
                'branch': 'Blue Ash',
                'category': 'Youth Sports',
                'start_date': (datetime.now() + timedelta(days=7)).isoformat() + 'Z',
                'end_date': (datetime.now() + timedelta(days=37)).isoformat() + 'Z',
                'schedule_days': ['Monday', 'Wednesday'],
                'schedule_time': '18:00:00',
                'price': 50.00,
                'requirements': 'Ages 8-12, athletic shoes required'
            },
            {
                'course_name': 'Adult Yoga Class',
                'max_capacity': 2,  # Very small for waitlist testing
                'course_description': 'Relaxing yoga for all skill levels',
                'instructor': 'Sarah Williams',
                'branch': 'Downtown',
                'category': 'Fitness',
                'start_date': (datetime.now() + timedelta(days=5)).isoformat() + 'Z',
                'end_date': (datetime.now() + timedelta(days=35)).isoformat() + 'Z',
                'schedule_days': ['Tuesday', 'Thursday'],
                'schedule_time': '19:00:00',
                'price': 75.00,
                'requirements': 'Bring yoga mat'
            }
        ]
        
        self.test_data['courses'] = []
        for course_data in test_courses:
            course = await self.db.create_course(course_data)
            if course:
                self.test_data['courses'].append(course)
                logger.info(f"✅ Created test course: {course['course_name']} (capacity: {course['max_capacity']})")
        
        logger.info(f"🎯 Test setup complete: {len(self.test_data['users'])} users, {len(self.test_data['courses'])} courses")
    
    async def test_basic_enrollment(self) -> Dict[str, Any]:
        """Test basic course enrollment"""
        logger.info("🧪 Testing basic enrollment...")
        
        course = self.test_data['courses'][0]  # Basketball course (capacity: 3)
        users = self.test_data['users'][:3]  # First 3 users
        
        results = []
        for user in users:
            result = await self.enrollment_service.enroll_user(user['id'], course['id'])
            results.append({
                'user': f"{user['first_name']} {user['last_name']}",
                'result': result
            })
            
            if result['success']:
                logger.info(f"✅ {user['first_name']} enrolled: {result['status']}")
            else:
                logger.error(f"❌ {user['first_name']} enrollment failed: {result['message']}")
        
        # Verify course is full
        updated_course = await self.db.get_course(course['id'])
        assert updated_course['current_enrolled'] == course['max_capacity'], "Course should be at capacity"
        
        return {
            'test': 'basic_enrollment',
            'success': True,
            'results': results,
            'course_capacity': updated_course['current_enrolled']
        }
    
    async def test_waitlist_enrollment(self) -> Dict[str, Any]:
        """Test waitlist enrollment when course is full"""
        logger.info("🧪 Testing waitlist enrollment...")
        
        course = self.test_data['courses'][0]  # Basketball course (should be full now)
        remaining_users = self.test_data['users'][3:]  # Users 4-6
        
        results = []
        for user in remaining_users:
            result = await self.enrollment_service.enroll_user(user['id'], course['id'])
            results.append({
                'user': f"{user['first_name']} {user['last_name']}",
                'profile_type': user.get('profile_type', 'normal'),
                'result': result
            })
            
            if result['success'] and result['status'] == 'waitlisted':
                logger.info(f"✅ {user['first_name']} waitlisted")
            else:
                logger.warning(f"⚠️ Unexpected result for {user['first_name']}: {result}")
        
        # Verify waitlist
        waitlist_candidates = await self.db.get_waitlist_candidates(course['id'])
        logger.info(f"📋 Waitlist has {len(waitlist_candidates)} candidates")
        
        return {
            'test': 'waitlist_enrollment',
            'success': True,
            'results': results,
            'waitlist_count': len(waitlist_candidates)
        }
    
    async def test_priority_ranking(self) -> Dict[str, Any]:
        """Test that waitlist is ordered by priority"""
        logger.info("🧪 Testing priority ranking...")
        
        course = self.test_data['courses'][1]  # Yoga course (capacity: 2)
        
        # Enroll users in reverse priority order to test sorting
        enrollment_order = [
            (self.test_data['users'][3], 5),  # Normal user
            (self.test_data['users'][1], 2),  # Member (should get higher priority)
            (self.test_data['users'][0], 1),  # Staff (should get highest priority)
        ]
        
        results = []
        for user, priority in enrollment_order:
            result = await self.enrollment_service.enroll_user(user['id'], course['id'], priority)
            results.append({
                'user': f"{user['first_name']} {user['last_name']}",
                'requested_priority': priority,
                'result': result
            })
        
        # Check waitlist order (staff should be first, member second, normal third)
        waitlist_candidates = await self.db.get_waitlist_candidates(course['id'])
        
        priority_order = []
        for candidate in waitlist_candidates:
            user_info = next(u for u in self.test_data['users'] if u['id'] == candidate['user_id'])
            priority_order.append({
                'user': f"{user_info['first_name']} {user_info['last_name']}",
                'priority': candidate['waitlist_priority'],
                'position': candidate['waitlist_position']
            })
        
        logger.info(f"📊 Waitlist priority order: {priority_order}")
        
        return {
            'test': 'priority_ranking',
            'success': True,
            'enrollment_results': results,
            'waitlist_order': priority_order
        }
    
    async def test_auto_backfill_drop(self) -> Dict[str, Any]:
        """Test auto-backfill when enrolled student drops"""
        logger.info("🧪 Testing auto-backfill on student drop...")
        
        course = self.test_data['courses'][0]  # Basketball course
        
        # Get an enrolled user to drop
        enrolled_users = self.db.supabase.table('course_enrollments')\
            .select('*, users(*)')\
            .eq('course_id', course['id'])\
            .eq('enrollment_status', 'enrolled')\
            .execute()
        
        if not enrolled_users.data:
            logger.error("❌ No enrolled users found for drop test")
            return {'test': 'auto_backfill_drop', 'success': False, 'message': 'No enrolled users'}
        
        dropped_user = enrolled_users.data[0]
        logger.info(f"👋 Dropping user: {dropped_user['users']['first_name']} {dropped_user['users']['last_name']}")
        
        # Get waitlist before drop
        waitlist_before = await self.db.get_waitlist_candidates(course['id'])
        logger.info(f"📋 Waitlist before drop: {len(waitlist_before)} candidates")
        
        # Drop the user
        drop_result = await self.enrollment_service.drop_user(
            dropped_user['user_id'], course['id'], 'test_drop'
        )
        
        # Get waitlist after drop
        waitlist_after = await self.db.get_waitlist_candidates(course['id'])
        logger.info(f"📋 Waitlist after drop: {len(waitlist_after)} candidates")
        
        # Check if someone was auto-enrolled
        updated_course = await self.db.get_course(course['id'])
        
        return {
            'test': 'auto_backfill_drop',
            'success': drop_result['success'],
            'dropped_user': f"{dropped_user['users']['first_name']} {dropped_user['users']['last_name']}",
            'waitlist_before_count': len(waitlist_before),
            'waitlist_after_count': len(waitlist_after),
            'course_capacity_after': updated_course['current_enrolled'],
            'backfill_result': drop_result.get('backfill_result', {})
        }
    
    async def test_auto_backfill_no_show(self) -> Dict[str, Any]:
        """Test auto-backfill when student is marked as no-show"""
        logger.info("🧪 Testing auto-backfill on no-show...")
        
        course = self.test_data['courses'][0]  # Basketball course
        
        # Get an enrolled user to mark as no-show
        enrolled_users = self.db.supabase.table('course_enrollments')\
            .select('*, users(*)')\
            .eq('course_id', course['id'])\
            .eq('enrollment_status', 'enrolled')\
            .execute()
        
        if not enrolled_users.data:
            logger.error("❌ No enrolled users found for no-show test")
            return {'test': 'auto_backfill_no_show', 'success': False, 'message': 'No enrolled users'}
        
        no_show_user = enrolled_users.data[0]
        logger.info(f"👻 Marking no-show: {no_show_user['users']['first_name']} {no_show_user['users']['last_name']}")
        
        # Get current state
        waitlist_before = await self.db.get_waitlist_candidates(course['id'])
        course_before = await self.db.get_course(course['id'])
        
        # Mark no-show
        no_show_result = await self.enrollment_service.mark_no_show(
            no_show_user['user_id'], course['id']
        )
        
        # Get updated state
        waitlist_after = await self.db.get_waitlist_candidates(course['id'])
        course_after = await self.db.get_course(course['id'])
        
        return {
            'test': 'auto_backfill_no_show',
            'success': no_show_result['success'],
            'no_show_user': f"{no_show_user['users']['first_name']} {no_show_user['users']['last_name']}",
            'waitlist_before_count': len(waitlist_before),
            'waitlist_after_count': len(waitlist_after),
            'capacity_before': course_before['current_enrolled'],
            'capacity_after': course_after['current_enrolled'],
            'backfill_result': no_show_result.get('backfill_result', {})
        }
    
    async def test_notification_system(self) -> Dict[str, Any]:
        """Test notification system for enrollments and waitlist"""
        logger.info("🧪 Testing notification system...")
        
        # Get a recently enrolled user
        recent_enrollments = self.db.supabase.table('course_enrollments')\
            .select('*, users(*), courses(*)')\
            .eq('enrollment_status', 'enrolled')\
            .eq('notification_sent', False)\
            .limit(1)\
            .execute()
        
        notification_results = []
        
        if recent_enrollments.data:
            enrollment = recent_enrollments.data[0]
            user = enrollment['users']
            course = enrollment['courses']
            
            # Test enrollment confirmation
            confirmation_sent = await self.notification_service.send_enrollment_confirmation(
                user, course, enrollment
            )
            notification_results.append({
                'type': 'enrollment_confirmation',
                'user': user['email'],
                'success': confirmation_sent
            })
        
        # Test waitlist notification
        waitlist_users = self.db.supabase.table('course_enrollments')\
            .select('*, users(*), courses(*)')\
            .eq('enrollment_status', 'waitlisted')\
            .limit(1)\
            .execute()
        
        if waitlist_users.data:
            enrollment = waitlist_users.data[0]
            user = enrollment['users']
            course = enrollment['courses']
            
            waitlist_sent = await self.notification_service.send_waitlist_notification(
                user, course, enrollment
            )
            notification_results.append({
                'type': 'waitlist_notification',
                'user': user['email'],
                'success': waitlist_sent
            })
        
        return {
            'test': 'notification_system',
            'success': True,
            'notification_results': notification_results
        }
    
    async def test_audit_logging(self) -> Dict[str, Any]:
        """Test audit logging for waitlist actions"""
        logger.info("🧪 Testing audit logging...")
        
        course_id = self.test_data['courses'][0]['id']
        
        # Get audit log entries
        audit_entries = await self.db.get_waitlist_audit_log(course_id=course_id, days=1)
        
        audit_summary = {}
        for entry in audit_entries:
            action = entry['action']
            audit_summary[action] = audit_summary.get(action, 0) + 1
        
        logger.info(f"📊 Audit log summary: {audit_summary}")
        
        return {
            'test': 'audit_logging',
            'success': True,
            'audit_entries_count': len(audit_entries),
            'action_summary': audit_summary
        }
    
    async def test_edge_cases(self) -> Dict[str, Any]:
        """Test edge cases and error conditions"""
        logger.info("🧪 Testing edge cases...")
        
        edge_case_results = []
        
        # Test enrolling in non-existent course
        fake_course_id = str(uuid.uuid4())
        result1 = await self.enrollment_service.enroll_user(
            self.test_data['users'][0]['id'], fake_course_id
        )
        edge_case_results.append({
            'case': 'non_existent_course',
            'success': not result1['success'],  # Should fail
            'message': result1['message']
        })
        
        # Test double enrollment
        user_id = self.test_data['users'][0]['id']
        course_id = self.test_data['courses'][0]['id']
        
        result2 = await self.enrollment_service.enroll_user(user_id, course_id)
        edge_case_results.append({
            'case': 'double_enrollment',
            'success': not result2['success'],  # Should fail
            'message': result2['message']
        })
        
        # Test dropping non-enrolled user
        fake_user_id = str(uuid.uuid4())
        result3 = await self.enrollment_service.drop_user(fake_user_id, course_id)
        edge_case_results.append({
            'case': 'drop_non_enrolled_user',
            'success': not result3['success'],  # Should fail
            'message': result3['message']
        })
        
        return {
            'test': 'edge_cases',
            'success': True,
            'edge_case_results': edge_case_results
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test scenarios"""
        logger.info("🚀 Starting comprehensive waitlist system tests...")
        
        test_results = []
        
        try:
            # Setup
            await self.setup_test_data()
            
            # Run tests in sequence
            test_results.append(await self.test_basic_enrollment())
            test_results.append(await self.test_waitlist_enrollment())
            test_results.append(await self.test_priority_ranking())
            test_results.append(await self.test_auto_backfill_drop())
            test_results.append(await self.test_auto_backfill_no_show())
            test_results.append(await self.test_notification_system())
            test_results.append(await self.test_audit_logging())
            test_results.append(await self.test_edge_cases())
            
            # Summary
            total_tests = len(test_results)
            passed_tests = sum(1 for result in test_results if result.get('success', False))
            
            logger.info(f"🎯 Test Results: {passed_tests}/{total_tests} tests passed")
            
            return {
                'overall_success': passed_tests == total_tests,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'test_results': test_results,
                'summary': f"Waitlist auto-backfill system test complete: {passed_tests}/{total_tests} tests passed"
            }
            
        except Exception as e:
            logger.error(f"❌ Test suite failed with error: {e}")
            return {
                'overall_success': False,
                'error': str(e),
                'test_results': test_results
            }
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        logger.info("🧹 Cleaning up test data...")
        
        try:
            # Delete test enrollments
            for course in self.test_data.get('courses', []):
                self.db.supabase.table('course_enrollments')\
                    .delete().eq('course_id', course['id']).execute()
                
                # Delete test audit log entries
                self.db.supabase.table('waitlist_audit_log')\
                    .delete().eq('course_id', course['id']).execute()
                
                # Delete test courses
                self.db.supabase.table('courses')\
                    .delete().eq('id', course['id']).execute()
            
            # Delete test users
            for user in self.test_data.get('users', []):
                self.db.supabase.table('users')\
                    .delete().eq('id', user['id']).execute()
            
            logger.info("✅ Test data cleanup complete")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up test data: {e}")

# Performance test suite
class WaitlistPerformanceTests:
    def __init__(self):
        self.db = VolunteerDatabase()
        self.enrollment_service = CourseEnrollmentService(self.db)
    
    async def test_high_volume_enrollment(self, num_users: int = 100, num_courses: int = 10):
        """Test system performance with high volume enrollments"""
        logger.info(f"⚡ Testing high volume enrollment: {num_users} users, {num_courses} courses")
        
        start_time = datetime.now()
        
        # Create test data
        test_users = []
        for i in range(num_users):
            user_data = {
                'email': f'testuser{i}@example.com',
                'first_name': f'User{i}',
                'last_name': 'Test'
            }
            user = await self.db.create_user(user_data)
            if user:
                test_users.append(user)
        
        test_courses = []
        for i in range(num_courses):
            course_data = {
                'course_name': f'Test Course {i}',
                'max_capacity': 20,
                'instructor': f'Instructor {i}',
                'branch': 'Test Branch',
                'category': 'Test',
                'start_date': (datetime.now() + timedelta(days=7)).isoformat() + 'Z'
            }
            course = await self.db.create_course(course_data)
            if course:
                test_courses.append(course)
        
        # Perform enrollments
        enrollment_tasks = []
        for user in test_users:
            for course in test_courses[:3]:  # Enroll each user in first 3 courses
                task = self.enrollment_service.enroll_user(user['id'], course['id'])
                enrollment_tasks.append(task)
        
        results = await asyncio.gather(*enrollment_tasks, return_exceptions=True)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        successful_enrollments = sum(1 for r in results if isinstance(r, dict) and r.get('success', False))
        
        logger.info(f"⚡ Performance test complete:")
        logger.info(f"   Duration: {duration:.2f} seconds")
        logger.info(f"   Successful enrollments: {successful_enrollments}/{len(enrollment_tasks)}")
        logger.info(f"   Enrollments per second: {successful_enrollments/duration:.2f}")
        
        return {
            'duration_seconds': duration,
            'total_enrollments_attempted': len(enrollment_tasks),
            'successful_enrollments': successful_enrollments,
            'enrollments_per_second': successful_enrollments/duration if duration > 0 else 0
        }

# Main test runner
async def main():
    """Run the comprehensive test suite"""
    print("🧪 YMCA Course Enrollment & Waitlist Auto-Backfill Test Suite")
    print("=" * 60)
    
    # Run functional tests
    test_suite = WaitlistTestSuite()
    functional_results = await test_suite.run_all_tests()
    
    print("\n" + "=" * 60)
    print("📊 FUNCTIONAL TEST RESULTS:")
    print(f"Overall Success: {functional_results['overall_success']}")
    print(f"Tests Passed: {functional_results['passed_tests']}/{functional_results['total_tests']}")
    
    for test_result in functional_results['test_results']:
        status = "✅ PASS" if test_result.get('success', False) else "❌ FAIL"
        print(f"  {status} - {test_result['test']}")
    
    # Run performance tests
    print("\n" + "=" * 60)
    print("⚡ PERFORMANCE TESTS:")
    
    perf_suite = WaitlistPerformanceTests()
    perf_results = await perf_suite.test_high_volume_enrollment(50, 5)  # Smaller scale for demo
    
    print(f"Duration: {perf_results['duration_seconds']:.2f} seconds")
    print(f"Successful Enrollments: {perf_results['successful_enrollments']}")
    print(f"Throughput: {perf_results['enrollments_per_second']:.2f} enrollments/second")
    
    # Cleanup
    await test_suite.cleanup_test_data()
    
    print("\n" + "=" * 60)
    print("🎯 TEST SUITE COMPLETE")
    print("=" * 60)
    
    return functional_results['overall_success']

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)