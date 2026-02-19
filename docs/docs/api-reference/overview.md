---
sidebar_position: 1
title: API Overview
description: Complete reference for the KasaAI REST API
---

# API Reference

The KasaAI API is organized around REST principles. Our API has predictable resource-oriented URLs, accepts JSON-encoded request bodies, returns JSON-encoded responses, and uses standard HTTP response codes, authentication, and verbs.

## Base URL

All API requests should be made to:

```
https://developer.ailabsafrica.com/api/v1
```

## Authentication

The KasaAI API uses API keys to authenticate requests. You can view and manage your API keys in the [Developer Console](https://developer.ailabsafrica.com).

Include your API key in all requests using the `X-API-Key` header:

```bash
curl https://developer.ailabsafrica.com/api/v1/assistants \
  -H "X-API-Key: your_api_key_here"
```

:::warning Keep Your API Keys Secure
Your API keys carry many privileges, so be sure to keep them secure! Do not share your secret API keys in publicly accessible areas such as GitHub, client-side code, etc.
:::

## Request Format

All POST, PUT, and PATCH requests must include a `Content-Type: application/json` header with a JSON body:

```bash
curl -X POST https://developer.ailabsafrica.com/api/v1/assistants \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Assistant", ...}'
```

## Response Format

All responses are returned in JSON format with consistent structure:

### Success Response

```json
{
  "id": "asst_1234567890",
  "name": "My Assistant",
  "status": "active",
  "created_at": "2025-10-23T12:00:00Z",
  ...
}
```

### Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid phone number format",
    "field": "phone_number"
  },
  "request_id": "req_1234567890",
  "timestamp": "2025-10-23T12:00:00Z"
}
```

## HTTP Status Codes

KasaAI uses conventional HTTP response codes to indicate success or failure:

| Status Code | Description |
|------------|-------------|
| <span class="method-get">200</span> | **OK** - Request succeeded |
| <span class="method-post">201</span> | **Created** - Resource created successfully |
| <span class="method-put">400</span> | **Bad Request** - Invalid request format |
| <span class="method-delete">401</span> | **Unauthorized** - Invalid API key |
| <span class="method-delete">403</span> | **Forbidden** - Insufficient permissions |
| <span class="method-put">404</span> | **Not Found** - Resource not found |
| <span class="method-put">422</span> | **Validation Error** - Request validation failed |
| <span class="method-delete">429</span> | **Too Many Requests** - Rate limit exceeded |
| <span class="method-delete">500</span> | **Internal Server Error** - Something went wrong on our end |

## Rate Limiting

The API uses a token bucket rate limiting algorithm:

- **Free Plan:** 10 requests/minute, 100 requests/day
- **Starter Plan:** 60 requests/minute, 10,000 requests/month
- **Professional Plan:** 300 requests/minute, 100,000 requests/month
- **Enterprise Plan:** Custom limits

Rate limit information is included in response headers:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1635724800
```

When you exceed your rate limit, you'll receive a 429 status code:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again in 30 seconds.",
    "retry_after": 30
  }
}
```

## Pagination

List endpoints return paginated results using cursor-based pagination:

```bash
curl "https://developer.ailabsafrica.com/api/v1/assistants?limit=20&cursor=asst_abc123" \
  -H "X-API-Key: your_api_key_here"
```

**Parameters:**
- `limit` (optional): Number of items to return (default: 20, max: 100)
- `cursor` (optional): Cursor for pagination (from previous response)

**Response:**
```json
{
  "data": [
    {"id": "asst_1", ...},
    {"id": "asst_2", ...}
  ],
  "pagination": {
    "has_more": true,
    "next_cursor": "asst_xyz789",
    "total_count": 150
  }
}
```

## Idempotency

To safely retry requests without performing the same operation twice, include an `Idempotency-Key` header:

```bash
curl -X POST https://developer.ailabsafrica.com/api/v1/calls \
  -H "X-API-Key: your_api_key_here" \
  -H "Idempotency-Key: unique_key_12345" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

## Versioning

The API version is included in the URL path (`/api/v1`). We maintain backwards compatibility within major versions. Breaking changes will result in a new major version (`/api/v2`).

**Current Version:** `v1`

## Webhooks

KasaAI can send webhooks to notify your application of events:

```json
{
  "event": "call.completed",
  "data": {
    "id": "call_1234567890",
    "status": "completed",
    "duration_seconds": 120
  },
  "timestamp": "2025-10-23T12:00:00Z"
}
```

[Learn more about webhooks →](/guides/workflows/webhook-handlers)

