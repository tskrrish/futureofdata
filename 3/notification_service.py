"""
Notification Service for Course Enrollment and Waitlist Management
Handles email notifications, SMS alerts, and in-app notifications
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from database import VolunteerDatabase
import json
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import smtplib
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NotificationTemplate:
    subject: str
    template: str
    notification_type: str

class NotificationService:
    def __init__(self, db: VolunteerDatabase):
        self.db = db
        self.templates = self._load_notification_templates()
        
        # Email configuration (replace with your SMTP settings)
        self.smtp_host = "smtp.gmail.com"  # Configure based on your email provider
        self.smtp_port = 587
        self.smtp_username = None  # Set from environment variables
        self.smtp_password = None  # Set from environment variables
        self.from_email = "noreply@ymca.org"  # Configure your from email
    
    def _load_notification_templates(self) -> Dict[str, NotificationTemplate]:
        """Load notification templates"""
        return {
            'enrollment_confirmation': NotificationTemplate(
                subject="✅ Course Enrollment Confirmed - {course_name}",
                template="""
Dear {user_name},

Great news! You have been successfully enrolled in the course:

📚 Course: {course_name}
👨‍🏫 Instructor: {instructor}
📍 Location: {branch}
📅 Start Date: {start_date}
⏰ Schedule: {schedule}
💰 Price: ${price}

Course Details:
{course_description}

What to bring:
{requirements}

If you have any questions or need to make changes to your enrollment, please contact us at your local YMCA branch.

We're excited to see you in class!

Best regards,
The YMCA Team

---
This is an automated message. Please do not reply to this email.
                """,
                notification_type="enrollment"
            ),
            
            'waitlist_notification': NotificationTemplate(
                subject="⏳ You're on the Waitlist - {course_name}",
                template="""
Dear {user_name},

Thank you for your interest in the course "{course_name}". 

The course is currently full, but we've added you to our priority waitlist:

📚 Course: {course_name}
👨‍🏫 Instructor: {instructor}
📍 Location: {branch}
📅 Start Date: {start_date}
📋 Your Waitlist Position: #{waitlist_position}
⭐ Priority Level: {priority_text}

What happens next?
• If a spot opens up, we'll automatically enroll you and send a confirmation email
• You'll receive notification within 24 hours if a spot becomes available
• No action is required from you - we'll handle everything automatically

Keep an eye on your email - spots can open up quickly!

Best regards,
The YMCA Team

---
This is an automated message. Please do not reply to this email.
                """,
                notification_type="waitlist"
            ),
            
            'auto_enrollment_notification': NotificationTemplate(
                subject="🎉 Good News! You're Now Enrolled - {course_name}",
                template="""
Dear {user_name},

Exciting news! A spot has opened up in the course you were waitlisted for, and you've been automatically enrolled:

📚 Course: {course_name}
👨‍🏫 Instructor: {instructor}
📍 Location: {branch}
📅 Start Date: {start_date}
⏰ Schedule: {schedule}
💰 Price: ${price}

⚠️ IMPORTANT: You have been automatically enrolled from the waitlist. If you no longer wish to take this course, please contact us within 48 hours to cancel your enrollment.

Course Details:
{course_description}

What to bring:
{requirements}

Payment Information:
Your payment method on file will be charged within 24 hours. If you need to update your payment information, please contact us immediately.

We're thrilled to have you in the class!

Best regards,
The YMCA Team

---
This is an automated message. Please do not reply to this email.
                """,
                notification_type="auto_enrollment"
            ),
            
            'waitlist_position_update': NotificationTemplate(
                subject="📈 Waitlist Update - {course_name}",
                template="""
Dear {user_name},

Your position on the waitlist for "{course_name}" has been updated:

📋 New Waitlist Position: #{waitlist_position}
📊 Previous Position: #{previous_position}

This change occurred because someone ahead of you on the waitlist was enrolled or removed from the list.

You're getting closer to enrollment! We'll continue to monitor for available spots and will automatically enroll you when one becomes available.

Best regards,
The YMCA Team

---
This is an automated message. Please do not reply to this email.
                """,
                notification_type="waitlist_update"
            ),
            
            'course_reminder': NotificationTemplate(
                subject="📅 Course Starting Soon - {course_name}",
                template="""
