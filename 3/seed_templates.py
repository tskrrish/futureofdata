#!/usr/bin/env python3
"""
Seed script for message templates
Run this to populate the database with default message templates
"""
import asyncio
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import VolunteerDatabase

DEFAULT_TEMPLATES = [
    {
        "name": "Welcome New Volunteer",
        "description": "Welcome message for new volunteers who just signed up",
        "category": "welcome",
        "subject": "Welcome to YMCA Volunteering, {{user.first_name}}!",
        "content": """Dear {{user.first_name}},

Welcome to the YMCA volunteer family! We're thrilled to have you join us in making a positive impact in our community.

Here's what happens next:
1. Complete your volunteer profile
2. Attend a brief orientation session at {{user.member_branch}} YMCA
3. Start making a difference!

Your volunteer coordinator will be in touch within 2-3 business days to schedule your orientation.

Thank you for your commitment to strengthening our community!

Best regards,
The YMCA Volunteer Team
{{org.contact_email}} | {{org.phone}}""",
        "merge_fields": ["user.first_name", "user.member_branch", "org.contact_email", "org.phone"],
        "is_active": True
    },
    {
        "name": "Follow-up After First Session",
        "description": "Follow-up message after volunteer's first session",
        "category": "follow_up",
        "subject": "How was your first volunteer experience?",
        "content": """Hi {{user.first_name}},

Thank you for volunteering with us! We hope you enjoyed your first session and felt the impact of your contribution to our community.

Your First Session Summary:
- Hours contributed: {{volunteer.session_hours}}
- Location: {{volunteer.branch}}
- Activity: {{volunteer.activity}}

We'd love to hear about your experience. Please take a moment to share any feedback or questions you might have.

Looking forward to seeing you again soon!

Warm regards,
Your YMCA Team""",
        "merge_fields": ["user.first_name", "volunteer.session_hours", "volunteer.branch", "volunteer.activity"],
        "is_active": True
    },
    {
        "name": "Volunteer Hour Milestone",
        "description": "Congratulatory message when volunteer reaches hour milestones",
        "category": "thank_you",
        "subject": "Congratulations! You've reached {{volunteer.total_hours}} volunteer hours!",
        "content": """Dear {{user.first_name}},

What an incredible achievement! You've now contributed {{volunteer.total_hours}} hours of service to your community through the YMCA.

Your Impact:
- Total volunteer hours: {{volunteer.total_hours}}
- Sessions completed: {{volunteer.sessions}}
- Primary focus area: {{volunteer.interests}}
- Favorite location: {{volunteer.top_branch}}

Your dedication and commitment make a real difference in the lives of those we serve. Thank you for being such an important part of our volunteer community.

Keep up the amazing work!

With gratitude,
The YMCA Team""",
        "merge_fields": ["user.first_name", "volunteer.total_hours", "volunteer.sessions", "volunteer.interests", "volunteer.top_branch"],
        "is_active": True
    },
    {
        "name": "Event Reminder",
        "description": "Reminder for upcoming volunteer events",
        "category": "reminder",
        "subject": "Reminder: {{event.name}} tomorrow at {{event.location}}",
        "content": """Hi {{user.first_name}},

This is a friendly reminder about your upcoming volunteer commitment:

Event: {{event.name}}
Date: {{event.date}}
Time: {{event.time}}
Location: {{event.location}}
Address: {{event.address}}

What to bring:
- Comfortable clothing
- Water bottle
- Your enthusiasm!

If you need to cancel or reschedule, please contact us at least 24 hours in advance.

See you there!

Best,
{{event.coordinator}}
{{org.contact_email}}""",
        "merge_fields": ["user.first_name", "event.name", "event.date", "event.time", "event.location", "event.address", "event.coordinator", "org.contact_email"],
        "is_active": True
    },
    {
        "name": "Monthly Volunteer Newsletter",
        "description": "Monthly newsletter template for volunteers",
        "category": "general",
        "subject": "YMCA Volunteer Newsletter - {{system.current_month}} {{system.current_year}}",
        "content": """Dear {{user.first_name}},

Here's your monthly volunteer update for {{system.current_month}} {{system.current_year}}:

🎯 YOUR IMPACT THIS MONTH:
- Hours contributed: {{volunteer.month_hours}}
- Community members served: {{volunteer.people_served}}

🌟 UPCOMING OPPORTUNITIES:
- Special Events: {{events.upcoming}}
- New Programs: {{programs.new}}
- Training Sessions: {{training.available}}

📊 COMMUNITY IMPACT:
Our volunteers contributed {{community.total_hours}} hours this month, serving {{community.people_served}} community members across all programs.

💭 VOLUNTEER SPOTLIGHT:
{{spotlight.story}}

Thank you for being part of our community impact!

Stay connected,
The YMCA Volunteer Team""",
        "merge_fields": ["user.first_name", "system.current_month", "system.current_year", "volunteer.month_hours", "volunteer.people_served", "events.upcoming", "programs.new", "training.available", "community.total_hours", "community.people_served", "spotlight.story"],
        "is_active": True
    },
    {
        "name": "Re-engagement for Inactive Volunteers",
        "description": "Re-engagement message for volunteers who haven't been active",
        "category": "follow_up",
        "subject": "We miss you, {{user.first_name}}! Come back and volunteer with us",
        "content": """Hi {{user.first_name}},

We noticed it's been a while since your last volunteer session with us, and we wanted to reach out because we miss having you as part of our team!

Your past contributions:
- Total hours: {{volunteer.total_hours}}
- Last session: {{volunteer.last_date}}
- Favorite activities: {{volunteer.interests}}

We understand life gets busy, but we'd love to have you back when you're ready. Here are some flexible opportunities that might work for you:

🕐 Short-term commitments (1-2 hours)
🏠 Virtual volunteer opportunities
📅 Weekend and evening options
🎯 Special events and seasonal activities

If you're interested in returning or have questions about new opportunities, just reply to this email or call us at {{org.phone}}.

We're here whenever you're ready to make an impact again!

Hope to see you soon,
Your YMCA Volunteer Team""",
        "merge_fields": ["user.first_name", "volunteer.total_hours", "volunteer.last_date", "volunteer.interests", "org.phone"],
        "is_active": True
    }
]

