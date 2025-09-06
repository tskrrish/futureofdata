#!/usr/bin/env python3
"""
Simple test for webhook functionality
"""
import asyncio
from webhook_service import webhook_service, WebhookConfig, WebhookEvent
from datetime import datetime

async def test_webhook_service():
    """Test the webhook service functionality"""
    print("🧪 Testing webhook service...")
    
    # Test 1: Register a webhook
    config = WebhookConfig(
        url="https://httpbin.org/post",
        event_types=["volunteer.registered", "volunteer.rsvp"],
        secret="test-secret"
    )
    
    success = await webhook_service.register_webhook("test-webhook", config)
    print(f"✅ Webhook registration: {'SUCCESS' if success else 'FAILED'}")
    
    # Test 2: Get webhook stats
    stats = webhook_service.get_webhook_stats()
    print(f"📊 Webhook stats: {stats}")
    
    # Test 3: Test event triggering
    test_event = WebhookEvent(
        event_type="volunteer.registered",
        data={
            "volunteer_id": "123",
            "name": "Test Volunteer",
            "email": "test@example.com"
        },
        timestamp=datetime.now()
    )
    
    print("🔔 Triggering test webhook...")
    results = await webhook_service.trigger_webhook(test_event)
    print(f"📡 Webhook trigger results: {results}")
    
    # Test 4: Unregister webhook
    unregister_success = await webhook_service.unregister_webhook("test-webhook")
    print(f"🗑️  Webhook unregistration: {'SUCCESS' if unregister_success else 'FAILED'}")
    
    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_webhook_service())
        print("\n🎉 All webhook tests completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")