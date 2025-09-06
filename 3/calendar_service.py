"""
Calendar Service for RSVP System
Handles calendar invite generation and email sending
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
import uuid
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self, smtp_host: str = "smtp.gmail.com", smtp_port: int = 587, 
                 smtp_user: str = None, smtp_password: str = None):
        """Initialize calendar service with SMTP configuration"""
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
    
    def create_ical_content(self, event_data: Dict[str, Any], rsvp_data: Dict[str, Any]) -> str:
        """Create iCal content for calendar invite"""
        
        # Generate unique UID for this event
        uid = f"{event_data['id']}@ymca-volunteer-system.com"
        
        # Format dates for iCal
        start_time = datetime.fromisoformat(event_data['event_date'].replace('Z', '+00:00'))
        
        # If no end time provided, default to 2 hours after start
        if event_data.get('end_date'):
            end_time = datetime.fromisoformat(event_data['end_date'].replace('Z', '+00:00'))
        else:
            end_time = start_time + timedelta(hours=2)
        
        # Format for iCal (UTC)
        dtstart = start_time.strftime('%Y%m%dT%H%M%SZ')
        dtend = end_time.strftime('%Y%m%dT%H%M%SZ')
        dtstamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        
        # Clean description
        description = event_data.get('description', '').replace('\n', '\\n')
        location = event_data.get('location', 'YMCA')
        
        ical_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//YMCA//Volunteer System//EN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{event_data['title']}
DESCRIPTION:{description}
LOCATION:{location}
STATUS:CONFIRMED
ORGANIZER:MAILTO:{event_data.get('contact_email', 'volunteer@ymca.org')}
ATTENDEE;RSVP=TRUE;PARTSTAT=NEEDS-ACTION:MAILTO:{rsvp_data['email']}
BEGIN:VALARM
TRIGGER:-PT24H
ACTION:EMAIL
DESCRIPTION:Reminder: {event_data['title']} tomorrow
END:VALARM
BEGIN:VALARM
TRIGGER:-PT2H
ACTION:DISPLAY
DESCRIPTION:Reminder: {event_data['title']} in 2 hours
END:VALARM
END:VEVENT
END:VCALENDAR"""
        
        return ical_content
    
    def create_email_content(self, event_data: Dict[str, Any], rsvp_data: Dict[str, Any]) -> tuple[str, str]:
        """Create HTML and plain text email content"""
        
        # Format event date for display
        event_date = datetime.fromisoformat(event_data['event_date'].replace('Z', '+00:00'))
        formatted_date = event_date.strftime('%A, %B %d, %Y at %I:%M %p')
        
        # Plain text version
        plain_text = f"""Dear {rsvp_data.get('first_name', 'Volunteer')},

Thank you for RSVPing to: {event_data['title']}

Event Details:
- Date & Time: {formatted_date}
- Location: {event_data.get('location', 'YMCA')}
- Branch: {event_data.get('branch', 'N/A')}

{event_data.get('description', '')}

We're excited to have you volunteer with us! Please see the attached calendar invite.

If you need to cancel or have questions, please contact us at {event_data.get('contact_email', 'volunteer@ymca.org')}.

Thank you for your service!
YMCA Volunteer Team
"""
        
        # HTML version
        html_content = f"""
        <html>
        <head></head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: #0066cc; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin: 0;">YMCA Volunteer Confirmation</h2>
                </div>
                
                <div style="background: #f9f9f9; padding: 20px; margin: 20px 0;">
                    <h3 style="color: #0066cc; margin-top: 0;">Thank you for volunteering!</h3>
                    <p>Dear {rsvp_data.get('first_name', 'Volunteer')},</p>
                    <p>Thank you for RSVPing to <strong>{event_data['title']}</strong>.</p>
                </div>
                
                <div style="background: white; padding: 20px; border-left: 4px solid #0066cc;">
                    <h4 style="color: #0066cc; margin-top: 0;">Event Details</h4>
                    <ul style="list-style: none; padding: 0;">
                        <li style="padding: 5px 0;"><strong>📅 Date & Time:</strong> {formatted_date}</li>
                        <li style="padding: 5px 0;"><strong>📍 Location:</strong> {event_data.get('location', 'YMCA')}</li>
                        <li style="padding: 5px 0;"><strong>🏢 Branch:</strong> {event_data.get('branch', 'N/A')}</li>
                    </ul>
                    
                    {f'<p><strong>Description:</strong><br>{event_data.get("description", "")}</p>' if event_data.get("description") else ''}
                </div>
                
                <div style="margin: 20px 0; padding: 20px; background: #e8f4fd;">
                    <p>We're excited to have you volunteer with us! Please see the attached calendar invite to add this event to your calendar.</p>
                    
                    <p>If you need to cancel or have questions, please contact us at 
                    <a href="mailto:{event_data.get('contact_email', 'volunteer@ymca.org')}" style="color: #0066cc;">
                        {event_data.get('contact_email', 'volunteer@ymca.org')}
                    </a></p>
                </div>
                
                <div style="background: #333; color: white; padding: 15px; text-align: center; margin-top: 20px;">
                    <p style="margin: 0;">Thank you for your service!</p>
                    <p style="margin: 5px 0 0 0; font-weight: bold;">YMCA Volunteer Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return plain_text, html_content
    
    async def send_calendar_invite(self, event_data: Dict[str, Any], rsvp_data: Dict[str, Any]) -> bool:
        """Send calendar invite email"""
        
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured, calendar invite not sent")
            return False
        
        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"YMCA Volunteer Event: {event_data['title']}"
            msg['From'] = self.smtp_user
            msg['To'] = rsvp_data['email']
            
            # Create email content
            plain_text, html_content = self.create_email_content(event_data, rsvp_data)
            
            # Attach text and HTML parts
            text_part = MIMEText(plain_text, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Create and attach iCal file
            ical_content = self.create_ical_content(event_data, rsvp_data)
            ical_part = MIMEBase('text', 'calendar')
            ical_part.set_payload(ical_content)
            encoders.encode_base64(ical_part)
            ical_part.add_header('Content-Disposition', 'attachment', filename='invite.ics')
            ical_part.add_header('Content-Type', 'text/calendar', method='REQUEST')
            
            msg.attach(ical_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Calendar invite sent to {rsvp_data['email']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending calendar invite: {e}")
            return False
    
    async def send_reminder_email(self, event_data: Dict[str, Any], rsvp_data: Dict[str, Any], 
                                reminder_type: str = "24h") -> bool:
        """Send reminder email for upcoming event"""
        
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured, reminder not sent")
            return False
        
        try:
            # Determine reminder timing
            reminder_messages = {
                "24h": "Don't forget about your volunteer event tomorrow!",
                "2h": "Your volunteer event is starting in 2 hours!",
                "1h": "Your volunteer event is starting in 1 hour!"
            }
            
            reminder_msg = reminder_messages.get(reminder_type, "Reminder about your volunteer event")
            
            # Format event date
            event_date = datetime.fromisoformat(event_data['event_date'].replace('Z', '+00:00'))
            formatted_date = event_date.strftime('%A, %B %d, %Y at %I:%M %p')
            
            # Create reminder email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Reminder: {event_data['title']}"
            msg['From'] = self.smtp_user
            msg['To'] = rsvp_data['email']
            
            # Plain text version
            plain_text = f"""Dear {rsvp_data.get('first_name', 'Volunteer')},

