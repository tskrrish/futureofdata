# Auto-Draft Personalized Emails/SMS Feature

## Overview

This feature adds comprehensive AI-powered email and SMS auto-drafting capabilities to the YMCA Volunteer PathFinder system. It generates personalized outreach messages with contextual tone based on volunteer profiles, engagement history, and communication preferences.

## Implementation Files

### Core Modules

1. **`email_sms_drafting.py`** - Main drafting engine
   - `EmailSMSDraftingEngine` class for AI-powered message generation
   - Enum definitions for message types, tones, and purposes
   - Personalization context data structures
   - Template fallback system

2. **`contextual_tone_analyzer.py`** - Tone analysis engine
   - `ContextualToneAnalyzer` class for smart tone recommendations
   - Engagement pattern analysis
   - Communication style detection
   - Risk factor identification

3. **`message_templates.py`** - Template system
   - `MessageTemplateEngine` class with pre-built templates
   - Variable substitution logic
   - Template recommendation system
   - Personalization functions

4. **`main.py`** - Updated with new API endpoints
   - 5 new REST API endpoints
   - Integration with existing volunteer data
   - Request/response models

### Test Files

- **`test_core_features.py`** - Comprehensive feature testing
- **`simple_test.py`** - Basic module structure validation

## API Endpoints

### POST `/api/draft-message`
Generate a personalized email or SMS message.

**Request:**
```json
{
  "contact_id": "12345",
  "name": "John Smith",
  "purpose": "welcome_new",
  "message_type": "email",
  "tone": "welcoming",
  "urgency_level": 1,
  "custom_instructions": "Mention their interest in youth programs",
  "template_id": "welcome_new_email_welcoming"
}
```

**Response:**
```json
{
  "success": true,
  "message": {
    "subject": "Welcome to YMCA Volunteering John!",
    "content": "Hi John,\n\nWelcome to the YMCA volunteer community...",
    "message_type": "email",
    "tone": "welcoming",
    "character_count": 285,
    "personalization_score": 0.85,
    "estimated_engagement": 0.78
  },
  "context_used": {
    "has_name": true,
    "has_volunteer_history": false,
    "engagement_level": "new"
  },
  "optimal_send_time": {
    "optimal_hours": [9, 10, 14, 15],
    "optimal_days": ["Tuesday", "Wednesday", "Thursday"]
  }
}
```

### POST `/api/analyze-tone`
Analyze optimal tone for a message based on user context.

### POST `/api/draft-variants`
Generate multiple message variants for A/B testing.

### GET `/api/templates`
List available message templates with filtering options.

### POST `/api/render-template`
Render a specific template with personalization.

## Key Features

### 1. AI-Powered Personalization
- Integrates with existing AI assistant using Llama 3.2 model
- Contextual message generation based on volunteer profiles
- Smart fallback to template-based generation

### 2. Contextual Tone Analysis
- Analyzes engagement patterns (highly engaged, declining, dormant, etc.)
- Determines communication style preferences
- Assesses responsiveness levels
- Provides confidence scores and reasoning

### 3. Template System
- Pre-built templates for common scenarios:
  - Welcome new volunteers
  - Volunteer opportunity matching
  - Event invitations
  - Appreciation messages
  - Re-engagement campaigns
  - Follow-up inquiries
- Variable substitution with personalization
- Template recommendation engine

### 4. Smart Personalization
Uses existing YMCA volunteer data:
- Volunteer history and hours
- Branch membership
- Program preferences
- Age-appropriate messaging
- Past interaction patterns

### 5. Multi-Variant Generation
- A/B testing support with multiple message variants
- Different tones for same content
- Engagement prediction scoring
- Testing recommendations

### 6. Optimal Send Time Recommendations
- Time-of-day recommendations based on demographics
- Day-of-week optimization
- Age-specific preferences
- Message type considerations

## Message Types & Tones

### Message Types
- **Email** - Full-featured messages with subjects
- **SMS** - Concise messages under 160 characters

### Available Tones
- **Welcoming** - Warm, inclusive, community-focused
- **Encouraging** - Motivational, empowering, positive
- **Informative** - Clear, factual, professional
- **Urgent** - Time-sensitive, compelling, action-focused
- **Appreciation** - Grateful, recognizing, heartfelt
- **Follow-up** - Caring, supportive, helpful
- **Personalized** - Tailored to individual history and interests

### Outreach Purposes
- **Welcome New** - New volunteer onboarding
- **Volunteer Match** - Opportunity recommendations
- **Event Invitation** - Program and event invitations
- **Follow-up Inquiry** - Checking in on interests
- **Appreciation** - Recognizing contributions
- **Re-engagement** - Bringing back inactive volunteers
- **Reminder** - Process or deadline reminders
- **Update** - Program or policy updates

## Integration Points

### Existing YMCA Data
- Volunteer profiles from Excel dataset
- Historical interaction data
- Branch information and preferences
- Program participation history

### AI Assistant Integration
- Uses existing `VolunteerAIAssistant` class
- Leverages Llama 3.2 model inference
- Maintains conversation context
- Provides fallback responses

### Database Integration
- Links with existing Supabase database
- Tracks message generation analytics
- Stores template usage statistics
- Maintains interaction history

## Usage Examples

### 1. Welcome New Volunteer
```python
person_context = PersonalizationContext(
    name="Sarah Johnson",
    age=28,
    is_ymca_member=True,
    member_branch="Blue Ash YMCA"
)

message_context = MessageContext(
    purpose=OutreachPurpose.WELCOME_NEW,
    tone=MessageTone.WELCOMING,
    message_type=MessageType.EMAIL
)

drafted_message = await drafting_engine.draft_message(
    person_context=person_context,
    message_context=message_context
)
```

### 2. Appreciation Message for Champion Volunteer
```python
person_context = PersonalizationContext(
    name="Robert Chen",
    engagement_level="champion",
    volunteer_history={'total_hours': 150, 'sessions': 45}
)

message_context = MessageContext(
    purpose=OutreachPurpose.APPRECIATION,
    tone=MessageTone.APPRECIATION,
    message_type=MessageType.EMAIL
)
```

### 3. Re-engagement SMS
```python
message_context = MessageContext(
    purpose=OutreachPurpose.RE_ENGAGEMENT,
    tone=MessageTone.ENCOURAGING,
    message_type=MessageType.SMS
)
```

## Quality Metrics

Each generated message includes:
- **Personalization Score** (0-1) - How well personalized the message is
- **Estimated Engagement** (0-1) - Predicted likelihood of response
- **Character Count** - Message length tracking
- **Context Usage** - What data was used for personalization

## Testing Results

✅ All core features tested and working:
- Enum system for message classification
- Personalization context handling
- Template variable substitution
- Tone recommendation logic
- Message length optimization
- API request/response structures

## Future Enhancements

Potential improvements:
1. Machine learning model training on response data
2. Seasonal messaging adjustments
3. Integration with email/SMS delivery systems
4. Advanced A/B testing analytics
5. Multi-language support
6. Rich text formatting for emails
7. Dynamic image insertion
8. Social media message generation

## Dependencies

- Existing YMCA Volunteer PathFinder system
- FastAPI web framework
- AI assistant with Llama 3.2 integration
- Supabase database
- Python 3.8+ with typing support

## Security Considerations

- No sensitive data stored in message templates
- Personal information properly masked in logs
- API rate limiting should be implemented
- Message content validation prevents injection attacks
- Compliance with communication privacy regulations