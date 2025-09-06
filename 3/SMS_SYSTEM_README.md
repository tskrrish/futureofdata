# YMCA Volunteer PathFinder SMS System

A comprehensive SMS reminder and confirmation system using Twilio for the YMCA Volunteer PathFinder application.

## Features

### 🔔 SMS Reminders
- **Volunteer Opportunity Reminders**: Automated reminders for upcoming volunteer opportunities
- **Customizable Timing**: Schedule reminders at optimal times (24h, 2h before events)
- **Rich Content**: Include event details, location, contact information

### 🤝 Two-Way Confirmations
- **Interactive Confirmations**: Send confirmation requests that volunteers can respond to
- **Keyword Recognition**: YES/NO responses automatically processed
- **Status Tracking**: Track confirmation status in database

### 💬 Keyword Flows
- **Smart Keywords**: Handle common responses (YES, NO, HELP, INFO, STOP)
- **Context-Aware**: Responses adapt based on recent messages and user context
- **Automated Responses**: Immediate replies to common queries

### 📊 Analytics & Tracking
- **Message History**: Complete SMS conversation history per user
- **Analytics Dashboard**: Usage statistics, response rates, subscriber metrics
- **Error Tracking**: Monitor failed messages and delivery issues

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│   SMS Service    │────│  Twilio API     │
│   (main.py)     │    │  (sms_service.py)│    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         │                        │                       │
         ▼                        ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    Database     │    │   Webhook        │    │  SMS Gateway    │
│  (database.py)  │    │   Endpoints      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Database Schema

### SMS Messages
```sql
CREATE TABLE sms_messages (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    phone_number VARCHAR(20),
    message_content TEXT,
    sms_type VARCHAR(30), -- 'reminder', 'confirmation', 'welcome', etc.
    direction VARCHAR(10), -- 'inbound', 'outbound'
    status VARCHAR(20),    -- 'sent', 'received', 'failed', 'delivered'
    twilio_sid VARCHAR(100),
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### SMS Reminders
```sql
CREATE TABLE sms_reminders (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    phone_number VARCHAR(20),
    reminder_type VARCHAR(30),
    opportunity_data JSONB,
    scheduled_for TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'scheduled'
);
```

### SMS Preferences
```sql
CREATE TABLE sms_preferences (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    phone_number VARCHAR(20),
    is_subscribed BOOLEAN DEFAULT TRUE,
    preferences JSONB,
    unsubscribed_at TIMESTAMP WITH TIME ZONE
);
```

## Setup Instructions

### 1. Twilio Account Setup
1. Create a [Twilio account](https://www.twilio.com/)
2. Get a phone number with SMS capabilities
3. Note your Account SID and Auth Token

### 2. Environment Configuration
Add to your `.env` file or environment variables:

```bash
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
SMS_WEBHOOK_URL=https://yourdomain.com/webhooks/sms
```

### 3. Webhook Configuration
In your Twilio Console:
1. Go to Phone Numbers → Manage → Active Numbers
2. Click on your SMS-enabled phone number
3. Set the webhook URL for incoming messages:
   ```
   https://yourdomain.com/webhooks/sms
   ```
4. Set HTTP method to POST

### 4. Database Setup
Run the database initialization to create SMS tables:

```python
from database import VolunteerDatabase
import asyncio

async def setup():
    db = VolunteerDatabase()
    await db.initialize_tables()

asyncio.run(setup())
```

## API Endpoints

### Send SMS
```http
POST /api/sms/send
Content-Type: application/json

{
    "phone": "+1234567890",
    "message": "Your message here",
    "user_id": "user-uuid",
    "sms_type": "reminder"
}
```

### Send Reminder
```http
POST /api/sms/reminder
Content-Type: application/json

{
    "user_id": "user-uuid",
    "phone": "+1234567890",
    "opportunity": {
        "project_name": "Youth Basketball Coaching",
        "branch": "Blue Ash",
        "date": "Saturday, Sept 14",
        "time": "9:00 AM - 12:00 PM"
    }
}
```

### Send Confirmation Request
```http
POST /api/sms/confirmation
Content-Type: application/json

{
    "user_id": "user-uuid",
    "phone": "+1234567890",
    "event_details": {
        "name": "Community Garden Cleanup",
        "date": "Sunday, Sept 22 at 10:00 AM",
        "location": "M.E. Lyons YMCA"
    }
}
```

### Webhook Endpoint (Twilio → Your App)
```http
POST /webhooks/sms
Content-Type: application/x-www-form-urlencoded

MessageSid=SM123...
From=%2B1234567890
To=%2B0987654321
Body=YES
```

### Get SMS Analytics
```http
GET /api/sms/analytics?days=30
```

Response:
```json
{
    "period_days": 30,
    "messages_sent": 145,
    "messages_received": 67,
    "reminders_sent": 89,
    "active_subscribers": 234,
    "generated_at": "2025-09-06T20:30:00Z"
}
```

### Get SMS History
```http
GET /api/sms/history/{user_id}?limit=50
```

### SMS Preferences
```http
GET /api/sms/preferences/{user_id}
POST /api/sms/preferences/{user_id}
```

## Usage Examples

### Basic SMS Service Usage
```python
from sms_service import SMSService, SMSType

sms_service = SMSService()

# Send welcome message
result = await sms_service.send_welcome_message(
    user_id="user-123",
    phone="+1234567890",
    user_name="Sarah Johnson"
)

