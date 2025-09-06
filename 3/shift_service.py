"""
Shift Management Service for YMCA Volunteer System
Handles shift creation, notifications, and approval workflows
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import logging

from pydantic import BaseModel
from database import VolunteerDatabase
from slack_integration import slack_integration, ShiftNotification, ApprovalRequest

logger = logging.getLogger(__name__)

class Shift(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    location: str
    branch: str
    coordinator_email: str
    skills_required: Optional[List[str]] = None
    max_volunteers: int = 1
    current_volunteers: int = 0
    requires_approval: bool = True
    status: str = "active"  # active, cancelled, completed
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ShiftSignup(BaseModel):
    id: Optional[str] = None
    shift_id: str
    volunteer_id: str
    volunteer_name: str
    volunteer_email: str
    status: str = "pending"  # pending, approved, denied, cancelled
    signup_time: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None

class ShiftService:
    def __init__(self):
        self.database = VolunteerDatabase()
        
    async def create_shift(self, shift_data: Shift, announce: bool = True) -> str:
        """Create a new volunteer shift and optionally announce it"""
        try:
            # Generate shift ID
            shift_id = str(uuid.uuid4())
            shift_data.id = shift_id
            shift_data.created_at = datetime.now()
            shift_data.updated_at = datetime.now()
            
            # Save to database (placeholder - implement based on your database schema)
            await self._save_shift_to_database(shift_data)
            
            # Send announcement to Slack if enabled
            if announce:
                notification = ShiftNotification(
                    shift_id=shift_id,
                    volunteer_id="",  # General announcement
                    volunteer_name="",
                    volunteer_email="",
                    shift_title=shift_data.title,
                    shift_description=shift_data.description,
                    start_time=shift_data.start_time,
                    end_time=shift_data.end_time,
                    location=shift_data.location,
                    branch=shift_data.branch,
                    coordinator_email=shift_data.coordinator_email,
                    skills_required=shift_data.skills_required,
                    notification_type="new"
                )
                
                await slack_integration.send_channel_announcement(notification)
            
            logger.info(f"Created shift {shift_id}: {shift_data.title}")
            return shift_id
            
        except Exception as e:
            logger.error(f"Error creating shift: {e}")
            raise

    async def signup_for_shift(self, shift_id: str, volunteer_id: str, volunteer_name: str, 
                             volunteer_email: str) -> str:
        """Sign up volunteer for a shift"""
        try:
            # Get shift details
            shift = await self._get_shift_from_database(shift_id)
            if not shift:
                raise ValueError(f"Shift {shift_id} not found")
                
            if shift.status != "active":
                raise ValueError(f"Shift {shift_id} is not active")
                
            if shift.current_volunteers >= shift.max_volunteers:
                raise ValueError(f"Shift {shift_id} is full")
            
            # Create signup record
            signup_id = str(uuid.uuid4())
            signup = ShiftSignup(
                id=signup_id,
                shift_id=shift_id,
                volunteer_id=volunteer_id,
                volunteer_name=volunteer_name,
                volunteer_email=volunteer_email,
                status="approved" if not shift.requires_approval else "pending",
                signup_time=datetime.now()
            )
            
            # Save signup to database
            await self._save_signup_to_database(signup)
            
            # Send notification to volunteer
            notification = ShiftNotification(
                shift_id=shift_id,
                volunteer_id=volunteer_id,
                volunteer_name=volunteer_name,
                volunteer_email=volunteer_email,
                shift_title=shift.title,
                shift_description=shift.description,
                start_time=shift.start_time,
                end_time=shift.end_time,
                location=shift.location,
                branch=shift.branch,
                coordinator_email=shift.coordinator_email,
                skills_required=shift.skills_required,
                notification_type="new"
            )
            
            await slack_integration.send_direct_message(notification)
            
            # If approval required, send approval request
            if shift.requires_approval:
                approval_request = ApprovalRequest(
                    request_id=signup_id,
                    volunteer_id=volunteer_id,
                    volunteer_name=volunteer_name,
                    volunteer_email=volunteer_email,
                    shift_id=shift_id,
                    shift_title=shift.title,
                    request_type="signup",
                    request_details={"signup_time": signup.signup_time.isoformat()},
                    approver_email=shift.coordinator_email,
                    created_at=datetime.now()
                )
                
                await slack_integration.send_approval_request(approval_request)
            
            logger.info(f"Volunteer {volunteer_id} signed up for shift {shift_id}")
            return signup_id
            
        except Exception as e:
            logger.error(f"Error signing up for shift: {e}")
            raise

    async def approve_signup(self, signup_id: str, approver_id: str, notes: Optional[str] = None) -> bool:
        """Approve a volunteer signup"""
        try:
            # Get signup details
            signup = await self._get_signup_from_database(signup_id)
            if not signup:
                raise ValueError(f"Signup {signup_id} not found")
                
            if signup.status != "pending":
                raise ValueError(f"Signup {signup_id} is not pending")
            
            # Update signup status
            signup.status = "approved"
            signup.approved_by = approver_id
            signup.approved_at = datetime.now()
            signup.notes = notes
            
            await self._update_signup_in_database(signup)
            
            # Get shift details for notification
            shift = await self._get_shift_from_database(signup.shift_id)
            
            # Send confirmation to volunteer
            notification = ShiftNotification(
                shift_id=signup.shift_id,
                volunteer_id=signup.volunteer_id,
                volunteer_name=signup.volunteer_name,
                volunteer_email=signup.volunteer_email,
                shift_title=shift.title,
                shift_description=shift.description,
                start_time=shift.start_time,
                end_time=shift.end_time,
                location=shift.location,
                branch=shift.branch,
                coordinator_email=shift.coordinator_email,
                notification_type="new"
            )
            
            await slack_integration.send_direct_message(notification)
            
            logger.info(f"Approved signup {signup_id} by {approver_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error approving signup: {e}")
            raise

    async def cancel_shift(self, shift_id: str, reason: str = "") -> bool:
        """Cancel a shift and notify all signed-up volunteers"""
        try:
            # Get shift details
            shift = await self._get_shift_from_database(shift_id)
            if not shift:
                raise ValueError(f"Shift {shift_id} not found")
            
            # Update shift status
            shift.status = "cancelled"
            shift.updated_at = datetime.now()
            await self._update_shift_in_database(shift)
            
            # Get all volunteers signed up for this shift
            signups = await self._get_shift_signups(shift_id)
            
            # Send cancellation notifications
            for signup in signups:
                if signup.status == "approved":
                    notification = ShiftNotification(
                        shift_id=shift_id,
                        volunteer_id=signup.volunteer_id,
                        volunteer_name=signup.volunteer_name,
                        volunteer_email=signup.volunteer_email,
                        shift_title=shift.title,
                        shift_description=f"Cancelled: {reason}" if reason else "This shift has been cancelled.",
                        start_time=shift.start_time,
                        end_time=shift.end_time,
                        location=shift.location,
                        branch=shift.branch,
                        coordinator_email=shift.coordinator_email,
                        notification_type="cancellation"
                    )
                    
                    await slack_integration.send_direct_message(notification)
            
            logger.info(f"Cancelled shift {shift_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling shift: {e}")
            return False

    async def send_shift_reminders(self, hours_before: int = 24) -> int:
        """Send reminders for upcoming shifts"""
        try:
            # Get shifts starting in the specified timeframe
            reminder_time = datetime.now() + timedelta(hours=hours_before)
            upcoming_shifts = await self._get_upcoming_shifts(reminder_time, hours_before)
            
            reminders_sent = 0
            
            for shift in upcoming_shifts:
                # Get approved signups for this shift
                signups = await self._get_approved_signups(shift.id)
                
                for signup in signups:
                    notification = ShiftNotification(
                        shift_id=shift.id,
                        volunteer_id=signup.volunteer_id,
                        volunteer_name=signup.volunteer_name,
                        volunteer_email=signup.volunteer_email,
                        shift_title=shift.title,
                        shift_description=shift.description,
                        start_time=shift.start_time,
                        end_time=shift.end_time,
                        location=shift.location,
                        branch=shift.branch,
                        coordinator_email=shift.coordinator_email,
                        notification_type="reminder"
                    )
                    
                    success = await slack_integration.send_shift_reminder(notification, hours_before)
                    if success:
                        reminders_sent += 1
            
            logger.info(f"Sent {reminders_sent} shift reminders")
            return reminders_sent
            
        except Exception as e:
            logger.error(f"Error sending shift reminders: {e}")
            return 0

    async def get_volunteer_shifts(self, volunteer_id: str) -> List[Dict[str, Any]]:
        """Get all shifts for a volunteer"""
        try:
            signups = await self._get_volunteer_signups(volunteer_id)
            shifts_data = []
            
            for signup in signups:
                shift = await self._get_shift_from_database(signup.shift_id)
                if shift:
                    shifts_data.append({
                        "shift": shift.dict(),
                        "signup": signup.dict()
                    })
            
            return shifts_data
            
        except Exception as e:
            logger.error(f"Error getting volunteer shifts: {e}")
            return []

    # Database interaction methods (placeholders - implement based on your database schema)
    
    async def _save_shift_to_database(self, shift: Shift):
        """Save shift to database"""
        # Placeholder - implement based on your database schema
        logger.info(f"Saving shift to database: {shift.id}")

    async def _get_shift_from_database(self, shift_id: str) -> Optional[Shift]:
        """Get shift from database"""
        # Placeholder - implement based on your database schema
        logger.info(f"Getting shift from database: {shift_id}")
        return None

    async def _update_shift_in_database(self, shift: Shift):
        """Update shift in database"""
        logger.info(f"Updating shift in database: {shift.id}")

    async def _save_signup_to_database(self, signup: ShiftSignup):
        """Save signup to database"""
        logger.info(f"Saving signup to database: {signup.id}")

    async def _get_signup_from_database(self, signup_id: str) -> Optional[ShiftSignup]:
        """Get signup from database"""
        logger.info(f"Getting signup from database: {signup_id}")
        return None

    async def _update_signup_in_database(self, signup: ShiftSignup):
        """Update signup in database"""
        logger.info(f"Updating signup in database: {signup.id}")

    async def _get_shift_signups(self, shift_id: str) -> List[ShiftSignup]:
        """Get all signups for a shift"""
        logger.info(f"Getting signups for shift: {shift_id}")
        return []

    async def _get_approved_signups(self, shift_id: str) -> List[ShiftSignup]:
        """Get approved signups for a shift"""
        logger.info(f"Getting approved signups for shift: {shift_id}")
        return []

    async def _get_volunteer_signups(self, volunteer_id: str) -> List[ShiftSignup]:
        """Get all signups for a volunteer"""
        logger.info(f"Getting signups for volunteer: {volunteer_id}")
        return []

    async def _get_upcoming_shifts(self, reminder_time: datetime, hours_before: int) -> List[Shift]:
        """Get shifts that need reminders"""
        logger.info(f"Getting upcoming shifts for reminders")
        return []

# Singleton instance
shift_service = ShiftService()