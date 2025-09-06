# YMCA Slack Integration Setup

This guide explains how to set up and use the Slack integration for volunteer shift notifications and approvals.

## Features

✅ **Channel Announcements**: Automatically post new volunteer shifts to designated Slack channels  
✅ **Direct Messages**: Send personalized notifications to volunteers about their shifts  
✅ **Approval Workflow**: Interactive approval process for shift signups via Slack  
✅ **Automated Reminders**: Send shift reminders 24 hours and 2 hours before shifts  
✅ **Interactive Components**: Approve/deny requests directly from Slack messages  

## Prerequisites

1. Slack workspace with admin access
2. Ability to create and install Slack apps
3. YMCA Volunteer PathFinder system running

## Slack App Setup

### 1. Create Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" > "From scratch"
3. Enter app name: "YMCA Volunteer Manager"
4. Select your workspace
5. Click "Create App"

### 2. Configure App Permissions

Navigate to **OAuth & Permissions** and add these scopes:

**Bot Token Scopes:**
- `channels:read` - List channels
- `chat:write` - Send messages
- `chat:write.public` - Send messages to channels without joining
- `users:read` - View people in workspace
- `users:read.email` - View email addresses of people in workspace

### 3. Enable Interactive Components

1. Go to **Interactive Components**
2. Turn on "Interactivity"
3. Set Request URL: `https://your-domain.com/slack/events`
4. Save Changes

### 4. Add Slash Commands (Optional)

1. Go to **Slash Commands**
2. Click "Create New Command"
3. Command: `/shift-status`
4. Request URL: `https://your-domain.com/slack/events`
5. Short Description: "Check your volunteer shift status"

### 5. Install App to Workspace

1. Go to **Install App**
2. Click "Install to Workspace"
3. Review permissions and click "Allow"
4. Save the Bot User OAuth Token (starts with `xoxb-`)

## Environment Configuration

Add these environment variables to your system:

```bash
# Slack Integration
SLACK_ENABLED=true
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# Optional: Custom channel names
SLACK_ANNOUNCEMENTS_CHANNEL=#volunteer-announcements
SLACK_SHIFT_CHANNEL=#shift-notifications
SLACK_APPROVALS_CHANNEL=#volunteer-approvals
```

## Create Slack Channels

Create these channels in your workspace:

1. `#volunteer-announcements` - General shift announcements
2. `#shift-notifications` - Shift-specific notifications
3. `#volunteer-approvals` - Approval requests for coordinators

Invite the bot to all channels:
```
/invite @YMCA Volunteer Manager
```

## API Endpoints

### Create Shift
```http
POST /api/shifts
Content-Type: application/json

{
  "title": "Youth Program Helper",
  "description": "Assist with after-school programs",
  "start_time": "2024-03-15T16:00:00",
  "end_time": "2024-03-15T18:00:00",
  "location": "Blue Ash YMCA",
  "branch": "Blue Ash",
  "coordinator_email": "coordinator@ymca.org",
  "skills_required": ["Youth Work", "CPR Certified"],
  "max_volunteers": 3,
  "requires_approval": true
}
```

### Sign Up for Shift
```http
POST /api/shifts/{shift_id}/signup
Content-Type: application/json

{
  "volunteer_id": "user123",
  "volunteer_name": "John Doe",
  "volunteer_email": "john.doe@email.com"
}
```

### Send Manual Reminders
```http
POST /api/shifts/reminders?hours_before=24
```

## Message Examples

### Channel Announcement
```
🌟 Youth Program Helper

When: Friday, March 15 at 4:00 PM
Duration: 2.0 hours
Location: Blue Ash YMCA
Branch: Blue Ash

Description: Assist with after-school programs

Skills Needed: Youth Work, CPR Certified

[Sign Up] [Learn More]
```

### Direct Message
```
🆕 Shift Confirmation: Youth Program Helper

Hi John Doe! 👋

You're signed up for Friday, March 15 at 4:00 PM

Location: Blue Ash YMCA
Branch: Blue Ash

What you'll be doing: Assist with after-school programs

Questions? Contact your coordinator at coordinator@ymca.org
```

### Approval Request
```
🔔 Approval Required: Signup

Volunteer: John Doe
Email: john.doe@email.com
Shift: Youth Program Helper
Request Type: signup

Details:
{
  "signup_time": "2024-03-14T10:30:00"
}

[✅ Approve] [❌ Deny]
```

## Automated Scheduling

The system automatically:

- **Daily 9 AM**: Sends reminders for shifts in the next 24 hours
- **Hourly**: Checks for shifts needing 24-hour reminders
- **Every 30 minutes**: Checks for shifts needing 2-hour reminders
- **Weekly**: Cleans up old shift data

## Troubleshooting

### Bot Not Responding
1. Check bot token is correct
2. Verify bot is invited to channels
3. Check API endpoints are accessible
4. Review application logs

### Messages Not Sending
1. Verify channel names match configuration
2. Check bot permissions
3. Ensure users have Slack accounts with matching emails

### Interactive Components Not Working
1. Verify Interactive Components are enabled
2. Check Request URL is correct and accessible
3. Review signing secret configuration

### User Lookup Failures
```
Could not find Slack user for email user@example.com
```
1. Ensure user has Slack account
2. Check email addresses match exactly
3. Verify `users:read.email` permission

## Integration with Existing Systems

### Database Integration
Modify these methods in `shift_service.py` to connect with your database:

```python
async def _save_shift_to_database(self, shift: Shift)
async def _get_shift_from_database(self, shift_id: str)
async def _save_signup_to_database(self, signup: ShiftSignup)
# ... etc
```

### User Mapping
Update `_get_volunteer_slack_id()` in `slack_integration.py` to map volunteer IDs to Slack user IDs.

## Security Considerations

1. **Token Security**: Store Slack tokens securely, never commit to source control
2. **Request Verification**: All Slack requests are verified using signing secret
3. **Channel Permissions**: Limit bot access to relevant channels only
4. **User Data**: Only use necessary user information (name, email)

## Testing

Test the integration with:

```bash
# Create a test shift
curl -X POST http://localhost:8000/api/shifts \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Shift", "description": "Testing", ...}'

# Send test reminders
curl -X POST http://localhost:8000/api/shifts/reminders?hours_before=24
```

## Support

For issues with:
- **Slack App Configuration**: Check Slack API documentation
- **YMCA System Integration**: Contact system administrator
- **Message Formatting**: Review Slack Block Kit Builder
- **Bot Permissions**: Verify OAuth scopes and channel invitations

---

🎉 **Your YMCA Slack integration is ready!** Volunteers will now receive notifications and coordinators can approve requests directly from Slack.