"""
YMCA Course Enrollment with Waitlist Auto-Backfill System
Main application integration demonstrating the complete system
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from database import VolunteerDatabase
from course_enrollment_service import CourseEnrollmentService, WaitlistBackgroundService
from notification_service import NotificationService, NotificationBackgroundService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WaitlistAutoBackfillApp:
    def __init__(self):
        # Initialize core services
        self.db = VolunteerDatabase()
        self.enrollment_service = CourseEnrollmentService(self.db)
        self.notification_service = NotificationService(self.db)
        
        # Initialize background services
        self.waitlist_bg_service = WaitlistBackgroundService(self.enrollment_service)
        self.notification_bg_service = NotificationBackgroundService(self.notification_service)
        
        # Application state
        self.running = False
    
    async def initialize(self):
        """Initialize the application and database"""
        logger.info("🚀 Initializing YMCA Course Enrollment System...")
        
        # Initialize database tables
        await self.db.initialize_tables()
        
        logger.info("✅ Application initialized successfully")
    
    async def create_sample_data(self):
        """Create sample courses and users for demonstration"""
        logger.info("📝 Creating sample data...")
        
        # Sample courses
        sample_courses = [
            {
                'course_name': 'Youth Basketball Skills Development',
                'course_description': 'Comprehensive basketball training for kids aged 8-14. Focus on fundamentals, teamwork, and fun!',
                'instructor': 'Coach Michael Jordan Jr.',
                'branch': 'Blue Ash YMCA',
                'category': 'Youth Sports',
                'max_capacity': 15,
                'current_enrolled': 0,
                'start_date': (datetime.now() + timedelta(days=14)).isoformat() + 'Z',
                'end_date': (datetime.now() + timedelta(days=44)).isoformat() + 'Z',
                'schedule_days': ['Monday', 'Wednesday', 'Friday'],
                'schedule_time': '18:00:00',
                'price': 75.00,
                'requirements': 'Ages 8-14, athletic shoes required, water bottle recommended',
                'status': 'open'
            },
            {
                'course_name': 'Adult Yoga & Meditation',
                'course_description': 'Relaxing yoga sessions combined with mindfulness meditation for stress relief.',
                'instructor': 'Sarah Williams, Certified Yoga Instructor',
                'branch': 'Downtown YMCA',
                'category': 'Wellness',
                'max_capacity': 20,
                'current_enrolled': 0,
                'start_date': (datetime.now() + timedelta(days=10)).isoformat() + 'Z',
                'end_date': (datetime.now() + timedelta(days=40)).isoformat() + 'Z',
                'schedule_days': ['Tuesday', 'Thursday'],
                'schedule_time': '19:00:00',
                'price': 90.00,
                'requirements': 'Bring yoga mat and comfortable clothing',
                'status': 'open'
            },
            {
                'course_name': 'Senior Water Aerobics',
                'course_description': 'Low-impact water exercise program designed for seniors to improve strength and flexibility.',
                'instructor': 'Linda Thompson, Aquatic Specialist',
                'branch': 'Westside YMCA',
                'category': 'Aquatics',
                'max_capacity': 12,
                'current_enrolled': 0,
                'start_date': (datetime.now() + timedelta(days=7)).isoformat() + 'Z',
                'end_date': (datetime.now() + timedelta(days=37)).isoformat() + 'Z',
                'schedule_days': ['Monday', 'Wednesday', 'Friday'],
                'schedule_time': '10:00:00',
                'price': 60.00,
                'requirements': 'Ages 55+, basic swimming ability helpful but not required',
                'status': 'open'
            }
        ]
        
        created_courses = []
        for course_data in sample_courses:
            course = await self.db.create_course(course_data)
            if course:
                created_courses.append(course)
                logger.info(f"✅ Created course: {course['course_name']}")
        
        # Sample users with different priorities
        sample_users = [
            {
                'email': 'staff.trainer@ymca.org',
                'first_name': 'Alex',
                'last_name': 'Staff',
                'phone': '+1234567890',
                'age': 28,
                'city': 'Cincinnati',
                'state': 'OH',
                'is_ymca_member': True,
                'member_branch': 'Blue Ash YMCA',
                'profile_type': 'staff'
            },
            {
                'email': 'premium.member@example.com',
                'first_name': 'Jennifer',
                'last_name': 'Premium',
                'phone': '+1234567891',
                'age': 35,
                'city': 'Cincinnati',
                'state': 'OH',
                'is_ymca_member': True,
                'member_branch': 'Downtown YMCA',
                'profile_type': 'member'
            },
            {
                'email': 'returning.student@example.com',
                'first_name': 'Michael',
                'last_name': 'Returning',
                'phone': '+1234567892',
                'age': 42,
                'city': 'Cincinnati',
                'state': 'OH',
                'is_ymca_member': True,
                'member_branch': 'Blue Ash YMCA',
                'profile_type': 'returning'
            },
            {
                'email': 'new.member1@example.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'phone': '+1234567893',
                'age': 29,
                'city': 'Cincinnati',
                'state': 'OH',
                'is_ymca_member': False,
                'profile_type': 'normal'
            },
            {
                'email': 'new.member2@example.com',
                'first_name': 'David',
                'last_name': 'Wilson',
                'phone': '+1234567894',
                'age': 31,
                'city': 'Cincinnati',
                'state': 'OH',
                'is_ymca_member': False,
                'profile_type': 'normal'
            },
            {
                'email': 'senior.member@example.com',
                'first_name': 'Margaret',
                'last_name': 'Senior',
                'phone': '+1234567895',
                'age': 67,
                'city': 'Cincinnati',
                'state': 'OH',
                'is_ymca_member': True,
                'member_branch': 'Westside YMCA',
                'profile_type': 'senior'
            }
        ]
        
        created_users = []
        for user_data in sample_users:
            profile_type = user_data.pop('profile_type')
            user = await self.db.create_user(user_data)
            if user:
                user['profile_type'] = profile_type
                created_users.append(user)
                logger.info(f"✅ Created user: {user['email']} ({profile_type})")
        
        return created_courses, created_users
    
    async def demonstrate_enrollment_flow(self, courses: List[Dict], users: List[Dict]):
        """Demonstrate the complete enrollment and waitlist flow"""
        logger.info("🎯 Demonstrating enrollment flow...")
        
        # Select basketball course for demonstration (smallest capacity for waitlist demo)
        target_course = courses[0]  # Youth Basketball
        logger.info(f"🏀 Target course: {target_course['course_name']} (capacity: {target_course['max_capacity']})")
        
        # Phase 1: Initial enrollments (fill course to capacity)
        logger.info("\n📝 Phase 1: Initial Enrollments")
        enrollment_results = []
        
        for i, user in enumerate(users):
            if i >= target_course['max_capacity']:
                break
            
            result = await self.enrollment_service.enroll_user(
                user['id'], 
                target_course['id'],
                self._get_priority_for_user(user)
            )
            
            enrollment_results.append({
                'user': f"{user['first_name']} {user['last_name']}",
                'profile': user['profile_type'],
                'result': result
            })
            
            status_icon = "✅" if result['success'] else "❌"
            logger.info(f"  {status_icon} {user['first_name']} {user['last_name']} ({user['profile_type']}): {result['status']}")
            
            # Small delay to simulate real enrollment timing
            await asyncio.sleep(0.1)
        
        # Phase 2: Waitlist enrollments (additional users)
        logger.info("\n⏳ Phase 2: Waitlist Enrollments")
        waitlist_results = []
        
        for user in users[target_course['max_capacity']:]:
            result = await self.enrollment_service.enroll_user(
                user['id'],
                target_course['id'],
                self._get_priority_for_user(user)
            )
            
            waitlist_results.append({
                'user': f"{user['first_name']} {user['last_name']}",
                'profile': user['profile_type'],
                'result': result
            })
            
            if result['success'] and result['status'] == 'waitlisted':
                position = result.get('enrollment', {}).get('waitlist_position', 'TBD')
                logger.info(f"  📋 {user['first_name']} {user['last_name']} ({user['profile_type']}): Waitlisted at position #{position}")
            
            await asyncio.sleep(0.1)
        
        # Show current waitlist status
        await self._show_waitlist_status(target_course['id'])
        
        # Phase 3: Simulate drop and auto-backfill
        logger.info("\n👋 Phase 3: Student Drop and Auto-Backfill")
        
        # Get an enrolled student to drop
        enrolled_students = self.db.supabase.table('course_enrollments')\
            .select('*, users(*)')\
            .eq('course_id', target_course['id'])\
            .eq('enrollment_status', 'enrolled')\
            .limit(1)\
            .execute()
        
        if enrolled_students.data:
            student_to_drop = enrolled_students.data[0]
            logger.info(f"  👋 Dropping {student_to_drop['users']['first_name']} {student_to_drop['users']['last_name']}")
            
            drop_result = await self.enrollment_service.drop_user(
                student_to_drop['user_id'], 
                target_course['id'], 
                'demonstration_drop'
            )
            
            if drop_result['success']:
                backfill_info = drop_result.get('backfill_result', {})
                if backfill_info.get('enrolled_count', 0) > 0:
                    promoted_users = backfill_info.get('enrolled_users', [])
                    for promoted_user in promoted_users:
                        logger.info(f"  🎉 Auto-enrolled from waitlist: {promoted_user['user_name']}")
                else:
                    logger.info("  📋 No suitable candidates found on waitlist for auto-enrollment")
        
        # Show updated status
        await self._show_waitlist_status(target_course['id'])
        
        # Phase 4: Simulate no-show and auto-backfill
        logger.info("\n👻 Phase 4: No-Show and Auto-Backfill")
        
        enrolled_students = self.db.supabase.table('course_enrollments')\
            .select('*, users(*)')\
            .eq('course_id', target_course['id'])\
            .eq('enrollment_status', 'enrolled')\
            .limit(1)\
            .execute()
        
        if enrolled_students.data:
            no_show_student = enrolled_students.data[0]
            logger.info(f"  👻 Marking no-show: {no_show_student['users']['first_name']} {no_show_student['users']['last_name']}")
            
            no_show_result = await self.enrollment_service.mark_no_show(
                no_show_student['user_id'], 
                target_course['id']
            )
            
            if no_show_result['success']:
                backfill_info = no_show_result.get('backfill_result', {})
                if backfill_info.get('enrolled_count', 0) > 0:
                    promoted_users = backfill_info.get('enrolled_users', [])
                    for promoted_user in promoted_users:
                        logger.info(f"  🎉 Auto-enrolled from waitlist: {promoted_user['user_name']}")
        
        # Final status
        await self._show_waitlist_status(target_course['id'])
        
        return {
            'initial_enrollments': enrollment_results,
            'waitlist_enrollments': waitlist_results,
            'demonstration_complete': True
        }
    
    async def demonstrate_notifications(self, courses: List[Dict]):
        """Demonstrate notification system"""
        logger.info("\n📧 Demonstrating Notification System...")
        
        # Process pending notifications
        notification_result = await self.notification_service.process_pending_notifications()
        logger.info(f"  📧 Processed {notification_result.get('notifications_sent', 0)} pending notifications")
        
        # Send course reminders (simulated)
        reminder_result = await self.notification_service.send_course_reminders(days_before=1)
        logger.info(f"  📅 Sent {reminder_result.get('reminders_sent', 0)} course reminders")
        
        return notification_result
    
    async def show_analytics(self, courses: List[Dict]):
        """Display system analytics"""
        logger.info("\n📊 System Analytics")
        logger.info("=" * 50)
        
        for course in courses:
            # Course analytics
            course_analytics = await self.db.get_course_analytics(course['id'], days=1)
            
            logger.info(f"\n📚 {course['course_name']}:")
            logger.info(f"  🎯 Total Enrollments: {course_analytics.get('total_enrollments', 0)}")
            logger.info(f"  ✅ Currently Enrolled: {course_analytics.get('enrolled', 0)}")
            logger.info(f"  ⏳ On Waitlist: {course_analytics.get('waitlisted', 0)}")
            logger.info(f"  👋 Dropped: {course_analytics.get('dropped', 0)}")
            logger.info(f"  🤖 Auto-Enrolled: {course_analytics.get('auto_enrolled', 0)}")
        
        # Overall user analytics
        user_analytics = await self.db.get_user_analytics(days=1)
        logger.info(f"\n👥 User Statistics:")
        logger.info(f"  🆕 New Users: {user_analytics.get('new_users', 0)}")
        logger.info(f"  💬 Conversations: {user_analytics.get('conversations', 0)}")
        logger.info(f"  📝 Messages: {user_analytics.get('messages', 0)}")
    
    async def show_audit_log(self, courses: List[Dict]):
        """Display audit log for waitlist actions"""
        logger.info("\n📋 Waitlist Audit Log")
        logger.info("=" * 50)
        
        for course in courses:
            audit_entries = await self.db.get_waitlist_audit_log(course['id'], days=1)
            
            if audit_entries:
                logger.info(f"\n📚 {course['course_name']}:")
                for entry in audit_entries[:10]:  # Show last 10 entries
                    timestamp = entry['created_at'][:19]  # Remove timezone info for display
                    user_name = f"{entry.get('users', {}).get('first_name', 'Unknown')} {entry.get('users', {}).get('last_name', 'User')}"
                    logger.info(f"  {timestamp} - {entry['action']} - {user_name} - {entry['reason']}")
    
    async def _show_waitlist_status(self, course_id: str):
        """Show current course and waitlist status"""
        course = await self.db.get_course(course_id)
        waitlist_candidates = await self.db.get_waitlist_candidates(course_id)
        
        logger.info(f"\n📊 Current Status for {course['course_name']}:")
        logger.info(f"  🎯 Enrolled: {course['current_enrolled']}/{course['max_capacity']}")
        logger.info(f"  📋 Waitlist: {len(waitlist_candidates)} candidates")
        
        if waitlist_candidates:
            logger.info("  📋 Waitlist Order:")
            for i, candidate in enumerate(waitlist_candidates[:5]):  # Show top 5
                user_info = candidate['users']
                priority_text = self._get_priority_text(candidate['waitlist_priority'])
                logger.info(f"    #{i+1}: {user_info['first_name']} {user_info['last_name']} ({priority_text})")
    
    def _get_priority_for_user(self, user: Dict) -> int:
        """Determine waitlist priority based on user profile"""
        if user['profile_type'] == 'staff':
            return 1  # Highest priority
        elif user['profile_type'] == 'member':
            return 2  # Member priority
        elif user['profile_type'] == 'returning':
            return 3  # Returning student priority
        elif user['profile_type'] == 'senior':
            return 2  # Senior member priority
        else:
            return 5  # Normal priority
    
    def _get_priority_text(self, priority: int) -> str:
        """Convert priority number to text"""
        priority_map = {
            1: "Staff/VIP",
            2: "Member", 
            3: "Returning Student",
            4: "Early Bird",
            5: "Standard"
        }
        return priority_map.get(priority, "Standard")
    
    async def start_background_services(self):
        """Start background services for automatic processing"""
        logger.info("🔄 Starting background services...")
        
        # Start waitlist monitoring service
        waitlist_task = asyncio.create_task(self.waitlist_bg_service.start())
        
        # Start notification processing service
        notification_task = asyncio.create_task(self.notification_bg_service.start())
        
        logger.info("✅ Background services started")
        
        return waitlist_task, notification_task
    
    async def stop_background_services(self):
        """Stop background services"""
        logger.info("🛑 Stopping background services...")
        
        self.waitlist_bg_service.stop()
        self.notification_bg_service.stop()
        
        logger.info("✅ Background services stopped")
    
    async def run_demonstration(self):
        """Run complete system demonstration"""
        try:
            # Initialize system
            await self.initialize()
            
            # Create sample data
            courses, users = await self.create_sample_data()
            
            # Demonstrate core functionality
            await self.demonstrate_enrollment_flow(courses, users)
            
            # Demonstrate notifications
            await self.demonstrate_notifications(courses)
            
            # Show analytics
            await self.show_analytics(courses)
            
            # Show audit log
            await self.show_audit_log(courses)
            
            logger.info("\n🎉 Demonstration Complete!")
            logger.info("=" * 60)
            logger.info("✅ YMCA Course Enrollment with Waitlist Auto-Backfill System")
            logger.info("   • Intelligent priority-based waitlist management")
            logger.info("   • Automatic backfill on drops and no-shows")
            logger.info("   • Multi-channel notifications")
            logger.info("   • Comprehensive audit logging")
            logger.info("   • Real-time analytics and reporting")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Demonstration failed: {e}")
            raise

async def main():
    """Main application entry point"""
    print("🏢 YMCA Course Enrollment & Waitlist Auto-Backfill System")
    print("=" * 60)
    print("This system demonstrates automated waitlist management with")
    print("intelligent ranking and auto-backfill capabilities.")
    print("=" * 60)
    
    app = WaitlistAutoBackfillApp()
    
    try:
        await app.run_demonstration()
    except KeyboardInterrupt:
        logger.info("👋 Application interrupted by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        raise
    finally:
        await app.stop_background_services()

if __name__ == "__main__":
    asyncio.run(main())