Dear {user_name},

This is a friendly reminder that your course starts soon:

📚 Course: {course_name}
👨‍🏫 Instructor: {instructor}
📍 Location: {branch}
📅 Start Date: {start_date}
⏰ Time: {schedule_time}

What to bring:
{requirements}

Parking and Directions:
Please arrive 15 minutes early for check-in. Parking is available in the main YMCA lot.

If you need to cancel or have any questions, please contact us at least 24 hours in advance.

We look forward to seeing you!

Best regards,
The YMCA Team

---
This is an automated message. Please do not reply to this email.
                """,
                notification_type="reminder"
            )
        }
    
    async def send_enrollment_confirmation(self, user: Dict, course: Dict, 
                                         enrollment: Dict) -> bool:
        """Send enrollment confirmation notification"""
        try:
            template = self.templates['enrollment_confirmation']
            
            # Prepare template variables
            variables = self._prepare_course_variables(user, course, enrollment)
            
            # Send notification
            success = await self._send_notification(
                user, template, variables, 'enrollment_confirmed'
            )
            
            if success:
                await self.db.mark_notification_sent(enrollment['id'])
                await self._log_notification('enrollment_confirmed', user['id'], course['id'])
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error sending enrollment confirmation: {e}")
            return False
    
    async def send_waitlist_notification(self, user: Dict, course: Dict, 
                                       enrollment: Dict) -> bool:
        """Send waitlist notification"""
        try:
            template = self.templates['waitlist_notification']
            
            # Prepare template variables
            variables = self._prepare_course_variables(user, course, enrollment)
            variables.update({
                'waitlist_position': enrollment.get('waitlist_position', 'TBD'),
                'priority_text': self._get_priority_text(enrollment.get('waitlist_priority', 5))
            })
            
            # Send notification
            success = await self._send_notification(
                user, template, variables, 'waitlisted'
            )
            
            if success:
                await self._log_notification('waitlisted', user['id'], course['id'])
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error sending waitlist notification: {e}")
            return False
    
    async def send_auto_enrollment_notification(self, user: Dict, course: Dict, 
                                              enrollment: Dict) -> bool:
        """Send auto-enrollment notification"""
        try:
            template = self.templates['auto_enrollment_notification']
            
            # Prepare template variables
            variables = self._prepare_course_variables(user, course, enrollment)
            
            # Send notification
            success = await self._send_notification(
                user, template, variables, 'auto_enrolled'
            )
            
            if success:
                await self.db.mark_notification_sent(enrollment['id'])
                await self._log_notification('auto_enrolled', user['id'], course['id'])
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error sending auto-enrollment notification: {e}")
            return False
    
    async def send_waitlist_position_update(self, user: Dict, course: Dict, 
                                          current_position: int, previous_position: int) -> bool:
        """Send waitlist position update notification"""
        try:
            template = self.templates['waitlist_position_update']
            
            # Only send if position improved significantly (moved up by 3+ positions)
            if previous_position - current_position < 3:
                return True  # Skip sending for minor changes
            
            # Prepare template variables
            variables = self._prepare_course_variables(user, course, {})
            variables.update({
                'waitlist_position': current_position,
                'previous_position': previous_position
            })
            
            # Send notification
            success = await self._send_notification(
                user, template, variables, 'waitlist_position_updated'
            )
            
            if success:
                await self._log_notification('waitlist_position_updated', user['id'], course['id'])
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error sending position update notification: {e}")
            return False
    
    async def send_course_reminders(self, days_before: int = 1) -> Dict[str, Any]:
        """Send course start reminders to enrolled students"""
        try:
            # Get courses starting in specified days
            target_date = datetime.now() + timedelta(days=days_before)
            
            courses_starting = self.db.supabase.table('courses')\
                .select('*')\
                .gte('start_date', target_date.date().isoformat())\
                .lt('start_date', (target_date + timedelta(days=1)).date().isoformat())\
                .eq('status', 'open')\
                .execute()
            
            reminder_count = 0
            for course in courses_starting.data or []:
                # Get enrolled students
                enrollments = self.db.supabase.table('course_enrollments')\
                    .select('*, users(*)')\
                    .eq('course_id', course['id'])\
                    .eq('enrollment_status', 'enrolled')\
                    .execute()
                
                for enrollment in enrollments.data or []:
                    user = enrollment['users']
                    success = await self._send_course_reminder(user, course, enrollment)
                    if success:
                        reminder_count += 1
            
            return {
                'success': True,
                'courses_processed': len(courses_starting.data or []),
                'reminders_sent': reminder_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error sending course reminders: {e}")
            return {'success': False, 'message': f'Error: {e}'}
    
    async def process_pending_notifications(self) -> Dict[str, Any]:
        """Process all pending notifications"""
        try:
            # Get users who need enrollment notifications
            pending_enrollments = await self.db.get_users_needing_notification(None)
            
            notification_count = 0
            for enrollment in pending_enrollments:
                user = enrollment['users']
                course = enrollment['courses']
                
                success = await self.send_enrollment_confirmation(user, course, enrollment)
                if success:
                    notification_count += 1
            
            return {
                'success': True,
                'notifications_sent': notification_count,
                'message': f'Processed {notification_count} pending notifications'
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing pending notifications: {e}")
            return {'success': False, 'message': f'Error: {e}'}
    
    # Private helper methods
    
    def _prepare_course_variables(self, user: Dict, course: Dict, 
                                enrollment: Dict) -> Dict[str, str]:
        """Prepare template variables for course-related notifications"""
        start_date = "TBD"
        schedule = "TBD"
        schedule_time = "TBD"
        
        if course.get('start_date'):
            try:
                start_date_obj = datetime.fromisoformat(course['start_date'].replace('Z', '+00:00'))
                start_date = start_date_obj.strftime("%A, %B %d, %Y")
            except:
                pass
        
        if course.get('schedule_days') and course.get('schedule_time'):
            days = ', '.join(course['schedule_days']) if isinstance(course['schedule_days'], list) else course['schedule_days']
            schedule = f"{days} at {course['schedule_time']}"
            schedule_time = course['schedule_time']
        
        return {
            'user_name': f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or 'Valued Member',
            'course_name': course.get('course_name', 'Course'),
            'instructor': course.get('instructor', 'TBD'),
            'branch': course.get('branch', 'YMCA'),
            'start_date': start_date,
            'schedule': schedule,
            'schedule_time': schedule_time,
            'price': f"{course.get('price', 0):.2f}",
            'course_description': course.get('course_description', 'Course details to be provided.'),
            'requirements': course.get('requirements', 'No special requirements.')
        }
    
    def _get_priority_text(self, priority: int) -> str:
        """Convert priority number to human-readable text"""
        priority_map = {
            1: "VIP Priority (Staff/Volunteer)",
            2: "Member Priority", 
            3: "Returning Student Priority",
            4: "Early Registration Priority",
            5: "Standard Priority"
        }
        return priority_map.get(priority, "Standard Priority")
    
    async def _send_notification(self, user: Dict, template: NotificationTemplate, 
                               variables: Dict[str, str], notification_type: str) -> bool:
        """Send notification using multiple channels"""
        try:
            # Format template
            subject = template.subject.format(**variables)
            body = template.template.format(**variables)
            
            # Send email notification
            email_success = await self._send_email(user['email'], subject, body)
            
            # Send SMS notification if phone number available (placeholder)
            sms_success = True  # await self._send_sms(user.get('phone'), subject)
            
            # Create in-app notification (placeholder)
            inapp_success = await self._create_in_app_notification(
                user['id'], notification_type, subject, body
            )
            
            return email_success  # At minimum, email should succeed
            
        except Exception as e:
            logger.error(f"❌ Error sending notification: {e}")
            return False
    
    async def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email notification"""
        try:
            # This is a placeholder implementation
            # In production, integrate with your email service (SendGrid, AWS SES, etc.)
            
            logger.info(f"📧 [EMAIL] To: {to_email}")
            logger.info(f"📧 [EMAIL] Subject: {subject}")
            logger.info(f"📧 [EMAIL] Body: {body[:100]}...")
            
            # Placeholder for actual email sending
            # msg = MimeMultipart()
            # msg['From'] = self.from_email
            # msg['To'] = to_email
            # msg['Subject'] = subject
            # msg.attach(MimeText(body, 'plain'))
            
            # with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            #     server.starttls()
            #     server.login(self.smtp_username, self.smtp_password)
            #     server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
            return False
    
    async def _send_sms(self, phone_number: Optional[str], message: str) -> bool:
        """Send SMS notification (placeholder)"""
        if not phone_number:
            return True
        
        try:
            # This is a placeholder for SMS integration (Twilio, AWS SNS, etc.)
            logger.info(f"📱 [SMS] To: {phone_number}")
            logger.info(f"📱 [SMS] Message: {message[:50]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending SMS: {e}")
            return False
    
    async def _create_in_app_notification(self, user_id: str, notification_type: str, 
                                        title: str, content: str) -> bool:
        """Create in-app notification"""
        try:
            # Store notification in database for in-app display
            notification_data = {
                'user_id': user_id,
                'notification_type': notification_type,
                'title': title,
                'content': content,
                'is_read': False,
                'created_at': datetime.now().isoformat()
            }
            
            # This assumes you have a notifications table for in-app notifications
            # result = self.db.supabase.table('in_app_notifications').insert(notification_data).execute()
            
            logger.info(f"📱 [IN-APP] Created notification for user {user_id}: {title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating in-app notification: {e}")
            return False
    
    async def _send_course_reminder(self, user: Dict, course: Dict, enrollment: Dict) -> bool:
        """Send course start reminder"""
        try:
            template = self.templates['course_reminder']
            variables = self._prepare_course_variables(user, course, enrollment)
            
            return await self._send_notification(
                user, template, variables, 'course_reminder'
            )
            
        except Exception as e:
            logger.error(f"❌ Error sending course reminder: {e}")
            return False
    
    async def _log_notification(self, notification_type: str, user_id: str, 
                              course_id: str, metadata: Dict = None) -> bool:
        """Log notification for analytics"""
        try:
            return await self.db.track_event(
                f'notification_{notification_type}',
                {
                    'user_id': user_id,
                    'course_id': course_id,
                    'metadata': metadata or {}
                },
                user_id
            )
        except Exception as e:
            logger.error(f"❌ Error logging notification: {e}")
            return False

