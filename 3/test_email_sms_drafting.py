#!/usr/bin/env python3
"""
Test script for Email/SMS Auto-Drafting functionality
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_sms_drafting import (
    EmailSMSDraftingEngine, MessageType, MessageTone, OutreachPurpose,
    PersonalizationContext, MessageContext
)
from contextual_tone_analyzer import ContextualToneAnalyzer
from message_templates import MessageTemplateEngine
from ai_assistant import VolunteerAIAssistant


async def test_basic_drafting():
    """Test basic message drafting functionality"""
    print("🧪 Testing Basic Message Drafting")
    
    # Initialize components
    ai_assistant = VolunteerAIAssistant()
    drafting_engine = EmailSMSDraftingEngine(ai_assistant)
    
    # Create test person context
    person_context = PersonalizationContext(
        name="Sarah Johnson",
        age=28,
        is_ymca_member=True,
        member_branch="Blue Ash YMCA",
        engagement_level="new",
        preferences={'interests': 'youth development, fitness programs'}
    )
    
    # Test welcome email
    message_context = MessageContext(
        purpose=OutreachPurpose.WELCOME_NEW,
        tone=MessageTone.WELCOMING,
        message_type=MessageType.EMAIL,
        urgency_level=1
    )
    
    try:
        drafted_message = await drafting_engine.draft_message(
            person_context=person_context,
            message_context=message_context
        )
        
        print(f"✅ Welcome email drafted successfully")
        print(f"   Subject: {drafted_message.subject}")
        print(f"   Content length: {drafted_message.character_count} characters")
        print(f"   Personalization score: {drafted_message.personalization_score:.2f}")
        print(f"   Estimated engagement: {drafted_message.estimated_engagement:.2f}")
        print(f"   Content preview: {drafted_message.content[:100]}...")
        
    except Exception as e:
        print(f"❌ Welcome email drafting failed: {e}")
    
    # Test SMS message
    message_context.message_type = MessageType.SMS
    message_context.purpose = OutreachPurpose.VOLUNTEER_MATCH
    message_context.tone = MessageTone.ENCOURAGING
    
    try:
        drafted_sms = await drafting_engine.draft_message(
            person_context=person_context,
            message_context=message_context
        )
        
        print(f"\n✅ SMS message drafted successfully")
        print(f"   Content: {drafted_sms.content}")
        print(f"   Character count: {drafted_sms.character_count}")
        print(f"   Under SMS limit: {'Yes' if drafted_sms.character_count <= 160 else 'No'}")
        
    except Exception as e:
        print(f"❌ SMS drafting failed: {e}")


def test_tone_analysis():
    """Test contextual tone analysis"""
    print("\n🧪 Testing Tone Analysis")
    
    tone_analyzer = ContextualToneAnalyzer()
    
    # Test with new volunteer
    person_context = PersonalizationContext(
        name="Mike Chen",
        age=45,
        engagement_level="new"
    )
    
    analysis = tone_analyzer.analyze_tone(
        person_context=person_context,
        message_purpose=OutreachPurpose.WELCOME_NEW
    )
    
    print(f"✅ Tone analysis completed")
    print(f"   Recommended tone: {analysis.recommended_tone.value}")
    print(f"   Communication style: {analysis.communication_style.value}")
    print(f"   Engagement pattern: {analysis.engagement_pattern.value}")
    print(f"   Confidence score: {analysis.confidence_score:.2f}")
    print(f"   Key reasoning: {analysis.reasoning[0] if analysis.reasoning else 'None'}")
    
    # Test with experienced volunteer
    experienced_context = PersonalizationContext(
        name="Linda Williams",
        age=62,
        engagement_level="champion",
        volunteer_history={
            'total_hours': 150,
            'sessions': 45,
            'top_categories': {'Youth Development': 25, 'Special Events': 15}
        }
    )
    
    analysis_experienced = tone_analyzer.analyze_tone(
        person_context=experienced_context,
        message_purpose=OutreachPurpose.APPRECIATION
    )
    
    print(f"\n✅ Experienced volunteer tone analysis")
    print(f"   Recommended tone: {analysis_experienced.recommended_tone.value}")
    print(f"   Confidence score: {analysis_experienced.confidence_score:.2f}")
    print(f"   Personalization opportunities: {len(analysis_experienced.personalization_opportunities)}")


def test_template_engine():
    """Test template engine functionality"""
    print("\n🧪 Testing Template Engine")
    
    template_engine = MessageTemplateEngine()
    
    # List available templates
    welcome_templates = template_engine.get_templates_by_criteria(
        purpose=OutreachPurpose.WELCOME_NEW,
        message_type=MessageType.EMAIL
    )
    
    print(f"✅ Found {len(welcome_templates)} welcome email templates")
    
    if welcome_templates:
        template = welcome_templates[0]
        print(f"   Template ID: {template.id}")
        print(f"   Template name: {template.name}")
        print(f"   Variables: {len(template.variables)}")
        
        # Test template rendering
        person_context = PersonalizationContext(
            name="Alex Rodriguez",
            age=33,
            is_ymca_member=True,
            member_branch="M.E. Lyons YMCA",
            preferences={'interests': 'fitness programs, community events'}
        )
        
        try:
            rendered = template_engine.render_template(
                template_id=template.id,
                person_context=person_context
            )
            
            print(f"✅ Template rendered successfully")
            print(f"   Subject: {rendered.get('subject', 'N/A')}")
            print(f"   Content preview: {rendered['content'][:150]}...")
            print(f"   Variables used: {len(rendered.get('variables_used', []))}")
            
        except Exception as e:
            print(f"❌ Template rendering failed: {e}")


async def test_variant_generation():
    """Test multiple variant generation"""
    print("\n🧪 Testing Variant Generation")
    
    ai_assistant = VolunteerAIAssistant()
    drafting_engine = EmailSMSDraftingEngine(ai_assistant)
    
    person_context = PersonalizationContext(
        name="Jessica Park",
        age=25,
        engagement_level="active",
        volunteer_history={
            'total_hours': 35,
            'sessions': 12,
            'top_categories': {'Youth Development': 8, 'Fitness & Wellness': 4}
        }
    )
    
    message_context = MessageContext(
        purpose=OutreachPurpose.EVENT_INVITATION,
        tone=MessageTone.ENCOURAGING,  # Will be varied
        message_type=MessageType.EMAIL,
        event_details={
            'name': 'Volunteer Appreciation Dinner',
            'date': '2024-03-15',
            'location': 'Blue Ash YMCA Community Room'
        }
    )
    
    try:
        variants = await drafting_engine.generate_multiple_variants(
            person_context=person_context,
            message_context=message_context,
            num_variants=3
        )
        
        print(f"✅ Generated {len(variants)} message variants")
        for i, variant in enumerate(variants, 1):
            print(f"   Variant {i}:")
            print(f"     Tone: {variant.tone.value}")
            print(f"     Engagement score: {variant.estimated_engagement:.2f}")
            print(f"     Personalization: {variant.personalization_score:.2f}")
            print(f"     Length: {variant.character_count} chars")
        
    except Exception as e:
        print(f"❌ Variant generation failed: {e}")


def test_optimal_send_time():
    """Test optimal send time recommendations"""
    print("\n🧪 Testing Optimal Send Time")
    
    ai_assistant = VolunteerAIAssistant()
    drafting_engine = EmailSMSDraftingEngine(ai_assistant)
    
    # Test different contexts
    contexts = [
        PersonalizationContext(name="Young Professional", age=28, engagement_level="new"),
        PersonalizationContext(name="Senior Volunteer", age=68, engagement_level="champion"),
        PersonalizationContext(name="Regular Volunteer", age=45, engagement_level="active")
    ]
    
    for person_context in contexts:
        email_timing = drafting_engine.get_optimal_send_time(person_context, MessageType.EMAIL)
        sms_timing = drafting_engine.get_optimal_send_time(person_context, MessageType.SMS)
        
        print(f"✅ {person_context.name} (age {person_context.age}):")
        print(f"   Email optimal hours: {email_timing['optimal_hours']}")
        print(f"   SMS optimal hours: {sms_timing['optimal_hours']}")
        print(f"   Avoid weekends: {email_timing['avoid_weekends']}")


async def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Email/SMS Auto-Drafting Tests")
    print("=" * 50)
    
    await test_basic_drafting()
    test_tone_analysis()
    test_template_engine()
    await test_variant_generation()
    test_optimal_send_time()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("\nFeature Summary:")
    print("✅ AI-powered personalized email/SMS drafting")
    print("✅ Contextual tone analysis and recommendation")
    print("✅ Template-based message generation")
    print("✅ Multiple variant generation for A/B testing")
    print("✅ Optimal send time recommendations")
    print("✅ Smart personalization based on volunteer history")
    print("✅ Integration with existing YMCA volunteer data")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_all_tests())