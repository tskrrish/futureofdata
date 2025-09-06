#!/usr/bin/env python3
"""
Test script for SSO functionality
"""
import asyncio
import sys
from pathlib import Path

async def test_database():
    """Test database connection and user operations"""
    print("🧪 Testing database...")
    
    try:
        from database import VolunteerDatabase
        
        db = VolunteerDatabase()
        
        if not db._is_available():
            print("❌ Database not available")
            return False
        
        # Test user creation
        test_user = {
            'email': 'test.sso@example.com',
            'first_name': 'Test',
            'last_name': 'SSO User',
            'sso_provider': 'google',
            'sso_id': 'test123'
        }
        
        user = await db.create_user(test_user)
        if user:
            print(f"✅ Created test user: {user['id']}")
            
            # Test user retrieval
            retrieved = await db.get_user(email='test.sso@example.com')
            if retrieved:
                print(f"✅ Retrieved user: {retrieved['email']}")
            
            # Clean up
            # Note: In production, you'd want proper cleanup methods
            print("✅ Database tests passed")
            return True
        else:
            print("❌ Failed to create test user")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_auth_config():
    """Test authentication configuration"""
    print("🧪 Testing auth configuration...")
    
    try:
        from config import settings
        from auth import SSOAuth
        from database import VolunteerDatabase
        
        db = VolunteerDatabase()
        auth = SSOAuth(db)
        
        # Test Google OAuth URL generation
        try:
            google_url = auth.get_google_auth_url(state="test")
            if google_url and "accounts.google.com" in google_url:
                print("✅ Google OAuth URL generation works")
            else:
                print("❌ Google OAuth URL generation failed")
                return False
        except Exception as e:
            print(f"❌ Google OAuth test failed: {e}")
            return False
        
        # Test Microsoft OAuth URL generation
        try:
            ms_url = auth.get_microsoft_auth_url(state="test")
            if ms_url and "login.microsoftonline.com" in ms_url:
                print("✅ Microsoft OAuth URL generation works")
            else:
                print("❌ Microsoft OAuth URL generation failed")
                return False
        except Exception as e:
            print(f"❌ Microsoft OAuth test failed: {e}")
            return False
        
        # Test JWT token creation
        try:
            test_user_data = {
                'id': 'test-id-123',
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
            token = auth.create_jwt_token(test_user_data)
            if token and len(token.split('.')) == 3:  # JWT has 3 parts
                print("✅ JWT token creation works")
            else:
                print("❌ JWT token creation failed")
                return False
        except Exception as e:
            print(f"❌ JWT token test failed: {e}")
            return False
        
        print("✅ Auth configuration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Auth configuration test failed: {e}")
        return False

def test_api_endpoints():
    """Test that the API endpoints are properly configured"""
    print("🧪 Testing API endpoints...")
    
    try:
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            print("✅ Health endpoint works")
        else:
            print("❌ Health endpoint failed")
            return False
        
        # Test auth endpoints exist
        response = client.get("/auth/google")
        if response.status_code == 200:
            print("✅ Google auth endpoint works")
        else:
            print(f"❌ Google auth endpoint failed: {response.status_code}")
            return False
        
        response = client.get("/auth/microsoft")
        if response.status_code == 200:
            print("✅ Microsoft auth endpoint works")
        else:
            print(f"❌ Microsoft auth endpoint failed: {response.status_code}")
            return False
        
        # Test login page
        response = client.get("/login")
        if response.status_code == 200:
            print("✅ Login page endpoint works")
        else:
            print(f"❌ Login page endpoint failed: {response.status_code}")
            return False
        
        print("✅ API endpoint tests passed")
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Starting SSO Implementation Tests")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test database
    if await test_database():
        tests_passed += 1
    
    # Test auth configuration
    if test_auth_config():
        tests_passed += 1
    
    # Test API endpoints
    if test_api_endpoints():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"🧪 Tests completed: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! SSO implementation is ready.")
        print("\n🚀 Next steps:")
        print("1. Set up OAuth providers (Google, Microsoft)")
        print("2. Configure environment variables")
        print("3. Run: python main.py")
        print("4. Test login flow at http://localhost:8000")
        return True
    else:
        print(f"❌ {total_tests - tests_passed} test(s) failed. Please fix issues and try again.")
        return False

if __name__ == "__main__":
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Please run this script from the directory containing main.py")
        sys.exit(1)
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)