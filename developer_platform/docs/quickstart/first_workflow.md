# Trigger n8n Workflows via API

Welcome! This guide will help you create and trigger n8n workflows through the KasaAI API in just 5 minutes.

## What You'll Build

By the end of this guide, you'll have:
- ✅ A working n8n workflow
- ✅ The ability to trigger workflows via API
- ✅ Understanding of workflow automation

---

## Prerequisites

- ✅ KasaAI API key ([get one here](https://developer.ailabsafrica.com))
- ✅ Basic understanding of workflows (helpful but not required)
- ✅ `curl`, Python, or JavaScript/Node.js installed

---

## Step 1: Understand Workflows

**What is an n8n Workflow?**

A workflow is a series of automated steps that process data. Think of it like a recipe:
1. **Trigger**: Something that starts the workflow (e.g., API call, webhook, schedule)
2. **Actions**: Things the workflow does (e.g., send email, update database, call API)
3. **Output**: The result of the workflow

**Common Use Cases:**
- Send notification when a call completes
- Process form submissions
- Sync data between systems
- Generate reports
- Automate customer follow-ups

---

## Step 2: Get Your API Key

If you haven't already:

1. Go to [developer.ailabsafrica.com](https://developer.ailabsafrica.com)
2. Sign up or log in
3. Navigate to **API Keys**
4. Click **Create API Key**
5. Copy your key (it looks like: `ksa_abc123...`)

**Security Note:** Never share your API key or commit it to version control.

---

## Step 3: Create Your First Workflow

Let's create a simple workflow that receives data via webhook and sends a notification.

### Using cURL

```bash
export KASAAI_API_KEY=your_api_key_here

curl -X POST "https://developer.ailabsafrica.com/api/v1/workflows" \
  -H "X-API-Key: $KASAAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Notification Workflow",
    "nodes": [
      {
        "name": "Webhook",
        "type": "n8n-nodes-base.webhook",
        "position": [250, 300],
        "parameters": {
          "path": "notify",
          "httpMethod": "POST",
          "responseMode": "onReceived"
        }
      },
      {
        "name": "Send Email",
        "type": "n8n-nodes-base.emailSend",
        "position": [450, 300],
        "parameters": {
          "to": "notifications@example.com",
          "subject": "New Notification",
          "text": "={{ $json.message }}"
        }
      }
    ],
    "connections": {
      "Webhook": {
        "main": [[{"node": "Send Email", "type": "main", "index": 0}]]
      }
    }
  }'
```

### Using Python

```python
import requests
import os

API_KEY = os.getenv('KASAAI_API_KEY')
BASE_URL = 'https://developer.ailabsafrica.com'

workflow_data = {
    "name": "Notification Workflow",
    "nodes": [
        {
            "name": "Webhook",
            "type": "n8n-nodes-base.webhook",
            "position": [250, 300],
            "parameters": {
                "path": "notify",
                "httpMethod": "POST",
                "responseMode": "onReceived"
            }
        },
        {
            "name": "Send Email",
            "type": "n8n-nodes-base.emailSend",
            "position": [450, 300],
            "parameters": {
                "to": "notifications@example.com",
                "subject": "New Notification",
                "text": "={{ $json.message }}"
            }
        }
    ],
    "connections": {
        "Webhook": {
            "main": [[{"node": "Send Email", "type": "main", "index": 0}]]
        }
    }
}

response = requests.post(
    f'{BASE_URL}/api/v1/workflows',
    headers={
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    },
    json=workflow_data
)

if response.status_code == 201:
    workflow = response.json()
    print(f"✅ Workflow created: {workflow['id']}")
    print(f"   Name: {workflow['name']}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.json())
```

### Using JavaScript

```javascript
const API_KEY = process.env.KASAAI_API_KEY;
const BASE_URL = 'https://developer.ailabsafrica.com';

const workflowData = {
  name: 'Notification Workflow',
  nodes: [
    {
      name: 'Webhook',
      type: 'n8n-nodes-base.webhook',
      position: [250, 300],
      parameters: {
        path: 'notify',
        httpMethod: 'POST',
        responseMode: 'onReceived'
      }
    },
    {
      name: 'Send Email',
      type: 'n8n-nodes-base.emailSend',
      position: [450, 300],
      parameters: {
        to: 'notifications@example.com',
        subject: 'New Notification',
        text: '={{ $json.message }}'
      }
    }
  ],
  connections: {
    Webhook: {
      main: [[{ node: 'Send Email', type: 'main', index: 0 }]]
    }
  }
};

const response = await fetch(`${BASE_URL}/api/v1/workflows`, {
  method: 'POST',
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(workflowData)
});

if (response.ok) {
  const workflow = await response.json();
  console.log(`✅ Workflow created: ${workflow.id}`);
  console.log(`   Name: ${workflow.name}`);
} else {
  console.error(`❌ Error: ${response.status}`);
}
```

**Success Response:**
```json
{
  "id": "wf_abc123",
  "name": "Notification Workflow",
  "active": false,
  "created_at": "2025-10-24T10:00:00Z",
  "webhook_url": "https://n8n.ailabsafrica.com/webhook/notify"
}
```

**📝 Save the `workflow_id` and `webhook_url` - you'll need them!**

---

## Step 4: Activate Your Workflow

Workflows are created in inactive state. Let's activate it:

### Using cURL

```bash
WORKFLOW_ID=wf_abc123  # Replace with your workflow ID

curl -X POST "https://developer.ailabsafrica.com/api/v1/workflows/$WORKFLOW_ID/activate" \
  -H "X-API-Key: $KASAAI_API_KEY"
```

### Using Python

```python
workflow_id = "wf_abc123"  # Replace with your workflow ID

response = requests.post(
    f'{BASE_URL}/api/v1/workflows/{workflow_id}/activate',
    headers={'X-API-Key': API_KEY}
)

if response.status_code == 200:
    print("✅ Workflow activated!")
else:
    print(f"❌ Error: {response.status_code}")
```

### Using JavaScript

```javascript
const workflowId = 'wf_abc123';  // Replace with your workflow ID

const response = await fetch(
  `${BASE_URL}/api/v1/workflows/${workflowId}/activate`,
  {
    method: 'POST',
    headers: { 'X-API-Key': API_KEY }
  }
);

if (response.ok) {
  console.log('✅ Workflow activated!');
}
```

---

## Step 5: Execute Your Workflow

Now let's trigger the workflow!

### Using cURL

```bash
curl -X POST "https://developer.ailabsafrica.com/api/v1/executions" \
  -H "X-API-Key: $KASAAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "wf_abc123",
    "data": {
      "message": "Hello from the API!",
      "priority": "high"
    }
  }'
```

### Using Python

```python
execution_data = {
    "workflow_id": workflow_id,
    "data": {
        "message": "Hello from the API!",
        "priority": "high"
    }
}

response = requests.post(
    f'{BASE_URL}/api/v1/executions',
    headers={
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    },
    json=execution_data
)

if response.status_code == 201:
    execution = response.json()
    print(f"✅ Workflow executed: {execution['id']}")
    print(f"   Status: {execution['status']}")
else:
    print(f"❌ Error: {response.status_code}")
```

### Using JavaScript

```javascript
const executionData = {
  workflow_id: workflowId,
  data: {
    message: 'Hello from the API!',
    priority: 'high'
  }
};

const response = await fetch(`${BASE_URL}/api/v1/executions`, {
  method: 'POST',
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(executionData)
});

if (response.ok) {
  const execution = await response.json();
  console.log(`✅ Workflow executed: ${execution.id}`);
  console.log(`   Status: ${execution.status}`);
}
```

**Success Response:**
```json
{
  "id": "exec_xyz789",
  "workflow_id": "wf_abc123",
  "status": "running",
  "started_at": "2025-10-24T10:01:00Z"
}
```

---

## Step 6: Check Execution Status

Monitor your workflow execution:

### Using cURL

```bash
EXECUTION_ID=exec_xyz789  # Replace with your execution ID

curl -X GET "https://developer.ailabsafrica.com/api/v1/executions/$EXECUTION_ID" \
  -H "X-API-Key: $KASAAI_API_KEY"
```

**Response:**
```json
{
  "id": "exec_xyz789",
  "workflow_id": "wf_abc123",
  "status": "success",
  "started_at": "2025-10-24T10:01:00Z",
  "finished_at": "2025-10-24T10:01:05Z",
  "execution_time": 5.2,
  "data": {
    "output": "Email sent successfully"
  }
}
```

---

## Common Workflow Patterns

### 1. Data Processing Workflow

```json
{
  "name": "Process Customer Data",
  "nodes": [
    {
      "name": "Receive Data",
      "type": "n8n-nodes-base.webhook"
    },
    {
      "name": "Validate Data",
      "type": "n8n-nodes-base.function",
      "parameters": {
        "functionCode": "// Validation logic here"
      }
    },
    {
      "name": "Save to Database",
      "type": "n8n-nodes-base.postgres"
    },
    {
      "name": "Send Confirmation",
      "type": "n8n-nodes-base.emailSend"
    }
  ]
}
```

### 2. Notification Workflow

```json
{
  "name": "Call Status Notifications",
  "nodes": [
    {
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook"
    },
    {
      "name": "Check Status",
      "type": "n8n-nodes-base.switch",
      "parameters": {
        "rules": [
          { "value": "completed", "output": 0 },
          { "value": "failed", "output": 1 }
        ]
      }
    },
    {
      "name": "Success Notification",
      "type": "n8n-nodes-base.emailSend"
    },
    {
      "name": "Failure Alert",
      "type": "n8n-nodes-base.slack"
    }
  ]
}
```

### 3. Scheduled Workflow

```json
{
  "name": "Daily Report Generation",
  "nodes": [
    {
      "name": "Schedule",
      "type": "n8n-nodes-base.cron",
      "parameters": {
        "cronExpression": "0 9 * * *"
      }
    },
    {
      "name": "Fetch Data",
      "type": "n8n-nodes-base.httpRequest"
    },
    {
      "name": "Generate Report",
      "type": "n8n-nodes-base.function"
    },
    {
      "name": "Email Report",
      "type": "n8n-nodes-base.emailSend"
    }
  ]
}
```

---

## Troubleshooting

### Workflow Won't Activate

**Problem:** Workflow fails to activate
**Solution:** Check that all required node parameters are filled

```bash
# Get workflow details
curl -X GET "https://developer.ailabsafrica.com/api/v1/workflows/$WORKFLOW_ID" \
  -H "X-API-Key: $KASAAI_API_KEY"
```

### Execution Fails

**Problem:** Workflow execution returns error
**Solution:** Check execution details for error message

```bash
# Get execution details
curl -X GET "https://developer.ailabsafrica.com/api/v1/executions/$EXECUTION_ID" \
  -H "X-API-Key: $KASAAI_API_KEY"
```

### No Response from Webhook

**Problem:** Webhook doesn't trigger workflow
**Solution:** Verify webhook URL and ensure workflow is active

---

## Best Practices

1. **Name workflows descriptively**
   - ✅ "Customer Onboarding Notification"
   - ❌ "Workflow 1"

2. **Handle errors gracefully**
   - Add error handling nodes
   - Set up failure notifications
   - Log errors for debugging

3. **Test before production**
   - Use test data first
   - Monitor executions
   - Check execution logs

4. **Keep workflows simple**
   - Break complex workflows into smaller ones
   - Use clear node names
   - Document workflow purpose

5. **Monitor performance**
   - Check execution times
   - Optimize slow nodes
   - Set appropriate timeouts

---

## Next Steps

**Now that you've created your first workflow:**

1. **Explore More Examples**
   - Check out [workflow examples](../examples/python/create_workflow.py)
   - Browse n8n node documentation

2. **Integrate with Voice Assistants**
   - Trigger workflows from voice calls
   - Process call transcripts
   - Send post-call notifications

3. **Build Complex Automations**
   - Chain multiple workflows
   - Use conditional logic
   - Integrate external services

4. **Monitor and Optimize**
   - Track execution metrics
   - Identify bottlenecks
   - Improve performance

---

## Complete Example: Voice Call Follow-up

Here's a complete workflow that sends a follow-up email after a voice call:

```python
# 1. Create the workflow
follow_up_workflow = {
    "name": "Call Follow-up Workflow",
    "nodes": [
        {
            "name": "Call Webhook",
            "type": "n8n-nodes-base.webhook",
            "parameters": {
                "path": "call-ended",
                "httpMethod": "POST"
            }
        },
        {
            "name": "Extract Call Data",
            "type": "n8n-nodes-base.function",
            "parameters": {
                "functionCode": """
                const callData = items[0].json;
                return {
                    customer_name: callData.customer_name,
                    call_duration: callData.duration,
                    call_summary: callData.summary
                };
                """
            }
        },
        {
            "name": "Send Follow-up Email",
            "type": "n8n-nodes-base.emailSend",
            "parameters": {
                "to": "={{ $json.customer_email }}",
                "subject": "Thank you for your call",
                "text": "Thank you {{ $json.customer_name }} for calling us today!"
            }
        }
    ],
    "connections": {
        "Call Webhook": {
            "main": [[{"node": "Extract Call Data"}]]
        },
        "Extract Call Data": {
            "main": [[{"node": "Send Follow-up Email"}]]
        }
    }
}

# 2. Create and activate
response = requests.post(f'{BASE_URL}/api/v1/workflows', ...)
workflow_id = response.json()['id']

requests.post(f'{BASE_URL}/api/v1/workflows/{workflow_id}/activate', ...)

# 3. Trigger after a call
call_data = {
    "workflow_id": workflow_id,
    "data": {
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "duration": 245,
        "summary": "Discussed product features"
    }
}

requests.post(f'{BASE_URL}/api/v1/executions', json=call_data, ...)
```

---

## Resources

- **API Reference**: [developer.ailabsafrica.com/api/v1/docs](https://developer.ailabsafrica.com/api/v1/docs)
- **Code Examples**: [GitHub](https://github.com/ailabsafrica/kasaai-examples)
- **n8n Documentation**: [n8n.io/docs](https://n8n.io/docs)
- **Support**: support@ailabsafrica.com

---

**Congratulations!** 🎉 You've created and triggered your first n8n workflow via API.

**Total time:** ~5 minutes

Ready to build more? Check out our [Voice Assistant Guide](./first_assistant.md) to combine workflows with AI calls!
