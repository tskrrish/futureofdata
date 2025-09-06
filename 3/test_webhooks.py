#!/usr/bin/env python3
"""
Test script for webhook functionality
Tests the Zapier/Make webhook integration
"""
import asyncio
import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# Test webhook endpoint URL (replace with your test endpoint)
TEST_WEBHOOK_URL = "https://webhook.site/unique-id"  # Use webhook.site for testing
API_BASE_URL = "http://localhost:8000"

def make_http_request(url: str, data: dict = None, method: str = "GET") -> tuple[bool, dict]:
    """Make HTTP request using urllib"""
    try:
        headers = {"Content-Type": "application/json"}
        
        if method == "POST" and data:
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=json_data, headers=headers, method=method)
        elif method == "DELETE":
            req = urllib.request.Request(url, headers=headers, method=method)
        else:
            req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            response_text = response.read().decode('utf-8')
            status_code = response.status
            
            try:
                result = json.loads(response_text) if response_text else {}
            except json.JSONDecodeError:
                result = {"response": response_text}
            
            return status_code < 400, {"status_code": status_code, "data": result}
            
    except urllib.error.HTTPError as e:
        try:
            error_text = e.read().decode('utf-8')
            error_data = json.loads(error_text) if error_text else {}
        except:
            error_data = {"error": str(e)}
        return False, {"status_code": e.code, "error": error_data}
    except Exception as e:
        return False, {"error": str(e)}

async def test_webhook_registration():
    """Test webhook registration"""
    print("🧪 Testing webhook registration...")
    
    webhook_data = {
        "webhook_id": "test-webhook-1",
        "url": TEST_WEBHOOK_URL,
        "event_types": ["volunteer.registered", "volunteer.rsvp"],
        "secret": "test-secret-key"
    }
    
    try:
        success, result = await asyncio.get_event_loop().run_in_executor(
            None, make_http_request, f"{API_BASE_URL}/api/webhooks/register", webhook_data, "POST"
        )
        
        if success:
            print(f"✅ Webhook registered: {result}")
            return True
        else:
            print(f"❌ Registration failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False

async def test_volunteer_registration_webhook():
    """Test volunteer registration webhook trigger"""
    print("🧪 Testing volunteer registration webhook...")
    
    async with httpx.AsyncClient() as client:
        volunteer_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "555-1234",
            "age": 25,
            "city": "Cincinnati",
            "state": "OH",
            "is_ymca_member": True,
            "member_branch": "Blue Ash"
        }
        
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/webhooks/trigger/volunteer-registered",
                json=volunteer_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Volunteer registration webhook triggered: {result}")
                return True
            else:
                print(f"❌ Volunteer webhook failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Volunteer webhook error: {e}")
            return False

async def test_rsvp_webhook():
    """Test volunteer RSVP webhook trigger"""
    print("🧪 Testing volunteer RSVP webhook...")
    
    async with httpx.AsyncClient() as client:
        rsvp_data = {
            "volunteer_id": "123e4567-e89b-12d3-a456-426614174000",
            "volunteer_name": "John Doe",
            "volunteer_email": "john@example.com",
            "project_id": "proj-456",
            "project_name": "Community Garden Cleanup",
            "branch": "Blue Ash",
            "event_date": "2025-10-15",
            "rsvp_status": "confirmed",
            "hours_pledged": 4.0
        }
        
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/webhooks/trigger/volunteer-rsvp",
                json=rsvp_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ RSVP webhook triggered: {result}")
                return True
            else:
                print(f"❌ RSVP webhook failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ RSVP webhook error: {e}")
            return False

async def test_webhook_stats():
    """Test webhook statistics endpoint"""
    print("🧪 Testing webhook stats...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_BASE_URL}/api/webhooks/stats",
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Webhook stats: {json.dumps(result, indent=2)}")
                return True
            else:
                print(f"❌ Stats failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Stats error: {e}")
            return False

async def test_webhook_test_endpoint():
    """Test the webhook test endpoint"""
    print("🧪 Testing webhook test endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/webhooks/test-webhook-1/test",
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Webhook test: {result}")
                return True
            else:
                print(f"❌ Webhook test failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Webhook test error: {e}")
            return False

async def cleanup_test_webhook():
    """Clean up test webhook"""
    print("🧹 Cleaning up test webhook...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{API_BASE_URL}/api/webhooks/test-webhook-1",
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Webhook cleanup: {result}")
                return True
            else:
                print(f"❌ Cleanup failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
            return False

async def main():
    """Run all webhook tests"""
    print("🚀 Starting webhook tests...")
    print(f"📡 Using API base URL: {API_BASE_URL}")
    print(f"🎯 Using test webhook URL: {TEST_WEBHOOK_URL}")
    print()
    
    tests = [
        ("Webhook Registration", test_webhook_registration),
        ("Webhook Stats", test_webhook_stats),
        ("Volunteer Registration Webhook", test_volunteer_registration_webhook),
        ("RSVP Webhook", test_rsvp_webhook),
        ("Webhook Test Endpoint", test_webhook_test_endpoint),
        ("Cleanup", cleanup_test_webhook),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            success = await test_func()
            if success:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED with exception: {e}")
        
        # Small delay between tests
        await asyncio.sleep(0.5)
    
    print(f"\n🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All webhook tests passed!")
    else:
        print("⚠️  Some webhook tests failed. Check the output above for details.")
    
    return failed == 0

if __name__ == "__main__":
    print("=" * 60)
    print("🎯 YMCA Volunteer PathFinder - Webhook Test Suite")
    print("=" * 60)
    
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        exit(1)