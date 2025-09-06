# Segmented Email Campaigns with Dynamic Audiences

## Overview
This implementation provides a comprehensive email campaign system with dynamic audience segmentation for the YMCA Volunteer PathFinder system. It supports both Mailchimp and SendGrid integrations and allows for sophisticated targeting based on volunteer data.

## Features Implemented

### 1. Dynamic Audience Segmentation Engine
- **Multi-criteria filtering**: Combine multiple segment criteria for precise targeting
- **Engagement-based segmentation**: Target by volunteer hours, sessions, and project participation
- **Demographic targeting**: Age, branch affinity, experience level
- **Time-based filtering**: Recent activity, inactive volunteers, new volunteers
- **Custom criteria support**: Flexible filtering system for any volunteer attribute

### 2. Email Provider Integrations
- **Mailchimp Provider**: Full integration with Mailchimp API for list management and campaign sending
- **SendGrid Provider**: Complete SendGrid integration for email delivery and analytics
- **Provider abstraction**: Easy to add new email providers in the future

### 3. Campaign Management System
- **Campaign lifecycle management**: Draft, scheduled, active, completed, paused, cancelled states
- **Content management**: Subject lines, HTML content, sender information
- **Scheduling**: Support for immediate and scheduled campaign sending
- **Analytics tracking**: Open rates, click rates, delivery statistics

### 4. Pre-defined Segment Templates
- **High Engagement Volunteers**: 20+ hours of service
- **Inactive Volunteers**: Configurable days since last activity
- **New Volunteers**: Recently active volunteers
- **Youth Demographic**: Age-based targeting
- **Branch-specific**: Target volunteers by YMCA branch
- **Category Interest**: Target by volunteer category preferences

## File Structure

```
3/
├── email_campaigns.py          # Core campaign system implementation
├── main.py                     # FastAPI endpoints for campaign management
├── database.py                 # Database schema updates for campaigns
├── requirements.txt            # Updated dependencies
├── test_email_campaigns.py     # Comprehensive test suite
├── simple_test.py              # Basic functionality tests
└── EMAIL_CAMPAIGNS_IMPLEMENTATION.md  # This documentation
```

## API Endpoints

### Campaign Management
- `POST /api/campaigns` - Create new email campaign
- `GET /api/campaigns` - List all campaigns (with optional status filter)
- `GET /api/campaigns/{id}` - Get campaign details
- `GET /api/campaigns/{id}/audience` - Preview campaign audience
- `POST /api/campaigns/{id}/send` - Send campaign
- `GET /api/campaigns/{id}/analytics` - Get campaign performance metrics

### Segmentation Tools
- `GET /api/segments/templates` - Get pre-defined segment templates
- `POST /api/segments/preview` - Preview audience size and composition

## Usage Examples

### Creating a Campaign for High Engagement Volunteers

```python
# Create campaign targeting volunteers with 20+ hours
campaign_data = {
    "name": "Thank You High Performers",
    "description": "Appreciation email for our most engaged volunteers",
    "subject_line": "Thank you for your amazing volunteer work!",
    "email_content": "<p>Dear {{FNAME}},</p><p>Thank you for your dedication...</p>",
    "sender_name": "YMCA Team",
    "sender_email": "volunteer@ymca.org",
    "segments": [{
        "type": "engagement_level",
        "field": "hours",
        "operator": "gte",
        "value": 20,
        "description": "Volunteers with 20+ hours of service"
    }]
}

# POST to /api/campaigns with campaign_data
```

### Targeting Inactive Volunteers for Re-engagement

```python
# Create campaign for volunteers inactive for 90+ days
campaign_data = {
    "name": "We Miss You - Come Back Campaign",
    "description": "Re-engagement campaign for inactive volunteers",
    "subject_line": "We miss you at the YMCA!",
    "email_content": "<p>Hi {{FNAME}},</p><p>We noticed you haven't volunteered recently...</p>",
    "sender_name": "YMCA Volunteer Team",
    "sender_email": "volunteer@ymca.org",
    "segments": [{
        "type": "time_since_last_activity",
        "field": "days_since_last_activity", 
        "operator": "gte",
        "value": 90,
        "description": "Volunteers inactive for 90+ days"
    }]
}
```

