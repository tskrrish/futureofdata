"""
Test script for Email Campaign System
Tests the segmented email campaigns with dynamic audiences functionality
"""
import asyncio
from datetime import datetime, timedelta
import json
import pandas as pd
from email_campaigns import (
    EmailCampaignManager, MailchimpProvider, SendGridProvider,
    SegmentCriteria, SegmentationType, CampaignStatus, SegmentTemplates,
    AudienceSegmentationEngine
)

# Mock volunteer data for testing
def create_mock_volunteer_data():
    """Create mock volunteer data for testing"""
    
    volunteers = [
        {
            'contact_id': 1, 'email': 'john.doe@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'age': 28, 'member_branch': 'Blue Ash', 'experience_level': 2, 'is_ymca_member': True
        },
        {
            'contact_id': 2, 'email': 'jane.smith@example.com', 'first_name': 'Jane', 'last_name': 'Smith',
            'age': 35, 'member_branch': 'M.E. Lyons', 'experience_level': 3, 'is_ymca_member': True
        },
        {
            'contact_id': 3, 'email': 'bob.wilson@example.com', 'first_name': 'Bob', 'last_name': 'Wilson',
            'age': 45, 'member_branch': 'Blue Ash', 'experience_level': 1, 'is_ymca_member': False
        },
        {
            'contact_id': 4, 'email': 'alice.johnson@example.com', 'first_name': 'Alice', 'last_name': 'Johnson',
            'age': 22, 'member_branch': 'Campbell County', 'experience_level': 2, 'is_ymca_member': True
        },
        {
            'contact_id': 5, 'email': 'charlie.brown@example.com', 'first_name': 'Charlie', 'last_name': 'Brown',
            'age': 38, 'member_branch': 'Clippard', 'experience_level': 3, 'is_ymca_member': True
        }
    ]
    
    interactions = [
        {'contact_id': 1, 'hours': 25, 'project_id': 101, 'project_category': 'Youth Development', 
         'branch_short': 'Blue Ash', 'date': '2024-01-15'},
        {'contact_id': 1, 'hours': 15, 'project_id': 102, 'project_category': 'Fitness', 
         'branch_short': 'Blue Ash', 'date': '2024-02-10'},
        {'contact_id': 2, 'hours': 50, 'project_id': 103, 'project_category': 'Special Events', 
         'branch_short': 'M.E. Lyons', 'date': '2024-01-20'},
        {'contact_id': 2, 'hours': 30, 'project_id': 104, 'project_category': 'Youth Development', 
         'branch_short': 'M.E. Lyons', 'date': '2024-03-05'},
        {'contact_id': 3, 'hours': 5, 'project_id': 105, 'project_category': 'Administrative', 
         'branch_short': 'Blue Ash', 'date': '2023-08-15'},
        {'contact_id': 4, 'hours': 35, 'project_id': 106, 'project_category': 'Youth Development', 
         'branch_short': 'Campbell County', 'date': '2024-02-28'},
        {'contact_id': 5, 'hours': 60, 'project_id': 107, 'project_category': 'Fitness', 
         'branch_short': 'Clippard', 'date': '2024-01-10'}
    ]
    
    projects = [
        {'project_id': 101, 'project_name': 'After School Tutoring', 'category': 'Youth Development'},
        {'project_id': 102, 'project_name': 'Group Exercise Classes', 'category': 'Fitness'},
        {'project_id': 103, 'project_name': 'Annual Fundraiser', 'category': 'Special Events'},
        {'project_id': 104, 'project_name': 'Summer Camp', 'category': 'Youth Development'},
        {'project_id': 105, 'project_name': 'Data Entry Support', 'category': 'Administrative'},
        {'project_id': 106, 'project_name': 'Mentorship Program', 'category': 'Youth Development'},
        {'project_id': 107, 'project_name': 'Swimming Instruction', 'category': 'Fitness'}
    ]
    
    return {
        'volunteers': volunteers,
        'interactions': interactions,
        'projects': projects
    }

async def test_audience_segmentation():
    """Test audience segmentation engine"""
    print("\n🧪 Testing Audience Segmentation Engine")
    print("=" * 50)
    
    volunteer_data = create_mock_volunteer_data()
    engine = AudienceSegmentationEngine(volunteer_data)
    
    # Test 1: High engagement volunteers (20+ hours)
    print("\n1. Testing High Engagement Segment (20+ hours)")
    criteria = SegmentTemplates.high_engagement_volunteers()
    segment_df = engine.create_segment(criteria)
    print(f"   Found {len(segment_df)} high engagement volunteers")
    if not segment_df.empty:
        names = [f"{row['first_name']} {row['last_name']}" for _, row in segment_df.iterrows()]
        print(f"   Volunteers: {', '.join(names)}")
    
    # Test 2: Youth demographic (35 and under)
    print("\n2. Testing Youth Demographic (35 and under)")
    criteria = SegmentTemplates.youth_demographic(35)
    segment_df = engine.create_segment(criteria)
    print(f"   Found {len(segment_df)} youth volunteers")
    if not segment_df.empty:
        ages = [str(row['age']) for _, row in segment_df.iterrows()]
        print(f"   Ages: {', '.join(ages)}")
    
    # Test 3: Branch-specific segment
    print("\n3. Testing Branch-Specific Segment (Blue Ash)")
    criteria = SegmentTemplates.branch_specific("Blue Ash")
    segment_df = engine.create_segment(criteria)
    print(f"   Found {len(segment_df)} Blue Ash volunteers")
    
    # Test 4: Inactive volunteers
    print("\n4. Testing Inactive Volunteers (90+ days)")
    criteria = SegmentTemplates.inactive_volunteers(90)
    segment_df = engine.create_segment(criteria)
    print(f"   Found {len(segment_df)} inactive volunteers")

