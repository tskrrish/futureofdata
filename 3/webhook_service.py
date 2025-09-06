"""
Webhook Service for Zapier/Make Integration
Handles webhook triggers for volunteer and RSVP events
"""
import asyncio
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import hmac
import hashlib
import base64

logger = logging.getLogger(__name__)

@dataclass
class WebhookEvent:
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    webhook_id: Optional[str] = None

class WebhookConfig:
    def __init__(self, url: str, event_types: List[str], active: bool = True, 
                 secret: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        self.url = url
        self.event_types = event_types
        self.active = active
        self.secret = secret
        self.headers = headers or {}

class WebhookService:
    def __init__(self):
        self.webhooks: Dict[str, WebhookConfig] = {}
    
    async def register_webhook(self, webhook_id: str, config: WebhookConfig) -> bool:
        """Register a new webhook endpoint"""
        try:
            self.webhooks[webhook_id] = config
            logger.info(f"Registered webhook {webhook_id} for events: {config.event_types}")
            return True
        except Exception as e:
            logger.error(f"Failed to register webhook {webhook_id}: {e}")
            return False
    
    async def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook endpoint"""
        try:
            if webhook_id in self.webhooks:
                del self.webhooks[webhook_id]
                logger.info(f"Unregistered webhook {webhook_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister webhook {webhook_id}: {e}")
            return False
    
    async def trigger_webhook(self, event: WebhookEvent) -> Dict[str, Any]:
        """Trigger all registered webhooks for a specific event type"""
        results = {}
        
        for webhook_id, config in self.webhooks.items():
            if not config.active or event.event_type not in config.event_types:
                continue
            
            try:
                result = await self._send_webhook(webhook_id, config, event)
                results[webhook_id] = result
            except Exception as e:
                logger.error(f"Failed to send webhook {webhook_id}: {e}")
                results[webhook_id] = {"success": False, "error": str(e)}
        
        return results
    
    async def _send_webhook(self, webhook_id: str, config: WebhookConfig, event: WebhookEvent) -> Dict[str, Any]:
        """Send webhook to a specific endpoint"""
        payload = {
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "data": event.data,
            "webhook_id": webhook_id
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "YMCA-VolunteerPathfinder-Webhook/1.0"
        }
        
        if config.headers:
            headers.update(config.headers)
        
        if config.secret:
            message = json.dumps(payload, sort_keys=True).encode('utf-8')
            signature = hmac.new(
                config.secret.encode('utf-8'),
                message,
                hashlib.sha256
            ).digest()
            headers["X-Webhook-Signature"] = base64.b64encode(signature).decode('utf-8')
        
        try:
            # Run in thread pool to avoid blocking
            return await asyncio.get_event_loop().run_in_executor(
                None, self._send_sync_webhook, config.url, payload, headers
            )
            
        except Exception as e:
            return {"success": False, "error": f"Request error: {str(e)}"}
    
    def _send_sync_webhook(self, url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        """Synchronous webhook sending using urllib"""
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_text = response.read().decode('utf-8')[:500]
                return {
                    "success": response.status < 400,
                    "status_code": response.status,
                    "response": response_text
                }
                
        except urllib.error.HTTPError as e:
            return {
                "success": False,
                "status_code": e.code,
                "error": f"HTTP Error: {e.code} - {e.reason}"
            }
        except urllib.error.URLError as e:
            return {"success": False, "error": f"URL Error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Request error: {str(e)}"}
    
    async def test_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Send a test event to a webhook"""
        if webhook_id not in self.webhooks:
            return {"success": False, "error": "Webhook not found"}
        
        test_event = WebhookEvent(
            event_type="test",
            data={"message": "This is a test webhook from YMCA Volunteer PathFinder"},
            timestamp=datetime.now(),
            webhook_id=webhook_id
        )
        
        config = self.webhooks[webhook_id]
        return await self._send_webhook(webhook_id, config, test_event)
    
    def get_webhook_stats(self) -> Dict[str, Any]:
        """Get webhook statistics"""
        active_webhooks = sum(1 for config in self.webhooks.values() if config.active)
        
        event_types = set()
        for config in self.webhooks.values():
            event_types.update(config.event_types)
        
        return {
            "total_webhooks": len(self.webhooks),
            "active_webhooks": active_webhooks,
            "supported_event_types": list(event_types)
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        # No cleanup needed for urllib
        pass

webhook_service = WebhookService()