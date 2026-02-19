# Create Your First Voice Assistant in 5 Minutes

Welcome to the KasaAI Developer Platform! This quickstart guide will help you create your first AI-powered voice assistant in just 5 minutes.

## What You'll Build

By the end of this guide, you'll have:
- ✅ A working AI voice assistant
- ✅ The ability to make and receive calls
- ✅ Understanding of the core API concepts

## Prerequisites

- **API Key**: Sign up at [developer.ailabsafrica.com](https://developer.ailabsafrica.com) to get your API key
- **Tool**: Python 3.8+, Node.js 16+, or just cURL (choose one)

## Step 1: Get Your API Key (1 minute)

1. Go to [developer.ailabsafrica.com/signup](https://developer.ailabsafrica.com/signup)
2. Sign up for a free account
3. Navigate to **Dashboard → API Keys**
4. Click **"Create New API Key"**
5. Copy your API key (it looks like `kasa_live_abc123...`)

**⚠️ Important:** Keep your API key secret! Never commit it to GitHub or expose it in client-side code.

## Step 2: Create Your First Assistant (2 minutes)

Choose your preferred language:

### Option A: Python

```python
import requests

API_KEY = "your_api_key_here"  # Replace with your actual API key
BASE_URL = "https://developer.ailabsafrica.com"

# Create an assistant
response = requests.post(
    f"{BASE_URL}/api/v1/assistants",
    headers={
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "name": "My First Assistant",
        "system_prompt": "You are a helpful assistant for a tech company. Be friendly and professional.",
        "voice": "alloy",
        "language": "en",
        "first_message": "Hello! How can I help you today?"
    }
)

if response.status_code == 201:
    assistant = response.json()
    print(f"✅ Success! Created assistant: {assistant['id']}")
    print(f"   Name: {assistant['name']}")
    print(f"   Status: {assistant['status']}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.json())
```

**Run it:**
```bash
python create_assistant.py
```

### Option B: JavaScript/Node.js

```javascript
const API_KEY = 'your_api_key_here';  // Replace with your actual API key
const BASE_URL = 'https://developer.ailabsafrica.com';

async function createAssistant() {
  const response = await fetch(`${BASE_URL}/api/v1/assistants`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'My First Assistant',
      system_prompt: 'You are a helpful assistant for a tech company. Be friendly and professional.',
      voice: 'alloy',
      language: 'en',
      first_message: 'Hello! How can I help you today?'
    })
  });

  if (response.ok) {
    const assistant = await response.json();
    console.log(`✅ Success! Created assistant: ${assistant.id}`);
    console.log(`   Name: ${assistant.name}`);
    console.log(`   Status: ${assistant.status}`);
  } else {
    const error = await response.json();
    console.error(`❌ Error: ${response.status}`);
    console.error(error);
  }
}

createAssistant();
```

**Run it:**
```bash
node create_assistant.js
```

### Option C: cURL

```bash
curl -X POST "https://developer.ailabsafrica.com/api/v1/assistants" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Assistant",
    "system_prompt": "You are a helpful assistant for a tech company. Be friendly and professional.",
    "voice": "alloy",
    "language": "en",
    "first_message": "Hello! How can I help you today?"
  }'
```

### Expected Response

```json
{
  "id": "asst_abc123xyz",
  "name": "My First Assistant",
  "status": "active",
  "voice": "alloy",
  "language": "en",
  "created_at": "2025-10-24T14:30:00Z",
  "updated_at": "2025-10-24T14:30:00Z"
}
```

**🎉 Congratulations!** You just created your first AI voice assistant!

## Step 3: Test Your Assistant (2 minutes)

Now let's make a test call with your assistant.

### Python

```python
# Using the assistant_id from Step 2
assistant_id = "asst_abc123xyz"  # Replace with your actual assistant ID

# Initiate a call
response = requests.post(
    f"{BASE_URL}/api/v1/calls",
    headers={
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "assistant_id": assistant_id,
        "phone_number": "+1234567890",  # Replace with a real phone number
        "task": "outbound"
    }
)

if response.status_code == 201:
    call = response.json()
    print(f"✅ Call initiated! Call ID: {call['id']}")
    print(f"   Status: {call['status']}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.json())
```

### JavaScript

```javascript
const assistantId = 'asst_abc123xyz';  // Replace with your actual assistant ID

async function makeCall() {
  const response = await fetch(`${BASE_URL}/api/v1/calls`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      assistant_id: assistantId,
      phone_number: '+1234567890',  // Replace with a real phone number
      task: 'outbound'
    })
  });

  if (response.ok) {
    const call = await response.json();
    console.log(`✅ Call initiated! Call ID: ${call.id}`);
    console.log(`   Status: ${call.status}`);
  } else {
    const error = await response.json();
    console.error(`❌ Error: ${response.status}`);
    console.error(error);
  }
}

makeCall();
```

### cURL

```bash
curl -X POST "https://developer.ailabsafrica.com/api/v1/calls" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: "application/json" \
  -d '{
    "assistant_id": "asst_abc123xyz",
    "phone_number": "+1234567890",
    "task": "outbound"
  }'
```

## Understanding the Response

```json
{
  "id": "call_xyz789abc",
  "assistant_id": "asst_abc123xyz",
  "status": "queued",
  "phone_number": "+1234567890",
  "type": "outbound",
  "created_at": "2025-10-24T14:35:00Z"
}
```

**Status values:**
- `queued` - Call is scheduled
- `ringing` - Phone is ringing
- `in-progress` - Call connected
- `completed` - Call ended successfully
- `failed` - Call failed

## What Just Happened?

1. ✅ You created an AI voice assistant with custom personality
2. ✅ You initiated an outbound call to a phone number
3. ✅ Your assistant will call that number and have a conversation!

## Next Steps

Now that you've created your first assistant, explore these advanced features:

### 1. List Your Assistants

```bash
curl -X GET "https://developer.ailabsafrica.com/api/v1/assistants" \
  -H "X-API-Key: your_api_key_here"
```

### 2. Check Call Status

```bash
curl -X GET "https://developer.ailabsafrica.com/api/v1/calls/call_xyz789abc" \
  -H "X-API-Key: your_api_key_here"
```

### 3. Get Usage Statistics

```bash
curl -X GET "https://developer.ailabsafrica.com/api/v1/usage/stats" \
  -H "X-API-Key: your_api_key_here"
```

### 4. Explore More Features

- **[Create n8n Workflows](./first_workflow.md)** - Automate tasks with workflows
- **[Handle Webhooks](./webhooks.md)** - Get real-time call updates
- **[API Reference](/docs/api/v1/)** - Full API documentation
- **[Code Examples](/docs/examples/)** - More complete examples

## Pricing & Rate Limits

**Free Tier:**
- 10 requests/minute
- 100 requests/hour
- 1,000 requests/day
- 1 credit per assistant created
- 10 credits per call minute

**Check your usage:**
```bash
curl -X GET "https://developer.ailabsafrica.com/api/v1/usage/quota" \
  -H "X-API-Key: your_api_key_here"
```

## Common Issues & Solutions

### Issue: "Invalid API key"
**Solution:** Double-check your API key. Make sure you copied it correctly and there are no extra spaces.

### Issue: "Rate limit exceeded"
**Solution:** You've made too many requests. Wait a minute and try again, or upgrade your plan.

### Issue: "Phone number invalid"
**Solution:** Use E.164 format: `+[country_code][number]` (e.g., `+14155552671`)

### Issue: "Insufficient credits"
**Solution:** Add credits to your account at [developer.ailabsafrica.com/billing](https://developer.ailabsafrica.com/billing)

## Need Help?

- 📚 **[Full API Documentation](../../API_DOCUMENTATION.md)**
- 💬 **[Discord Community](https://discord.gg/kasaai)**
- 📧 **[Email Support](mailto:support@ailabsafrica.com)**
- 🐛 **[Report Issues](https://github.com/ailabsafrica/kasaai/issues)**

## What's Next?

Congratulations on creating your first voice assistant! Here are some ideas for what to build next:

1. **Customer Support Bot** - Handle common customer questions
2. **Appointment Scheduler** - Book meetings via phone
3. **Survey Caller** - Conduct automated surveys
4. **Reminder Service** - Send voice reminders
5. **Lead Qualifier** - Qualify sales leads automatically

**Ready to build something amazing?** Start exploring our [full API documentation](../../API_DOCUMENTATION.md)!

---

**Estimated completion time:** ⏱️ 5 minutes

**Difficulty:** 🟢 Beginner

**Last Updated:** 2025-10-24
