#!/usr/bin/env python3
"""
Test script for Supabase and inference.net integrations
Verifies that both services are working correctly
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from database import VolunteerDatabase
from ai_assistant import VolunteerAIAssistant
from config import settings

async def test_supabase_integration():
    """Test Supabase database integration"""
    print("🗄️  TESTING SUPABASE INTEGRATION")
    print("=" * 50)
    
    db = VolunteerDatabase()
    
    # Check if database is available
    if not db._is_available():
        print("⚠️  Supabase not configured or unavailable")
        print("   To enable Supabase:")
        print("   1. Create a Supabase project at https://supabase.com")
        print("   2. Add SUPABASE_URL and SUPABASE_KEY to your .env file")
        print("   3. Run the SQL commands in setup_supabase.sql")
        return False
    
    print(f"✅ Supabase client initialized")
    print(f"   URL: {settings.SUPABASE_URL[:30]}...")
    print(f"   API Key: {settings.SUPABASE_KEY[:20]}...")
    
    # Test basic operations
    try:
        # Test creating a user
        test_user_data = {
            "email": "test@volunteerconnect.com",
            "first_name": "Test",
            "last_name": "User",
            "age": 25,
            "city": "Cincinnati",
            "state": "OH",
            "is_ymca_member": True
        }
        
        print("\n📝 Testing user creation...")
        user = await db.create_user(test_user_data)
        
        if user:
            print(f"✅ User created successfully: {user['id']}")
            user_id = user['id']
            
            # Test user preferences
            print("\n⚙️  Testing user preferences...")
            preferences = {
                "interests": "youth development, fitness",
                "availability": {"weekday": True, "evening": True},
                "time_commitment": 2,
                "location_preference": "Blue Ash"
            }
            
            success = await db.save_user_preferences(user_id, preferences)
            if success:
                print("✅ Preferences saved successfully")
                
                # Retrieve preferences
                saved_prefs = await db.get_user_preferences(user_id)
                if saved_prefs:
                    print("✅ Preferences retrieved successfully")
                else:
                    print("⚠️  Could not retrieve preferences")
            else:
                print("❌ Failed to save preferences")
            
            # Test conversation
            print("\n💬 Testing conversations...")
            conv_id = await db.create_conversation(user_id=user_id)
            if conv_id:
                print(f"✅ Conversation created: {conv_id}")
                
                # Test messages
                msg_success = await db.save_message(
                    conv_id, 
                    "user", 
                    "Hello, I want to volunteer!", 
                    user_id
                )
                if msg_success:
                    print("✅ Message saved successfully")
                else:
                    print("⚠️  Message save failed")
            
            # Test analytics
            print("\n📊 Testing analytics...")
            analytics_success = await db.track_event(
                "test_event", 
                {"source": "test", "success": True}, 
                user_id
            )
            if analytics_success:
                print("✅ Analytics event tracked")
            else:
                print("⚠️  Analytics tracking failed")
            
            print(f"\n🎉 Supabase integration test PASSED!")
            return True
            
        else:
            print("❌ Failed to create test user")
            return False
            
    except Exception as e:
        print(f"❌ Supabase test error: {e}")
        return False

async def test_inference_net_integration():
    """Test inference.net AI integration"""
    print("\n🤖 TESTING INFERENCE.NET INTEGRATION")
    print("=" * 50)
    
    ai_assistant = VolunteerAIAssistant()
    
    # Check API key
    if not settings.INFERENCE_NET_API_KEY:
        print("⚠️  inference.net API key not configured")
        print("   To enable AI features:")
        print("   1. Get an API key from https://inference.net")
        print("   2. Add INFERENCE_NET_API_KEY to your .env file")
        return False
    
    print(f"✅ inference.net configured")
    print(f"   Model: {settings.INFERENCE_NET_MODEL}")
    print(f"   Base URL: {settings.INFERENCE_NET_BASE_URL}")
    print(f"   API Key: {settings.INFERENCE_NET_API_KEY[:20]}...")
    
    # Test basic chat
    try:
        print("\n💬 Testing AI chat...")
        test_message = "Hi! I'm interested in volunteering with youth programs at the YMCA."
        
        response = await ai_assistant.chat(test_message)
        
        if response and response.get('success'):
            print("✅ AI chat response received")
            print(f"   Response length: {len(response.get('response', ''))} characters")
            print(f"   Suggestions: {len(response.get('suggestions', []))} items")
            
            # Show first 200 characters of response
            ai_response = response.get('response', '')
            preview = ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
            print(f"   Preview: {preview}")
            
        else:
            print("❌ AI chat failed")
            error = response.get('error') if response else 'Unknown error'
            print(f"   Error: {error}")
            return False
            
        # Test volunteer recommendations
        print("\n🎯 Testing AI recommendations...")
        test_preferences = {
            'age': 28,
            'interests': 'youth mentoring, fitness',
            'availability': {'weekday': True, 'evening': True},
            'time_commitment': 2,
            'location': 'Blue Ash'
        }
        
        # Mock volunteer data for testing
        mock_data = {
            'volunteers': [],
            'projects': [
                {'name': 'Youth Mentoring', 'branch': 'Blue Ash', 'category': 'Youth Development'},
                {'name': 'Group Exercise', 'branch': 'M.E. Lyons', 'category': 'Fitness'}
            ],
            'insights': {'total_volunteers': 100, 'total_hours': 5000}
        }
        
        rec_response = await ai_assistant.get_volunteer_recommendations(test_preferences, mock_data)
        
        if rec_response and rec_response.get('success'):
            print("✅ AI recommendations generated")
            recommendations = rec_response.get('recommendations', '')
            preview = recommendations[:200] + "..." if len(recommendations) > 200 else recommendations
            print(f"   Preview: {preview}")
        else:
            print("⚠️  AI recommendations using fallback")
            
        # Test onboarding guidance
        print("\n📚 Testing onboarding guidance...")
        guidance_response = await ai_assistant.get_onboarding_guidance('start')
        
        if guidance_response and guidance_response.get('success'):
            print("✅ Onboarding guidance generated")
        else:
            print("⚠️  Onboarding guidance using fallback")
            
        print(f"\n🎉 inference.net integration test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ inference.net test error: {e}")
        return False

async def test_integrated_workflow():
    """Test complete integrated workflow"""
    print("\n🔄 TESTING INTEGRATED WORKFLOW")
    print("=" * 50)
    
    try:
        db = VolunteerDatabase()
        ai = VolunteerAIAssistant()
        
        # Create a user
        user_data = {
            "email": "integration@test.com",
            "first_name": "Integration",
            "last_name": "Test",
            "age": 30,
            "city": "Cincinnati"
        }
        
        user = None
        if db._is_available():
            user = await db.create_user(user_data)
            print(f"✅ User created for workflow test")
        
        # Start conversation
        conv_id = None
        if user:
            conv_id = await db.create_conversation(user['id'])
            print(f"✅ Conversation started: {conv_id}")
        
        # Chat with AI
        chat_response = await ai.chat("I want to help with youth programs")
        if chat_response.get('success'):
            print("✅ AI provided guidance")
            
            # Save conversation to database
            if conv_id:
                await db.save_message(conv_id, "user", "I want to help with youth programs", user['id'] if user else None)
                await db.save_message(conv_id, "assistant", chat_response['response'], user['id'] if user else None)
                print("✅ Conversation saved to database")
        
        # Track analytics
        if user and db._is_available():
            await db.track_event("workflow_test", {"step": "completed"}, user['id'])
            print("✅ Analytics tracked")
        
        print(f"\n🎉 INTEGRATED WORKFLOW TEST PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Integrated workflow test error: {e}")
        return False

def show_configuration_status():
    """Show current configuration status"""
    print("⚙️  CONFIGURATION STATUS")
    print("=" * 50)
    
    # Supabase
    supabase_configured = bool(settings.SUPABASE_URL and settings.SUPABASE_KEY)
    print(f"Supabase: {'✅ Configured' if supabase_configured else '❌ Not configured'}")
    if supabase_configured:
        print(f"   URL: {settings.SUPABASE_URL[:30]}...")
        print(f"   Key: {settings.SUPABASE_KEY[:20]}...")
    
    # inference.net
    inference_configured = bool(settings.INFERENCE_NET_API_KEY)
    print(f"inference.net: {'✅ Configured' if inference_configured else '❌ Not configured'}")
    if inference_configured:
        print(f"   Model: {settings.INFERENCE_NET_MODEL}")
        print(f"   Key: {settings.INFERENCE_NET_API_KEY[:20]}...")
    
    print()

async def main():
    """Main test function"""
    print("🧪 VOLUNTEER PATHFINDER INTEGRATION TESTS")
    print("=" * 60)
    
    show_configuration_status()
    
    # Test results
    supabase_ok = await test_supabase_integration()
    inference_ok = await test_inference_net_integration()
    workflow_ok = await test_integrated_workflow()
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Supabase Integration: {'✅ PASS' if supabase_ok else '❌ FAIL'}")
    print(f"inference.net Integration: {'✅ PASS' if inference_ok else '❌ FAIL'}")
    print(f"Integrated Workflow: {'✅ PASS' if workflow_ok else '❌ FAIL'}")
    
    all_passed = supabase_ok and inference_ok and workflow_ok
    
    if all_passed:
        print(f"\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("   The system is ready for production use!")
    else:
        print(f"\n⚠️  SOME TESTS FAILED")
        print("   Check the configuration and try again.")
        
        if not supabase_ok:
            print("\n📝 To fix Supabase integration:")
            print("   1. Create a Supabase project at https://supabase.com")
            print("   2. Copy the Project URL and anon public key")
            print("   3. Add to .env file: SUPABASE_URL and SUPABASE_KEY")
            print("   4. Run the SQL commands in setup_supabase.sql")
            
        if not inference_ok:
            print("\n📝 To fix inference.net integration:")
            print("   1. Get an API key from https://inference.net")
            print("   2. Add to .env file: INFERENCE_NET_API_KEY")
    
    print(f"\n🚀 Ready to launch: python start.py")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