{reminder_msg}

Event: {event_data['title']}
Date & Time: {formatted_date}
Location: {event_data.get('location', 'YMCA')}

We look forward to seeing you there!

YMCA Volunteer Team
"""
            
            # HTML version
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: #ff9900; color: white; padding: 20px; text-align: center;">
                        <h2 style="margin: 0;">Volunteer Reminder</h2>
                    </div>
                    
                    <div style="padding: 20px;">
                        <p>Dear {rsvp_data.get('first_name', 'Volunteer')},</p>
                        <p><strong>{reminder_msg}</strong></p>
                        
                        <div style="background: #f9f9f9; padding: 15px; margin: 15px 0;">
                            <p><strong>Event:</strong> {event_data['title']}</p>
                            <p><strong>Date & Time:</strong> {formatted_date}</p>
                            <p><strong>Location:</strong> {event_data.get('location', 'YMCA')}</p>
                        </div>
                        
                        <p>We look forward to seeing you there!</p>
                        <p>YMCA Volunteer Team</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_part = MIMEText(plain_text, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send reminder
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Reminder sent to {rsvp_data['email']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending reminder: {e}")
            return False

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_calendar_service():
        calendar_service = CalendarService()
        
        # Test event data
        event_data = {
            'id': 'test-event-123',
            'title': 'Community Garden Volunteer Day',
            'description': 'Help us plant flowers and vegetables in our community garden.',
            'event_date': '2025-09-15T09:00:00Z',
            'end_date': '2025-09-15T12:00:00Z',
            'location': 'YMCA Blue Ash Community Garden',
            'branch': 'Blue Ash YMCA',
            'contact_email': 'volunteer@ymca.org'
        }
        
        rsvp_data = {
            'email': 'volunteer@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        # Generate iCal content
        ical_content = calendar_service.create_ical_content(event_data, rsvp_data)
        print("Generated iCal content:")
        print(ical_content[:500] + "...")
        
        # Generate email content
        plain_text, html_content = calendar_service.create_email_content(event_data, rsvp_data)
        print("\nGenerated email content (first 300 chars):")
        print(plain_text[:300] + "...")
    
    # Run test
    asyncio.run(test_calendar_service())