## Metadata

Many resources support a `metadata` field for storing custom key-value pairs:

```json
{
  "assistant_id": "asst_123",
  "metadata": {
    "customer_id": "cust_456",
    "campaign": "summer_2025",
    "internal_ref": "ticket_789"
  }
}
```

Metadata is:
- Limited to 50 keys
- Keys must be strings (max 40 characters)
- Values must be strings (max 500 characters)
- Not searchable via API (use for reference only)

## Timestamps

All timestamps are returned in ISO 8601 format with UTC timezone:

```json
{
  "created_at": "2025-10-23T12:00:00Z",
  "updated_at": "2025-10-23T13:30:00Z"
}
```

## Resource IDs

Resource IDs use prefixes to indicate their type:

- `asst_` - Assistants
- `call_` - Calls
- `wf_` - Workflows
- `exec_` - Workflow Executions
- `phone_` - Phone Numbers
- `key_` - API Keys

## Testing

### Test Mode

All API keys have a test mode available. Test mode:
- Does not make real phone calls
- Does not charge your account
- Returns simulated responses
- Uses the same endpoints

To use test mode, append `_test` to your API key:

```bash
-H "X-API-Key: your_api_key_here_test"
```

### Sandbox Numbers

For testing, you can use these sandbox phone numbers:
- `+15555550100` - Always answers and completes successfully
- `+15555550101` - Always answers then hangs up after 10 seconds
- `+15555550102` - Always goes to voicemail
- `+15555550103` - Always busy signal

## SDKs & Libraries

Official SDKs are available for popular languages:

<div class="card-container">

### Python
```bash
pip install kasaai
```
[View on PyPI](https://pypi.org/project/kasaai)

### Node.js
```bash
npm install @kasaai/sdk
```
[View on npm](https://npmjs.com/package/@kasaai/sdk)

### PHP
```bash
composer require kasaai/kasaai-php
```
[View on Packagist](https://packagist.org/packages/kasaai/kasaai-php)

### Go
```bash
go get github.com/kasaai/kasaai-go
```
[View on GitHub](https://github.com/kasaai/kasaai-go)

</div>

## API Resources

### Core Resources

<div class="api-endpoint">
  <div class="api-endpoint__header">
    <span class="method-badge method-post">POST</span>
    <span class="api-endpoint__path">/assistants</span>
  </div>
  Create and manage voice assistants with custom configurations
  <br />
  [View Assistants API →](/api-reference/assistants/create-assistant)
</div>

<div class="api-endpoint">
  <div class="api-endpoint__header">
    <span class="method-badge method-post">POST</span>
    <span class="api-endpoint__path">/calls</span>
  </div>
  Initiate and manage phone calls with your assistants
  <br />
  [View Calls API →](/api-reference/calls/create-call)
</div>

<div class="api-endpoint">
  <div class="api-endpoint__header">
    <span class="method-badge method-post">POST</span>
    <span class="api-endpoint__path">/workflows</span>
  </div>
  Create automation workflows and integrate with n8n
  <br />
  [View Workflows API →](/api-reference/workflows/create-workflow)
</div>

### Analytics & Usage

<div class="api-endpoint">
  <div class="api-endpoint__header">
    <span class="method-badge method-get">GET</span>
    <span class="api-endpoint__path">/usage/summary</span>
  </div>
  Get quota status, rate limits, and usage statistics
  <br />
  [View Usage API →](/api-reference/usage/get-summary)
</div>

## Examples

### Creating an Assistant and Making a Call

```bash
# 1. Create an assistant
ASSISTANT_ID=$(curl -X POST https://developer.ailabsafrica.com/api/v1/assistants \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Bot",
    "voice": {"provider": "elevenlabs", "voice_id": "21m00Tcm4TlvDq8ikWAM"},
    "model": {"provider": "openai", "model": "gpt-4"},
    "first_message": "Hi! I'm calling about your recent inquiry."
  }' | jq -r '.id')

# 2. Make a call
curl -X POST https://developer.ailabsafrica.com/api/v1/calls \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d "{
    \"assistant_id\": \"$ASSISTANT_ID\",
    \"phone_number\": \"+1234567890\"
  }"
```

## Need Help?

- **API Status:** [status.ailabsafrica.com](https://status.ailabsafrica.com)
- **Support:** support@ailabsafrica.com
- **Discord:** [Join our community](https://discord.gg/kasaai)
- **GitHub:** [Report issues](https://github.com/ailabsafrica/kasaai)

---

Explore the full API reference using the sidebar navigation →
