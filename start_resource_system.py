#!/usr/bin/env python3
"""
Resource/Equipment Assignment System Startup Script
Starts both the backend API and frontend development servers for the resource management feature
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def main():
    """Start the resource management system"""
    print("🚀 Starting Resource/Equipment Assignment System")
    print("=" * 60)
    
    # Get the repository root
    repo_root = Path(__file__).parent
    
    # Backend directory (project 3)
    backend_dir = repo_root / "3"
    frontend_dir = repo_root / "1"
    
    # Check if directories exist
    if not backend_dir.exists():
        print("❌ Backend directory not found at:", backend_dir)
        sys.exit(1)
        
    if not frontend_dir.exists():
        print("❌ Frontend directory not found at:", frontend_dir)
        sys.exit(1)
    
    processes = []
    
    try:
        # Start backend API server
        print("🔧 Starting Backend API Server...")
        print(f"   Working directory: {backend_dir}")
        
        # Check if we have the resource API file
        resource_api_path = backend_dir / "resource_api.py"
        if resource_api_path.exists():
            backend_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "resource_api:app",
                "--reload", "--host", "0.0.0.0", "--port", "8000"
            ], cwd=backend_dir)
            processes.append(("Backend API", backend_process))
            print("✅ Backend API server started on http://localhost:8000")
        else:
            print("⚠️  Resource API file not found, starting basic main.py instead...")
            backend_process = subprocess.Popen([
                sys.executable, "main.py"
            ], cwd=backend_dir)
            processes.append(("Backend", backend_process))
        
        # Give backend time to start
        time.sleep(2)
        
        # Start frontend development server
        print("\n🌐 Starting Frontend Development Server...")
        print(f"   Working directory: {frontend_dir}")
        
        # Check if we have package.json
        package_json_path = frontend_dir / "package.json"
        if package_json_path.exists():
            # Try to install dependencies first
            print("📦 Installing frontend dependencies...")
            npm_install = subprocess.run(["npm", "install"], cwd=frontend_dir, capture_output=True)
            if npm_install.returncode != 0:
                print("⚠️  npm install failed, but continuing...")
            
            frontend_process = subprocess.Popen([
                "npm", "run", "dev"
            ], cwd=frontend_dir)
            processes.append(("Frontend Dev Server", frontend_process))
            print("✅ Frontend development server starting on http://localhost:5173")
        else:
            print("❌ package.json not found in frontend directory")
            
        print("\n" + "=" * 60)
        print("🎉 Resource Management System is starting up!")
        print()
        print("📍 Available endpoints:")
        print("   • Frontend:     http://localhost:5173")
        print("   • Backend API:  http://localhost:8000")
        print("   • API Docs:     http://localhost:8000/docs")
        print()
        print("📚 Features available:")
        print("   • Shift Management")
        print("   • Resource/Equipment Inventory")
        print("   • Resource Assignment to Shifts")
        print("   • Usage Tracking & Analytics")
        print("   • Maintenance Scheduling")
        print()
        print("💡 Navigate to the 'Resources & Shifts' tab in the web interface")
        print()
        print("Press Ctrl+C to stop all servers")
        print("=" * 60)
        
        # Wait for KeyboardInterrupt
        try:
            while True:
                time.sleep(1)
                # Check if any process has died
                for name, process in processes:
                    if process.poll() is not None:
                        print(f"⚠️  {name} process has stopped unexpectedly")
        except KeyboardInterrupt:
            print("\n🛑 Shutting down servers...")
            
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        
    finally:
        # Clean up processes
        for name, process in processes:
            try:
                print(f"   Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   Force killing {name}...")
                process.kill()
            except Exception as e:
                print(f"   Error stopping {name}: {e}")
        
        print("✅ All servers stopped")
        print("👋 Thanks for using the Resource Management System!")

if __name__ == "__main__":
    main()