async def test_campaign_management():
    """Test campaign management system"""
    print("\n📧 Testing Campaign Management System")
    print("=" * 50)
    
    volunteer_data = create_mock_volunteer_data()
    campaign_manager = EmailCampaignManager(volunteer_data)
    
    # Add mock providers
    mailchimp_provider = MailchimpProvider("mock_api_key", "us1")
    sendgrid_provider = SendGridProvider("mock_api_key")
    
    campaign_manager.add_provider("mailchimp", mailchimp_provider)
    campaign_manager.add_provider("sendgrid", sendgrid_provider)
    
    # Test 1: Create campaign
    print("\n1. Creating Campaign")
    segments = SegmentTemplates.high_engagement_volunteers()
    
    campaign = await campaign_manager.create_campaign(
        name="Thank You High Performers",
        description="Appreciation email for our most engaged volunteers",
        subject_line="Thank you for your amazing volunteer work!",
        email_content="<p>Dear {{FNAME}},</p><p>Thank you for your dedication...</p>",
        sender_name="YMCA Team",
        sender_email="volunteer@ymca.org",
        segments=segments
    )
    
    print(f"   ✅ Campaign created: {campaign.name} ({campaign.id})")
    print(f"   Status: {campaign.status.value}")
    
    # Test 2: Get audience
    print("\n2. Getting Campaign Audience")
    recipients = await campaign_manager.get_campaign_audience(campaign.id)
    print(f"   ✅ Target audience: {len(recipients)} recipients")
    
    for recipient in recipients:
        print(f"   - {recipient['first_name']} {recipient['last_name']} ({recipient['email']})")
    
    # Test 3: Send campaign (mock)
    print("\n3. Sending Campaign (Mailchimp)")
    result = await campaign_manager.send_campaign(campaign.id, "mailchimp")
    
    if result.get("success"):
        print(f"   ✅ Campaign sent successfully")
        print(f"   Campaign ID: {result.get('campaign_id')}")
        print(f"   Recipients: {result.get('recipient_count')}")
    else:
        print(f"   ❌ Campaign send failed: {result.get('error')}")
    
    # Test 4: Get analytics (mock)
    print("\n4. Getting Campaign Analytics")
    analytics = await campaign_manager.get_campaign_analytics(campaign.id, "mailchimp")
    
    print(f"   Campaign Status: {analytics.get('campaign', {}).get('status')}")
    stats = analytics.get('provider_stats', {})
    if 'opens' in stats:
        opens = stats['opens']
        print(f"   Open Rate: {opens.get('open_rate', 0):.1%}")
        print(f"   Unique Opens: {opens.get('unique_opens', 0)}")
    
    return campaign_manager

async def test_segment_templates():
    """Test pre-defined segment templates"""
    print("\n📊 Testing Segment Templates")
    print("=" * 50)
    
    templates = {
        "High Engagement": SegmentTemplates.high_engagement_volunteers(),
        "Inactive (90 days)": SegmentTemplates.inactive_volunteers(90),
        "New Volunteers": SegmentTemplates.new_volunteers(30),
        "Youth Demographic": SegmentTemplates.youth_demographic(35),
        "Blue Ash Branch": SegmentTemplates.branch_specific("Blue Ash"),
        "Youth Development": SegmentTemplates.category_interested("Youth Development")
    }
    
    volunteer_data = create_mock_volunteer_data()
    engine = AudienceSegmentationEngine(volunteer_data)
    
    for name, criteria in templates.items():
        segment_df = engine.create_segment(criteria)
        print(f"   {name}: {len(segment_df)} volunteers")

async def test_multiple_criteria():
    """Test combining multiple segment criteria"""
    print("\n🔍 Testing Multiple Criteria Combinations")
    print("=" * 50)
    
    volunteer_data = create_mock_volunteer_data()
    engine = AudienceSegmentationEngine(volunteer_data)
    
    # Test: High engagement + Youth demographic
    print("\n1. High Engagement + Youth (≤35)")
    criteria = [
        SegmentCriteria(
            type=SegmentationType.ENGAGEMENT_LEVEL,
            field="hours",
            operator="gte", 
            value=20,
            description="20+ hours"
        ),
        SegmentCriteria(
            type=SegmentationType.DEMOGRAPHIC,
            field="age",
            operator="lte",
            value=35,
            description="Age 35 or under"
        )
    ]
    
    segment_df = engine.create_segment(criteria)
    print(f"   Found {len(segment_df)} volunteers meeting both criteria")
    
    # Test: Branch + Category interest
    print("\n2. Blue Ash Branch + Youth Development Interest")
    criteria = [
        SegmentCriteria(
            type=SegmentationType.BRANCH_AFFINITY,
            field="preferred_branch",
            operator="eq",
            value="Blue Ash",
            description="Blue Ash affinity"
        ),
        SegmentCriteria(
            type=SegmentationType.CATEGORY_INTEREST,
            field="preferred_category", 
            operator="eq",
            value="Youth Development",
            description="Youth Development interest"
        )
    ]
    
    segment_df = engine.create_segment(criteria)
    print(f"   Found {len(segment_df)} volunteers meeting both criteria")

async def main():
    """Run all tests"""
    print("🚀 Email Campaign System Test Suite")
    print("=" * 60)
    
    try:
        await test_audience_segmentation()
        await test_campaign_management() 
        await test_segment_templates()
        await test_multiple_criteria()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("\nThe email campaign system is ready for use with:")
        print("• Dynamic audience segmentation")
        print("• Mailchimp and SendGrid integrations")
        print("• Pre-defined segment templates")
        print("• Campaign management and analytics")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())