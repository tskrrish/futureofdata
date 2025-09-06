"""
Example usage of the YMCA Volunteer PathFinder SMS System
This demonstrates how to use the SMS reminders, confirmations, and keyword flows
"""
import asyncio
import requests
import json
from datetime import datetime, timedelta
from sms_service import SMSService
from database import VolunteerDatabase

# Configuration for testing
API_BASE_URL = "http://localhost:8000"

async def demo_sms_system():
    """Demonstrate the SMS system functionality"""
    
    print("🚀 YMCA Volunteer SMS System Demo")
    print("=" * 50)
    
    # Initialize services
    sms_service = SMSService()
    database = VolunteerDatabase()
    
    # Example user data
    user_data = {
        "first_name": "Sarah",
        "last_name": "Johnson",
        "phone": "+15551234567",  # Replace with a real test number
        "email": "sarah.johnson@example.com",
        "age": 28,
        "city": "Cincinnati",
        "is_ymca_member": True,
        "member_branch": "Blue Ash"
    }
    
    print(f"👤 Demo user: {user_data['first_name']} {user_data['last_name']}")
    print(f"📱 Phone: {user_data['phone']}")
    print()
    
    # 1. Create user with SMS welcome
    print("1️⃣ Creating user and sending welcome SMS...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/users/with-sms",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            user = response.json()["user"]
            user_id = user["id"]
            print(f"✅ User created with ID: {user_id}")
            print(f"📲 SMS welcome sent: {user.get('sms_welcome_sent', False)}")
        else:
            print(f"❌ Failed to create user: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return
    
    print()
    
    # 2. Send volunteer opportunity reminder
    print("2️⃣ Sending volunteer opportunity reminder...")
    opportunity = {
        "project_name": "Youth Basketball Coaching",
        "branch": "Blue Ash",
        "date": "Saturday, September 14",
        "time": "9:00 AM - 12:00 PM",
        "location": "Blue Ash YMCA Gymnasium",
        "contact": "Mike Smith - Youth Director"
    }
    
    reminder_data = {
        "user_id": user_id,
        "phone": user_data["phone"],
        "opportunity": opportunity
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/sms/reminder",
            json=reminder_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Reminder sent successfully")
            print(f"📋 Project: {opportunity['project_name']}")
            print(f"🏢 Branch: {opportunity['branch']}")
            print(f"📅 Date: {opportunity['date']} {opportunity['time']}")
        else:
            print(f"❌ Failed to send reminder: {response.text}")
    except Exception as e:
        print(f"❌ Error sending reminder: {e}")
    
    print()
    
    # 3. Send confirmation request
    print("3️⃣ Sending volunteer confirmation request...")
    event_details = {
        "name": "Community Garden Cleanup",
        "date": "Sunday, September 22 at 10:00 AM",
        "location": "M.E. Lyons YMCA",
        "description": "Help beautify our community garden for fall season",
        "duration": "2-3 hours",
        "what_to_bring": "Work gloves, water bottle"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/sms/confirmation",
            json={
                "user_id": user_id,
                "phone": user_data["phone"],
                "event_details": event_details
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Confirmation request sent")
            print(f"📋 Event: {event_details['name']}")
            print(f"📅 When: {event_details['date']}")
            print(f"📍 Where: {event_details['location']}")
        else:
            print(f"❌ Failed to send confirmation: {response.text}")
    except Exception as e:
        print(f"❌ Error sending confirmation: {e}")
    
    print()
    
    # 4. Simulate incoming SMS responses
    print("4️⃣ Simulating incoming SMS responses...")
    
    # Simulate different keyword responses
    test_responses = [
        {"body": "YES", "description": "Confirming availability"},
        {"body": "HELP", "description": "Requesting help"},
        {"body": "INFO", "description": "Requesting information"},
        {"body": "NO", "description": "Declining opportunity"}
    ]
    
    for response_data in test_responses:
        print(f"📱 Simulating: '{response_data['body']}' - {response_data['description']}")
        
        webhook_data = {
            "MessageSid": f"SM{datetime.now().strftime('%Y%m%d%H%M%S')}test",
            "From": user_data["phone"],
            "To": "+15551234568",  # Your Twilio number
            "Body": response_data["body"],
            "AccountSid": "AC_test_account"
        }
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/webhooks/sms",
                json=webhook_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                action = result.get("result", {}).get("action_taken", "processed")
                print(f"  ✅ Processed - Action: {action}")
            else:
                print(f"  ❌ Failed to process: {response.text}")
        except Exception as e:
            print(f"  ❌ Error processing webhook: {e}")
    
    print()
    
    # 5. Get SMS analytics
    print("5️⃣ Getting SMS analytics...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/sms/analytics?days=30")
        
        if response.status_code == 200:
            analytics = response.json()
            print("📊 SMS Analytics (Last 30 days):")
            print(f"   📤 Messages sent: {analytics.get('messages_sent', 0)}")
            print(f"   📥 Messages received: {analytics.get('messages_received', 0)}")
            print(f"   ⏰ Reminders sent: {analytics.get('reminders_sent', 0)}")
            print(f"   👥 Active subscribers: {analytics.get('active_subscribers', 0)}")
        else:
            print(f"❌ Failed to get analytics: {response.text}")
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")
    
    print()
    
    # 6. Get SMS history for user
    print("6️⃣ Getting SMS history...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/sms/history/{user_id}")
        
        if response.status_code == 200:
            history_data = response.json()
            history = history_data.get("history", [])
            count = history_data.get("count", 0)
            
            print(f"📜 SMS History for user ({count} messages):")
            for i, msg in enumerate(history[-5:], 1):  # Show last 5
                direction = "📤" if msg['direction'] == 'outbound' else "📥"
                sms_type = msg.get('sms_type', 'unknown')
                status = msg.get('status', 'unknown')
                created = msg.get('created_at', '')[:19]  # Trim microseconds
                
                print(f"   {i}. {direction} {sms_type.title()} - {status} - {created}")
        else:
            print(f"❌ Failed to get history: {response.text}")
    except Exception as e:
        print(f"❌ Error getting history: {e}")
    
    print()
    print("🎉 SMS System Demo Complete!")
    print()
    print("📱 Features Demonstrated:")
    print("   • Welcome SMS for new users")
    print("   • Volunteer opportunity reminders")
    print("   • Two-way confirmation requests")
    print("   • Keyword-based response handling")
    print("   • SMS analytics and history tracking")
    print("   • Webhook processing for incoming messages")

def test_api_endpoints():
    """Test SMS API endpoints manually"""
    print("🧪 Testing SMS API Endpoints")
    print("=" * 40)
    
    # Test data
    test_phone = "+15551234567"
    
    endpoints = [
        ("GET", "/health", None, "Health check"),
        ("GET", "/api/sms/analytics", None, "SMS analytics"),
        ("GET", "/webhooks/sms", None, "SMS webhook status"),
    ]
    
    for method, endpoint, data, description in endpoints:
        print(f"Testing: {method} {endpoint} - {description}")
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE_URL}{endpoint}")
            else:
                response = requests.post(
                    f"{API_BASE_URL}{endpoint}",
                    json=data,
                    headers={"Content-Type": "application/json"}
                )
            
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✅ Success")
            else:
                print(f"  ❌ Failed: {response.text[:100]}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test-api":
        test_api_endpoints()
    else:
        # Run the full demo
        asyncio.run(demo_sms_system())
    
    print()
    print("📚 Usage Instructions:")
    print("1. Set up Twilio account and get credentials")
    print("2. Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER to environment")
    print("3. Configure webhook URL in Twilio console: <your-domain>/webhooks/sms")
    print("4. Start the FastAPI server: python main.py")
    print("5. Run this demo: python sms_example.py")
    print("6. Test individual endpoints: python sms_example.py test-api")