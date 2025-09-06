# 📧 Message Templates Feature

The YMCA Volunteer PathFinder now includes a comprehensive message templates system with merge fields for reusable communications.

## Features

### 🎯 Core Functionality
- **Template Management**: Create, edit, delete, and organize message templates
- **Merge Fields**: Dynamic content replacement using `{{field.name}}` syntax
- **Categories**: Organize templates by purpose (welcome, follow-up, reminder, thank_you, general)
- **Usage Tracking**: Monitor template usage and effectiveness
- **AI Integration**: Get AI assistance for creating and optimizing templates

### 📊 Database Schema
The system includes two new database tables:
- `message_templates`: Store template definitions with merge fields
- `template_usage`: Track when and how templates are used

## Usage

### 🌐 Web Interface
Access the template manager at: `http://localhost:8000/templates`

Features:
- Create new templates with rich text editor
- Browse existing templates by category
- Preview templates with sample data
- Edit and delete templates
- Search and filter capabilities

### 🔧 API Endpoints

#### Basic CRUD Operations
- `GET /api/templates` - List all templates
- `POST /api/templates` - Create new template
- `GET /api/templates/{id}` - Get specific template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template (soft delete)

#### Template Operations
- `POST /api/templates/render` - Render template with merge data
- `GET /api/templates/{id}/usage` - Get usage statistics
- `GET /api/templates/categories` - Get available categories
- `GET /api/merge-fields` - Get available merge fields

#### AI-Powered Features
- `POST /api/templates/ai/suggest` - Get AI template suggestions
- `POST /api/templates/ai/create` - AI-assisted template creation
- `POST /api/templates/ai/optimize` - AI content optimization

## 🏗️ Setup Instructions

### 1. Database Setup
Run the SQL commands from `database.py` in your Supabase dashboard to create the required tables.

### 2. Seed Default Templates
```bash
cd /path/to/project
python3 seed_templates.py
```

This creates 6 default templates covering common volunteer communication scenarios.

### 3. Environment Configuration
Ensure your `.env` or config has:
- Supabase credentials for database access
- AI API credentials for AI-powered features

## 📝 Creating Templates

### Template Structure
```json
{
  "name": "Welcome New Volunteer",
  "description": "Welcome message for new volunteers",
  "category": "welcome",
  "subject": "Welcome to YMCA, {{user.first_name}}!",
  "content": "Dear {{user.first_name}},\\n\\nWelcome to our volunteer family!...",
  "merge_fields": ["user.first_name", "user.member_branch"],
  "is_active": true
}
```

### Merge Fields Syntax
Use double curly braces for merge fields: `{{field.name}}`

Available merge field categories:
- **User**: `{{user.first_name}}`, `{{user.email}}`, `{{user.member_branch}}`
- **Volunteer**: `{{volunteer.total_hours}}`, `{{volunteer.sessions}}`, `{{volunteer.interests}}`
- **Organization**: `{{org.name}}`, `{{org.contact_email}}`, `{{org.phone}}`
- **System**: `{{system.current_date}}`, `{{system.current_year}}`

### Template Categories
- **welcome**: New volunteer onboarding
- **follow_up**: Post-activity communications
- **reminder**: Event and commitment reminders
- **thank_you**: Appreciation and milestones
- **general**: Other communications

## 🤖 AI Integration

The system includes AI-powered features to help create and improve templates:

### Template Suggestions
Get AI recommendations for which template category to use:
```python
context = {
    "situation": "New volunteer just completed registration",
    "volunteer_info": {"first_session": True}
}
suggestion = await ai_assistant.suggest_template(context)
```

### AI-Assisted Creation
Get help creating templates:
```python
request = {
    "purpose": "Welcome new volunteers to youth programs",
    "category": "welcome",
    "audience": "new youth mentors",
    "tone": "warm and encouraging"
}
draft = await ai_assistant.help_create_template(request)
```

### Content Optimization
Improve existing templates:
```python
optimized = await ai_assistant.optimize_template_content(
    existing_content="Current template content...",
    feedback="Make it more engaging and include call-to-action"
)
```

## 📈 Usage Analytics

Track template effectiveness:
- Monitor usage frequency by template
- Analyze popular templates and categories
- Track rendering and actual sending statistics

Access usage data via:
- `GET /api/templates/{id}/usage` for specific templates
- Database queries on `template_usage` table for custom analytics

## 🔒 Security Considerations

- Templates are soft-deleted (marked inactive) rather than permanently removed
- Usage tracking helps identify potentially problematic templates
- Merge field validation prevents malicious content injection
- Template creation is tracked with user attribution

## 📱 Example Use Cases

### Welcome New Volunteers
Create personalized welcome messages with volunteer-specific information and next steps.

### Follow-up Communications
Send personalized follow-ups after volunteer sessions with hour tracking and appreciation.

### Event Reminders
Automated reminders with event details, location, and personalized instructions.

### Milestone Recognition
Celebrate volunteer achievements with hour milestones and impact summaries.

### Re-engagement
Reach out to inactive volunteers with personalized messages based on their history.

## 🚀 Future Enhancements

Potential additions:
- Email integration for direct sending
- Template versioning and A/B testing
- More sophisticated merge field logic
- Template approval workflows
- Multilingual template support
- Integration with calendar systems for automated reminders

## 🆘 Troubleshooting

### Common Issues
1. **Templates not rendering**: Check merge field syntax and data availability
2. **AI features not working**: Verify API credentials and connectivity
3. **Database errors**: Ensure Supabase tables are created and accessible
4. **Missing templates**: Run the seed script to create defaults

### Support
For technical issues:
1. Check application logs for error details
2. Verify database connectivity and permissions
3. Test API endpoints individually
4. Review merge field data structure

This feature provides a robust foundation for volunteer communication management while maintaining flexibility for future enhancements.