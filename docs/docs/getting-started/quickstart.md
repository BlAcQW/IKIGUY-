---
sidebar_position: 2
title: Quickstart
description: Get started with KasaAI in 5 minutes
---

# Quickstart Guide

Get up and running with KasaAI in just 5 minutes. This guide will walk you through creating your first voice assistant and making your first call.

## Prerequisites

- A KasaAI account ([Sign up here](https://developer.ailabsafrica.com))
- An API key from the Developer Console
- `curl` or your favorite HTTP client

## Step 1: Get Your API Key

1. Log in to the [Developer Console](https://developer.ailabsafrica.com)
2. Navigate to **Settings → API Keys**
3. Click **Create New API Key**
4. Copy your API key (keep it secure!)

:::tip Keep Your API Key Safe
Never commit your API key to version control or share it publicly. Store it in environment variables or a secure secrets manager.
:::

## Step 2: Create Your First Assistant

Let's create a simple customer support assistant:

```bash
curl -X POST https://developer.ailabsafrica.com/api/v1/assistants \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Support Bot",
    "voice": {
      "provider": "elevenlabs",
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "stability": 0.5,
      "similarity_boost": 0.75
    },
    "model": {
      "provider": "openai",
      "model": "gpt-4",
      "temperature": 0.7,
      "max_tokens": 500
    },
    "first_message": "Hello! I'\''m your customer support assistant. How can I help you today?",
    "system_prompt": "You are a helpful customer support assistant. Be friendly, professional, and concise.",
    "language": "en-US"
  }'
```

**Response:**
```json
{
  "id": "asst_1234567890",
  "name": "Customer Support Bot",
  "voice": {
    "provider": "elevenlabs",
    "voice_id": "21m00Tcm4TlvDq8ikWAM"
  },
  "status": "active",
  "created_at": "2025-10-23T12:00:00Z"
}
```

:::success Assistant Created!
Your assistant is now ready to make calls. Save the `id` from the response - you'll need it in the next step.
:::

## Step 3: Make Your First Call

Now let's make a call using your new assistant:

```bash
curl -X POST https://developer.ailabsafrica.com/api/v1/calls \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "asst_1234567890",
    "phone_number": "+1234567890",
    "max_duration_minutes": 5,
    "metadata": {
      "customer_id": "cust_123",
      "purpose": "support"
    }
  }'
```

**Response:**
```json
{
  "id": "call_9876543210",
  "assistant_id": "asst_1234567890",
  "phone_number": "+1234567890",
  "status": "queued",
  "created_at": "2025-10-23T12:05:00Z"
}
```

:::info Call Status
Calls are processed asynchronously. The initial status is `queued`, then transitions to `ringing`, `in_progress`, and finally `completed`.
:::

## Step 4: Check Call Status

Monitor your call's progress:

```bash
curl -X GET https://developer.ailabsafrica.com/api/v1/calls/call_9876543210 \
  -H "X-API-Key: your_api_key_here"
```

**Response:**
```json
{
  "id": "call_9876543210",
  "status": "completed",
  "duration_seconds": 45,
  "cost": 0.50,
  "transcript": "Assistant: Hello! I'm your customer support assistant...",
  "recording_url": "https://recordings.kasaai.com/call_9876543210.mp3",
  "ended_at": "2025-10-23T12:06:00Z"
}
```

## Step 5: Review Usage

Check your API usage and quotas:

```bash
curl -X GET https://developer.ailabsafrica.com/api/v1/usage/summary \
  -H "X-API-Key: your_api_key_here"
```

**Response:**
```json
{
  "quota": {
    "plan": "free",
    "daily": {
      "limit": 100,
      "used": 1,
      "remaining": 99
    }
  },
  "stats": {
    "total_requests": 1,
    "total_cost": 0.50
  }
}
```

## 🎉 Success!

You've successfully:
- ✅ Created a voice assistant
- ✅ Made your first call
- ✅ Checked call status
- ✅ Reviewed your usage

## What's Next?

<div class="card-container">

### 📚 Learn More
- [Authentication Guide](/getting-started/authentication)
- [Core Concepts](/getting-started/core-concepts)
- [API Reference](/api-reference/overview)

### 🎯 Build Something
- [Customer Support Bot](/use-cases/customer-support-bot)
- [Appointment Reminders](/use-cases/appointment-reminders)
- [Lead Qualification](/use-cases/lead-qualification)

### ⚙️ Advanced Features
- [Custom Tools](/guides/voice-assistants/adding-tools)
- [Workflow Integration](/guides/workflows/creating-workflows)
- [Webhook Handlers](/guides/workflows/webhook-handlers)

</div>

## Code Examples

### Python

```python
import requests

API_KEY = "your_api_key_here"
BASE_URL = "https://developer.ailabsafrica.com/api/v1"

# Create assistant
response = requests.post(
    f"{BASE_URL}/assistants",
    headers={"X-API-Key": API_KEY},
    json={
        "name": "Customer Support Bot",
        "voice": {"provider": "elevenlabs", "voice_id": "21m00Tcm4TlvDq8ikWAM"},
        "model": {"provider": "openai", "model": "gpt-4"},
        "first_message": "Hello! How can I help you?",
    }
)
assistant = response.json()

# Make call
call_response = requests.post(
    f"{BASE_URL}/calls",
    headers={"X-API-Key": API_KEY},
    json={
        "assistant_id": assistant["id"],
        "phone_number": "+1234567890",
    }
)
print(call_response.json())
```

### Node.js

```javascript
const axios = require('axios');

const API_KEY = 'your_api_key_here';
const BASE_URL = 'https://developer.ailabsafrica.com/api/v1';

// Create assistant
const assistant = await axios.post(
  `${BASE_URL}/assistants`,
  {
    name: 'Customer Support Bot',
    voice: { provider: 'elevenlabs', voice_id: '21m00Tcm4TlvDq8ikWAM' },
    model: { provider: 'openai', model: 'gpt-4' },
    first_message: 'Hello! How can I help you?',
  },
  { headers: { 'X-API-Key': API_KEY } }
);

// Make call
const call = await axios.post(
  `${BASE_URL}/calls`,
  {
    assistant_id: assistant.data.id,
    phone_number: '+1234567890',
  },
  { headers: { 'X-API-Key': API_KEY } }
);

console.log(call.data);
```

### PHP

```php
<?php
$apiKey = 'your_api_key_here';
$baseUrl = 'https://developer.ailabsafrica.com/api/v1';

// Create assistant
$ch = curl_init("$baseUrl/assistants");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'X-API-Key: ' . $apiKey,
    'Content-Type: application/json'
]);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
    'name' => 'Customer Support Bot',
    'voice' => ['provider' => 'elevenlabs', 'voice_id' => '21m00Tcm4TlvDq8ikWAM'],
    'model' => ['provider' => 'openai', 'model' => 'gpt-4'],
    'first_message' => 'Hello! How can I help you?'
]));

$assistant = json_decode(curl_exec($ch), true);
curl_close($ch);

// Make call
$ch = curl_init("$baseUrl/calls");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'X-API-Key: ' . $apiKey,
    'Content-Type: application/json'
]);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
    'assistant_id' => $assistant['id'],
    'phone_number' => '+1234567890'
]));

$call = json_decode(curl_exec($ch), true);
curl_close($ch);

print_r($call);
?>
```

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Check that your API key is correct
- Ensure you're using the `X-API-Key` header (not `Authorization`)

**422 Validation Error**
- Review the error message for missing or invalid fields
- Check that phone numbers are in E.164 format (+1234567890)

**429 Rate Limit Exceeded**
- You've exceeded your plan's rate limit
- Wait a moment and try again, or upgrade your plan

**500 Internal Server Error**
- This is on our end - check [status.ailabsafrica.com](https://status.ailabsafrica.com)
- Contact support if the issue persists

## Getting Help

- **Documentation:** You're reading it! 📚
- **Discord Community:** [Join here](https://discord.gg/kasaai) 💬
- **Email Support:** support@ailabsafrica.com 📧
- **Status Page:** [status.ailabsafrica.com](https://status.ailabsafrica.com) 📊

---

Ready to dive deeper? Check out [Core Concepts](/getting-started/core-concepts) to learn how KasaAI works under the hood.