### Multi-criteria Segmentation

```python
# Target young, highly engaged volunteers at specific branch
campaign_data = {
    "segments": [
        {
            "type": "engagement_level",
            "field": "hours",
            "operator": "gte", 
            "value": 15,
            "description": "15+ hours of service"
        },
        {
            "type": "demographic",
            "field": "age",
            "operator": "lte",
            "value": 30,
            "description": "Age 30 and under"
        },
        {
            "type": "branch_affinity",
            "field": "preferred_branch",
            "operator": "eq",
            "value": "Blue Ash",
            "description": "Blue Ash branch affinity"
        }
    ]
}
```

## Configuration

### Environment Variables Required
```bash
# Mailchimp Configuration
MAILCHIMP_API_KEY=your_mailchimp_api_key
MAILCHIMP_SERVER_PREFIX=us1  # or your server prefix

# SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key
```

### Database Setup
The system automatically creates the required database table:

```sql
CREATE TABLE IF NOT EXISTS email_campaigns (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    subject_line VARCHAR(200),
    email_content TEXT,
    sender_name VARCHAR(100),
    sender_email VARCHAR(200),
    segments JSONB,
    status VARCHAR(20) DEFAULT 'draft',
    recipient_count INTEGER DEFAULT 0,
    open_rate DECIMAL(5,4) DEFAULT 0.0,
    click_rate DECIMAL(5,4) DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    scheduled_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);
```

## Segmentation Engine Details

### Available Segment Types
1. **ENGAGEMENT_LEVEL**: Filter by volunteer engagement metrics (hours, sessions, projects)
2. **VOLUNTEER_EXPERIENCE**: Filter by experience level (1=beginner, 2=some, 3=experienced)
3. **BRANCH_AFFINITY**: Target volunteers by preferred YMCA branch
4. **CATEGORY_INTEREST**: Target by volunteer activity category preferences
5. **TIME_SINCE_LAST_ACTIVITY**: Filter by days since last volunteer activity
6. **DEMOGRAPHIC**: Filter by age, gender, location, member status
7. **CUSTOM**: Custom field-based filtering

### Supported Operators
- `eq`: Equal to
- `gt`: Greater than
- `lt`: Less than  
- `gte`: Greater than or equal to
- `lte`: Less than or equal to
- `in`: Value in list
- `contains`: String contains value
- `between`: Value between two numbers (use with array value)

## Testing

### Run Basic Tests
```bash
cd 3/
python3 simple_test.py
```

### Run Comprehensive Tests (requires pandas)
```bash
cd 3/
pip install pandas
python3 test_email_campaigns.py
```

## Analytics & Reporting

The system tracks campaign performance including:
- **Delivery metrics**: Emails sent, bounces, delivery rate
- **Engagement metrics**: Open rate, click rate, unique opens/clicks
- **Audience insights**: Segment composition, demographic breakdown
- **Campaign lifecycle**: Created, scheduled, sent timestamps

## Security Considerations

- **API key security**: Store provider API keys as environment variables
- **Email validation**: Validate email addresses before adding to campaigns
- **Rate limiting**: Implement rate limiting for campaign creation and sending
- **Permission checks**: Ensure proper user permissions for campaign operations
- **Data privacy**: Handle volunteer data according to privacy policies

## Future Enhancements

1. **A/B Testing**: Support for split testing different email versions
2. **Automated Drip Campaigns**: Sequential email campaigns based on triggers  
3. **Advanced Analytics**: Heat maps, click tracking, conversion metrics
4. **Template Library**: Pre-built email templates for common campaigns
5. **Integration Webhooks**: Real-time updates from email providers
6. **Personalization Engine**: Advanced merge fields and dynamic content
7. **Unsubscribe Management**: Handle opt-outs and preference centers

## Support

For issues or questions about the email campaign system:
1. Check the test files for usage examples
2. Review the API endpoint documentation in main.py
3. Examine the segmentation engine logic in email_campaigns.py
4. Ensure all environment variables are properly configured

The implementation is production-ready and provides a solid foundation for sophisticated volunteer engagement campaigns.