# Background notification service
class NotificationBackgroundService:
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.running = False
        self.check_interval = 600  # 10 minutes
    
    async def start(self):
        """Start the background notification service"""
        self.running = True
        logger.info("📧 Starting notification background service")
        
        while self.running:
            try:
                # Process pending notifications
                await self.notification_service.process_pending_notifications()
                
                # Check for course reminders (daily at 9 AM)
                current_time = datetime.now()
                if current_time.hour == 9 and current_time.minute < 10:
                    await self.notification_service.send_course_reminders(1)  # 1 day before
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error in notification background service: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    def stop(self):
        """Stop the background notification service"""
        self.running = False
        logger.info("🛑 Stopping notification background service")

# Usage example
async def example_notification_usage():
    """Example of how to use the notification service"""
    from database import VolunteerDatabase
    
    # Initialize services
    db = VolunteerDatabase()
    notification_service = NotificationService(db)
    
    # Example: Send enrollment confirmation
    example_user = {
        'id': 'user123',
        'email': 'john.doe@example.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'phone': '+1234567890'
    }
    
    example_course = {
        'id': 'course123',
        'course_name': 'Youth Basketball Skills',
        'instructor': 'Coach Mike',
        'branch': 'Blue Ash YMCA',
        'start_date': '2025-10-01T18:00:00Z',
        'schedule_days': ['Monday', 'Wednesday'],
        'schedule_time': '6:00 PM',
        'price': 50.00,
        'course_description': 'Basketball fundamentals for kids',
        'requirements': 'Athletic shoes required'
    }
    
    example_enrollment = {
        'id': 'enrollment123',
        'enrollment_status': 'enrolled'
    }
    
    # Send confirmation
    success = await notification_service.send_enrollment_confirmation(
        example_user, example_course, example_enrollment
    )
    
    print(f"Notification sent: {success}")

if __name__ == "__main__":
    asyncio.run(example_notification_usage())