async def seed_templates():
    """Seed the database with default message templates"""
    print("🌱 Seeding message templates...")
    
    db = VolunteerDatabase()
    
    if not db._is_available():
        print("❌ Database not available. Please check your Supabase configuration.")
        return
    
    created_count = 0
    
    for template_data in DEFAULT_TEMPLATES:
        try:
            # Check if template already exists
            existing_templates = await db.get_message_templates()
            existing_names = [t['name'] for t in existing_templates]
            
            if template_data['name'] in existing_names:
                print(f"⏭️  Template '{template_data['name']}' already exists, skipping...")
                continue
            
            template = await db.create_message_template(template_data)
            
            if template:
                print(f"✅ Created template: {template_data['name']}")
                created_count += 1
            else:
                print(f"❌ Failed to create template: {template_data['name']}")
                
        except Exception as e:
            print(f"❌ Error creating template '{template_data['name']}': {e}")
    
    print(f"\n🎉 Seeding complete! Created {created_count} new templates.")
    
    # Display summary
    all_templates = await db.get_message_templates()
    print(f"📊 Total templates in database: {len(all_templates)}")
    
    # Group by category
    categories = {}
    for template in all_templates:
        category = template.get('category', 'general')
        if category not in categories:
            categories[category] = 0
        categories[category] += 1
    
    print("\n📋 Templates by category:")
    for category, count in categories.items():
        print(f"  - {category}: {count} templates")

if __name__ == "__main__":
    asyncio.run(seed_templates())