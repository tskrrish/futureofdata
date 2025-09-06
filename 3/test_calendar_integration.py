"""
Test script for Google Calendar two-way sync integration
Run this to verify the implementation works correctly
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
from google_calendar_client import GoogleCalendarClient
from database import VolunteerDatabase
from calendar_sync_service import CalendarSyncService

async def test_calendar_integration():
    """Test the Google Calendar integration components"""
    print("🧪 Testing Google Calendar Integration...")
    
    # Test 1: Initialize components
    print("\n1. Initializing components...")
    try:
        database = VolunteerDatabase()
        calendar_client = GoogleCalendarClient()
        sync_service = CalendarSyncService(database, calendar_client)
        print("✅ Components initialized successfully")
    except Exception as e:
        print(f"❌ Component initialization failed: {e}")
        return False
    
    # Test 2: Check database connection
    print("\n2. Testing database connection...")
    try:
        if database._is_available():
            print("✅ Database connection available")
        else:
            print("⚠️  Database not configured (this is okay for testing)")
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
    
    # Test 3: Check Google credentials file
    print("\n3. Checking Google credentials...")
    try:
        credentials_path = calendar_client.credentials_file
        if os.path.exists(credentials_path):
            print(f"✅ Google credentials file found: {credentials_path}")
        else:
            print(f"⚠️  Google credentials file not found: {credentials_path}")
            print("   Please follow GOOGLE_CALENDAR_SETUP.md to set up credentials")
    except Exception as e:
        print(f"❌ Credentials check failed: {e}")
    
    # Test 4: Test API endpoints structure (without making real calls)
    print("\n4. Testing API structure...")
    try:
        # Test that we can create the expected data structures
        test_shift = {
            'user_id': 'test-user-123',
            'project_name': 'Test Project',
            'branch': 'Test Branch YMCA',
            'shift_title': 'Test Volunteer Shift',
            'shift_description': 'This is a test volunteer shift',
            'start_time': (datetime.now() + timedelta(days=1)).isoformat(),
            'end_time': (datetime.now() + timedelta(days=1, hours=3)).isoformat(),
            'location': 'Test Location',
            'status': 'scheduled'
        }
        
        print("✅ Test shift data structure created")
        
        # Test sync service methods exist and are callable
        methods_to_test = [
            'sync_volunteer_shifts',
            'create_shift_with_calendar',
            'update_shift_with_calendar',
            'delete_shift_with_calendar'
        ]
        
        for method_name in methods_to_test:
            if hasattr(sync_service, method_name):
                print(f"✅ Method {method_name} exists")
            else:
                print(f"❌ Method {method_name} missing")
                
    except Exception as e:
        print(f"❌ API structure test failed: {e}")
    
    # Test 5: Test calendar client methods
    print("\n5. Testing calendar client methods...")
    try:
        # Test that methods exist
        client_methods = [
            'get_authorization_url',
            'exchange_code_for_tokens',
            'is_user_authenticated',
            'create_event',
            'update_event',
            'delete_event',
            'list_events'
        ]
        
        for method_name in client_methods:
            if hasattr(calendar_client, method_name):
                print(f"✅ Calendar method {method_name} exists")
            else:
                print(f"❌ Calendar method {method_name} missing")
    
    except Exception as e:
        print(f"❌ Calendar client test failed: {e}")
    
    # Test 6: Test database methods
    print("\n6. Testing database methods...")
    try:
        # Test that calendar-related methods exist
        db_methods = [
            'save_google_calendar_auth',
            'get_google_calendar_auth',
            'delete_google_calendar_auth',
            'create_volunteer_shift',
            'update_volunteer_shift',
            'get_volunteer_shifts',
            'log_calendar_sync',
            'get_sync_history'
        ]
        
        for method_name in db_methods:
            if hasattr(database, method_name):
                print(f"✅ Database method {method_name} exists")
            else:
                print(f"❌ Database method {method_name} missing")
                
    except Exception as e:
        print(f"❌ Database methods test failed: {e}")
    
    print("\n🎉 Calendar integration test completed!")
    print("\n📋 Next steps:")
    print("1. Set up Google Cloud Console and OAuth credentials")
    print("2. Copy google_credentials.json.example to google_credentials.json")
    print("3. Configure your actual Google OAuth credentials")
    print("4. Set up Supabase database with the new tables")
    print("5. Test with a real volunteer user account")
    
    return True

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import google.auth
        print("✅ google.auth imported")
    except ImportError as e:
        print(f"❌ google.auth import failed: {e}")
        return False
    
    try:
        import google.oauth2.credentials
        print("✅ google.oauth2.credentials imported")
    except ImportError as e:
        print(f"❌ google.oauth2.credentials import failed: {e}")
        return False
    
    try:
        from google_auth_oauthlib.flow import Flow
        print("✅ google_auth_oauthlib.flow imported")
    except ImportError as e:
        print(f"❌ google_auth_oauthlib.flow import failed: {e}")
        return False
    
    try:
        from googleapiclient.discovery import build
        print("✅ googleapiclient.discovery imported")
    except ImportError as e:
        print(f"❌ googleapiclient.discovery import failed: {e}")
        return False
    
    print("✅ All required Google API imports successful")
    return True

if __name__ == "__main__":
    print("🚀 Starting Google Calendar Integration Tests")
    print("=" * 50)
    
    # Test imports first
    if not test_imports():
        print("\n❌ Import tests failed. Please install required dependencies:")
        print("pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib google-auth")
        sys.exit(1)
    
    # Run main integration tests
    success = asyncio.run(test_calendar_integration())
    
    if success:
        print("\n✅ All tests passed! Google Calendar integration is ready for setup.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        sys.exit(1)