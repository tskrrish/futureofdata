#!/usr/bin/env python3
"""
Setup script for SSO integration
This script helps configure the OAuth providers and test the integration
"""
import os
import sys
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_section(text):
    print(f"\n{'-'*40}")
    print(f"  {text}")
    print(f"{'-'*40}")

def main():
    print_header("YMCA Volunteer PathFinder SSO Setup")
    
    print("""
This setup script will help you configure Single Sign-On (SSO) with Google and Microsoft.
    """)
    
    # Check if config.py exists
    config_path = Path(__file__).parent / "config.py"
    if not config_path.exists():
        print("❌ config.py not found! Please copy config.example.py to config.py first.")
        sys.exit(1)
    
    print("✅ config.py found")
    
    # Check environment variables
    print_section("Environment Variables")
    
    required_vars = [
        ('GOOGLE_CLIENT_ID', 'Google OAuth Client ID'),
        ('GOOGLE_CLIENT_SECRET', 'Google OAuth Client Secret'),
        ('MICROSOFT_CLIENT_ID', 'Microsoft App Registration Client ID'),
        ('MICROSOFT_CLIENT_SECRET', 'Microsoft App Registration Client Secret'),
        ('SECRET_KEY', 'JWT Secret Key (generate a secure random string)'),
        ('SUPABASE_URL', 'Supabase Project URL'),
        ('SUPABASE_KEY', 'Supabase Anon Key'),
    ]
    
    missing_vars = []
    for var, description in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * min(len(value), 20)}...")
        else:
            print(f"❌ {var}: Not set ({description})")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing {len(missing_vars)} environment variable(s). Please set them and run again.")
        print("\nExample .env file:")
        print("```")
        for var in missing_vars:
            print(f"{var}=your_value_here")
        print("```")
    else:
        print("\n✅ All required environment variables are set!")
    
    # OAuth Provider Setup Instructions
    print_section("OAuth Provider Setup")
    
    print("""
🔧 GOOGLE OAUTH SETUP:
1. Go to https://console.developers.google.com/
2. Create a new project or select existing
3. Enable Google+ API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Set Application type: Web application
6. Add authorized redirect URI: http://localhost:8000/auth/callback/google
7. Copy Client ID and Client Secret to environment variables

🔧 MICROSOFT OAUTH SETUP:
1. Go to https://portal.azure.com/
2. Navigate to Azure Active Directory → App registrations
3. Click "New registration"
4. Set Name: "YMCA Volunteer PathFinder"
5. Set Redirect URI: http://localhost:8000/auth/callback/microsoft
6. After creation, go to "Certificates & secrets"
7. Create a new client secret
8. Copy Application (client) ID and client secret to environment variables

🔧 SUPABASE SETUP:
1. Go to https://supabase.com/
2. Create a new project
3. Go to Settings → API
4. Copy Project URL and anon public key to environment variables
5. Run the SQL commands from database.py to create tables
    """)
    
    # Test database connection
    print_section("Database Test")
    
    try:
        from database import VolunteerDatabase
        db = VolunteerDatabase()
        if db._is_available():
            print("✅ Database connection successful")
        else:
            print("❌ Database not available - check Supabase credentials")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    # Test OAuth endpoints
    print_section("OAuth Endpoints Test")
    
    try:
        from config import settings
        
        if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            print("✅ Google OAuth configured")
        else:
            print("❌ Google OAuth not configured")
        
        if settings.MICROSOFT_CLIENT_ID and settings.MICROSOFT_CLIENT_SECRET:
            print("✅ Microsoft OAuth configured")
        else:
            print("❌ Microsoft OAuth not configured")
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    # Final instructions
    print_section("Next Steps")
    
    if not missing_vars:
        print("""
🚀 READY TO START:
1. Install dependencies: pip install -r requirements.txt
2. Start the server: python main.py
3. Open http://localhost:8000 in your browser
4. Click "Sign In to Start" to test SSO
5. Try both Google and Microsoft authentication

📝 TESTING:
- Test login flow with both providers
- Verify user data is stored in database
- Test chat functionality with authenticated users
- Test logout functionality
        """)
    else:
        print("""
⚠️  CONFIGURATION NEEDED:
Please set the missing environment variables and run this script again.
        """)
    
    print_header("Setup Complete")

if __name__ == "__main__":
    main()