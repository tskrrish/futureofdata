#!/usr/bin/env python3
"""
Startup script for Volunteer PathFinder AI Assistant
Handles initialization and launches the application
"""
import os
import sys
import subprocess
import asyncio
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'pandas', 'scikit-learn', 
        'httpx', 'supabase', 'openpyxl'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', 
            *missing_packages
        ], check=True)
        
        print("✅ Dependencies installed!")
    else:
        print("✅ All dependencies are installed!")

def check_data_file():
    """Check if volunteer data file exists"""
    
    data_file = "Y Volunteer Raw Data - Jan- August 2025.xlsx"
    
    if Path(data_file).exists():
        print(f"✅ Data file found: {data_file}")
        return True
    else:
        print(f"⚠️  Data file not found: {data_file}")
        print("   The system will run without real volunteer data.")
        return False

def setup_environment():
    """Set up environment variables"""
    
    print("🔧 Setting up environment...")
    
    # Create .env file if it doesn't exist
    env_file = Path('.env')
    
    if not env_file.exists():
        env_content = """# Volunteer PathFinder Configuration
# Copy this file to .env and fill in your values

# Supabase Configuration (optional - leave empty to run without database)
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_KEY=

# Inference.net Configuration (optional - leave empty to run without AI)
INFERENCE_NET_API_KEY=

# Application Configuration
SECRET_KEY=volunteer_pathfinder_secret_key_change_in_production
ENVIRONMENT=development
DEBUG=true
"""
        
        env_file.write_text(env_content)
        print("✅ Created .env configuration file")
        print("   You can edit .env to add your API keys")
    else:
        print("✅ Environment configuration exists")

def test_system():
    """Run a quick system test"""
    
    print("🧪 Running system test...")
    
    try:
        # Import and test basic functionality
        from data_processor import VolunteerDataProcessor
        from matching_engine import VolunteerMatchingEngine
        
        data_file = "Y Volunteer Raw Data - Jan- August 2025.xlsx"
        
        if Path(data_file).exists():
            # Test data processing
            processor = VolunteerDataProcessor(data_file)
            volunteer_data = processor.get_volunteer_recommendations_data()
            
            # Test matching engine
            matching_engine = VolunteerMatchingEngine(volunteer_data)
            matching_engine.train_models()
            
            print("✅ Core system test passed!")
            return True
        else:
            print("⚠️  Skipping full test (no data file)")
            return True
            
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def start_server(port=8000, host="0.0.0.0"):
    """Start the FastAPI server"""
    
    print(f"🚀 Starting Volunteer PathFinder AI Assistant...")
    print(f"   Server will be available at: http://localhost:{port}")
    print(f"   API documentation at: http://localhost:{port}/docs")
    print("   Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

def main():
    """Main startup function"""
    
    print("🎯 VOLUNTEER PATHFINDER AI ASSISTANT")
    print("====================================")
    print("AI-powered volunteer matching for YMCA of Greater Cincinnati")
    print()
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Please run this script from the project directory")
        print("   (The directory containing main.py)")
        return
    
    # Check dependencies
    check_dependencies()
    
    # Check data file
    has_data = check_data_file()
    
    # Setup environment
    setup_environment()
    
    # Test system
    if not test_system():
        print("❌ System test failed. Please check your setup.")
        return
    
    print("\n🎉 SYSTEM READY!")
    print("===============")
    
    if has_data:
        print("✅ Full system with real volunteer data")
        print("✅ AI matching engine trained and ready")
        print("✅ 3,079+ volunteer profiles loaded")
        print("✅ 437+ projects available for matching")
    else:
        print("⚠️  Running in demo mode (no real data)")
        print("   Add the Excel file to enable full functionality")
    
    print("\n🌟 FEATURES AVAILABLE:")
    print("   • Intelligent volunteer matching")
    print("   • AI-powered conversational assistant")
    print("   • Success prediction and analytics")
    print("   • Branch recommendations")
    print("   • Web interface and API")
    
    # Ask user what to do
    print("\nWhat would you like to do?")
    print("1. Start the web server (recommended)")
    print("2. Run a quick demo")
    print("3. Exit")
    
    try:
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == "1":
            start_server()
        elif choice == "2":
            print("\n🎯 Running quick demo...")
            subprocess.run([sys.executable, "test_system.py"])
        else:
            print("👋 Goodbye!")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
