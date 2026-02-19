# Handle Webhooks

This guide will help you set up and handle webhooks from the KasaAI platform to receive real-time updates about events.

## What You'll Learn

By the end of this guide, you'll understand:
- ✅ What webhooks are and why they're useful
- ✅ How to set up webhook endpoints
- ✅ How to handle different event types
- ✅ How to secure webhook endpoints

---

## What Are Webhooks?

**Webhooks** are HTTP callbacks that allow our platform to notify your application about events in real-time.

**Instead of polling:**
```
Your App → API: "Are there new events?" (every 5 seconds)
API → Your App: "No" / "Yes, here they are"
```

**Webhooks push data to you:**
```
Event occurs → API → Your App: "Here's what happened!"
```

**Common Use Cases:**
- Call status updates (started, completed, failed)
- Workflow execution results
- Transcript availability
- Recording ready notifications
- Usage threshold alerts

---

## Prerequisites

- ✅ KasaAI API key ([get one here](https://developer.ailabsafrica.com))
- ✅ A publicly accessible HTTPS endpoint
- ✅ Python, Node.js, or any web framework
- ✅ Basic understanding of HTTP requests

---

## Step 1: Create a Webhook Endpoint

Your webhook endpoint is a URL on your server that receives HTTP POST requests from our platform.

### Using Python (Flask)

```python
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

# Your webhook secret (get from dashboard)
WEBHOOK_SECRET = "whsec_abc123..."

@app.route('/webhooks/kasaai', methods=['POST'])
def handle_webhook():
    # Verify webhook signature (security!)
    signature = request.headers.get('X-KasaAI-Signature')
    if not verify_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 401

    # Get the event data
    event = request.json
    event_type = event.get('type')

    print(f"📥 Received webhook: {event_type}")

    # Handle different event types
    if event_type == 'call.completed':
        handle_call_completed(event['data'])
    elif event_type == 'call.failed':
        handle_call_failed(event['data'])
    elif event_type == 'workflow.completed':
        handle_workflow_completed(event['data'])
    elif event_type == 'transcript.ready':
        handle_transcript_ready(event['data'])
    else:
        print(f"⚠️  Unknown event type: {event_type}")

    # Always return 200 to acknowledge receipt
    return jsonify({'status': 'received'}), 200

def verify_signature(payload, signature):
    """Verify webhook signature for security."""
    if not signature:
        return False

    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f'sha256={expected}', signature)

def handle_call_completed(data):
    """Handle completed call event."""
    call_id = data['id']
    duration = data['duration']
    status = data['status']

    print(f"✅ Call {call_id} completed")
    print(f"   Duration: {duration}s")
    print(f"   Status: {status}")

    # Your business logic here
    # - Update database
    # - Send notification
    # - Trigger follow-up workflow

def handle_call_failed(data):
    """Handle failed call event."""
    call_id = data['id']
    error = data.get('error_message')

    print(f"❌ Call {call_id} failed")
    print(f"   Error: {error}")

    # Your business logic here
    # - Log error
    # - Alert team
    # - Retry logic

def handle_workflow_completed(data):
    """Handle workflow completion."""
    workflow_id = data['workflow_id']
    execution_id = data['id']
    result = data.get('result')

    print(f"✅ Workflow {workflow_id} completed")
    print(f"   Execution: {execution_id}")
    print(f"   Result: {result}")

def handle_transcript_ready(data):
    """Handle transcript ready event."""
    call_id = data['call_id']
    transcript_url = data['transcript_url']

    print(f"📝 Transcript ready for call {call_id}")
    print(f"   URL: {transcript_url}")

    # Your business logic here
    # - Download transcript
    # - Analyze sentiment
    # - Extract action items

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Using Node.js (Express)

```javascript
const express = require('express');
const crypto = require('crypto');

const app = express();
app.use(express.raw({ type: 'application/json' }));

// Your webhook secret (get from dashboard)
const WEBHOOK_SECRET = 'whsec_abc123...';

app.post('/webhooks/kasaai', (req, res) => {
  // Verify webhook signature (security!)
  const signature = req.headers['x-kasaai-signature'];
  if (!verifySignature(req.body, signature)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // Parse event data
  const event = JSON.parse(req.body);
  const eventType = event.type;

  console.log(`📥 Received webhook: ${eventType}`);

  // Handle different event types
  switch (eventType) {
    case 'call.completed':
      handleCallCompleted(event.data);
      break;
    case 'call.failed':
      handleCallFailed(event.data);
      break;
    case 'workflow.completed':
      handleWorkflowCompleted(event.data);
      break;
    case 'transcript.ready':
      handleTranscriptReady(event.data);
      break;
    default:
      console.log(`⚠️  Unknown event type: ${eventType}`);
  }

  // Always return 200 to acknowledge receipt
  res.status(200).json({ status: 'received' });
});

function verifySignature(payload, signature) {
  if (!signature) return false;

  const expected = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(payload)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(`sha256=${expected}`),
    Buffer.from(signature)
  );
}

function handleCallCompleted(data) {
  const { id, duration, status } = data;
  console.log(`✅ Call ${id} completed`);
  console.log(`   Duration: ${duration}s`);
  console.log(`   Status: ${status}`);

  // Your business logic here
}

function handleCallFailed(data) {
  const { id, error_message } = data;
  console.log(`❌ Call ${id} failed`);
  console.log(`   Error: ${error_message}`);

  // Your business logic here
}

function handleWorkflowCompleted(data) {
  const { workflow_id, id, result } = data;
  console.log(`✅ Workflow ${workflow_id} completed`);
  console.log(`   Execution: ${id}`);
  console.log(`   Result: ${result}`);

  // Your business logic here
}

function handleTranscriptReady(data) {
  const { call_id, transcript_url } = data;
  console.log(`📝 Transcript ready for call ${call_id}`);
  console.log(`   URL: ${transcript_url}`);

  // Your business logic here
}

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`🚀 Webhook server running on port ${PORT}`);
});
```

---

## Step 2: Make Your Endpoint Public

Your webhook endpoint must be accessible from the internet.

### Local Development with ngrok

For testing, use [ngrok](https://ngrok.com) to expose your local server:

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com/download

# Start your webhook server
python webhook_server.py  # or node webhook_server.js

# In another terminal, expose port 5000
ngrok http 5000
```

