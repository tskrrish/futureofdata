# Zapier/Make Webhook Integration

This document explains how to use the YMCA Volunteer PathFinder webhook system to integrate with Zapier, Make, and other automation platforms.

## Overview

The webhook system allows you to trigger automated workflows when:
- New volunteers register
- Volunteers RSVP to events

## Event Types

### volunteer.registered
Triggered when a new volunteer creates a profile.

**Data structure:**
```json
{
  "event_type": "volunteer.registered",
  "timestamp": "2025-09-06T20:47:55.311360",
  "data": {
    "volunteer_id": "uuid-string",
    "email": "volunteer@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "555-1234",
    "age": 25,
    "city": "Cincinnati",
    "state": "OH",
    "is_ymca_member": true,
    "member_branch": "Blue Ash",
    "registration_timestamp": "2025-09-06T20:47:55.311360"
  },
  "webhook_id": "your-webhook-id"
}
```

### volunteer.rsvp
Triggered when a volunteer RSVPs to an event or project.

**Data structure:**
```json
{
  "event_type": "volunteer.rsvp",
  "timestamp": "2025-09-06T20:47:55.311360",
  "data": {
    "rsvp_id": "uuid-string",
    "volunteer_id": "uuid-string",
    "volunteer_name": "John Doe",
    "volunteer_email": "volunteer@example.com",
    "project_id": "proj-456",
    "project_name": "Community Garden Cleanup",
    "branch": "Blue Ash",
    "event_date": "2025-10-15",
    "rsvp_status": "confirmed",
    "hours_pledged": 4.0,
    "rsvp_timestamp": "2025-09-06T20:47:55.311360"
  },
  "webhook_id": "your-webhook-id"
}
```

## API Endpoints

### Register a Webhook
Register a new webhook endpoint to receive event notifications.

```http
POST /api/webhooks/register
```

**Request body:**
```json
{
  "webhook_id": "unique-webhook-id",
  "url": "https://hooks.zapier.com/hooks/catch/your-hook-id",
  "event_types": ["volunteer.registered", "volunteer.rsvp"],
  "secret": "optional-secret-for-signature-verification",
  "headers": {
    "Authorization": "Bearer your-token"
  }
}
```

### Unregister a Webhook
Remove a webhook registration.

```http
DELETE /api/webhooks/{webhook_id}
```

### Test a Webhook
Send a test payload to verify your webhook is working.

```http
POST /api/webhooks/{webhook_id}/test
```

### Get Webhook Statistics
View information about registered webhooks.

```http
GET /api/webhooks/stats
```

## Setting up with Zapier

1. **Create a new Zap** in Zapier
2. **Choose "Webhooks by Zapier"** as your trigger app
3. **Select "Catch Hook"** as the trigger event
4. **Copy the webhook URL** provided by Zapier
5. **Register your webhook** using the API endpoint above:

```bash
curl -X POST http://localhost:8000/api/webhooks/register \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_id": "zapier-volunteer-alerts",
    "url": "https://hooks.zapier.com/hooks/catch/12345/abcdef",
    "event_types": ["volunteer.registered", "volunteer.rsvp"]
  }'
```

6. **Test the connection** by sending a test webhook:
```bash
curl -X POST http://localhost:8000/api/webhooks/zapier-volunteer-alerts/test
```

7. **Configure your Zap actions** based on the webhook data received

## Setting up with Make (formerly Integromat)

1. **Create a new scenario** in Make
2. **Add a "Webhook" module** as your trigger
3. **Copy the webhook URL** from Make
4. **Register your webhook** using the same process as Zapier
5. **Run the scenario** and test with the test endpoint

## Security

### Webhook Signatures
If you provide a `secret` when registering your webhook, each request will include an `X-Webhook-Signature` header containing an HMAC-SHA256 signature of the payload.

To verify the signature:
```python
import hmac
import hashlib
import base64

def verify_webhook_signature(payload, signature, secret):
    expected_signature = base64.b64encode(
        hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')
    
    return hmac.compare_digest(signature, expected_signature)
```

## Example Automation Ideas

### For Volunteer Registration
- Send welcome email with volunteer handbook
- Add volunteer to CRM system
- Notify volunteer coordinator
- Add to branch-specific communication lists
- Schedule orientation session

### For Volunteer RSVP
- Send confirmation email with event details
- Add to volunteer schedule
- Update project participant counts
- Send reminder emails before event
- Track volunteer hours for reporting

## Troubleshooting

### Webhook Not Receiving Events
1. Check that your webhook is registered: `GET /api/webhooks/stats`
2. Verify the event type matches: events must be in the `event_types` array
3. Test webhook connectivity: `POST /api/webhooks/{webhook_id}/test`
4. Check webhook URL is accessible from the server

### Payload Issues
1. Ensure your endpoint accepts POST requests
2. Verify Content-Type is `application/json`
3. Check webhook signature if using secrets
4. Log incoming requests to debug payload format

## Example Webhook Handler (Python Flask)

```python
from flask import Flask, request, jsonify
import hmac
import hashlib
import base64

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.get_data(as_text=True)
    signature = request.headers.get('X-Webhook-Signature')
    
    # Verify signature if needed
    if signature and not verify_signature(payload, signature):
        return jsonify({'error': 'Invalid signature'}), 403
    
    data = request.json
    event_type = data.get('event_type')
    
    if event_type == 'volunteer.registered':
        # Handle new volunteer registration
        volunteer_data = data.get('data', {})
        print(f"New volunteer: {volunteer_data.get('first_name')} {volunteer_data.get('last_name')}")
        
    elif event_type == 'volunteer.rsvp':
        # Handle volunteer RSVP
        rsvp_data = data.get('data', {})
        print(f"RSVP from {rsvp_data.get('volunteer_name')} for {rsvp_data.get('project_name')}")
    
    return jsonify({'status': 'received'})

def verify_signature(payload, signature):
    secret = "your-webhook-secret"
    expected = base64.b64encode(
        hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(signature, expected)

if __name__ == '__main__':
    app.run(port=5000)
```

## Testing

Use the included test scripts to verify webhook functionality:

```bash
# Simple test
python3 simple_webhook_test.py

# Full API test suite (requires running server)
python3 test_webhooks.py
```