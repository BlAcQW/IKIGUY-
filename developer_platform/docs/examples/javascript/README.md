# JavaScript Examples for KasaAI Developer Platform

Complete JavaScript/Node.js examples demonstrating how to use the KasaAI API.

## Prerequisites

- Node.js 16 or higher
- npm or yarn package manager
- KasaAI API key (get one at [developer.ailabsafrica.com](https://developer.ailabsafrica.com))

## Setup

1. **Install dependencies (if needed):**

The examples use native `fetch` API (available in Node.js 18+). For older versions, install `node-fetch`:

```bash
npm install node-fetch
```

2. **Set your API key as an environment variable:**

```bash
export KASAAI_API_KEY=your_api_key_here
```

Or create a `.env` file:
```
KASAAI_API_KEY=your_api_key_here
```

For `.env` file support, install `dotenv`:
```bash
npm install dotenv
```

And add to your script:
```javascript
require('dotenv').config();
```

## Available Examples

### 1. Create an Assistant (`create_assistant.js`)

Create a new voice assistant with custom configuration.

```bash
node create_assistant.js
```

**Features:**
- Creates a customer service assistant
- Creates a sales assistant with custom settings
- Error handling and validation

### 2. List Assistants (`list_assistants.js`)

Retrieve a list of all your voice assistants.

```bash
node list_assistants.js
```

**Features:**
- Lists all assistants with pagination
- Gets details for specific assistant
- Displays summary information

### 3. Initiate a Call (`initiate_call.js`)

Start an outbound call using your assistant.

```bash
node initiate_call.js <assistant_id> <phone_number>
```

**Example:**
```bash
node initiate_call.js asst_123abc +1234567890
```

**Features:**
- Initiates outbound calls
- Monitors call status in real-time
- Displays call details and duration

### 4. Create a Workflow (`create_workflow.js`)

Create an n8n workflow for automation.

```bash
node create_workflow.js
```

**Features:**
- Creates a webhook-triggered workflow
- Adds processing nodes
- Activates the workflow

### 5. Execute a Workflow (`execute_workflow.js`)

Execute an n8n workflow.

```bash
node execute_workflow.js <workflow_id>
```

**Example:**
```bash
node execute_workflow.js wf_123abc
```

**Features:**
- Executes workflows with data
- Monitors execution status
- Retrieves execution results

### 6. Check Usage (`check_usage.js`)

Check your API usage and quota.

```bash
node check_usage.js
```

**Features:**
- Displays current usage
- Shows remaining quota
- Rate limit information
- Usage breakdown by endpoint

## Using in Your Project

### Basic Usage

```javascript
const KASAAI_API_KEY = process.env.KASAAI_API_KEY;
const BASE_URL = 'https://developer.ailabsafrica.com';

async function createAssistant() {
  const response = await fetch(`${BASE_URL}/api/v1/assistants`, {
    method: 'POST',
    headers: {
      'X-API-Key': KASAAI_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      name: 'My Assistant',
      system_prompt: 'You are a helpful assistant.',
      voice: 'alloy',
      language: 'en',
      model: 'gpt-4o-mini',
      provider: 'openai'
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}
```

### With Error Handling

```javascript
async function apiRequest(endpoint, options = {}) {
  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'X-API-Key': KASAAI_API_KEY,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error.message);
    throw error;
  }
}

// Usage
const assistant = await apiRequest('/api/v1/assistants', {
  method: 'POST',
  body: JSON.stringify({ name: 'Test', ... })
});
```

### TypeScript Usage

```typescript
interface Assistant {
  id: string;
  name: string;
  status: string;
  created_at: string;
  system_prompt: string;
  voice: string;
  language: string;
}

interface CreateAssistantRequest {
  name: string;
  system_prompt: string;
  voice: string;
  language: string;
  model: string;
  provider: string;
}

async function createAssistant(
  data: CreateAssistantRequest
): Promise<Assistant> {
  const response = await fetch(`${BASE_URL}/api/v1/assistants`, {
    method: 'POST',
    headers: {
      'X-API-Key': process.env.KASAAI_API_KEY!,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}
```

## Response Handling

### Success Responses

```javascript
// 201 Created
{
  id: "asst_123abc",
  name: "My Assistant",
  status: "active",
  created_at: "2025-10-24T10:00:00Z",
  ...
}

// 200 OK
{
  assistants: [...],
  total: 10,
  limit: 10,
  offset: 0
}
```

### Error Responses

```javascript
// 400 Bad Request
{
  detail: {
    error: "Validation error",
    field: "name",
    message: "Name must be at least 3 characters"
  }
}

// 429 Too Many Requests
{
  detail: {
    error: "Rate limit exceeded",
    limit: "10/minute",
    retry_after: 45
  }
}
```

## Error Handling Patterns

### Try-Catch Pattern

```javascript
try {
  const assistant = await createAssistant(data);
  console.log('Success:', assistant);
} catch (error) {
  console.error('Failed:', error.message);
  // Handle error appropriately
}
```

### Promise Chain Pattern

```javascript
createAssistant(data)
  .then(assistant => {
    console.log('Success:', assistant);
    return assistant;
  })
  .catch(error => {
    console.error('Failed:', error.message);
  });
```

### Retry Pattern with Exponential Backoff

```javascript
async function retryRequest(fn, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;

      // Exponential backoff: 1s, 2s, 4s
      const delay = Math.pow(2, i) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

// Usage
const assistant = await retryRequest(() => createAssistant(data));
```

## Rate Limiting

The API enforces rate limits based on your plan:

- **Free tier**: 10 requests/minute
- **Starter tier**: 60 requests/minute
- **Professional tier**: 300 requests/minute

Handle rate limits gracefully:

```javascript
async function makeRequestWithRetry(fn) {
  try {
    return await fn();
  } catch (error) {
    if (error.message.includes('Rate limit exceeded')) {
      // Wait for retry_after seconds
      const retryAfter = error.retry_after || 60;
      console.log(`Rate limited. Retrying in ${retryAfter}s...`);
      await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
      return await fn();
    }
    throw error;
  }
}
```

## Testing

### Unit Testing with Jest

```javascript
// assistant.test.js
const { createAssistant } = require('./create_assistant');

describe('Assistant API', () => {
  test('creates assistant successfully', async () => {
    const assistant = await createAssistant();
    expect(assistant).toHaveProperty('id');
    expect(assistant.status).toBe('active');
  });

  test('handles invalid input', async () => {
    await expect(createAssistant({ name: '' })).rejects.toThrow();
  });
});
```

### Integration Testing

```javascript
// integration.test.js
describe('Full Assistant Workflow', () => {
  let assistantId;

  test('create assistant', async () => {
    const assistant = await createAssistant();
    assistantId = assistant.id;
    expect(assistantId).toBeDefined();
  });

  test('initiate call', async () => {
    const call = await initiateCall(assistantId, '+1234567890');
    expect(call.status).toBe('queued');
  });

  test('cleanup', async () => {
    await deleteAssistant(assistantId);
  });
});
```

## Best Practices

1. **Always set timeouts:**
   ```javascript
   const controller = new AbortController();
   const timeoutId = setTimeout(() => controller.abort(), 30000);

   const response = await fetch(url, {
     signal: controller.signal
   });

   clearTimeout(timeoutId);
   ```

2. **Use environment variables for sensitive data:**
   ```javascript
   const API_KEY = process.env.KASAAI_API_KEY;
   ```

3. **Validate input before API calls:**
   ```javascript
   if (!phoneNumber.match(/^\+\d{10,15}$/)) {
     throw new Error('Invalid phone number format');
   }
   ```

4. **Log requests for debugging:**
   ```javascript
   console.log(`[${new Date().toISOString()}] ${method} ${endpoint}`);
   ```

## Troubleshooting

### "fetch is not defined"
- Upgrade to Node.js 18+ or install `node-fetch`

### "KASAAI_API_KEY is not defined"
- Set environment variable: `export KASAAI_API_KEY=your_key`

### "UnhandledPromiseRejectionWarning"
- Always use try-catch with async/await or .catch() with promises

### CORS errors (browser)
- The API supports CORS for allowed origins
- Contact support to whitelist your domain

## Next Steps

- Check out the [Python examples](../python/) for server-side integrations
- Read the [API documentation](https://developer.ailabsafrica.com/docs)
- Explore the [quickstart guide](../../quickstart/)
- Try the [TypeScript examples](../typescript/) for type safety

## Support

- Documentation: https://developer.ailabsafrica.com/docs
- API Reference: https://developer.ailabsafrica.com/api/v1/docs
- Email: support@ailabsafrica.com