**ngrok will give you a public URL:**
```
Forwarding   https://abc123.ngrok.io -> http://localhost:5000
```

Use `https://abc123.ngrok.io/webhooks/kasaai` as your webhook URL.

### Production Deployment

For production, deploy to:
- **AWS Lambda** (serverless)
- **Google Cloud Functions** (serverless)
- **Heroku** (easy deployment)
- **DigitalOcean** (VPS)
- **Vercel/Netlify** (serverless functions)

**Requirements:**
- ✅ HTTPS (required for security)
- ✅ Fast response (< 5 seconds)
- ✅ High availability (99.9% uptime)

---

## Step 3: Register Your Webhook

Tell the KasaAI platform where to send webhooks:

### Via API

```bash
curl -X POST "https://developer.ailabsafrica.com/api/v1/webhooks" \
  -H "X-API-Key: $KASAAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.com/webhooks/kasaai",
    "events": [
      "call.started",
      "call.completed",
      "call.failed",
      "workflow.completed",
      "transcript.ready"
    ],
    "description": "Production webhook endpoint"
  }'
```

**Response:**
```json
{
  "id": "wh_abc123",
  "url": "https://your-domain.com/webhooks/kasaai",
  "secret": "whsec_xyz789...",
  "events": ["call.started", "call.completed", ...],
  "active": true,
  "created_at": "2025-10-24T10:00:00Z"
}
```

**📝 Save the `secret` - you'll need it to verify webhook signatures!**

### Via Dashboard