# Send reminder
opportunity = {
    "project_name": "Youth Basketball Coaching",
    "branch": "Blue Ash", 
    "date": "Saturday, Sept 14",
    "time": "9:00 AM - 12:00 PM"
}

result = await sms_service.send_volunteer_reminder(
    user_id="user-123",
    phone="+1234567890",
    volunteer_opportunity=opportunity
)
```

### Processing Incoming Messages
```python
# This happens automatically via webhook, but you can test manually:
result = await sms_service.process_incoming_sms(
    from_phone="+1234567890",
    message_body="YES",
    twilio_sid="SM123456789"
)

print(f"Action taken: {result['action_taken']}")
print(f"Response sent: {result['response_sent']}")
```

## Supported Keywords

Users can text these keywords to interact with the system:

- **YES** / **Y** / **CONFIRM** - Confirm availability or interest
- **NO** / **N** / **DECLINE** - Decline opportunity or cancel
- **HELP** - Get help and available commands
- **INFO** - Get information about volunteer opportunities
- **STOP** / **UNSUBSCRIBE** - Opt out of SMS messages
- **START** / **SUBSCRIBE** - Opt back in to SMS messages

## Message Types

### 1. Welcome Messages
Sent to new volunteers when they sign up:
```
🎉 Welcome to YMCA Volunteering!

Hi Sarah! Welcome to the YMCA volunteer community.

We're excited to have you join us in strengthening our community through volunteer service.

🤖 SMS Features:
• Volunteer opportunity reminders  
• Quick confirmations (YES/NO)
• Event updates and info

Reply HELP anytime for assistance!
```

### 2. Reminders
Sent before volunteer opportunities:
```
🏃‍♂️ YMCA Volunteer Reminder

Hi! Don't forget about your volunteer opportunity:

📋 Youth Basketball Coaching
🏢 Blue Ash YMCA
📅 Saturday, September 14 at 9:00 AM - 12:00 PM

Reply YES to confirm or NO to cancel.
Reply HELP for more info.

Thank you for volunteering! 💪
```

### 3. Confirmation Requests
Sent to gauge interest in new opportunities:
```
🤔 YMCA Volunteer Confirmation

We have a great opportunity for you:

📋 Community Garden Cleanup
📅 Sunday, September 22 at 10:00 AM  
📍 M.E. Lyons YMCA

Are you interested and available?

Reply YES to confirm your interest
Reply NO if you can't make it
Reply INFO for more details

We'd love to have you volunteer with us! 🌟
```

## Error Handling

The system includes comprehensive error handling:

- **Invalid Phone Numbers**: Validated and cleaned before sending
- **Twilio Errors**: API errors logged and user notified via alternative methods
- **Database Failures**: Graceful degradation, SMS still sent even if logging fails
- **Webhook Issues**: Retry logic and error notifications

## Testing

Run the example script to test all functionality:

```bash
# Full demo
python sms_example.py

# API endpoint testing only  
python sms_example.py test-api
```

## Monitoring

### Key Metrics to Monitor
- SMS delivery rates
- Response rates to confirmations
- Keyword usage patterns
- Error rates and types
- Subscriber growth/churn

### Database Queries for Analytics
```sql
-- Message volume by day
SELECT DATE(created_at), COUNT(*), sms_type
FROM sms_messages 
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), sms_type
ORDER BY DATE(created_at) DESC;

-- Response rates
SELECT 
    COUNT(CASE WHEN direction = 'outbound' AND sms_type = 'confirmation' THEN 1 END) as confirmations_sent,
    COUNT(CASE WHEN direction = 'inbound' AND message_content ILIKE '%yes%' THEN 1 END) as yes_responses
FROM sms_messages 
WHERE created_at >= NOW() - INTERVAL '7 days';

-- Active subscribers
SELECT COUNT(*) FROM sms_preferences WHERE is_subscribed = true;
```

## Security Considerations

### Phone Number Privacy
- Phone numbers are stored securely and encrypted in transit
- Access logs maintained for compliance
- Automatic cleanup of old message content

### Webhook Security
- Validate Twilio signatures on webhook requests
- Rate limiting on webhook endpoints
- Input validation on all incoming data

### Compliance
- **TCPA Compliance**: Clear opt-in/opt-out mechanisms
- **Data Retention**: Configurable retention policies for message history
- **Audit Trail**: Complete logging of all SMS interactions

## Troubleshooting

### Common Issues

**SMS Not Sending**
- Check Twilio credentials in environment variables
- Verify phone number format (+1xxxxxxxxxx)
- Check Twilio account balance and phone number status

**Webhook Not Working**
- Ensure webhook URL is publicly accessible (use ngrok for local testing)
- Check webhook URL configuration in Twilio console
- Verify SSL certificate if using HTTPS

**Database Connection Issues**
- Verify Supabase credentials
- Check database table creation
- Review network connectivity

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
- **Rich Media**: Image and document attachments
- **Scheduling UI**: Admin interface for scheduling campaigns
- **Templates**: Message template management system
- **Internationalization**: Multi-language support
- **Advanced Analytics**: Response time analysis, engagement metrics

### Integration Opportunities
- **Calendar Integration**: Google Calendar, Outlook sync
- **CRM Integration**: Salesforce, HubSpot connections
- **Email Backup**: SMS + Email for critical messages
- **Push Notifications**: Mobile app notifications as backup

## Support

For technical support or feature requests:
1. Check the logs for error messages
2. Review Twilio console for delivery status
3. Test with the included example script
4. Consult the API documentation at `/docs` endpoint

Remember to test thoroughly with small groups before rolling out to all volunteers!