"""
SMS Service for Volunteer PathFinder using Twilio
Handles reminders, two-way confirmations, and keyword flows
"""
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from config import settings
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import json
import asyncio
from database import VolunteerDatabase
from enum import Enum

logger = logging.getLogger(__name__)

class SMSType(Enum):
    REMINDER = "reminder"
    CONFIRMATION = "confirmation"
    WELCOME = "welcome"
    FOLLOW_UP = "follow_up"
    KEYWORD_RESPONSE = "keyword_response"

class SMSKeyword(Enum):
    YES = "yes"
    NO = "no"
    STOP = "stop"
    HELP = "help"
    INFO = "info"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

class SMSService:
    def __init__(self):
        """Initialize Twilio client and database connection"""
        self.client = None
        self.database = VolunteerDatabase()
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        
        try:
            if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
                self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                logger.info("✅ Twilio SMS client initialized")
            else:
                logger.warning("⚠️  Twilio credentials not configured. SMS features will be disabled.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Twilio client: {e}")
            self.client = None
    
    def _is_available(self) -> bool:
        """Check if SMS service is available"""
        return self.client is not None and self.phone_number
    
    async def send_sms(self, to_phone: str, message: str, sms_type: SMSType = SMSType.REMINDER, 
                      user_id: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send SMS message via Twilio"""
        if not self._is_available():
            logger.warning("SMS service not available")
            return {"success": False, "error": "SMS service not configured"}
        
        try:
            # Clean phone number
            clean_phone = self._clean_phone_number(to_phone)
            if not clean_phone:
                return {"success": False, "error": "Invalid phone number"}
            
            # Send message
            message_obj = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=clean_phone
            )
            
            # Log to database
            await self.database.save_sms_message(
                user_id=user_id,
                phone_number=clean_phone,
                message_content=message,
                sms_type=sms_type.value,
                direction="outbound",
                status="sent",
                twilio_sid=message_obj.sid,
                metadata=metadata
            )
            
            logger.info(f"✅ SMS sent to {clean_phone[:8]}*** - Type: {sms_type.value}")
            
            return {
                "success": True,
                "message_sid": message_obj.sid,
                "to": clean_phone,
                "type": sms_type.value
            }
            
        except TwilioException as e:
            logger.error(f"❌ Twilio error sending SMS: {e}")
            await self.database.save_sms_message(
                user_id=user_id,
                phone_number=clean_phone if 'clean_phone' in locals() else to_phone,
                message_content=message,
                sms_type=sms_type.value,
                direction="outbound",
                status="failed",
                error_message=str(e),
                metadata=metadata
            )
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Error sending SMS: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_volunteer_reminder(self, user_id: str, phone: str, volunteer_opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Send volunteer opportunity reminder"""
        project_name = volunteer_opportunity.get("project_name", "Volunteer Opportunity")
        branch = volunteer_opportunity.get("branch", "YMCA")
        date = volunteer_opportunity.get("date", "upcoming")
        time = volunteer_opportunity.get("time", "")
        
        message = f"""🏃‍♂️ YMCA Volunteer Reminder
        
Hi! Don't forget about your volunteer opportunity:

📋 {project_name}
🏢 {branch} YMCA
📅 {date} {time}

Reply YES to confirm or NO to cancel.
Reply HELP for more info or STOP to unsubscribe.

Thank you for volunteering! 💪"""
        
        return await self.send_sms(
            to_phone=phone,
            message=message,
            sms_type=SMSType.REMINDER,
            user_id=user_id,
            metadata=volunteer_opportunity
        )
    
    async def send_confirmation_request(self, user_id: str, phone: str, event_details: Dict[str, Any]) -> Dict[str, Any]:
        """Send two-way confirmation request"""
        event_name = event_details.get("name", "Volunteer Event")
        date = event_details.get("date", "")
        location = event_details.get("location", "YMCA")
        
        message = f"""🤔 YMCA Volunteer Confirmation
        
We have a great opportunity for you:

📋 {event_name}
📅 {date}
📍 {location}

Are you interested and available?

Reply YES to confirm your interest
Reply NO if you can't make it
Reply INFO for more details

We'd love to have you volunteer with us! 🌟"""
        
        return await self.send_sms(
            to_phone=phone,
            message=message,
            sms_type=SMSType.CONFIRMATION,
            user_id=user_id,
            metadata=event_details
        )
    
    async def send_welcome_message(self, user_id: str, phone: str, user_name: str = None) -> Dict[str, Any]:
        """Send welcome message to new volunteer"""
        name = user_name or "there"
        
        message = f"""🎉 Welcome to YMCA Volunteering!
        
Hi {name}! Welcome to the YMCA volunteer community.

We're excited to have you join us in strengthening our community through volunteer service.

🤖 SMS Features:
• Volunteer opportunity reminders
• Quick confirmations (YES/NO)
• Event updates and info

📱 Keywords:
• HELP - Get assistance
• INFO - Learn more about opportunities
• STOP - Unsubscribe (we hope you don't!)

Ready to make a difference? Let's go! 💪"""
        
        return await self.send_sms(
            to_phone=phone,
            message=message,
            sms_type=SMSType.WELCOME,
            user_id=user_id,
            metadata={"welcome": True}
        )
    
    async def process_incoming_sms(self, from_phone: str, message_body: str, twilio_sid: str = None) -> Dict[str, Any]:
        """Process incoming SMS and handle keywords/responses"""
        try:
            # Clean and normalize input
            clean_phone = self._clean_phone_number(from_phone)
            message_lower = message_body.strip().lower()
            
            # Find user by phone number
            user = await self._find_user_by_phone(clean_phone)
            user_id = user.get("id") if user else None
            
            # Log incoming message
            await self.database.save_sms_message(
                user_id=user_id,
                phone_number=clean_phone,
                message_content=message_body,
                sms_type=SMSType.KEYWORD_RESPONSE.value,
                direction="inbound",
                status="received",
                twilio_sid=twilio_sid
            )
            
            # Process keywords and responses
            response_message = None
            action_taken = None
            
            if self._is_affirmative(message_lower):
                response_message, action_taken = await self._handle_yes_response(user_id, clean_phone)
            elif self._is_negative(message_lower):
                response_message, action_taken = await self._handle_no_response(user_id, clean_phone)
            elif message_lower in ["stop", "unsubscribe", "quit"]:
                response_message, action_taken = await self._handle_unsubscribe(user_id, clean_phone)
            elif message_lower in ["help", "support", "assist"]:
                response_message, action_taken = await self._handle_help_request(user_id, clean_phone)
            elif message_lower in ["info", "information", "details"]:
                response_message, action_taken = await self._handle_info_request(user_id, clean_phone)
            elif message_lower in ["subscribe", "start", "join"]:
                response_message, action_taken = await self._handle_subscribe(user_id, clean_phone)
            else:
                # Default response for unrecognized messages
                response_message = """Thank you for your message! 

I understand the following:
• YES - Confirm interest/availability
• NO - Decline or cancel
• HELP - Get assistance
• INFO - Get more information
• STOP - Unsubscribe

For complex requests, please visit our website or call your local YMCA branch."""
                action_taken = "default_response"
            
            # Send response if one was generated
            response_result = None
            if response_message:
                response_result = await self.send_sms(
                    to_phone=clean_phone,
                    message=response_message,
                    sms_type=SMSType.KEYWORD_RESPONSE,
                    user_id=user_id,
                    metadata={"triggered_by": message_body, "action": action_taken}
                )
            
            return {
                "success": True,
                "from_phone": clean_phone,
                "user_id": user_id,
                "original_message": message_body,
                "action_taken": action_taken,
                "response_sent": response_result is not None,
                "response_details": response_result
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing incoming SMS: {e}")
            return {"success": False, "error": str(e)}
    
    async def schedule_reminder(self, user_id: str, phone: str, opportunity: Dict[str, Any], 
                              send_at: datetime, reminder_type: str = "event") -> Dict[str, Any]:
        """Schedule a reminder to be sent later"""
        try:
            # Save to database
            success = await self.database.save_sms_reminder(
                user_id=user_id,
                phone_number=phone,
                reminder_type=reminder_type,
                opportunity_data=opportunity,
                scheduled_for=send_at
            )
            
            if success:
                # Track scheduled reminder
                await self.database.track_event(
                    "sms_reminder_scheduled",
                    {
                        "phone": phone,
                        "reminder_type": reminder_type,
                        "scheduled_for": send_at.isoformat()
                    },
                    user_id
                )
            
            logger.info(f"📅 Reminder scheduled for {phone[:8]}*** at {send_at}")
            
            return {
                "success": True,
                "scheduled_for": send_at.isoformat(),
                "reminder_type": reminder_type
            }
            
        except Exception as e:
            logger.error(f"❌ Error scheduling reminder: {e}")
            return {"success": False, "error": str(e)}
    
    def _clean_phone_number(self, phone: str) -> Optional[str]:
        """Clean and format phone number"""
        if not phone:
            return None
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Handle US phone numbers
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        elif digits.startswith('+'):
            return phone
        else:
            return None
    
    def _is_affirmative(self, message: str) -> bool:
        """Check if message is affirmative"""
        affirmative_words = ["yes", "y", "yeah", "yep", "sure", "ok", "okay", "confirm", "confirmed"]
        return any(word in message for word in affirmative_words)
    
    def _is_negative(self, message: str) -> bool:
        """Check if message is negative"""
        negative_words = ["no", "n", "nope", "cancel", "decline", "nah", "not interested"]
        return any(word in message for word in negative_words)
    
    async def _find_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Find user by phone number in database"""
        try:
            if not self.database._is_available():
                return None
            
            result = self.database.supabase.table('users')\
                .select('*')\
                .eq('phone', phone)\
                .execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error finding user by phone: {e}")
            return None
    
    
    async def _handle_yes_response(self, user_id: str, phone: str) -> tuple[str, str]:
        """Handle YES/confirmation responses"""
        message = """✅ Great! Thank you for confirming.

We've recorded your confirmation and will send you more details soon.

You'll receive a reminder 24 hours before the event with all the information you need.

Thank you for volunteering with the YMCA! 💪"""
        
        # Update any pending confirmations in database
        await self.database.track_event(
            "volunteer_confirmed",
            {"phone": phone, "confirmation_method": "sms"},
            user_id
        )
        
        return message, "confirmed_participation"
    
    async def _handle_no_response(self, user_id: str, phone: str) -> tuple[str, str]:
        """Handle NO/decline responses"""
        message = """👍 No problem at all!

Thank you for letting us know. We understand that schedules can be challenging.

We'll keep you in mind for future opportunities that might work better for you.

Reply INFO anytime to learn about other volunteer options."""
        
        # Log decline
        await self.database.track_event(
            "volunteer_declined",
            {"phone": phone, "decline_method": "sms"},
            user_id
        )
        
        return message, "declined_participation"
    
    async def _handle_unsubscribe(self, user_id: str, phone: str) -> tuple[str, str]:
        """Handle STOP/unsubscribe requests"""
        message = """📵 You have been unsubscribed from YMCA volunteer SMS messages.

We're sorry to see you go! If you'd like to re-subscribe in the future, text SUBSCRIBE.

You can always visit us online or call your local YMCA branch.

Thank you for your past support! 🙏"""
        
        # Update user preferences to disable SMS
        await self.database.track_event(
            "sms_unsubscribed",
            {"phone": phone},
            user_id
        )
        
        return message, "unsubscribed"
    
    async def _handle_help_request(self, user_id: str, phone: str) -> tuple[str, str]:
        """Handle HELP requests"""
        message = """🤝 YMCA Volunteer SMS Help

Here's what you can do:
• YES - Confirm availability/interest
• NO - Decline opportunity
• INFO - Get more details about opportunities
• STOP - Unsubscribe from SMS
• SUBSCRIBE - Re-enable SMS messages

📞 Need more help?
Visit: https://www.myy.org/volunteering
Call your local YMCA branch

We're here to help you make a difference! 💙"""
        
        return message, "provided_help"
    
    async def _handle_info_request(self, user_id: str, phone: str) -> tuple[str, str]:
        """Handle INFO requests"""
        message = """ℹ️ YMCA Volunteer Information

🎯 Volunteer Opportunities:
• Youth programs & camps
• Fitness & wellness support  
• Community events
• Administrative assistance
• Special programs

🕒 Time Commitments:
• One-time events (2-4 hours)
• Weekly ongoing (1-3 hours)
• Seasonal programs (flexible)

🌐 Learn More:
https://www.myy.org/volunteering

Ready to get involved? We'll match you with perfect opportunities! 🌟"""
        
        return message, "provided_info"
    
    async def _handle_subscribe(self, user_id: str, phone: str) -> tuple[str, str]:
        """Handle SUBSCRIBE requests"""
        message = """🎉 Welcome back to YMCA Volunteer SMS!

You're now subscribed to receive:
• Volunteer opportunity notifications
• Event reminders and confirmations
• Important updates

Reply HELP anytime for assistance or STOP to unsubscribe.

Ready to make a difference in your community! 💪"""
        
        # Re-enable SMS for user
        await self.database.track_event(
            "sms_subscribed",
            {"phone": phone},
            user_id
        )
        
        return message, "subscribed"

# Usage and testing functions
async def test_sms_service():
    """Test SMS service functionality"""
    sms_service = SMSService()
    
    if not sms_service._is_available():
        print("⚠️  SMS service not available - check Twilio configuration")
        return
    
    # Test phone number (replace with your test number)
    test_phone = "+1234567890"
    test_user_id = "test-user-123"
    
    # Test welcome message
    result = await sms_service.send_welcome_message(
        user_id=test_user_id,
        phone=test_phone,
        user_name="Test User"
    )
    
    if result["success"]:
        print("✅ Welcome SMS sent successfully")
    else:
        print(f"❌ Failed to send welcome SMS: {result['error']}")
    
    # Test reminder
    opportunity = {
        "project_name": "Youth Basketball Coaching",
        "branch": "Blue Ash",
        "date": "Saturday, Sept 14",
        "time": "9:00 AM - 12:00 PM"
    }
    
    result = await sms_service.send_volunteer_reminder(
        user_id=test_user_id,
        phone=test_phone,
        volunteer_opportunity=opportunity
    )
    
    if result["success"]:
        print("✅ Reminder SMS sent successfully")
    else:
        print(f"❌ Failed to send reminder SMS: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_sms_service())