1. Go to [developer.ailabsafrica.com/webhooks](https://developer.ailabsafrica.com/webhooks)
2. Click **Add Webhook**
3. Enter your URL
4. Select events to subscribe to
5. Click **Save**
6. Copy the webhook secret

---

## Step 4: Test Your Webhook

### Manual Test with cURL

```bash
curl -X POST "https://your-domain.com/webhooks/kasaai" \
  -H "Content-Type: application/json" \
  -H "X-KasaAI-Signature: test_signature" \
  -d '{
    "type": "call.completed",
    "id": "evt_test123",
    "created_at": "2025-10-24T10:00:00Z",
    "data": {
      "id": "call_abc123",
      "assistant_id": "asst_xyz789",
      "status": "completed",
      "duration": 245,
      "phone_number": "+1234567890",
      "started_at": "2025-10-24T09:55:00Z",
      "ended_at": "2025-10-24T10:00:05Z"
    }
  }'
```

### Test from Dashboard

1. Go to your webhook settings
2. Click **Send Test Event**
3. Select event type
4. Click **Send**
5. Check your server logs

---

## Event Types

### Call Events

#### `call.started`
```json
{
  "type": "call.started",
  "data": {
    "id": "call_abc123",
    "assistant_id": "asst_xyz789",
    "phone_number": "+1234567890",
    "started_at": "2025-10-24T09:55:00Z"
  }
}
```

#### `call.completed`
```json
{
  "type": "call.completed",
  "data": {
    "id": "call_abc123",
    "assistant_id": "asst_xyz789",
    "status": "completed",
    "duration": 245,
    "phone_number": "+1234567890",
    "started_at": "2025-10-24T09:55:00Z",
    "ended_at": "2025-10-24T10:00:05Z",
    "transcript_url": "https://..."
  }
}
```

#### `call.failed`
```json
{
  "type": "call.failed",
  "data": {
    "id": "call_abc123",
    "assistant_id": "asst_xyz789",
    "phone_number": "+1234567890",
    "error_code": "no_answer",
    "error_message": "Call was not answered",
    "attempted_at": "2025-10-24T09:55:00Z"
  }
}
```

### Workflow Events

#### `workflow.completed`
```json
{
  "type": "workflow.completed",
  "data": {
    "id": "exec_abc123",
    "workflow_id": "wf_xyz789",
    "status": "success",
    "started_at": "2025-10-24T10:00:00Z",
    "finished_at": "2025-10-24T10:00:15Z",
    "execution_time": 15.2,
    "result": {
      "output": "Email sent successfully"
    }
  }
}
```

#### `workflow.failed`
```json
{
  "type": "workflow.failed",
  "data": {
    "id": "exec_abc123",
    "workflow_id": "wf_xyz789",
    "status": "error",
    "error_message": "Node 'Send Email' failed: Invalid credentials",
    "started_at": "2025-10-24T10:00:00Z",
    "failed_at": "2025-10-24T10:00:05Z"
  }
}
```

### Transcript Events

#### `transcript.ready`
```json
{
  "type": "transcript.ready",
  "data": {
    "call_id": "call_abc123",
    "transcript_url": "https://storage.ailabsafrica.com/transcripts/...",
    "language": "en",
    "duration": 245,
    "word_count": 850
  }
}
```

---

## Security Best Practices

### 1. Always Verify Signatures

**Why?** Prevents attackers from sending fake webhooks.

```python
def verify_signature(payload, signature):
    """Verify webhook came from KasaAI."""
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f'sha256={expected}', signature)
```

### 2. Use HTTPS

**Why?** Encrypts data in transit.

```bash
# ❌ Bad
http://your-domain.com/webhooks

# ✅ Good
https://your-domain.com/webhooks
```

### 3. Implement Idempotency

**Why?** Webhooks may be sent multiple times.

```python
# Track processed events
processed_events = set()

def handle_webhook(event):
    event_id = event['id']

    # Check if already processed
    if event_id in processed_events:
        print(f"⚠️  Event {event_id} already processed")
        return

    # Process event
    process_event(event)

    # Mark as processed
    processed_events.add(event_id)
```

### 4. Respond Quickly

**Why?** Slow responses may cause retries.

```python
# ❌ Bad - do heavy processing in webhook handler
@app.route('/webhook')
def webhook():
    event = request.json
    # This takes 30 seconds!
    process_heavy_work(event)
    return 'OK'

# ✅ Good - queue for async processing
@app.route('/webhook')
def webhook():
    event = request.json
    # Quick response
    queue.enqueue(process_heavy_work, event)
    return 'OK', 200
```

### 5. Keep Secrets Secret

```python
# ❌ Bad
WEBHOOK_SECRET = "whsec_abc123..."  # hardcoded

# ✅ Good
import os
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
```

---

## Retry Logic

If your endpoint doesn't respond with 2xx, we'll retry:

| Attempt | Delay     |
|---------|-----------|
| 1       | Immediate |
| 2       | 5 seconds |
| 3       | 30 seconds |
| 4       | 5 minutes |
| 5       | 1 hour    |

**After 5 failed attempts, the webhook is marked as failed.**

---

## Debugging Webhooks

### Check Webhook Delivery Status

```bash
curl -X GET "https://developer.ailabsafrica.com/api/v1/webhooks/wh_abc123/deliveries" \
  -H "X-API-Key: $KASAAI_API_KEY"
```

**Response:**
```json
{
  "deliveries": [
    {
      "id": "del_xyz789",
      "event_type": "call.completed",
      "status": "success",
      "status_code": 200,
      "response_body": "{\"status\": \"received\"}",
      "attempt": 1,
      "delivered_at": "2025-10-24T10:00:00Z"
    },
    {
      "id": "del_abc456",
      "event_type": "call.failed",
      "status": "failed",
      "status_code": 500,
      "error_message": "Internal Server Error",
      "attempt": 3,
      "attempted_at": "2025-10-24T10:05:00Z"
    }
  ]
}
```

### Common Issues

#### Issue: "Signature verification failed"
**Solution:** Check that your secret matches the one from the dashboard

```python
# Debug signature verification
print(f"Received signature: {signature}")
print(f"Expected signature: sha256={expected}")
```

#### Issue: "Webhooks not arriving"
**Solution:**
1. Check webhook is active in dashboard
2. Verify your URL is publicly accessible
3. Check firewall/security group settings

```bash
# Test your endpoint is reachable
curl https://your-domain.com/webhooks/kasaai
```

#### Issue: "Duplicate webhooks"
**Solution:** Implement idempotency (track processed event IDs)

#### Issue: "Slow webhook processing"
**Solution:** Use async queue (Celery, Bull, etc.)

---

## Complete Example: Call Notification System

```python
from flask import Flask, request, jsonify
from twilio.rest import Client  # For SMS notifications
import hmac
import hashlib
import os

app = Flask(__name__)

# Configuration
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
TWILIO_SID = os.getenv('TWILIO_SID')
TWILIO_TOKEN = os.getenv('TWILIO_TOKEN')
ADMIN_PHONE = os.getenv('ADMIN_PHONE')

twilio = Client(TWILIO_SID, TWILIO_TOKEN)

@app.route('/webhooks/kasaai', methods=['POST'])
def handle_webhook():
    # Verify signature
    signature = request.headers.get('X-KasaAI-Signature')
    if not verify_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 401

    event = request.json
    event_type = event.get('type')

    if event_type == 'call.completed':
        notify_call_completed(event['data'])
    elif event_type == 'call.failed':
        alert_call_failed(event['data'])

    return jsonify({'status': 'received'}), 200

def verify_signature(payload, signature):
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f'sha256={expected}', signature)

def notify_call_completed(data):
    """Send SMS notification when call completes."""
    call_id = data['id']
    duration = data['duration']
    phone = data['phone_number']

    message = f"✅ Call completed!\nID: {call_id}\nPhone: {phone}\nDuration: {duration}s"

    twilio.messages.create(
        to=ADMIN_PHONE,
        from_="+1234567890",
        body=message
    )

    print(f"📱 SMS sent to {ADMIN_PHONE}")

def alert_call_failed(data):
    """Send urgent SMS when call fails."""
    call_id = data['id']
    error = data.get('error_message')
    phone = data['phone_number']

    message = f"🚨 ALERT: Call failed!\nID: {call_id}\nPhone: {phone}\nError: {error}"

    twilio.messages.create(
        to=ADMIN_PHONE,
        from_="+1234567890",
        body=message
    )

    print(f"🚨 Alert sent to {ADMIN_PHONE}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## Next Steps

**Now that you understand webhooks:**

1. **Set up monitoring**
   - Track webhook delivery success rate
   - Monitor response times
   - Alert on failures

2. **Build integrations**
   - Send data to CRM (Salesforce, HubSpot)
   - Update spreadsheets (Google Sheets, Airtable)
   - Post to Slack/Discord

3. **Automate workflows**
   - Trigger follow-up actions
   - Update databases
   - Generate reports

4. **Scale reliably**
   - Use message queues (Redis, RabbitMQ)
   - Implement retry logic
   - Add circuit breakers

---

## Resources

- **API Reference**: [developer.ailabsafrica.com/api/v1/docs](https://developer.ailabsafrica.com/api/v1/docs)
- **Webhook Security Guide**: [security best practices](https://developer.ailabsafrica.com/docs/security)
- **ngrok Documentation**: [ngrok.com/docs](https://ngrok.com/docs)
- **Support**: support@ailabsafrica.com

---

**Congratulations!** 🎉 You now know how to handle webhooks from the KasaAI platform.

**Total time:** ~10 minutes

Ready to build more? Check out:
- [Voice Assistant Guide](./first_assistant.md)
- [Workflow Automation Guide](./first_workflow.md)
- [Code Examples](../examples/)
