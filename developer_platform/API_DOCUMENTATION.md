# KasaAI Developer Platform API Documentation

**Version:** 1.7.0
**Base URL:** `https://developer.ailabsafrica.com`
**Status:** Production
**Last Updated:** 2025-11-08

---

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Request/Response Format](#requestresponse-format)
- [Error Handling](#error-handling)
- [Voice Assistants API](#voice-assistants-api)
- [Voice Calls API](#voice-calls-api)
- [Workflows API](#workflows-api)
- [Workflow Executions API](#workflow-executions-api)
- [LLM Services API](#llm-services-api) ⭐ NEW
- [ASR Services API](#asr-services-api) ⭐ NEW
- [TTS Services API](#tts-services-api) ⭐ NEW
- [RVC Voice Conversion API](#rvc-voice-conversion-api) ⭐ NEW v1.7.0
- [RAG Service API](#rag-service-api)
- [Document Processor API](#document-processor-api)
- [Wallet Service API](#wallet-service-api) ⭐ UPDATED v1.3.0
- [Analytics Service API](#analytics-service-api) ⭐ NEW v1.3.0
- [File Storage API](#file-storage-api) ⭐ NEW v1.3.0
- [Email Account Management API](#email-account-management-api) ⭐ NEW v1.5.0
- [ERP Partnership Management API](#erp-partnership-management-api) ⭐ NEW v1.6.0
- [Phone Numbers API](#phone-numbers-api) ⭐ NEW v1.7.0
- [Usage Calculator API](#usage-calculator-api)
- [Voice Engine API](#voice-engine-api) ⭐ NEW v1.7.0
- [Code Examples](#code-examples)
- [Webhooks](#webhooks)
- [Changelog](#changelog)
- [Support](#support)

---

## Overview

The KasaAI Developer Platform provides a stable, versioned API for building voice-powered applications and automation workflows. Our API enables you to:

- **Create and manage AI voice assistants** using Vapi
- **Provision virtual phone numbers** with Asterisk PBX integration ⭐ NEW
- **Initiate and control phone calls** with real-time AI conversation
- **Build and execute automation workflows** using n8n
- **Chat with large language models** (LLMs) with automatic billing ⭐ NEW
- **Transcribe audio files** with automatic speech recognition (ASR) ⭐ NEW
- **Convert text to speech** with multiple TTS providers and voice cloning ⭐ NEW
- **Access 20+ TTS models** through comprehensive TTS-WebUI platform ⭐ NEW v1.7.0
- **Transform voices** with RVC (Retrieval-based Voice Conversion) for character transformation, anonymization, and restoration ⭐ NEW v1.7.0
- **Build intelligent Q&A systems** with RAG (Retrieval-Augmented Generation)
- **Process and extract content** from documents (PDF, DOCX, TXT, HTML)
- **Manage user wallets and payments** with multi-currency support and automatic billing ⭐ NEW
- **Track comprehensive analytics** across all services including assistant costs ⭐ NEW
- **Store and manage files** with organization-scoped cloud storage (Hetzner Storage Box) ⭐ NEW
- **Create and manage email accounts** on iRedMail server for employees and users ⭐ NEW v1.5.0
- **Manage business partnerships** with lifecycle tracking, document management, and analytics ⭐ NEW v1.6.0
- **Calculate usage costs** with tiered pricing

### Key Features

✅ **RESTful API** - Simple, predictable HTTP endpoints
✅ **Stable Versioning** - v1 API contract guaranteed stable
✅ **Comprehensive Documentation** - Detailed guides and examples
✅ **Multiple Languages** - Support for 17+ languages
✅ **Rate Limited** - Fair usage policies
✅ **Usage Tracking** - Built-in analytics and quotas

---

## Getting Started

### 1. Create an Account

Sign up at [https://developer.ailabsafrica.com/signup](https://developer.ailabsafrica.com/signup)

### 2. Get Your API Key

1. Log in to your dashboard
2. Navigate to **Settings → API Keys**
3. Click **Create New API Key**
4. Copy and securely store your API key

⚠️ **Security Warning:** Never expose your API key in client-side code or public repositories.

### 3. Make Your First Request

```bash
curl -X GET https://developer.ailabsafrica.com/api/v1/assistants \
  -H "X-API-Key: your_api_key_here"
```

---

## Authentication

All API requests require authentication using an API key.

### API Key Authentication

Include your API key in the `X-API-Key` header:

```http
X-API-Key: kasa_live_1234567890abcdef
```

### API Key Types

- **Development Keys:** `kasa_dev_*` - For testing (lower rate limits)
- **Production Keys:** `kasa_live_*` - For production use
- **Sandbox Keys:** `kasa_sandbox_*` - For integration testing (no charges)

### Best Practices

1. **Store securely** - Use environment variables or secrets managers
2. **Rotate regularly** - Rotate keys every 90 days
3. **Use separate keys** - Different keys for dev/staging/production
4. **Monitor usage** - Track API calls in your dashboard

---

## Rate Limiting

Rate limits ensure fair usage and system stability.

### Default Limits

| Plan | Rate Limit | Burst Limit |
|------|------------|-------------|
| Free | 10 requests/minute | 20 requests |
| Starter | 60 requests/minute | 100 requests |
| Professional | 600 requests/minute | 1000 requests |
| Enterprise | Custom | Custom |

### Rate Limit Headers

Every API response includes rate limit information:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1634567890
```

### Handling Rate Limits

When you exceed the rate limit, you'll receive a `429 Too Many Requests` response:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 30 seconds.",
    "field": null
  },
  "request_id": "req_abc123",
  "timestamp": "2025-10-23T12:00:00Z"
}
```

**Best Practice:** Implement exponential backoff when you receive 429 responses.

---

## Request/Response Format

### Request Format

All API requests use JSON format with UTF-8 encoding.

**Required Headers:**
```http
Content-Type: application/json
X-API-Key: your_api_key_here
```

**Example Request:**
```http
POST /api/v1/assistants HTTP/1.1
Host: developer.ailabsafrica.com
Content-Type: application/json
X-API-Key: kasa_live_1234567890abcdef

{
  "name": "Sales Assistant",
  "system_prompt": "You are a helpful sales assistant...",
  "voice": "alloy",
  "language": "en"
}
```

### Response Format

All successful responses return JSON with a standard structure:

```json
{
  "id": "asst_123abc",
  "name": "Sales Assistant",
  "status": "active",
  "voice": "alloy",
  "language": "en",
  "created_at": "2025-10-23T12:00:00Z",
  "updated_at": null,
  "metadata": {}
}
```

### Pagination

List endpoints support pagination using query parameters:

```http
GET /api/v1/assistants?limit=20&offset=0
```

**Parameters:**
- `limit` - Number of items per page (default: 10, max: 100)
- `offset` - Starting position (default: 0)

**Response:**
```json
{
  "assistants": [...],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Assistant name must be at least 3 characters",
    "field": "name"
  },
  "request_id": "req_abc123",
  "timestamp": "2025-10-23T12:00:00Z"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Invalid or missing API key |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 501 | Not Implemented | Endpoint not yet implemented |

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `AUTHENTICATION_ERROR` | Invalid API key |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `RESOURCE_NOT_FOUND` | Resource doesn't exist |
| `QUOTA_EXCEEDED` | Usage quota exceeded |
| `INTERNAL_ERROR` | Server error |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable |

---

## Voice Assistants API

Create and manage AI voice assistants powered by Vapi.

### Create Assistant

Create a new voice assistant with custom personality and voice.

**Endpoint:** `POST /api/v1/assistants`

**Request Body:**
```json
{
  "name": "Customer Support Assistant",
  "system_prompt": "You are a helpful customer support assistant. Be polite and professional.",
  "voice": "alloy",
  "language": "en",
  "speed": 1.0,
  "call_type": "both",
  "max_duration": 600,
  "silence_timeout": 10,
  "record_calls": true,
  "metadata": {
    "department": "support",
    "created_by": "api"
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Assistant name (3-100 characters) |
| `system_prompt` | string | Yes | AI behavior instructions (min 10 characters) |
| `voice` | string | No | Voice ID: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer` (default: `alloy`) |
| `language` | string | No | Language code (ISO 639-1, default: `en`) |
| `speed` | float | No | Speaking speed 0.5-2.0 (default: 1.0) |
| `call_type` | string | No | `inbound`, `outbound`, `both` (default: `both`) |
| `max_duration` | integer | No | Max call duration in seconds 30-3600 (default: 600) |
| `silence_timeout` | integer | No | Silence timeout 5-60 seconds (default: 10) |
| `record_calls` | boolean | No | Record calls (default: true) |
| `metadata` | object | No | Custom metadata (max 10 key-value pairs) |

**Response:** `201 Created`
```json
{
  "id": "asst_123abc",
  "name": "Customer Support Assistant",
  "status": "active",
  "voice": "alloy",
  "language": "en",
  "created_at": "2025-10-23T12:00:00Z",
  "updated_at": null,
  "metadata": {
    "department": "support",
    "created_by": "api"
  }
}
```

---

### List Assistants

Get a paginated list of all assistants.

**Endpoint:** `GET /api/v1/assistants`

**Query Parameters:**
- `limit` (integer, optional) - Items per page (default: 10, max: 100)
- `offset` (integer, optional) - Starting position (default: 0)

**Response:** `200 OK`
```json
{
  "assistants": [
    {
      "id": "asst_123",
      "name": "Sales Assistant",
      "status": "active",
      "voice": "alloy",
      "language": "en",
      "created_at": "2025-10-23T12:00:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

---

### Get Assistant

Retrieve details of a specific assistant.

**Endpoint:** `GET /api/v1/assistants/{assistant_id}`

**Path Parameters:**
- `assistant_id` (string, required) - Assistant ID

**Response:** `200 OK`
```json
{
  "id": "asst_123abc",
  "name": "Sales Assistant",
  "status": "active",
  "voice": "alloy",
  "language": "en",
  "created_at": "2025-10-23T12:00:00Z",
  "updated_at": null,
  "metadata": {
    "department": "sales"
  }
}
```

---

### Update Assistant

Update an existing assistant.

**Endpoint:** `PATCH /api/v1/assistants/{assistant_id}`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Request Body:** (All fields optional)
```json
{
  "name": "Updated Assistant Name",
  "system_prompt": "Updated instructions...",
  "voice": "echo",
  "speed": 1.2
}
```

---

### Delete Assistant

Delete an assistant permanently.

**Endpoint:** `DELETE /api/v1/assistants/{assistant_id}`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Response:** `200 OK`
```json
{
  "id": "asst_123abc",
  "deleted": true
}
```

---

## Voice Calls API

Initiate and manage voice calls with AI assistants.

### Initiate Call

Start an outbound call using a voice assistant.

**Endpoint:** `POST /api/v1/calls`

**Request Body:**
```json
{
  "assistant_id": "asst_123abc",
  "to_number": "+14155551234",
  "from_number": "+14155559999",
  "metadata": {
    "campaign": "summer_sale",
    "customer_id": "cust_456"
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assistant_id` | string | Yes | Assistant ID to use |
| `to_number` | string | Yes | Phone number to call (E.164 format) |
| `from_number` | string | No | Caller ID (E.164 format, uses default if not provided) |
| `metadata` | object | No | Custom call metadata |

**Phone Number Format (E.164):**
- Must start with `+`
- Country code + number
- Example: `+14155551234` (US), `+442071234567` (UK)

**Response:** `201 Created`
```json
{
  "id": "call_789xyz",
  "assistant_id": "asst_123abc",
  "to_number": "+14155551234",
  "from_number": "+14155559999",
  "status": "initiated",
  "duration": null,
  "started_at": "2025-10-23T12:05:00Z",
  "ended_at": null,
  "recording_url": null,
  "metadata": {
    "campaign": "summer_sale"
  }
}
```

**Call Status Values:**
- `initiated` - Call request created
- `ringing` - Phone is ringing
- `answered` - Call connected
- `ended` - Call completed
- `failed` - Call failed

---

### List Calls

Get a paginated list of all calls.

**Endpoint:** `GET /api/v1/calls`

**Query Parameters:**
- `limit` (integer, optional) - Items per page (default: 10, max: 100)
- `offset` (integer, optional) - Starting position (default: 0)

**Response:** `200 OK`
```json
{
  "calls": [
    {
      "id": "call_789",
      "assistant_id": "asst_123",
      "to_number": "+14155551234",
      "status": "ended",
      "duration": 120,
      "started_at": "2025-10-23T12:05:00Z",
      "ended_at": "2025-10-23T12:07:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

---

### Get Call Details

Retrieve details of a specific call.

**Endpoint:** `GET /api/v1/calls/{call_id}`

**Path Parameters:**
- `call_id` (string, required) - Call ID

**Response:** `200 OK`
```json
{
  "id": "call_789xyz",
  "assistant_id": "asst_123abc",
  "to_number": "+14155551234",
  "from_number": "+14155559999",
  "status": "ended",
  "duration": 120,
  "started_at": "2025-10-23T12:05:00Z",
  "ended_at": "2025-10-23T12:07:00Z",
  "recording_url": "https://recordings.vapi.ai/call_789xyz.mp3",
  "metadata": {}
}
```

---

## Workflows API

Create and manage automation workflows using n8n.

### Create Workflow

Create a new automation workflow.

**Endpoint:** `POST /api/v1/workflows`

**Request Body:**
```json
{
  "name": "Customer Onboarding Workflow",
  "nodes": [
    {
      "id": "webhook",
      "type": "n8n-nodes-base.webhook",
      "name": "Webhook",
      "parameters": {
        "path": "customer-signup"
      }
    }
  ],
  "connections": {},
  "active": false,
  "settings": {},
  "tags": ["customer", "onboarding"]
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Workflow name (3-100 characters) |
| `nodes` | array | Yes | Workflow nodes (1-100 nodes) |
| `connections` | object | Yes | Node connections configuration |
| `active` | boolean | No | Whether workflow is active (default: false) |
| `settings` | object | No | Workflow settings |
| `tags` | array | No | Tags for categorization |

**Response:** `201 Created`
```json
{
  "id": "wf_123abc",
  "name": "Customer Onboarding",
  "active": false,
  "created_at": "2025-10-23T12:00:00Z",
  "updated_at": "2025-10-23T12:30:00Z",
  "tags": ["customer", "onboarding"],
  "webhook_url": "https://automate.example.com/webhook/customer-signup"
}
```

---

### List Workflows

Get a paginated list of all workflows.

**Endpoint:** `GET /api/v1/workflows`

**Status:** ✅ Fully Implemented

**Query Parameters:**
- `limit` (integer, optional) - Items per page (default: 10, max: 100)
- `offset` (integer, optional) - Starting position (default: 0)

**Response:** `200 OK`
```json
{
  "workflows": [
    {
      "id": "wf_123",
      "name": "Customer Onboarding",
      "active": true,
      "created_at": "2025-10-23T12:00:00Z",
      "tags": ["customer"]
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

---

### Get Workflow

Retrieve details of a specific workflow.

**Endpoint:** `GET /api/v1/workflows/{workflow_id}`

**Path Parameters:**
- `workflow_id` (string, required) - Workflow ID

**Response:** `200 OK`
```json
{
  "id": "wf_123abc",
  "name": "Customer Onboarding",
  "active": true,
  "created_at": "2025-10-23T12:00:00Z",
  "updated_at": "2025-10-23T12:30:00Z",
  "tags": ["customer", "onboarding"],
  "webhook_url": "https://automate.example.com/webhook/customer-signup"
}
```

---

### Update Workflow

Update an existing workflow.

**Endpoint:** `PATCH /api/v1/workflows/{workflow_id}`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

---

### Delete Workflow

Delete a workflow permanently.

**Endpoint:** `DELETE /api/v1/workflows/{workflow_id}`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

---

### Activate Workflow

Activate a workflow to start processing triggers.

**Endpoint:** `POST /api/v1/workflows/{workflow_id}/activate`

**Path Parameters:**
- `workflow_id` (string, required) - Workflow ID

**Response:** `200 OK`
```json
{
  "id": "wf_123abc",
  "name": "Customer Onboarding",
  "active": true,
  "created_at": "2025-10-23T12:00:00Z",
  "updated_at": "2025-10-23T12:35:00Z",
  "tags": ["customer"],
  "webhook_url": "https://automate.example.com/webhook/customer-signup"
}
```

---

## Workflow Executions API

Execute workflows and track execution status.

### Execute Workflow

Manually execute a workflow with input data.

**Endpoint:** `POST /api/v1/executions`

**Request Body:**
```json
{
  "workflow_id": "wf_123abc",
  "data": {
    "customer_email": "user@example.com",
    "customer_name": "John Doe",
    "plan": "professional"
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `workflow_id` | string | Yes | Workflow ID to execute |
| `data` | object | No | Input data for workflow |

**Response:** `201 Created`
```json
{
  "id": "exec_789xyz",
  "workflow_id": "wf_123abc",
  "status": "success",
  "started_at": "2025-10-23T12:05:00Z",
  "finished_at": "2025-10-23T12:05:30Z",
  "duration": 30000,
  "success": true,
  "error": null
}
```

**Execution Status Values:**
- `running` - Execution in progress
- `waiting` - Waiting for external trigger
- `success` - Execution completed successfully
- `error` - Execution failed

---

### List Executions

Get a paginated list of workflow executions.

**Endpoint:** `GET /api/v1/executions`

**Status:** ✅ Fully Implemented

**Query Parameters:**
- `workflow_id` (string, optional) - Filter by workflow ID
- `limit` (integer, optional) - Items per page (default: 10, max: 100)
- `offset` (integer, optional) - Starting position (default: 0)

**Response:** `200 OK`
```json
{
  "executions": [
    {
      "id": "exec_789",
      "workflow_id": "wf_123",
      "status": "success",
      "started_at": "2025-10-23T12:05:00Z",
      "finished_at": "2025-10-23T12:05:30Z",
      "duration": 30000,
      "success": true
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

---

### Get Execution Details

Retrieve details of a specific execution.

**Endpoint:** `GET /api/v1/executions/{execution_id}`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Path Parameters:**
- `execution_id` (string, required) - Execution ID

**Response:** `200 OK`
```json
{
  "id": "exec_789xyz",
  "workflow_id": "wf_123abc",
  "status": "success",
  "started_at": "2025-10-23T12:05:00Z",
  "finished_at": "2025-10-23T12:05:30Z",
  "duration": 30000,
  "success": true,
  "error": null
}
```

---

## LLM Services API

Access large language models for chat, text generation, and AI-powered conversations with automatic billing and cost tracking.

### Chat with LLM

Send messages to an LLM and receive AI-generated responses.

**Endpoint:** `POST /api/v1/llm/chat`

**Status:** ✅ Fully Implemented

**Request Body:**
```json
{
  "model_id": "kasaai_llama_twi",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "What is the capital of Ghana?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 500,
  "top_p": 0.9,
  "stream": false
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_id` | string | Yes | LLM model ID (e.g., `kasaai_llama_twi`, `llama_32_3b`) |
| `messages` | array | Yes | Conversation messages (1-100 messages) |
| `messages[].role` | string | Yes | Message role: `system`, `user`, `assistant` |
| `messages[].content` | string | Yes | Message content (min 1 character) |
| `temperature` | float | No | Sampling temperature 0.0-2.0 (default: 0.7) |
| `max_tokens` | integer | No | Maximum tokens to generate (default: model-specific) |
| `top_p` | float | No | Nucleus sampling 0.0-1.0 (default: 0.9) |
| `stream` | boolean | No | Enable streaming (default: false) |
| `system_prompt` | string | No | Override system prompt |

**Response:** `200 OK`
```json
{
  "message": "The capital of Ghana is Accra.",
  "model_id": "kasaai_llama_twi",
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 8,
    "total_tokens": 33
  },
  "finish_reason": "stop",
  "cost": 0.0012,
  "transaction_id": "txn_abc123",
  "processing_time": 1.5
}
```

**Cost Breakdown:**
- Input tokens: $0.01 per 1000 tokens
- Output tokens: $0.02 per 1000 tokens
- Cost automatically deducted from wallet

---

### Streaming Chat

Stream LLM responses token-by-token for real-time interactions.

**Endpoint:** `POST /api/v1/llm/chat/stream`

**Status:** ✅ Fully Implemented

**Request Body:** Same as non-streaming chat with `stream: true`

**Response:** `200 OK` (Server-Sent Events)
```
data: {"content": "The", "done": false}

data: {"content": " capital", "done": false}

data: {"content": " of Ghana is Accra.", "done": true}
```

**SSE Format:**
- Each line starts with `data: `
- JSON object with `content` (token text) and `done` (boolean)
- Billing occurs after stream completes

---

### List LLM Providers

Get all available LLM models with health status.

**Endpoint:** `GET /api/v1/llm/providers`

**Status:** ✅ Fully Implemented

**Query Parameters:**
- `force_refresh` (boolean, optional) - Force health check refresh (default: false)

**Response:** `200 OK`
```json
{
  "providers": {
    "kasaai_llama_twi": {
      "id": "kasaai_llama_twi",
      "name": "Kasaai Llama Twi",
      "endpoint": "https://ollama.ailabsafrica.com",
      "status": "online",
      "last_check": "2025-10-26T12:00:00Z",
      "response_time_ms": 150,
      "error_message": null,
      "provider_type": "llm"
    },
    "llama_32_3b": {
      "id": "llama_32_3b",
      "name": "Llama 3.2 3B",
      "endpoint": "https://ollama.ailabsafrica.com",
      "status": "online",
      "last_check": "2025-10-26T12:00:00Z",
      "response_time_ms": 145,
      "error_message": null,
      "provider_type": "llm"
    }
  },
  "count": 2,
  "online_count": 2,
  "offline_count": 0
}
```

**Provider Status:**
- `online` - Model available and responding
- `offline` - Model unavailable
- `degraded` - Model responding slowly

---

### Estimate LLM Cost

Estimate cost before sending a chat request.

**Endpoint:** `POST /api/v1/llm/estimate-cost`

**Status:** ✅ Fully Implemented

**Request Body:**
```json
{
  "model_id": "kasaai_llama_twi",
  "input_text": "What is the capital of Ghana? Please provide a detailed answer."
}
```

**Response:** `200 OK`
```json
{
  "estimated_cost": 0.0008,
  "estimated_tokens": 40,
  "model_id": "kasaai_llama_twi"
}
```

---

## ASR Services API

Transcribe audio files with automatic speech recognition (ASR) powered by Whisper and specialized models.

### Transcribe Audio

Convert speech to text with timestamp support.

**Endpoint:** `POST /api/v1/asr/transcribe`

**Status:** ✅ Fully Implemented

**Request:** `multipart/form-data`
```
Content-Type: multipart/form-data

audio_file: <binary audio data>
provider_id: whisper_large_v3
language: en
task: transcribe
response_format: json
temperature: 0.0
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audio_file` | file | Yes | Audio file (WAV, MP3, M4A, max 25MB) |
| `provider_id` | string | Yes | ASR provider ID (e.g., `whisper_large_v3`, `akan_whisper_giftmark`) |
| `language` | string | No | Language code (ISO 639-1, e.g., `en`, `tw`, `auto`) |
| `task` | string | No | Task type: `transcribe`, `translate` (default: `transcribe`) |
| `response_format` | string | No | Format: `json`, `text`, `srt`, `vtt` (default: `json`) |
| `temperature` | float | No | Sampling temperature 0.0-1.0 (default: 0.0) |

**Response:** `200 OK`
```json
{
  "text": "Hello, welcome to AI Labs Africa.",
  "provider_id": "whisper_large_v3",
  "language": "en",
  "duration": 3.5,
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 1.2,
      "text": "Hello,"
    },
    {
      "id": 1,
      "start": 1.2,
      "end": 3.5,
      "text": " welcome to AI Labs Africa."
    }
  ],
  "cost": 0.0035,
  "transaction_id": "txn_xyz789",
  "processing_time": 2.1,
  "model_name": "whisper-large-v3"
}
```

**Cost Breakdown:**
- Base rate: $0.001 per second of audio
- Cost automatically deducted from wallet

---

### List ASR Providers

Get all available ASR providers with health status.

**Endpoint:** `GET /api/v1/asr/providers`

**Status:** ✅ Fully Implemented

**Query Parameters:**
- `force_refresh` (boolean, optional) - Force health check refresh (default: false)

**Response:** `200 OK`
```json
{
  "providers": {
    "whisper_large_v3": {
      "id": "whisper_large_v3",
      "name": "Whisper Large V3",
      "endpoint": "https://whisper.ailabsafrica.com",
      "status": "online",
      "last_check": "2025-10-26T12:00:00Z",
      "response_time_ms": 200,
      "error_message": null,
      "provider_type": "asr"
    },
    "akan_whisper_giftmark": {
      "id": "akan_whisper_giftmark",
      "name": "Akan Whisper Giftmark",
      "endpoint": "https://akan-whisper.ailabsafrica.com",
      "status": "online",
      "last_check": "2025-10-26T12:00:00Z",
      "response_time_ms": 180,
      "error_message": null,
      "provider_type": "asr"
    }
  },
  "count": 2,
  "online_count": 2,
  "offline_count": 0
}
```

---

### Get Supported Languages

Get languages supported by an ASR provider.

**Endpoint:** `GET /api/v1/asr/languages/{provider_id}`

**Status:** ✅ Fully Implemented

**Response:** `200 OK`
```json
{
  "provider_id": "whisper_large_v3",
  "languages": ["en", "es", "fr", "de", "it", "pt", "ar", "zh", "ja", "ko"],
  "count": 10
}
```

---

### Estimate ASR Cost

Estimate transcription cost before processing.

**Endpoint:** `POST /api/v1/asr/estimate-cost`

**Status:** ✅ Fully Implemented

**Request Body:**
```json
{
  "provider_id": "whisper_large_v3",
  "audio_base64": "UklGRi..."
}
```

**Response:** `200 OK`
```json
{
  "estimated_cost": 0.0035,
  "estimated_duration": 3.5,
  "provider_id": "whisper_large_v3"
}
```

---

## TTS Services API

Convert text to natural speech using multiple TTS providers with voice cloning support.

**Current Status:** ✅ All 15+ TTS services online (verified Nov 9, 2025)
**Provider Availability:** 100% (RunPod GPU + Local Infrastructure)
**🌟 NEW:** Unified TTS Lab Hub at **https://ttslab.ailabsafrica.com**

### 🎯 TTS Lab - Unified Access Hub

**All TTS services are now accessible through a consolidated hub:**

- **URL:** https://ttslab.ailabsafrica.com
- **Features:** Modern landing page with service categorization, real-time status, and direct links
- **Services:** 15+ TTS providers across RunPod GPU and local infrastructure
- **Use Cases:** Research, development, production synthesis, and voice cloning

### Provider Endpoints

**RunPod GPU Services (NVIDIA A40, 46GB VRAM):**
- **TTS-WebUI:** `https://tts-webui.ailabsafrica.com` ⭐ 20+ models platform
- **GPT-SoVITS:** RunPod Proxy (Community #1, superior voice cloning)
- **Fish Speech:** RunPod Proxy (Zero-shot cloning, 5-6x real-time)
- **Zonos TTS:** RunPod Proxy (Emotion control sliders)
- **F5-TTS:** RunPod Proxy (Flow-matching architecture)
- **StyleTTS2:** `https://styletts.ailabsafrica.com` (Human-level quality)

**Local Infrastructure Services (NVIDIA RTX 4000 Ada, 20GB VRAM):**
- **Coqui XTTS:** `https://coqui.ailabsafrica.com` (20+ languages)
- **MeloTTS:** `https://melotts.ailabsafrica.com` (Fast synthesis)
- **OpenVoice:** `https://openvoice.ailabsafrica.com` (Tone transfer)
- **Kokoro TTS:** `https://kokoro.ailabsafrica.com` (11 voice packs)
- **F5-TTS API:** `https://f5tts.ailabsafrica.com` (Local API endpoint)

**Health Check Endpoint:** All providers expose `/health` for monitoring

### TTS-WebUI Platform

**NEW: Comprehensive TTS Platform** - TTS-WebUI provides access to 20+ TTS models through a unified interface.

**Features:**
- 🎨 React-based web UI (Next.js)
- 🔌 OpenAI-compatible API (port 7778)
- 🎛️ Extension Manager for easy model installation
- 🎙️ Multiple voice cloning providers
- 🌐 Multi-language support (varies by model)
- 🎵 Audio processing (Demucs, Vocos)
- 🎤 ASR integration (Whisper)
- 🎼 Music generation (MusicGen, Stable Audio)

**Available Models:**
- Core: StyleTTS2, RVC, Bark, Tortoise, MeloTTS, MMS
- Advanced: F5-TTS, XTTS v2, OpenVoice, Kokoro, Parler TTS
- Specialty: Whisper (ASR), MusicGen, Stable Audio, Demucs
- Experimental: GPT-SoVITS, Chatterbox, MahaTTS, VALL-E X

**Programmatic Access:**
- Web UI: `https://tts-webui.ailabsafrica.com`
- OpenAI API: `https://tts-webui.ailabsafrica.com/api/v1/audio/speech`
- Gradio Backend: Port 7770 (internal)

**Example Request (OpenAI-compatible API):**
```bash
curl -X POST https://tts-webui.ailabsafrica.com/api/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "styletts2",
    "input": "Hello from TTS-WebUI!",
    "voice": "default",
    "response_format": "wav"
  }'
```

**Python SDK Integration:**
```python
from apps.shared.services.tts_webui_service import (
    TTSWebUIService,
    TTSWebUISynthesisRequest,
    TTSWebUIProvider
)

service = TTSWebUIService()
request = TTSWebUISynthesisRequest(
    text="Hello world",
    provider_id=TTSWebUIProvider.STYLETTS2,
    language="en"
)
response = await service.synthesize(request)
```

---

### List TTS Providers

Get all available TTS providers with health status.

**Endpoint:** `GET /api/v1/tts/providers`

**Status:** ✅ Fully Implemented

**Query Parameters:**
- `force_refresh` (boolean, optional) - Force health check refresh (default: false)

**Response:** `200 OK`
```json
{
  "providers": {
    "coqui_xtts": {
      "id": "coqui_xtts",
      "name": "Coqui XTTS v2",
      "endpoint": "https://coqui.ailabsafrica.com",
      "status": "online",
      "languages": 17,
      "languageList": ["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "hu", "ko", "ja", "hi"],
      "capabilities": {
        "voiceCloning": true,
        "multiLanguage": true,
        "speedControl": true,
        "pitchControl": false
      },
      "description": "Multilingual TTS with voice cloning capabilities. Supports 17 languages with high-quality synthesis.",
      "icon": "🎙️"
    },
    "melotts": {
      "id": "melotts",
      "name": "MeloTTS",
      "endpoint": "https://melotts.ailabsafrica.com",
      "status": "online",
      "languages": 6,
      "languageList": ["EN", "ES", "FR", "ZH", "JP", "KR"],
      "capabilities": {
        "voiceCloning": false,
        "multiLanguage": true,
        "speedControl": true,
        "pitchControl": true,
        "multiSpeaker": true
      },
      "description": "Fast multilingual synthesis with multi-speaker support. Optimized for speed and quality.",
      "icon": "🔊"
    },
    "openvoice": {
      "id": "openvoice",
      "name": "OpenVoice",
      "endpoint": "https://openvoice.ailabsafrica.com",
      "status": "online",
      "languages": 2,
      "languageList": ["EN", "ZH"],
      "capabilities": {
        "voiceCloning": true,
        "multiLanguage": true,
        "speedControl": false,
        "pitchControl": true,
        "emotionControl": true
      },
      "description": "Advanced voice cloning with emotion control for English and Chinese.",
      "icon": "🎭"
    },
    "kokoro": {
      "id": "kokoro",
      "name": "Kokoro TTS",
      "endpoint": "https://kokoro.ailabsafrica.com",
      "status": "online",
      "languages": 1,
      "languageList": ["en"],
      "capabilities": {
        "voiceCloning": false,
        "multiLanguage": false,
        "speedControl": true,
        "pitchControl": false
      },
      "description": "High-quality English TTS synthesis.",
      "icon": "💬"
    },
    "f5tts": {
      "id": "f5tts",
      "name": "F5-TTS",
      "endpoint": "https://f5tts.ailabsafrica.com",
      "status": "online",
      "languages": 4,
      "languageList": ["en", "zh", "ja", "ko"],
      "capabilities": {
        "voiceCloning": true,
        "multiLanguage": true,
        "speedControl": true,
        "pitchControl": false
      },
      "description": "Flow-matching based TTS with voice cloning. Requires reference audio for synthesis.",
      "icon": "🌊"
    },
    "styletts2": {
      "id": "styletts2",
      "name": "StyleTTS2",
      "endpoint": "https://styletts.ailabsafrica.com",
      "status": "online",
      "languages": 1,
      "languageList": ["en"],
      "capabilities": {
        "voiceCloning": true,
        "multiLanguage": false,
        "speedControl": false,
        "pitchControl": false,
        "emotionControl": true
      },
      "description": "High-quality expressive TTS with style transfer. Requires reference audio for synthesis.",
      "icon": "🎨"
    }
  },
  "count": 6,
  "online_count": 6,
  "offline_count": 0
}
```

**Note:** Additional providers (Kyutai Moshi for real-time conversation, AKAN MMS for Ghanaian Twi) available for specialty use cases.

---

### Check Provider Health

Get health status for a specific TTS provider.

**Endpoint:** `GET /api/v1/tts/providers/{provider_id}/health`

**Status:** ✅ Fully Implemented

**Path Parameters:**
- `provider_id` (string, required) - Provider identifier (e.g., "coqui_xtts", "melotts")

**Direct Health Check (Alternative):**
You can also check provider health directly via the provider's endpoint:
```bash
curl https://coqui.ailabsafrica.com/health
curl https://melotts.ailabsafrica.com/health
curl https://openvoice.ailabsafrica.com/health
curl https://kokoro.ailabsafrica.com/health
curl https://f5tts.ailabsafrica.com/health
curl https://styletts.ailabsafrica.com/health
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda",
  "gpu_memory_allocated": "2.1 GB",
  "gpu_memory_total": "20.0 GB"
}
```

**Response (RunPod Providers):**
```json
{
  "status": "healthy",
  "device": "cuda",
  "model_loaded": true,
  "gpu_name": "NVIDIA A40",
  "gpu_memory_allocated": "0.69 GB",
  "gpu_memory_total": "44.43 GB"
}
```

**Error Response:** `503 Service Unavailable`
```json
{
  "status": "error",
  "message": "Provider offline or unhealthy",
  "provider_id": "melotts"
}
```

---

### Get Voice Samples

List available voice reference files for cloning.

**Endpoint:** `GET /api/v1/tts/voices`

**Status:** ✅ Fully Implemented

**Response:** `200 OK`
```json
{
  "voices": [
    {
      "id": "nana_aba",
      "name": "Nana Aba",
      "description": "Professional female Ghanaian voice",
      "file": "nana_aba.wav",
      "size": "6.1MB",
      "available": true
    },
    {
      "id": "adom_okyere",
      "name": "Adom Okyere",
      "description": "Male Ghanaian voice",
      "file": "adom_okyere.wav",
      "size": "13MB",
      "available": true
    }
  ],
  "count": 2
}
```

---

### Download Voice Sample

Download a voice reference file.

**Endpoint:** `GET /api/v1/tts/voices/{filename}`

**Status:** ✅ Fully Implemented

**Response:** `200 OK` (audio/wav)
- Returns WAV audio file
- Includes cache headers for performance

---

## Audio Conversion API

Convert audio files between multiple formats with quality control. Supports WAV, MP3, OGG, FLAC, and M4A formats with configurable bitrate settings.

### Get Format Information

Get details about all supported audio formats.

**Endpoint:** `GET /api/audio/info`

**Status:** ✅ Fully Implemented

**Response:** `200 OK`
```json
{
  "formats": {
    "wav": {
      "name": "WAV",
      "extension": ".wav",
      "type": "lossless",
      "mime_type": "audio/wav",
      "description": "Uncompressed audio, best quality"
    },
    "mp3": {
      "name": "MP3",
      "extension": ".mp3",
      "type": "lossy",
      "mime_type": "audio/mpeg",
      "bitrate_options": ["128k", "192k", "256k", "320k"],
      "default_bitrate": "192k",
      "description": "Most compatible format"
    },
    "ogg": {
      "name": "OGG Vorbis",
      "extension": ".ogg",
      "type": "lossy",
      "mime_type": "audio/ogg",
      "bitrate_options": ["128k", "192k", "256k", "320k"],
      "default_bitrate": "192k",
      "description": "Open-source alternative to MP3"
    },
    "flac": {
      "name": "FLAC",
      "extension": ".flac",
      "type": "lossless",
      "mime_type": "audio/flac",
      "description": "Lossless compression, smaller than WAV"
    },
    "m4a": {
      "name": "M4A/AAC",
      "extension": ".m4a",
      "type": "lossy",
      "mime_type": "audio/mp4",
      "bitrate_options": ["128k", "192k", "256k", "320k"],
      "default_bitrate": "192k",
      "description": "Apple's format, better quality than MP3"
    }
  }
}
```

---

### Convert Audio Format

Convert audio between different formats.

**Endpoint:** `POST /api/audio/convert`

**Status:** ✅ Fully Implemented

**Request Body:**
```json
{
  "audio_base64": "UklGRiQEAABXQVZFZm10...",
  "source_format": "wav",
  "target_format": "mp3",
  "bitrate": "192k"
}
```

**Parameters:**
- `audio_base64` (string, required) - Base64-encoded audio data
- `source_format` (string, required) - Input format: `wav`, `mp3`, `ogg`, `flac`, `m4a`
- `target_format` (string, required) - Output format: `wav`, `mp3`, `ogg`, `flac`, `m4a`
- `bitrate` (string, optional) - For lossy formats: `128k`, `192k`, `256k`, `320k` (default: `192k`)

**Response:** `200 OK`
```json
{
  "audio_base64": "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2Z...",
  "format": "mp3",
  "size_bytes": 24576,
  "conversion_time": 0.42
}
```

**Error Responses:**
- `400 Bad Request` - Invalid format or corrupted audio
- `422 Unprocessable Entity` - Invalid base64 or missing parameters

---

### Batch Convert Audio

Convert one audio file to multiple formats simultaneously.

**Endpoint:** `POST /api/audio/convert/batch`

**Status:** ✅ Fully Implemented

**Request Body:**
```json
{
  "audio_base64": "UklGRiQEAABXQVZFZm10...",
  "source_format": "wav",
  "target_formats": ["mp3", "ogg", "flac"],
  "bitrate": "256k"
}
```

**Parameters:**
- `audio_base64` (string, required) - Base64-encoded audio data
- `source_format` (string, required) - Input format
- `target_formats` (array, required) - List of output formats
- `bitrate` (string, optional) - Bitrate for lossy formats (default: `192k`)

**Response:** `200 OK`
```json
{
  "results": {
    "mp3": "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2Z...",
    "ogg": "T2dnUwACAAAAAAAAAABqBgAAAAAAAHq8uQ...",
    "flac": "ZkxhQwAAACIQABAAAAUJABtABfACAARAAAA..."
  },
  "total_time": 1.25,
  "format_count": 3
}
```

**Use Cases:**
- Export for multiple platforms
- Create quality variants
- Batch processing pipelines

---

### Convert Uploaded File

Upload and convert audio file via multipart form.

**Endpoint:** `POST /api/audio/convert/upload`

**Status:** ✅ Fully Implemented

**Request:** `multipart/form-data`
- `file` (file, required) - Audio file to convert
- `target_format` (string, required) - Output format
- `bitrate` (string, optional) - Bitrate for lossy formats

**Response:** `200 OK` (binary audio data)
- Returns converted audio file directly
- Content-Type matches target format MIME type
- Filename in Content-Disposition header

**Example (cURL):**
```bash
curl -X POST "https://api.ailabsafrica.com/api/audio/convert/upload" \
  -F "file=@input.wav" \
  -F "target_format=mp3" \
  -F "bitrate=320k" \
  -o output.mp3
```

---

### Format Comparison

| Format | Type | Size (1s audio) | Quality | Use Case |
|--------|------|----------------|---------|----------|
| **WAV** | Lossless | ~88KB | Perfect | Studio editing |
| **FLAC** | Lossless | ~44KB | Perfect | Archival |
| **MP3** (320k) | Lossy | ~40KB | Excellent | High-quality playback |
| **MP3** (192k) | Lossy | ~24KB | Very Good | General playback |
| **OGG** (192k) | Lossy | ~23KB | Very Good | Web streaming |
| **M4A** (192k) | Lossy | ~24KB | Very Good | Apple devices |
| **MP3** (128k) | Lossy | ~16KB | Good | Podcasts |

**Compression Ratios** (vs. WAV):
- FLAC: 2:1 (lossless)
- MP3/M4A/OGG (192k): ~8:1 (lossy)
- MP3 (128k): ~12:1 (lossy)

---

## RVC Voice Conversion API

Transform voice characteristics while preserving speech content using Retrieval-based Voice Conversion (RVC) with VITS framework and HiFi-GAN vocoder.

**Current Status:** ✅ Online (verified Nov 8, 2025)
**Endpoint:** `https://rvc.ailabsafrica.com`
**Port:** 8017 (RunPod NVIDIA A40)
**GPU:** 44GB VRAM, ~2GB during inference

### Overview

RVC Voice Conversion enables high-quality voice transformation for applications including:
- **Voice Character Transformation** - Match specific character or persona voices
- **Voice Anonymization** - Protect speaker identity while preserving content
- **Voice Restoration** - Improve quality of poor recordings
- **Multilingual Dubbing** - Maintain speaker characteristics across languages

**Key Features:**
- ✅ **VITS Framework** - Variational Inference with adversarial learning
- ✅ **HiFi-GAN Vocoder** - Natural audio generation
- ✅ **Multiple Pitch Methods** - RMVPE, Harvest, PM, FCPE, CREPE
- ✅ **Index-based Retrieval** - High-quality voice feature matching
- ✅ **GPU Accelerated** - CUDA-powered inference on A40
- ✅ **Model Training** - Gradio WebUI for custom voice models

**Performance:**
- Short Audio (5s): ~1-2 seconds
- Medium Audio (30s): ~6-8 seconds
- Long Audio (2min): ~25-30 seconds
- Pitch Accuracy: >95% with RMVPE
- Output Quality: 24kHz, 16-bit WAV

---

### Health Check

Check RVC service status and device information.

**Endpoint:** `GET https://rvc.ailabsafrica.com/health`

**Status:** ✅ Fully Implemented

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "device": "cuda:0",
  "current_model": null,
  "timestamp": 1762625858.296
}
```

**Example Request:**
```bash
curl https://rvc.ailabsafrica.com/health
```

**Python Example:**
```python
import requests

response = requests.get("https://rvc.ailabsafrica.com/health")
health = response.json()
print(f"Status: {health['status']}")
print(f"Device: {health['device']}")
```

---

### List Available Models

Get all available RVC models for voice conversion.

**Endpoint:** `GET https://rvc.ailabsafrica.com/models`

**Status:** ✅ Fully Implemented

**Response:** `200 OK`
```json
{
  "models": [
    {
      "name": "character_voice",
      "path": "logs/character_voice/model.pth",
      "size_mb": 54.2
    },
    {
      "name": "neutral_voice",
      "path": "logs/neutral_voice/model.pth",
      "size_mb": 53.8
    }
  ]
}
```

**Example Request:**
```bash
curl https://rvc.ailabsafrica.com/models
```

**Python Example:**
```python
import requests

response = requests.get("https://rvc.ailabsafrica.com/models")
models = response.json()

for model in models['models']:
    print(f"Model: {model['name']}")
    print(f"Path: {model['path']}")
    print(f"Size: {model['size_mb']:.1f} MB\n")
```

---

### Convert Voice

Transform voice using RVC model.

**Endpoint:** `POST https://rvc.ailabsafrica.com/convert`

**Status:** ✅ Fully Implemented

**Request Format:** `multipart/form-data`

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `audio` | file | Yes | - | Audio file to convert (WAV format) |
| `model_path` | string | Yes | - | Path to RVC model (e.g., "logs/my_model/model.pth") |
| `pitch_shift` | integer | No | 0 | Pitch shift in semitones (-12 to +12) |
| `index_rate` | float | No | 0.75 | Voice similarity (0.0-1.0) |
| `filter_radius` | integer | No | 3 | Smoothing radius (1-7) |
| `rms_mix_rate` | float | No | 0.25 | Volume matching (0.0-1.0) |
| `protect` | float | No | 0.33 | Consonant protection (0.0-0.5) |
| `f0_method` | string | No | rmvpe | Pitch extraction method |

**F0 Methods:**
- `rmvpe` - Robust Model for Voice Pitch Estimation (recommended)
- `harvest` - High-quality but slower
- `pm` - ParselMouth (fast but less accurate)
- `fcpe` - Fast and accurate
- `crepe` - Deep learning-based

**Response:** `200 OK`
- Content-Type: `audio/wav`
- Custom Headers:
  - `X-Inference-Time`: Processing time in seconds
  - `X-Output-Size`: Output file size in bytes

Returns converted audio file as binary WAV data.

**Example Request (cURL):**
```bash
curl -X POST https://rvc.ailabsafrica.com/convert \
  -F "audio=@input.wav" \
  -F "model_path=logs/character_voice/model.pth" \
  -F "pitch_shift=2" \
  -F "index_rate=0.8" \
  -F "filter_radius=3" \
  -F "rms_mix_rate=0.25" \
  -F "protect=0.33" \
  -F "f0_method=rmvpe" \
  --output converted_output.wav
```

**Python Example:**
```python
import requests
from pathlib import Path

# Read input audio
audio_path = Path("input_audio.wav")
with open(audio_path, "rb") as f:
    audio_data = f.read()

# Prepare request
files = {"audio": ("input.wav", audio_data, "audio/wav")}
data = {
    "model_path": "logs/character_voice/model.pth",
    "pitch_shift": 2,
    "index_rate": 0.8,
    "filter_radius": 3,
    "rms_mix_rate": 0.25,
    "protect": 0.33,
    "f0_method": "rmvpe"
}

# Send conversion request
response = requests.post(
    "https://rvc.ailabsafrica.com/convert",
    files=files,
    data=data
)

# Save converted audio
if response.status_code == 200:
    with open("converted_output.wav", "wb") as f:
        f.write(response.content)

    # Display metrics
    inference_time = response.headers.get('X-Inference-Time')
    output_size = response.headers.get('X-Output-Size')

    print(f"✓ Conversion successful")
    print(f"  Inference Time: {inference_time}s")
    print(f"  Output Size: {int(output_size) / 1024:.2f} KB")
else:
    print(f"✗ Error: {response.status_code}")
    print(response.text)
```

---

### Use Case Examples

#### 1. Voice Character Transformation

Transform narrator voice to match a specific character.

```python
import requests
from pathlib import Path

# Read narrator audio
with open("narrator_recording.wav", "rb") as f:
    audio_data = f.read()

# Convert to character voice
response = requests.post(
    "https://rvc.ailabsafrica.com/convert",
    files={"audio": ("input.wav", audio_data, "audio/wav")},
    data={
        "model_path": "logs/character_voice/model.pth",
        "pitch_shift": 2,        # Slightly higher pitch
        "index_rate": 0.8,       # High similarity to character
        "f0_method": "rmvpe"
    }
)

with open("character_voice.wav", "wb") as f:
    f.write(response.content)

print(f"✓ Character voice created in {response.headers['X-Inference-Time']}s")
```

#### 2. Voice Anonymization

Protect speaker identity while preserving speech content.

```python
import requests

# Read original interview
with open("original_interview.wav", "rb") as f:
    audio_data = f.read()

# Anonymize voice
response = requests.post(
    "https://rvc.ailabsafrica.com/convert",
    files={"audio": ("input.wav", audio_data, "audio/wav")},
    data={
        "model_path": "logs/neutral_voice/model.pth",
        "protect": 0.5,          # Preserve consonants for clarity
        "rms_mix_rate": 0.3,     # Match volume
        "f0_method": "rmvpe"
    }
)

with open("anonymized_interview.wav", "wb") as f:
    f.write(response.content)

print("✓ Voice anonymized successfully")
```

#### 3. Voice Restoration

Improve voice quality in poor recordings.

```python
import requests

# Read low-quality recording
with open("phone_recording.wav", "rb") as f:
    audio_data = f.read()

# Restore voice quality
response = requests.post(
    "https://rvc.ailabsafrica.com/convert",
    files={"audio": ("input.wav", audio_data, "audio/wav")},
    data={
        "model_path": "logs/clear_voice/model.pth",
        "filter_radius": 5,      # More smoothing
        "index_rate": 0.7,
        "f0_method": "rmvpe"
    }
)

with open("restored_audio.wav", "wb") as f:
    f.write(response.content)

print("✓ Voice quality restored")
```

#### 4. Multilingual Dubbing

Convert voice while maintaining speaker characteristics.

```python
import requests

# Read translated audio (different language)
with open("translated_audio.wav", "rb") as f:
    audio_data = f.read()

# Dub with original speaker's voice
response = requests.post(
    "https://rvc.ailabsafrica.com/convert",
    files={"audio": ("input.wav", audio_data, "audio/wav")},
    data={
        "model_path": "logs/original_speaker/model.pth",
        "pitch_shift": 0,
        "index_rate": 0.85,      # High fidelity to original
        "f0_method": "rmvpe"
    }
)

with open("dubbed_audio.wav", "wb") as f:
    f.write(response.content)

print("✓ Dubbing complete with original voice characteristics")
```

---

### Best Practices

**Parameter Tuning:**
- Start with default parameters and adjust based on results
- Use `index_rate` 0.5-0.9 for best voice similarity
- Increase `filter_radius` (up to 7) for smoother output
- Adjust `pitch_shift` for gender-matched transformations
- Use `rmvpe` f0_method for best pitch accuracy

**Audio Input:**
- Provide clean WAV files for best results
- Remove background noise before conversion
- Use consistent audio quality for training data
- Match source/target gender when possible

**Model Selection:**
- Use gender-matched models (male → male, female → female)
- Test multiple models to find best voice match
- Train custom models with 5-30 minutes of clean audio
- Store trained models in `logs/<model_name>/` directory

**Performance Optimization:**
- Batch multiple conversions during off-peak hours
- Cache converted audio to avoid reprocessing
- Monitor GPU usage before large batch jobs
- Use shorter audio segments for faster processing

---

### Error Handling

**Model Not Found (404):**
```json
{
  "detail": "Model file not found: logs/my_model/model.pth"
}
```
Solution: Verify model path exists on RunPod server.

**Out of Memory (500):**
```json
{
  "detail": "CUDA out of memory"
}
```
Solution: Wait for current processing to complete or reduce batch size.

**Invalid Parameters (400):**
```json
{
  "detail": "index_rate must be between 0.0 and 1.0"
}
```
Solution: Check parameter ranges in documentation.

**Poor Conversion Quality:**
- Adjust `index_rate` (try 0.5-0.9)
- Change `f0_method` (try `rmvpe` or `harvest`)
- Increase `filter_radius` for more smoothing
- Retrain model with more/better quality data

---

### Technical Details

**Architecture:**
- **Framework:** VITS (Variational Inference with adversarial learning)
- **Vocoder:** HiFi-GAN for natural audio generation
- **Feature Extractor:** ContentVec for voice features
- **Speech Model:** HuBERT base model (181MB)
- **Pitch Detector:** RMVPE model (173MB)

**Deployment:**
- **Platform:** RunPod GPU Cloud
- **GPU:** NVIDIA A40 (44.43GB VRAM)
- **Python:** 3.10 (required for fairseq compatibility)
- **PyTorch:** 2.1.0 with CUDA 12.1
- **Dependencies:** fairseq 0.12.2, gradio 3.34.0, librosa 0.9.1

**Resource Usage:**
- GPU Memory: ~2GB VRAM during inference
- CPU Usage: Minimal (GPU-accelerated)
- Bandwidth: ~88KB per second of audio (WAV format)
- Model Size: 50-100MB per trained model

**Documentation:**
- Service Docs: `@shared/voice_engine/RVC_VOICE_CONVERSION.md`
- Infrastructure: `@architecture/TTS_INFRASTRUCTURE.md`
- API Reference: https://rvc.ailabsafrica.com/docs
- GitHub: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI

---

## RAG Service API

Build intelligent Q&A systems with Retrieval-Augmented Generation (RAG) powered by vector embeddings and LLMs.

### Initialize Knowledge Base

Create or update a knowledge base from documents.

**Endpoint:** `POST /api/v1/rag/knowledge-bases`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Request Body:**
```json
{
  "collection_name": "customer_support_docs",
  "documents": [
    {
      "content": "How to reset your password: Go to Settings > Security...",
      "metadata": {
        "source": "help_center",
        "category": "authentication",
        "last_updated": "2025-10-20"
      }
    }
  ],
  "ai_provider": "gemini",
  "embedding_model": "text-embedding-004"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection_name` | string | Yes | Knowledge base identifier (3-100 characters, alphanumeric + underscore) |
| `documents` | array | Yes | Array of documents (1-1000 documents per request) |
| `documents[].content` | string | Yes | Document text content (min 10 characters) |
| `documents[].metadata` | object | No | Custom metadata (max 20 key-value pairs) |
| `ai_provider` | string | No | AI provider: `gemini`, `openai`, `anthropic` (default: `gemini`) |
| `embedding_model` | string | No | Embedding model (default: provider-specific default) |

**Response:** `201 Created`
```json
{
  "collection_name": "customer_support_docs",
  "documents_indexed": 1,
  "embedding_dimensions": 768,
  "ai_provider": "gemini",
  "created_at": "2025-10-23T12:00:00Z"
}
```

---

### Query Knowledge Base

Search knowledge base and get AI-generated answers.

**Endpoint:** `POST /api/v1/rag/query`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Request Body:**
```json
{
  "collection_name": "customer_support_docs",
  "query": "How do I reset my password?",
  "context": {
    "user_type": "customer",
    "platform": "web"
  },
  "filters": {
    "category": "authentication"
  },
  "max_results": 5,
  "confidence_threshold": 0.7
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection_name` | string | Yes | Knowledge base identifier |
| `query` | string | Yes | User question (min 3 characters) |
| `context` | object | No | Additional context for better answers |
| `filters` | object | No | Metadata filters for document selection |
| `max_results` | integer | No | Max documents to retrieve (1-20, default: 5) |
| `confidence_threshold` | float | No | Minimum confidence (0.0-1.0, default: 0.7) |

**Response:** `200 OK`
```json
{
  "answer": "To reset your password: 1. Go to Settings > Security 2. Click 'Reset Password' 3. Enter new password 4. Confirm",
  "confidence": 0.95,
  "sources": [
    {
      "content": "How to reset your password...",
      "metadata": {
        "source": "help_center",
        "category": "authentication"
      }
    }
  ],
  "tokens_used": {
    "input": 500,
    "output": 200,
    "total": 700
  }
}
```

**Confidence Levels:**
- `0.9 - 1.0` - Very High (answer directly from knowledge base)
- `0.8 - 0.9` - High (answer synthesized from multiple sources)
- `0.7 - 0.8` - Medium (answer inferred with some uncertainty)
- `< 0.7` - Low (insufficient information, may return error)

---

### List Knowledge Bases

Get a list of all knowledge bases.

**Endpoint:** `GET /api/v1/rag/knowledge-bases`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Query Parameters:**
- `limit` (integer, optional) - Items per page (default: 10, max: 100)
- `offset` (integer, optional) - Starting position (default: 0)

**Response:** `200 OK`
```json
{
  "knowledge_bases": [
    {
      "collection_name": "customer_support_docs",
      "documents_count": 150,
      "ai_provider": "gemini",
      "created_at": "2025-10-23T12:00:00Z",
      "last_updated": "2025-10-23T14:30:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

---

### Delete Knowledge Base

Delete a knowledge base permanently.

**Endpoint:** `DELETE /api/v1/rag/knowledge-bases/{collection_name}`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Response:** `200 OK`
```json
{
  "collection_name": "customer_support_docs",
  "deleted": true,
  "documents_removed": 150
}
```

---

## Document Processor API

Process documents (PDF, DOCX, TXT, HTML) and extract structured content with intelligent chunking.

### Process Document

Upload and process a document into chunks.

**Endpoint:** `POST /api/v1/documents/process`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Request:** `multipart/form-data`
```
Content-Type: multipart/form-data

file: <binary file data>
chunking_strategy: sentence_aware
chunk_size: 1000
chunk_overlap: 200
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | Document file (PDF, DOCX, TXT, HTML, max 50MB) |
| `chunking_strategy` | string | No | Strategy: `recursive`, `sentence_aware`, `paragraph_aware`, `fixed_size` (default: `recursive`) |
| `chunk_size` | integer | No | Target chunk size in characters (100-5000, default: 1000) |
| `chunk_overlap` | integer | No | Overlap between chunks (0-500, default: 200) |

**Chunking Strategies:**
- **`recursive`** - Splits on paragraph, sentence, word boundaries
- **`sentence_aware`** - Splits on sentence boundaries (best for Q&A)
- **`paragraph_aware`** - Splits on paragraph boundaries (best for summarization)
- **`fixed_size`** - Fixed-size chunks with overlap

**Response:** `200 OK`
```json
{
  "filename": "user_manual.pdf",
  "file_type": "pdf",
  "chunks": [
    {
      "content": "Chapter 1: Introduction. This manual covers...",
      "metadata": {
        "chunk_index": 0,
        "page_numbers": [1, 2],
        "section": "introduction"
      }
    }
  ],
  "chunks_count": 25,
  "metadata": {
    "num_pages": 50,
    "file_size_mb": 2.5,
    "processing_time_seconds": 3.2
  }
}
```

---

### Process Batch

Process multiple documents in batch.

**Endpoint:** `POST /api/v1/documents/process-batch`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Request:** `multipart/form-data`
```
Content-Type: multipart/form-data

files[]: <binary file 1>
files[]: <binary file 2>
chunking_strategy: sentence_aware
max_concurrent: 3
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `files[]` | array | Yes | Multiple document files (max 10 files, 50MB each) |
| `chunking_strategy` | string | No | Strategy for all documents |
| `max_concurrent` | integer | No | Concurrent processing (1-5, default: 3) |

**Response:** `200 OK`
```json
{
  "results": [
    {
      "filename": "doc1.pdf",
      "success": true,
      "chunks_count": 25,
      "error": null
    },
    {
      "filename": "doc2.docx",
      "success": false,
      "chunks_count": 0,
      "error": "File exceeds maximum size"
    }
  ],
  "total_files": 2,
  "successful": 1,
  "failed": 1
}
```

---

## Wallet Service API

Manage user wallets, payments, and transactions with multi-currency support and automatic billing integration.

**Version:** v1.3.0 (Fully Implemented)

All AI services (LLM, ASR, TTS, VAPI calls, Vonage, Twilio) automatically deduct costs from your wallet with detailed transaction records.

### Get Wallet Balance

Retrieve current wallet balance and details.

**Endpoint:** `GET /api/v1/wallet/balance`

**Status:** ✅ Fully Implemented

**Response:** `200 OK`
```json
{
  "id": "wallet_abc123",
  "user_id": "user_123abc",
  "balance": 95.50,
  "currency": "USD",
  "status": "active",
  "created_at": "2025-10-26T12:00:00Z",
  "updated_at": "2025-10-26T14:30:00Z"
}
```

**Supported Currencies:**
- `USD` - US Dollar (default)
- `GHS` - Ghanaian Cedi
- `EUR` - Euro
- `GBP` - British Pound
- `NGN` - Nigerian Naira
- `KES` - Kenyan Shilling
- `ZAR` - South African Rand

---

### Get Transaction History

Retrieve paginated transaction history with filtering options.

**Endpoint:** `GET /api/v1/wallet/transactions`

**Status:** ✅ Fully Implemented

**Query Parameters:**
- `start_date` (string, optional) - Filter from date (ISO 8601 format)
- `end_date` (string, optional) - Filter to date (ISO 8601 format)
- `transaction_type` (string, optional) - Filter by type: `credit`, `debit`
- `limit` (integer, optional) - Items per page (default: 20, max: 100)
- `skip` (integer, optional) - Number of items to skip (default: 0)

**Response:** `200 OK`
```json
{
  "transactions": [
    {
      "id": "txn_abc123",
      "wallet_id": "wallet_xyz789",
      "type": "debit",
      "amount": 5.50,
      "balance_before": 100.00,
      "balance_after": 94.50,
      "description": "LLM chat - kasaai_llama_twi",
      "metadata": {
        "service": "llm",
        "model_id": "kasaai_llama_twi",
        "input_tokens": 25,
        "output_tokens": 8,
        "total_tokens": 33,
        "request_id": "req_xyz789"
      },
      "created_at": "2025-10-26T14:30:00Z"
    },
    {
      "id": "txn_def456",
      "wallet_id": "wallet_xyz789",
      "type": "debit",
      "amount": 3.50,
      "balance_before": 94.50,
      "balance_after": 91.00,
      "description": "Vonage voice call - 120s to +1234567890",
      "metadata": {
        "service": "vonage",
        "service_type": "voice_call",
        "duration_seconds": 120,
        "phone_number": "+14155551234",
        "destination": "US",
        "assistant_id": "asst_123abc",
        "vapi_call_id": "call_789xyz"
      },
      "created_at": "2025-10-26T14:25:00Z"
    }
  ],
  "total": 2,
  "limit": 20,
  "skip": 0
}
```

**Transaction Types:**
- `credit` - Funds added to wallet (top-ups, refunds)
- `debit` - Funds deducted from wallet (AI service usage, calls, etc.)

**Service Types in Metadata:**
- `llm` - Large language model inference
- `asr` - Automatic speech recognition
- `tts` - Text-to-speech synthesis
- `vonage` - Vonage voice calls and SMS
- `twilio` - Twilio voice calls, SMS, MMS, WhatsApp
- `vapi` - VAPI assistant calls

---

### Top Up Wallet

Add funds to your wallet (payment integration required).

**Endpoint:** `POST /api/v1/wallet/topup`

**Status:** ✅ Fully Implemented

**Request Body:**
```json
{
  "amount": 50.00,
  "description": "Top-up via Paystack",
  "payment_provider": "paystack",
  "payment_reference": "ref_xyz789",
  "idempotency_key": "credit-abc123"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | decimal | Yes | Amount to credit (min: 0.01) |
| `description` | string | Yes | Transaction description |
| `payment_provider` | string | No | Provider: `paystack`, `stripe`, `momo` |
| `payment_reference` | string | No | External payment reference |
| `idempotency_key` | string | Yes | Unique key for deduplication |

**Response:** `200 OK`
```json
{
  "transaction_id": "txn_def456",
  "wallet_id": "wallet_abc123",
  "type": "credit",
  "amount": 50.00,
  "balance_before": 95.50,
  "balance_after": 145.50,
  "description": "Top-up via Paystack",
  "timestamp": "2025-10-23T15:00:00Z"
}
```

---

### Debit Wallet

Deduct funds from a wallet.

**Endpoint:** `POST /api/v1/wallets/{wallet_id}/debit`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Request Body:**
```json
{
  "amount": 5.50,
  "description": "RAG query usage",
  "idempotency_key": "debit-qa-session-123",
  "allow_negative": false
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | decimal | Yes | Amount to debit (min: 0.01) |
| `description` | string | Yes | Transaction description |
| `idempotency_key` | string | Yes | Unique key for deduplication |
| `allow_negative` | boolean | No | Allow negative balance (default: false) |

**Response:** `200 OK`
```json
{
  "transaction_id": "txn_ghi789",
  "wallet_id": "wallet_abc123",
  "type": "debit",
  "amount": 5.50,
  "balance_before": 145.50,
  "balance_after": 140.00,
  "description": "RAG query usage",
  "timestamp": "2025-10-23T15:05:00Z"
}
```

**Error Codes:**
- `INSUFFICIENT_BALANCE` - Wallet balance too low (when `allow_negative=false`)
- `WALLET_SUSPENDED` - Wallet is suspended or inactive

---

### Get Transaction History

Get wallet transaction history.

**Endpoint:** `GET /api/v1/wallets/{wallet_id}/transactions`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Query Parameters:**
- `start_date` (string, optional) - Filter from date (ISO 8601)
- `end_date` (string, optional) - Filter to date (ISO 8601)
- `type` (string, optional) - Filter by type: `credit`, `debit`
- `limit` (integer, optional) - Items per page (default: 20, max: 100)
- `offset` (integer, optional) - Starting position (default: 0)

**Response:** `200 OK`
```json
{
  "transactions": [
    {
      "transaction_id": "txn_ghi789",
      "type": "debit",
      "amount": 5.50,
      "balance_after": 140.00,
      "description": "RAG query usage",
      "timestamp": "2025-10-23T15:05:00Z"
    },
    {
      "transaction_id": "txn_def456",
      "type": "credit",
      "amount": 50.00,
      "balance_after": 145.50,
      "description": "Top-up via Paystack",
      "timestamp": "2025-10-23T15:00:00Z"
    }
  ],
  "total": 2,
  "limit": 20,
  "offset": 0
}
```

---

### Initiate Payment

Start a payment via Paystack or Stripe.

**Endpoint:** `POST /api/v1/payments/initiate`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Request Body:**
```json
{
  "wallet_id": "wallet_abc123",
  "amount": 100.00,
  "provider": "paystack",
  "callback_url": "https://yourapp.com/payment/callback",
  "metadata": {
    "user_email": "user@example.com",
    "plan": "professional"
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `wallet_id` | string | Yes | Target wallet ID |
| `amount` | decimal | Yes | Payment amount (min: 1.00) |
| `provider` | string | Yes | Payment provider: `paystack`, `stripe` |
| `callback_url` | string | Yes | URL to redirect after payment |
| `metadata` | object | No | Custom payment metadata |

**Response:** `200 OK`
```json
{
  "payment_id": "pay_jkl012",
  "authorization_url": "https://checkout.paystack.com/abc123",
  "reference": "ref_xyz789",
  "expires_at": "2025-10-23T16:00:00Z"
}
```

---

## Analytics Service API

Track comprehensive usage analytics across all services including detailed cost breakdowns for VAPI assistants.

**Version:** v1.3.0 (Fully Implemented)

### Get Usage Analytics

Retrieve usage statistics across all services for your account.

**Endpoint:** `GET /api/v1/analytics/usage`

**Status:** ✅ Fully Implemented

**Query Parameters:**
- `start_date` (string, optional) - Filter from date (ISO 8601 format)
- `end_date` (string, optional) - Filter to date (ISO 8601 format)
- `service` (string, optional) - Filter by service: `llm`, `asr`, `tts`, `vonage`, `twilio`, `vapi`

**Response:** `200 OK`
```json
{
  "period": {
    "start_date": "2025-10-20T00:00:00Z",
    "end_date": "2025-10-26T23:59:59Z"
  },
  "total_cost": 125.50,
  "total_requests": 450,
  "services": {
    "llm": {
      "requests": 150,
      "cost": 45.20,
      "total_tokens": 125000
    },
    "asr": {
      "requests": 80,
      "cost": 28.00,
      "total_duration_seconds": 28000
    },
    "tts": {
      "requests": 120,
      "cost": 32.30,
      "total_characters": 45000
    },
    "vonage": {
      "requests": 50,
      "cost": 15.00,
      "total_duration_seconds": 3000
    },
    "twilio": {
      "requests": 50,
      "cost": 5.00,
      "total_messages": 50
    }
  }
}
```

---

### Get Service-Specific Analytics

Retrieve analytics for a specific service.

**Endpoint:** `GET /api/v1/analytics/services/{service_type}`

**Status:** ✅ Fully Implemented

**Path Parameters:**
- `service_type` (string, required) - Service: `llm`, `asr`, `tts`, `vonage`, `twilio`, `vapi`

**Query Parameters:**
- `start_date` (string, optional) - Filter from date (ISO 8601 format)
- `end_date` (string, optional) - Filter to date (ISO 8601 format)

**Response:** `200 OK`
```json
{
  "service": "llm",
  "period": {
    "start_date": "2025-10-20T00:00:00Z",
    "end_date": "2025-10-26T23:59:59Z"
  },
  "total_cost": 45.20,
  "total_requests": 150,
  "models": {
    "kasaai_llama_twi": {
      "requests": 100,
      "cost": 30.50,
      "total_tokens": 85000
    },
    "llama_32_3b": {
      "requests": 50,
      "cost": 14.70,
      "total_tokens": 40000
    }
  }
}
```

---

### Get Assistant Analytics

**THE CENTERPIECE ENDPOINT** - Get comprehensive cost breakdown for a VAPI assistant across ALL services (VAPI, Vonage, Twilio, LLM, TTS, ASR).

**Endpoint:** `GET /api/v1/analytics/assistants/{assistant_id}`

**Status:** ✅ Fully Implemented

**Path Parameters:**
- `assistant_id` (string, required) - VAPI assistant ID

**Query Parameters:**
- `start_date` (string, optional) - Filter from date (ISO 8601 format, default: 30 days ago)
- `end_date` (string, optional) - Filter to date (ISO 8601 format, default: now)

**Response:** `200 OK`
```json
{
  "assistant_id": "asst_123abc",
  "period": {
    "start_date": "2025-09-26T00:00:00Z",
    "end_date": "2025-10-26T23:59:59Z"
  },
  "total_cost": 245.80,
  "cost_breakdown": {
    "vapi_calls": {
      "total_cost": 120.50,
      "call_count": 45,
      "total_duration_minutes": 180.5,
      "average_cost_per_call": 2.68,
      "average_duration_minutes": 4.01
    },
    "vonage_calls": {
      "total_cost": 85.30,
      "call_count": 45,
      "total_duration_seconds": 10830,
      "average_cost_per_call": 1.90
    },
    "twilio": {
      "total_cost": 15.00,
      "sms_count": 120,
      "voice_call_count": 5,
      "total_duration_seconds": 300
    },
    "llm": {
      "total_cost": 18.50,
      "request_count": 150,
      "total_tokens": 95000,
      "input_tokens": 60000,
      "output_tokens": 35000
    },
    "tts": {
      "total_cost": 4.50,
      "request_count": 50,
      "total_characters": 15000
    },
    "asr": {
      "total_cost": 2.00,
      "request_count": 20,
      "total_duration_seconds": 2000
    }
  },
  "usage_metrics": {
    "total_calls": 45,
    "successful_calls": 42,
    "failed_calls": 3,
    "success_rate": 0.933,
    "average_call_duration_minutes": 4.01,
    "total_call_duration_minutes": 180.5
  },
  "cost_distribution": {
    "vapi_calls": 49.0,
    "vonage_calls": 34.7,
    "twilio": 6.1,
    "llm": 7.5,
    "tts": 1.8,
    "asr": 0.8
  }
}
```

**Key Features:**
- Aggregates costs from **6 different services**: VAPI, Vonage, Twilio, LLM, TTS, ASR
- Provides **detailed usage metrics** for each service type
- Calculates **percentage distribution** of costs
- Shows **call success rates** and **average durations**
- Filters by date range for custom reporting periods

---

### Get Call Logs

Retrieve call logs with detailed information.

**Endpoint:** `GET /api/v1/analytics/calls`

**Status:** ✅ Fully Implemented

**Query Parameters:**
- `assistant_id` (string, optional) - Filter by assistant ID
- `start_date` (string, optional) - Filter from date (ISO 8601 format)
- `end_date` (string, optional) - Filter to date (ISO 8601 format)
- `status` (string, optional) - Filter by status: `completed`, `failed`, `in_progress`
- `limit` (integer, optional) - Items per page (default: 20, max: 100)
- `skip` (integer, optional) - Number of items to skip (default: 0)

**Response:** `200 OK`
```json
{
  "calls": [
    {
      "call_id": "call_abc123",
      "assistant_id": "asst_xyz789",
      "status": "completed",
      "duration_minutes": 4.5,
      "cost": 2.80,
      "created_at": "2025-10-26T14:30:00Z",
      "ended_at": "2025-10-26T14:34:30Z",
      "customer_number": "+1234567890",
      "metadata": {
        "vonage_cost": 1.50,
        "llm_cost": 0.80,
        "tts_cost": 0.30,
        "asr_cost": 0.20
      }
    }
  ],
  "total": 1,
  "limit": 20,
  "skip": 0
}
```

---

### Get Cost Summary

Get aggregated cost summary by time period.

**Endpoint:** `GET /api/v1/analytics/costs`

**Status:** ✅ Fully Implemented

**Query Parameters:**
- `start_date` (string, optional) - Filter from date (ISO 8601 format)
- `end_date` (string, optional) - Filter to date (ISO 8601 format)
- `group_by` (string, optional) - Group results: `day`, `week`, `month` (default: `day`)

**Response:** `200 OK`
```json
{
  "period": {
    "start_date": "2025-10-20T00:00:00Z",
    "end_date": "2025-10-26T23:59:59Z"
  },
  "total_cost": 245.80,
  "grouped_costs": [
    {
      "period": "2025-10-20",
      "cost": 35.20,
      "requests": 65
    },
    {
      "period": "2025-10-21",
      "cost": 42.10,
      "requests": 78
    },
    {
      "period": "2025-10-22",
      "cost": 38.50,
      "requests": 70
    }
  ]
}
```

---

## File Storage API

Organization-scoped cloud file storage using Hetzner Storage Box. All files are automatically isolated by organization ID for security and privacy.

**Version:** v1.3.0 (Fully Implemented)

**Base URL:** `/api/v1/storage`

**Storage Backend:** Hetzner Storage Box (WebDAV/SFTP)

### Key Features
- ✅ Organization-level data isolation
- ✅ Automatic directory creation
- ✅ File upload/download with multipart support
- ✅ Directory listing with metadata
- ✅ File metadata retrieval
- ✅ Secure deletion
- ✅ 100MB file size limit (Free tier)
- ✅ WebDAV and SFTP protocols

### File Path Structure

All files are stored with automatic organization scoping:

```
/kasaai/organizations/{organization_id}/{your_path}
```

Example:
```
Organization ID: org_abc123
Your path: documents/report.pdf
Actual storage path: /kasaai/organizations/org_abc123/documents/report.pdf
```

---

### Upload File

Upload a file to your organization's storage.

**Endpoint:** `POST /api/v1/storage/upload`

**Status:** ✅ Fully Implemented

**Rate Limit:** 10 uploads per minute (Free tier)

**Max File Size:** 100MB

**Request:** `multipart/form-data`

**Parameters:**
- `file` (file, required) - File to upload
- `path` (query, required) - Remote path (e.g., "documents/report.pdf")
- `overwrite` (query, optional) - Whether to overwrite existing file (default: false)

**Example Request:**
```bash
curl -X POST "https://developer-portal-api.ailabsafrica.com/api/v1/storage/upload?path=documents/report.pdf" \
  -H "X-API-Key: your-api-key" \
  -F "file=@/path/to/report.pdf"
```

**Response:** `200 OK`
```json
{
  "success": true,
  "filename": "report.pdf",
  "path": "documents/report.pdf",
  "size": 1024567,
  "url": "https://u497034-sub1.your-storagebox.de/kasaai/organizations/org_abc123/documents/report.pdf"
}
```

**Error Codes:**
- `413 Payload Too Large` - File exceeds 100MB limit
- `409 Conflict` - File exists and overwrite=false
- `500 Internal Server Error` - Storage system error

---

### Download File

Download a file from your organization's storage.

**Endpoint:** `GET /api/v1/storage/download/{file_path}`

**Status:** ✅ Fully Implemented

**Rate Limit:** 20 downloads per minute (Free tier)

**Example Request:**
```bash
curl -X GET "https://developer-portal-api.ailabsafrica.com/api/v1/storage/download/documents/report.pdf" \
  -H "X-API-Key: your-api-key" \
  --output report.pdf
```

**Response:** File binary stream with headers:
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="report.pdf"
```

**Error Codes:**
- `404 Not Found` - File doesn't exist
- `500 Internal Server Error` - Storage system error

---

### List Files

List files in a directory.

**Endpoint:** `GET /api/v1/storage/list`

**Status:** ✅ Fully Implemented

**Rate Limit:** 20 requests per minute (Free tier)

**Query Parameters:**
- `path` (string, optional) - Directory path to list (default: root)
- `recursive` (boolean, optional) - List files recursively (default: false)

**Example Request:**
```bash
curl -X GET "https://developer-portal-api.ailabsafrica.com/api/v1/storage/list?path=documents&recursive=false" \
  -H "X-API-Key: your-api-key"
```

**Response:** `200 OK`
```json
{
  "organization_id": "org_abc123",
  "path": "documents",
  "files": [
    {
      "name": "report.pdf",
      "path": "/kasaai/organizations/org_abc123/documents/report.pdf",
      "is_directory": false,
      "size": 1024567,
      "modified": "2025-10-26T14:30:00Z"
    },
    {
      "name": "images",
      "path": "/kasaai/organizations/org_abc123/documents/images",
      "is_directory": true,
      "size": 0,
      "modified": "2025-10-26T12:00:00Z"
    }
  ],
  "total": 2
}
```

---

### Get File Info

Get metadata for a specific file.

**Endpoint:** `GET /api/v1/storage/info/{file_path}`

**Status:** ✅ Fully Implemented

**Rate Limit:** 20 requests per minute (Free tier)

**Example Request:**
```bash
curl -X GET "https://developer-portal-api.ailabsafrica.com/api/v1/storage/info/documents/report.pdf" \
  -H "X-API-Key: your-api-key"
```

**Response:** `200 OK`
```json
{
  "name": "report.pdf",
  "path": "/kasaai/organizations/org_abc123/documents/report.pdf",
  "is_directory": false,
  "size": 1024567,
  "modified": "2025-10-26T14:30:00Z"
}
```

---

### Delete File

Delete a file from storage.

**Endpoint:** `DELETE /api/v1/storage/{file_path}`

**Status:** ✅ Fully Implemented

**Rate Limit:** 10 deletes per minute (Free tier)

**Warning:** This action cannot be undone.

**Example Request:**
```bash
curl -X DELETE "https://developer-portal-api.ailabsafrica.com/api/v1/storage/documents/old_report.pdf" \
  -H "X-API-Key: your-api-key"
```

**Response:** `200 OK`
```json
{
  "success": true,
  "path": "documents/old_report.pdf",
  "message": "File deleted successfully"
}
```

---

### Create Directory

Create a directory in storage.

**Endpoint:** `POST /api/v1/storage/create-directory`

**Status:** ✅ Fully Implemented

**Rate Limit:** 10 requests per minute (Free tier)

**Query Parameters:**
- `path` (string, required) - Directory path to create

**Example Request:**
```bash
curl -X POST "https://developer-portal-api.ailabsafrica.com/api/v1/storage/create-directory?path=documents/2025/reports" \
  -H "X-API-Key: your-api-key"
```

**Response:** `200 OK`
```json
{
  "success": true,
  "path": "documents/2025/reports",
  "message": "Directory created successfully"
}
```

---

### Usage Examples

#### Python

```python
import requests

API_BASE = "https://developer-portal-api.ailabsafrica.com"
API_KEY = "your-api-key"

headers = {"X-API-Key": API_KEY}

# Upload file
with open("report.pdf", "rb") as f:
    response = requests.post(
        f"{API_BASE}/api/v1/storage/upload",
        params={"path": "documents/report.pdf"},
        files={"file": f},
        headers=headers
    )
    print(response.json())

# List files
response = requests.get(
    f"{API_BASE}/api/v1/storage/list",
    params={"path": "documents", "recursive": False},
    headers=headers
)
print(response.json())

# Download file
response = requests.get(
    f"{API_BASE}/api/v1/storage/download/documents/report.pdf",
    headers=headers
)
with open("downloaded_report.pdf", "wb") as f:
    f.write(response.content)

# Delete file
response = requests.delete(
    f"{API_BASE}/api/v1/storage/documents/old_report.pdf",
    headers=headers
)
print(response.json())
```

#### JavaScript/TypeScript

```typescript
const API_BASE = "https://developer-portal-api.ailabsafrica.com";
const API_KEY = "your-api-key";

// Upload file
async function uploadFile(file: File, path: string) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `${API_BASE}/api/v1/storage/upload?path=${encodeURIComponent(path)}`,
    {
      method: 'POST',
      headers: {
        'X-API-Key': API_KEY
      },
      body: formData
    }
  );

  return await response.json();
}

// List files
async function listFiles(path: string = "", recursive: boolean = false) {
  const response = await fetch(
    `${API_BASE}/api/v1/storage/list?path=${encodeURIComponent(path)}&recursive=${recursive}`,
    {
      headers: {
        'X-API-Key': API_KEY
      }
    }
  );

  return await response.json();
}

// Download file
async function downloadFile(path: string, filename: string) {
  const response = await fetch(
    `${API_BASE}/api/v1/storage/download/${path}`,
    {
      headers: {
        'X-API-Key': API_KEY
      }
    }
  );

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
}

// Delete file
async function deleteFile(path: string) {
  const response = await fetch(
    `${API_BASE}/api/v1/storage/${path}`,
    {
      method: 'DELETE',
      headers: {
        'X-API-Key': API_KEY
      }
    }
  );

  return await response.json();
}
```

---

### Best Practices

#### 1. Directory Organization

Organize files by purpose and date:

```
documents/
├── 2025/
│   ├── contracts/
│   ├── invoices/
│   └── reports/
├── 2024/
└── archive/

media/
├── images/
├── videos/
└── audio/

user_data/
├── {user_id}/
│   ├── uploads/
│   └── exports/
```

#### 2. File Naming

Use safe, descriptive filenames:

```python
import re
from datetime import datetime

def safe_filename(filename: str) -> str:
    """Create safe filename."""
    # Remove special characters
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Lowercase
    return filename.lower()

def timestamped_filename(original: str) -> str:
    """Add timestamp to filename."""
    name, ext = os.path.splitext(original)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{name}_{timestamp}{ext}"

# Usage
safe_name = safe_filename("My Report (2025).pdf")
# Result: "my_report_2025.pdf"

timestamped = timestamped_filename("report.pdf")
# Result: "report_20251026_143000.pdf"
```

#### 3. Error Handling

Handle storage errors gracefully:

```python
from requests.exceptions import RequestException

def upload_with_retry(file_path: str, remote_path: str, max_retries: int = 3):
    """Upload file with automatic retries."""
    for attempt in range(max_retries):
        try:
            with open(file_path, "rb") as f:
                response = requests.post(
                    f"{API_BASE}/api/v1/storage/upload",
                    params={"path": remote_path},
                    files={"file": f},
                    headers=headers,
                    timeout=300  # 5 minutes for large files
                )

            if response.status_code == 200:
                return response.json()

            if response.status_code == 413:
                raise ValueError("File too large (max 100MB)")

            if response.status_code == 409:
                # File exists, try with overwrite
                response = requests.post(
                    f"{API_BASE}/api/v1/storage/upload",
                    params={"path": remote_path, "overwrite": True},
                    files={"file": open(file_path, "rb")},
                    headers=headers
                )
                return response.json()

        except RequestException as e:
            if attempt == max_retries - 1:
                raise
            print(f"Retry {attempt + 1}/{max_retries}...")
            time.sleep(2 ** attempt)  # Exponential backoff
```

#### 4. Large File Handling

For files approaching the 100MB limit:

```python
import os

def check_file_size(file_path: str, max_mb: int = 100):
    """Check if file is within size limit."""
    size_bytes = os.path.getsize(file_path)
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > max_mb:
        raise ValueError(f"File too large: {size_mb:.1f}MB (max {max_mb}MB)")

    return size_mb

# Check before upload
try:
    size = check_file_size("large_video.mp4")
    print(f"File size: {size:.1f}MB - OK to upload")
except ValueError as e:
    print(f"Error: {e}")
```

#### 5. Batch Operations

Upload multiple files efficiently:

```python
import concurrent.futures
from pathlib import Path

def upload_directory(local_dir: str, remote_base: str):
    """Upload all files in a directory."""
    local_path = Path(local_dir)
    files_to_upload = []

    # Collect all files
    for file_path in local_path.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(local_path)
            remote_path = f"{remote_base}/{relative_path}"
            files_to_upload.append((str(file_path), remote_path))

    # Upload in parallel (max 5 concurrent)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(upload_file_sync, local, remote)
            for local, remote in files_to_upload
        ]

        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                print(f"✓ Uploaded: {result['filename']}")
            except Exception as e:
                print(f"✗ Failed: {e}")

    return results
```

---

### Security Considerations

1. **Organization Isolation**: Files are automatically scoped to your organization
2. **API Key Authentication**: All requests require valid API key
3. **HTTPS Only**: All data transmitted over secure HTTPS
4. **File Type Validation**: Validate file types before upload
5. **Size Limits**: 100MB max to prevent abuse
6. **Rate Limiting**: Prevents excessive API usage

---

### Storage Quotas

| Tier | Storage Space | Max File Size | Upload Rate | Download Rate |
|------|--------------|---------------|-------------|---------------|
| **Free** | 10 GB | 100 MB | 10/min | 20/min |
| **Starter** | 50 GB | 500 MB | 30/min | 60/min |
| **Professional** | 200 GB | 2 GB | 60/min | 120/min |
| **Enterprise** | Unlimited | 10 GB | Unlimited | Unlimited |

Contact sales for custom quotas: sales@ailabsafrica.com

---

## Phone Numbers API

Provision and manage virtual phone numbers for voice assistants with webhook-based call routing powered by Asterisk PBX.

**Current Status:** ✅ Fully Implemented
**Integration:** Asterisk PBX via REST API
**Base URL:** `https://api.ailabsafrica.com/api/phone-numbers`

### Overview

The Phone Numbers API enables you to:
- **Provision Virtual Numbers** - Create Kasa AI virtual phone numbers
- **Import Existing Numbers** - Import from Twilio, Vonage, or other providers
- **SIP Registration** - Automatic SIP peer configuration with Asterisk
- **Webhook Routing** - Dynamic call routing to voice assistants via webhooks
- **Number Management** - List, update, and delete provisioned numbers
- **Testing** - Generate temporary test numbers with FastRTC

**Key Features:**
- ✅ **Multiple Providers** - Kasa AI, Twilio, Vonage support
- ✅ **Automatic SIP Setup** - Seamless Asterisk integration
- ✅ **Webhook-Based Routing** - Flexible call handling
- ✅ **E.164 Format** - International number support
- ✅ **Assistant Linking** - Direct connection to voice assistants
- ✅ **Real-time Testing** - Gradio FastRTC integration

---

### Provision Phone Number

Create a new virtual phone number with automatic SIP registration.

**Endpoint:** `POST /api/phone-numbers/provision`

**Status:** ✅ Fully Implemented

**Request Body:**
```json
{
  "provider": "kasaai",
  "country_code": "+1",
  "area_code": "555",
  "plan": "professional",
  "assistant_id": "asst_123abc"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | string | Yes | Provider: `kasaai`, `twilio`, `vonage` |
| `country_code` | string | Yes | E.164 country code (e.g., `+1`, `+233`, `+44`) |
| `area_code` | string | No | Area code for number selection |
| `plan` | string | Yes | Pricing plan: `basic`, `professional`, `enterprise` |
| `assistant_id` | string | No | Voice assistant ID for automatic linking |

**Response:** `201 Created`
```json
{
  "id": "pn_789xyz",
  "number": "+15551234567",
  "provider": "kasaai",
  "status": "active",
  "sip_credentials": {
    "username": "kasaai_20251112120000",
    "password": "secure_sip_password_abc123",
    "server": "asterisk.ailabsafrica.com",
    "port": 5060,
    "context": "kasaai-virtual"
  },
  "webhook_url": "https://api.ailabsafrica.com/voice/webhook/kasaai_20251112120000",
  "assistant_id": "asst_123abc",
  "plan": "professional",
  "monthly_cost": 5.00,
  "created_at": "2025-11-12T12:00:00Z",
  "metadata": {}
}
```

**Status Values:**
- `active` - Number provisioned and ready
- `pending` - Provisioning in progress
- `suspended` - Number temporarily disabled
- `error` - Provisioning failed

---

### Import Phone Number

Import an existing phone number from external provider.

**Endpoint:** `POST /api/phone-numbers/import`

**Status:** ✅ Fully Implemented

**Request Body:**
```json
{
  "provider": "twilio",
  "number": "+14155551234",
  "credentials": {
    "account_sid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "auth_token": "your_twilio_auth_token"
  },
  "plan": "professional",
  "assistant_id": "asst_123abc"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | string | Yes | Provider: `twilio`, `vonage`, `bandwidth` |
| `number` | string | Yes | Phone number in E.164 format |
| `credentials` | object | Yes | Provider-specific credentials |
| `plan` | string | Yes | Pricing plan |
| `assistant_id` | string | No | Voice assistant ID |

**Provider Credentials:**

**Twilio:**
```json
{
  "account_sid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "auth_token": "your_auth_token"
}
```

**Vonage:**
```json
{
  "api_key": "your_api_key",
  "api_secret": "your_api_secret"
}
```

**Bandwidth:**
```json
{
  "account_id": "your_account_id",
  "username": "your_username",
  "password": "your_password"
}
```

**Response:** `201 Created`
```json
{
  "id": "pn_456def",
  "number": "+14155551234",
  "provider": "twilio",
  "status": "active",
  "sip_credentials": {
    "username": "twilio_20251112120500",
    "password": "secure_sip_password_xyz789",
    "server": "asterisk.ailabsafrica.com",
    "port": 5060,
    "context": "kasaai-virtual"
  },
  "webhook_url": "https://api.ailabsafrica.com/voice/webhook/twilio_20251112120500",
  "assistant_id": "asst_123abc",
  "plan": "professional",
  "created_at": "2025-11-12T12:05:00Z"
}
```

---

### List Phone Numbers

Get all provisioned phone numbers for your organization.

**Endpoint:** `GET /api/phone-numbers`

**Status:** ✅ Fully Implemented

**Query Parameters:**
- `limit` (integer, optional) - Items per page (default: 20, max: 100)
- `offset` (integer, optional) - Starting position (default: 0)
- `provider` (string, optional) - Filter by provider
- `status` (string, optional) - Filter by status

**Response:** `200 OK`
```json
{
  "phone_numbers": [
    {
      "id": "pn_789xyz",
      "number": "+15551234567",
      "provider": "kasaai",
      "status": "active",
      "assistant_id": "asst_123abc",
      "assistant_name": "Customer Support Bot",
      "plan": "professional",
      "monthly_cost": 5.00,
      "created_at": "2025-11-12T12:00:00Z"
    },
    {
      "id": "pn_456def",
      "number": "+14155551234",
      "provider": "twilio",
      "status": "active",
      "assistant_id": "asst_456def",
      "assistant_name": "Sales Assistant",
      "plan": "professional",
      "monthly_cost": 5.00,
      "created_at": "2025-11-12T11:00:00Z"
    }
  ],
  "total": 2,
  "limit": 20,
  "offset": 0
}
```

---

### Get Phone Number Details

Retrieve details of a specific phone number.

**Endpoint:** `GET /api/phone-numbers/{phone_number_id}`

**Status:** ✅ Fully Implemented

**Path Parameters:**
- `phone_number_id` (string, required) - Phone number ID

**Response:** `200 OK`
```json
{
  "id": "pn_789xyz",
  "number": "+15551234567",
  "provider": "kasaai",
  "status": "active",
  "sip_credentials": {
    "username": "kasaai_20251112120000",
    "server": "asterisk.ailabsafrica.com",
    "port": 5060,
    "context": "kasaai-virtual"
  },
  "webhook_url": "https://api.ailabsafrica.com/voice/webhook/kasaai_20251112120000",
  "assistant_id": "asst_123abc",
  "assistant_name": "Customer Support Bot",
  "plan": "professional",
  "monthly_cost": 5.00,
  "call_count": 47,
  "total_minutes": 235,
  "created_at": "2025-11-12T12:00:00Z",
  "last_call_at": "2025-11-12T15:30:00Z",
  "metadata": {}
}
```

---

### Update Phone Number

Update phone number configuration.

**Endpoint:** `PATCH /api/phone-numbers/{phone_number_id}`

**Status:** ✅ Fully Implemented

**Request Body:** (All fields optional)
```json
{
  "assistant_id": "asst_456def",
  "plan": "enterprise",
  "metadata": {
    "department": "sales",
    "region": "north_america"
  }
}
```

**Response:** `200 OK`
```json
{
  "id": "pn_789xyz",
  "number": "+15551234567",
  "assistant_id": "asst_456def",
  "plan": "enterprise",
  "updated_at": "2025-11-12T16:00:00Z"
}
```

---

### Delete Phone Number

Remove a phone number and unregister from Asterisk.

**Endpoint:** `DELETE /api/phone-numbers/{phone_number_id}`

**Status:** ✅ Fully Implemented

**Path Parameters:**
- `phone_number_id` (string, required) - Phone number ID

**Response:** `200 OK`
```json
{
  "id": "pn_789xyz",
  "number": "+15551234567",
  "deleted": true,
  "sip_unregistered": true,
  "webhook_removed": true,
  "deleted_at": "2025-11-12T16:30:00Z"
}
```

---

### Generate Test Phone Number

Create a temporary test phone number using FastRTC.

**Endpoint:** `POST /api/phone-numbers/test`

**Status:** ✅ Fully Implemented

**Request Body:**
```json
{
  "assistant_id": "asst_123abc",
  "ui_title": "Test Customer Support",
  "duration_hours": 24
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assistant_id` | string | Yes | Voice assistant ID |
| `ui_title` | string | No | Title for UI interface |
| `duration_hours` | integer | No | Expiration time 1-168 hours (default: 24) |

**Response:** `201 Created`
```json
{
  "test_phone": {
    "number": "+15551234999",
    "country": "US",
    "expires_at": "2025-11-13T12:00:00Z"
  },
  "shareable_link": {
    "url": "https://vapi.ai/test/abc123xyz",
    "expires_in_hours": 24
  },
  "assistant_id": "asst_123abc",
  "created_at": "2025-11-12T12:00:00Z"
}
```

---

### Link Phone to Assistant

Associate a phone number with a voice assistant.

**Endpoint:** `POST /api/phone-numbers/{phone_number_id}/link`

**Status:** ✅ Fully Implemented

**Request Body:**
```json
{
  "assistant_id": "asst_123abc"
}
```

**Response:** `200 OK`
```json
{
  "phone_number_id": "pn_789xyz",
  "number": "+15551234567",
  "assistant_id": "asst_123abc",
  "assistant_name": "Customer Support Bot",
  "webhook_url": "https://api.ailabsafrica.com/voice/webhook/asst_123abc",
  "updated_at": "2025-11-12T17:00:00Z"
}
```

---

### Unlink Phone from Assistant

Remove assistant association from a phone number.

**Endpoint:** `POST /api/phone-numbers/{phone_number_id}/unlink`

**Status:** ✅ Fully Implemented

**Response:** `200 OK`
```json
{
  "phone_number_id": "pn_789xyz",
  "number": "+15551234567",
  "assistant_id": null,
  "webhook_url": null,
  "updated_at": "2025-11-12T17:30:00Z"
}
```

---

### Get Phone Statistics

Retrieve usage statistics for a phone number.

**Endpoint:** `GET /api/phone-numbers/{phone_number_id}/stats`

**Status:** ✅ Fully Implemented

**Query Parameters:**
- `start_date` (string, optional) - Start date (ISO 8601)
- `end_date` (string, optional) - End date (ISO 8601)

**Response:** `200 OK`
```json
{
  "phone_number_id": "pn_789xyz",
  "number": "+15551234567",
  "period": {
    "start": "2025-11-01T00:00:00Z",
    "end": "2025-11-12T23:59:59Z"
  },
  "statistics": {
    "total_calls": 47,
    "successful_calls": 45,
    "failed_calls": 2,
    "total_minutes": 235.5,
    "average_duration": 5.03,
    "total_cost": 23.55
  },
  "daily_breakdown": [
    {
      "date": "2025-11-12",
      "calls": 5,
      "minutes": 27.3,
      "cost": 2.73
    }
  ]
}
```

---

### Phone Number Pricing

| Plan | Monthly Cost | Included Minutes | Per-Minute Rate | Features |
|------|-------------|------------------|-----------------|----------|
| **Basic** | $2/mo | 100 min | $0.05/min | Single assistant, basic support |
| **Professional** | $5/mo | 500 min | $0.03/min | Multiple assistants, priority support |
| **Enterprise** | Custom | Custom | $0.02/min | Dedicated support, SLA, custom integration |

**Additional Costs:**
- Overage minutes: Per-minute rate applies
- International calls: Varies by destination
- SMS (if enabled): $0.0075 per message

---

### Asterisk Integration

All phone numbers are automatically registered with Asterisk PBX:

**SIP Configuration:**
- **Server:** asterisk.ailabsafrica.com
- **Port:** 5060 (SIP), 5061 (SIPS)
- **Transport:** UDP, TCP, TLS
- **Codecs:** ulaw, alaw, opus
- **Context:** kasaai-virtual

**Webhook Call Flow:**
```
Incoming Call → Asterisk PBX
                    ↓
            Lookup webhook from AstDB
                    ↓
            Invoke webhook with call details
                    ↓
            Voice Assistant processes call
                    ↓
            Call ends, recording saved
```

**Webhook Payload:**
```json
{
  "event": "call.incoming",
  "call_id": "1731419234.123",
  "caller": {
    "number": "+233244123456"
  },
  "called": {
    "number": "+15551234567"
  },
  "timestamp": "2025-11-12T13:30:00Z"
}
```

---

### Error Responses

**400 Bad Request - Invalid Number Format**
```json
{
  "error": {
    "code": "INVALID_NUMBER_FORMAT",
    "message": "Phone number must be in E.164 format (e.g., +15551234567)",
    "field": "number"
  }
}
```

**402 Payment Required - Insufficient Balance**
```json
{
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "Wallet balance insufficient for phone number provisioning",
    "required_amount": 5.00,
    "current_balance": 2.50
  }
}
```

**409 Conflict - Number Already Exists**
```json
{
  "error": {
    "code": "NUMBER_ALREADY_EXISTS",
    "message": "Phone number +15551234567 is already provisioned",
    "existing_id": "pn_789xyz"
  }
}
```

**503 Service Unavailable - Asterisk Offline**
```json
{
  "error": {
    "code": "ASTERISK_UNAVAILABLE",
    "message": "Asterisk PBX service is temporarily unavailable",
    "retry_after": 60
  }
}
```

---

### Code Examples

**Python - Provision Phone Number**
```python
import httpx

async def provision_phone_number(api_key: str, assistant_id: str):
    """Provision a new phone number"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.ailabsafrica.com/api/phone-numbers/provision",
            headers={"X-API-Key": api_key},
            json={
                "provider": "kasaai",
                "country_code": "+1",
                "area_code": "555",
                "plan": "professional",
                "assistant_id": assistant_id
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
result = await provision_phone_number(
    "kasa_live_1234567890abcdef",
    "asst_123abc"
)
print(f"Provisioned: {result['number']}")
print(f"SIP Username: {result['sip_credentials']['username']}")
```

**JavaScript - Import Phone Number**
```javascript
async function importPhoneNumber(apiKey, twilioNumber, credentials, assistantId) {
  const response = await fetch('https://api.ailabsafrica.com/api/phone-numbers/import', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey
    },
    body: JSON.stringify({
      provider: 'twilio',
      number: twilioNumber,
      credentials: {
        account_sid: credentials.accountSid,
        auth_token: credentials.authToken
      },
      plan: 'professional',
      assistant_id: assistantId
    })
  });

  return await response.json();
}

// Usage
const result = await importPhoneNumber(
  'kasa_live_1234567890abcdef',
  '+14155551234',
  {
    accountSid: 'ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    authToken: 'your_auth_token'
  },
  'asst_123abc'
);

console.log(`Imported: ${result.number}`);
console.log(`Webhook: ${result.webhook_url}`);
```

**cURL - List Phone Numbers**
```bash
curl -X GET "https://api.ailabsafrica.com/api/phone-numbers?limit=20" \
  -H "X-API-Key: kasa_live_1234567890abcdef"
```

**cURL - Delete Phone Number**
```bash
curl -X DELETE "https://api.ailabsafrica.com/api/phone-numbers/pn_789xyz" \
  -H "X-API-Key: kasa_live_1234567890abcdef"
```

---

## Usage Calculator API

Calculate costs for services with tiered pricing.

### Calculate RAG Cost

Calculate cost for RAG operations.

**Endpoint:** `POST /api/v1/usage/calculate/rag`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Request Body:**
```json
{
  "input_tokens": 500,
  "output_tokens": 200,
  "num_queries": 1,
  "pricing_tier": "basic"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `input_tokens` | integer | Yes | Input tokens consumed |
| `output_tokens` | integer | Yes | Output tokens generated |
| `num_queries` | integer | Yes | Number of queries (min: 1) |
| `pricing_tier` | string | No | Tier: `free`, `basic`, `premium`, `enterprise` (default: `basic`) |

**Response:** `200 OK`
```json
{
  "service": "rag",
  "unit_cost": 0.007,
  "quantity": 1,
  "total_cost": 0.007,
  "currency": "GHS",
  "pricing_tier": "basic",
  "breakdown": {
    "input_tokens_cost": 0.005,
    "output_tokens_cost": 0.002
  }
}
```

**Pricing Tiers:**
- **Free:** Standard rates, no discounts
- **Basic:** Standard rates
- **Premium:** 20% discount
- **Enterprise:** 40% discount

---

### Calculate Voice Call Cost

Calculate cost for voice calls.

**Endpoint:** `POST /api/v1/usage/calculate/voice`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Request Body:**
```json
{
  "duration_minutes": 5.5,
  "direction": "outbound",
  "platform": "vapi",
  "pricing_tier": "premium"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `duration_minutes` | float | Yes | Call duration (min: 0.01) |
| `direction` | string | Yes | Direction: `inbound`, `outbound` |
| `platform` | string | Yes | Platform: `vapi`, `voice_lab` |
| `pricing_tier` | string | No | Tier: `free`, `basic`, `premium`, `enterprise` |

**Response:** `200 OK`
```json
{
  "service": "voice_call",
  "unit_cost": 0.40,
  "quantity": 5.5,
  "total_cost": 2.20,
  "currency": "GHS",
  "pricing_tier": "premium",
  "breakdown": {
    "base_rate_per_minute": 0.50,
    "discount": 0.10
  }
}
```

---

### Calculate Document Processing Cost

Calculate cost for document processing.

**Endpoint:** `POST /api/v1/usage/calculate/document`

**Status:** ⚠️ Coming Soon (501 Not Implemented)

**Request Body:**
```json
{
  "num_pages": 50,
  "file_size_mb": 5.0,
  "pricing_tier": "enterprise"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `num_pages` | integer | Yes | Number of pages (min: 1) |
| `file_size_mb` | float | Yes | File size in MB (min: 0.01) |
| `pricing_tier` | string | No | Tier: `free`, `basic`, `premium`, `enterprise` |

**Response:** `200 OK`
```json
{
  "service": "document_processing",
  "unit_cost": 0.006,
  "quantity": 50,
  "total_cost": 0.30,
  "currency": "GHS",
  "pricing_tier": "enterprise",
  "breakdown": {
    "base_rate_per_page": 0.01,
    "discount": 0.004
  }
}
```

---

## Code Examples

### Python

```python
import requests

# Configuration
API_KEY = "kasa_live_1234567890abcdef"
BASE_URL = "https://developer.ailabsafrica.com"
headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Create an assistant
assistant_data = {
    "name": "Sales Assistant",
    "system_prompt": "You are a helpful sales assistant...",
    "voice": "alloy",
    "language": "en"
}

response = requests.post(
    f"{BASE_URL}/api/v1/assistants",
    headers=headers,
    json=assistant_data
)

if response.status_code == 201:
    assistant = response.json()
    print(f"Created assistant: {assistant['id']}")

    # Initiate a call
    call_data = {
        "assistant_id": assistant["id"],
        "to_number": "+14155551234"
    }

    call_response = requests.post(
        f"{BASE_URL}/api/v1/calls",
        headers=headers,
        json=call_data
    )

    if call_response.status_code == 201:
        call = call_response.json()
        print(f"Initiated call: {call['id']}")
else:
    print(f"Error: {response.json()}")

# ====================================================================
# LLM, ASR, and TTS Examples
# ====================================================================

# Chat with LLM
llm_request = {
    "model_id": "kasaai_llama_twi",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of Ghana?"}
    ],
    "temperature": 0.7
}

llm_response = requests.post(
    f"{BASE_URL}/api/v1/llm/chat",
    headers=headers,
    json=llm_request
)

if llm_response.status_code == 200:
    result = llm_response.json()
    print(f"LLM Response: {result['message']}")
    print(f"Cost: ${result['cost']:.4f}")
    print(f"Tokens used: {result['usage']['total_tokens']}")

# Transcribe audio
import base64

# Read audio file
with open('audio.wav', 'rb') as audio_file:
    files = {'audio_file': audio_file}
    data = {
        'provider_id': 'whisper_large_v3',
        'language': 'en'
    }

    asr_response = requests.post(
        f"{BASE_URL}/api/v1/asr/transcribe",
        headers={'X-API-Key': API_KEY},  # multipart/form-data, no Content-Type
        files=files,
        data=data
    )

    if asr_response.status_code == 200:
        result = asr_response.json()
        print(f"Transcription: {result['text']}")
        print(f"Cost: ${result['cost']:.4f}")
        print(f"Duration: {result['duration']}s")

# Get TTS providers
tts_response = requests.get(
    f"{BASE_URL}/api/v1/tts/providers",
    headers={'X-API-Key': API_KEY}
)

if tts_response.status_code == 200:
    providers = tts_response.json()
    print(f"Available TTS providers: {providers['count']}")
    for provider_id, provider in providers['providers'].items():
        print(f"  - {provider['name']} ({provider['status']})")
```

---

### JavaScript/Node.js

```javascript
const axios = require('axios');

const API_KEY = 'kasa_live_1234567890abcdef';
const BASE_URL = 'https://developer.ailabsafrica.com';

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  }
});

// Create an assistant
async function createAssistant() {
  try {
    const response = await client.post('/api/v1/assistants', {
      name: 'Sales Assistant',
      system_prompt: 'You are a helpful sales assistant...',
      voice: 'alloy',
      language: 'en'
    });

    console.log('Created assistant:', response.data.id);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

// Initiate a call
async function initiateCall(assistantId) {
  try {
    const response = await client.post('/api/v1/calls', {
      assistant_id: assistantId,
      to_number: '+14155551234'
    });

    console.log('Initiated call:', response.data.id);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

// Usage
(async () => {
  const assistant = await createAssistant();
  if (assistant) {
    await initiateCall(assistant.id);
  }
})();

// ====================================================================
// LLM, ASR, and TTS Examples
// ====================================================================

// Chat with LLM
async function chatWithLLM() {
  try {
    const response = await client.post('/api/v1/llm/chat', {
      model_id: 'kasaai_llama_twi',
      messages: [
        { role: 'system', content: 'You are a helpful assistant.' },
        { role: 'user', content: 'What is the capital of Ghana?' }
      ],
      temperature: 0.7
    });

    console.log('LLM Response:', response.data.message);
    console.log('Cost: $', response.data.cost.toFixed(4));
    console.log('Tokens:', response.data.usage.total_tokens);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

// Transcribe audio
async function transcribeAudio() {
  const FormData = require('form-data');
  const fs = require('fs');

  const form = new FormData();
  form.append('audio_file', fs.createReadStream('audio.wav'));
  form.append('provider_id', 'whisper_large_v3');
  form.append('language', 'en');

  try {
    const response = await axios.post(
      `${BASE_URL}/api/v1/asr/transcribe`,
      form,
      {
        headers: {
          'X-API-Key': API_KEY,
          ...form.getHeaders()
        }
      }
    );

    console.log('Transcription:', response.data.text);
    console.log('Cost: $', response.data.cost.toFixed(4));
    console.log('Duration:', response.data.duration, 's');
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

// Get TTS providers
async function getTTSProviders() {
  try {
    const response = await axios.get(
      `${BASE_URL}/api/v1/tts/providers`,
      { headers: { 'X-API-Key': API_KEY } }
    );

    console.log('Available TTS providers:', response.data.count);
    Object.entries(response.data.providers).forEach(([id, provider]) => {
      console.log(`  - ${provider.name} (${provider.status})`);
    });
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

// Run examples
(async () => {
  await chatWithLLM();
  await transcribeAudio();
  await getTTSProviders();
})();
```

---

### cURL

```bash
# Create an assistant
curl -X POST https://developer.ailabsafrica.com/api/v1/assistants \
  -H "X-API-Key: kasa_live_1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Assistant",
    "system_prompt": "You are a helpful sales assistant...",
    "voice": "alloy",
    "language": "en"
  }'

# List assistants
curl -X GET https://developer.ailabsafrica.com/api/v1/assistants \
  -H "X-API-Key: kasa_live_1234567890abcdef"

# Initiate a call
curl -X POST https://developer.ailabsafrica.com/api/v1/calls \
  -H "X-API-Key: kasa_live_1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "asst_123abc",
    "to_number": "+14155551234"
  }'

# Create a workflow
curl -X POST https://developer.ailabsafrica.com/api/v1/workflows \
  -H "X-API-Key: kasa_live_1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Onboarding",
    "nodes": [...],
    "connections": {},
    "active": false
  }'

# ====================================================================
# LLM, ASR, and TTS Examples
# ====================================================================

# Chat with LLM
curl -X POST https://developer.ailabsafrica.com/api/v1/llm/chat \
  -H "X-API-Key: kasa_live_1234567890abcdef" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "kasaai_llama_twi",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is the capital of Ghana?"}
    ],
    "temperature": 0.7
  }'

# Transcribe audio file
curl -X POST https://developer.ailabsafrica.com/api/v1/asr/transcribe \
  -H "X-API-Key: kasa_live_1234567890abcdef" \
  -F "audio_file=@audio.wav" \
  -F "provider_id=whisper_large_v3" \
  -F "language=en"

# Get TTS providers
curl -X GET https://developer.ailabsafrica.com/api/v1/tts/providers \
  -H "X-API-Key: kasa_live_1234567890abcdef"

# List LLM providers
curl -X GET https://developer.ailabsafrica.com/api/v1/llm/providers \
  -H "X-API-Key: kasa_live_1234567890abcdef"

# List ASR providers
curl -X GET https://developer.ailabsafrica.com/api/v1/asr/providers \
  -H "X-API-Key: kasa_live_1234567890abcdef"
```

---

### PHP

```php
<?php

$apiKey = 'kasa_live_1234567890abcdef';
$baseUrl = 'https://developer.ailabsafrica.com';

function makeRequest($method, $endpoint, $data = null) {
    global $apiKey, $baseUrl;

    $ch = curl_init($baseUrl . $endpoint);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'X-API-Key: ' . $apiKey,
        'Content-Type: application/json'
    ]);

    if ($method === 'POST') {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    }

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    return [
        'status' => $httpCode,
        'data' => json_decode($response, true)
    ];
}

// Create an assistant
$assistant = makeRequest('POST', '/api/v1/assistants', [
    'name' => 'Sales Assistant',
    'system_prompt' => 'You are a helpful sales assistant...',
    'voice' => 'alloy',
    'language' => 'en'
]);

if ($assistant['status'] === 201) {
    echo "Created assistant: " . $assistant['data']['id'] . "\n";

    // Initiate a call
    $call = makeRequest('POST', '/api/v1/calls', [
        'assistant_id' => $assistant['data']['id'],
        'to_number' => '+14155551234'
    ]);

    if ($call['status'] === 201) {
        echo "Initiated call: " . $call['data']['id'] . "\n";
    }
}

?>
```

---

## Webhooks

Receive real-time notifications about events in your account.

### Webhook Events

| Event | Description |
|-------|-------------|
| `assistant.created` | New assistant created |
| `call.initiated` | Call started |
| `call.answered` | Call answered |
| `call.ended` | Call completed |
| `workflow.activated` | Workflow activated |
| `execution.completed` | Workflow execution finished |

### Webhook Payload

```json
{
  "event": "call.ended",
  "timestamp": "2025-10-23T12:07:00Z",
  "data": {
    "id": "call_789xyz",
    "assistant_id": "asst_123abc",
    "status": "ended",
    "duration": 120,
    "recording_url": "https://recordings.vapi.ai/call_789xyz.mp3"
  }
}
```

### Webhook Security

All webhook requests include a signature header:

```http
X-Webhook-Signature: sha256=abc123...
```

**Verify the signature:**
```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## Email Account Management API

**Base URL:** `https://developer.ailabsafrica.com/api/v1/email`
**Authentication:** Required (X-API-Key header)
**Status:** ✅ Production (v1.5.0)
**Mail Server:** mail.ailabsafrica.com (iRedMail)

### Overview

The Email Account Management API allows developers to programmatically create, manage, and control email accounts on the organization's iRedMail server. This API is ideal for:

- **Employee Onboarding:** Automatically create email accounts when employees join
- **Account Lifecycle Management:** Disable/enable accounts during termination, leave, or return
- **HR System Integration:** Connect with HRIS systems for automated email provisioning
- **Bulk User Management:** Create email accounts for multiple users at once
- **Custom User Portals:** Build self-service email account request systems

#### Key Features

✅ **Automatic Email Generation** - Generates firstname.lastname@ailabsafrica.com format
✅ **Duplicate Handling** - Smart suffix addition (john.doe2@, john.doe3@, etc.)
✅ **Temporary Passwords** - Secure random passwords generated for each account
✅ **Account Suspension** - Disable accounts without losing email data
✅ **Account Restoration** - Re-enable disabled accounts
✅ **Quota Management** - Customizable mailbox sizes (1 MB - 10 GB)
✅ **Existence Checks** - Verify account availability before creation
✅ **Email Preview** - Generate email addresses without creating accounts

#### Rate Limits

| Endpoint | Rate Limit | Quota Cost |
|----------|-----------|------------|
| Create Account | 10 per minute | 1 credit |
| Disable/Enable | 10 per minute | Free |
| Check Exists | 20 per minute | Free |
| Generate Email | 20 per minute | Free |
| Get Config | 100 per minute | Free |

---

### Endpoints

#### 1. Create Email Account

**POST** `/api/v1/email/accounts`

Creates a new email account on the iRedMail server.

**Request Body:**

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@ailabsafrica.com",  // Optional - auto-generated if not provided
  "quota_mb": 512  // Optional - defaults to 512 MB
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `first_name` | string | ✅ Yes | Employee first name (min 1 char) |
| `last_name` | string | ✅ Yes | Employee last name (min 1 char) |
| `email` | string | ❌ No | Email address (auto-generated if omitted) |
| `quota_mb` | integer | ❌ No | Mailbox quota 1-10240 MB (default: 512) |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "email": "john.doe@ailabsafrica.com",
    "password": "rA9#mK2$pQ8@vL4!",
    "status": "created",
    "created_at": "2025-11-03T21:15:00.123456",
    "quota_mb": 512
  },
  "message": "Email account created successfully",
  "request_id": "req_abc123"
}
```

**Errors:**

| Status Code | Error Code | Description |
|-------------|-----------|-------------|
| 400 | VALIDATION_ERROR | Invalid request parameters |
| 409 | RESOURCE_CONFLICT | Email already exists |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | INTERNAL_ERROR | Server error creating account |

**Example - cURL:**

```bash
curl -X POST https://developer.ailabsafrica.com/api/v1/email/accounts \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "quota_mb": 1024
  }'
```

**Example - Python:**

```python
import requests

url = "https://developer.ailabsafrica.com/api/v1/email/accounts"
headers = {
    "X-API-Key": "your_api_key_here",
    "Content-Type": "application/json"
}
data = {
    "first_name": "John",
    "last_name": "Doe",
    "quota_mb": 1024
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

if result["success"]:
    print(f"Email created: {result['data']['email']}")
    print(f"Temporary password: {result['data']['password']}")
else:
    print(f"Error: {result['error']['message']}")
```

**Example - JavaScript/Node.js:**

```javascript
const axios = require('axios');

const createEmailAccount = async () => {
  try {
    const response = await axios.post(
      'https://developer.ailabsafrica.com/api/v1/email/accounts',
      {
        first_name: 'John',
        last_name: 'Doe',
        quota_mb: 1024
      },
      {
        headers: {
          'X-API-Key': 'your_api_key_here',
          'Content-Type': 'application/json'
        }
      }
    );

    const result = response.data;
    console.log('Email created:', result.data.email);
    console.log('Temporary password:', result.data.password);
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
};

createEmailAccount();
```

---

#### 2. Disable Email Account

**POST** `/api/v1/email/accounts/disable`

Disables an email account. The user cannot login, but all emails and folders are preserved. This is useful for employee termination or temporary suspension.

**Request Body:**

```json
{
  "email": "john.doe@ailabsafrica.com"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "email": "john.doe@ailabsafrica.com",
    "status": "disabled",
    "message": "Account disabled successfully"
  },
  "message": "Email account disabled successfully",
  "request_id": "req_def456"
}
```

**Example - cURL:**

```bash
curl -X POST https://developer.ailabsafrica.com/api/v1/email/accounts/disable \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@ailabsafrica.com"
  }'
```

---

#### 3. Enable Email Account

**POST** `/api/v1/email/accounts/enable`

Re-enables a previously disabled email account. The user can login and access emails again.

**Request Body:**

```json
{
  "email": "john.doe@ailabsafrica.com"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "email": "john.doe@ailabsafrica.com",
    "status": "enabled",
    "message": "Account enabled successfully"
  },
  "message": "Email account enabled successfully",
  "request_id": "req_ghi789"
}
```

---

#### 4. Check Email Exists

**POST** `/api/v1/email/accounts/check`

Checks if an email account exists on the server. Useful for verifying before creating accounts or checking for duplicates.

**Request Body:**

```json
{
  "email": "john.doe@ailabsafrica.com"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "email": "john.doe@ailabsafrica.com",
    "exists": true
  },
  "message": "Email check completed successfully",
  "request_id": "req_jkl012"
}
```

**Example - Python:**

```python
import requests

url = "https://developer.ailabsafrica.com/api/v1/email/accounts/check"
headers = {
    "X-API-Key": "your_api_key_here",
    "Content-Type": "application/json"
}
data = {
    "email": "john.doe@ailabsafrica.com"
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

if result["data"]["exists"]:
    print(f"Email {result['data']['email']} already exists")
else:
    print(f"Email {result['data']['email']} is available")
```

---

#### 5. Generate Email Address

**POST** `/api/v1/email/accounts/generate-email`

Generates and previews an email address without creating the account. Useful for checking availability and preview before account creation.

**Request Body:**

```json
{
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "email": "john.doe@ailabsafrica.com",
    "available": true
  },
  "message": "Email generated successfully",
  "request_id": "req_mno345"
}
```

**Example - cURL:**

```bash
curl -X POST https://developer.ailabsafrica.com/api/v1/email/accounts/generate-email \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe"
  }'
```

---

#### 6. Get Email Service Configuration

**GET** `/api/v1/email/config`

Retrieves email service configuration, including domain, quota limits, rate limits, and server details.

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "domain": "ailabsafrica.com",
    "default_quota_mb": 512,
    "max_quota_mb": 10240,
    "rate_limits": {
      "create": "10 per minute",
      "disable": "10 per minute",
      "enable": "10 per minute",
      "check": "20 per minute",
      "generate": "20 per minute",
      "config": "100 per minute"
    },
    "features": {
      "auto_generation": true,
      "duplicate_handling": true,
      "quota_customization": true,
      "account_suspension": true,
      "account_restoration": true
    },
    "server": {
      "webmail_url": "https://mail.ailabsafrica.com",
      "smtp_server": "mail.ailabsafrica.com",
      "smtp_port": 587,
      "imap_server": "mail.ailabsafrica.com",
      "imap_port": 993
    }
  },
  "message": "Email configuration retrieved successfully",
  "request_id": "req_pqr678"
}
```

**Example - cURL:**

```bash
curl -X GET https://developer.ailabsafrica.com/api/v1/email/config \
  -H "X-API-Key: your_api_key_here"
```

---

### Common Use Cases

#### Use Case 1: Employee Onboarding Automation

```python
import requests

def onboard_employee(first_name, last_name):
    """Automatically create email account during employee onboarding."""

    # Step 1: Generate email to check availability
    generate_url = "https://developer.ailabsafrica.com/api/v1/email/accounts/generate-email"
    headers = {"X-API-Key": "your_api_key_here", "Content-Type": "application/json"}

    response = requests.post(generate_url, headers=headers, json={
        "first_name": first_name,
        "last_name": last_name
    })

    email_preview = response.json()
    suggested_email = email_preview["data"]["email"]
    is_available = email_preview["data"]["available"]

    print(f"Suggested email: {suggested_email} (Available: {is_available})")

    # Step 2: Create the email account
    create_url = "https://developer.ailabsafrica.com/api/v1/email/accounts"
    response = requests.post(create_url, headers=headers, json={
        "first_name": first_name,
        "last_name": last_name,
        "quota_mb": 1024  # 1 GB for employees
    })

    result = response.json()

    if result["success"]:
        email = result["data"]["email"]
        password = result["data"]["password"]

        print(f"✅ Email account created successfully!")
        print(f"   Email: {email}")
        print(f"   Temporary Password: {password}")
        print(f"   Webmail: https://mail.ailabsafrica.com")

        # TODO: Send welcome email with credentials
        # TODO: Update HRIS database with email details

        return {
            "success": True,
            "email": email,
            "password": password
        }
    else:
        print(f"❌ Failed to create email: {result['error']['message']}")
        return {"success": False, "error": result["error"]["message"]}

# Example usage
onboard_employee("Jane", "Smith")
```

#### Use Case 2: Employee Termination

```python
import requests

def offboard_employee(email):
    """Disable email account during employee termination."""

    url = "https://developer.ailabsafrica.com/api/v1/email/accounts/disable"
    headers = {"X-API-Key": "your_api_key_here", "Content-Type": "application/json"}

    response = requests.post(url, headers=headers, json={"email": email})
    result = response.json()

    if result["success"]:
        print(f"✅ Email account disabled: {email}")
        print(f"   Status: {result['data']['status']}")
        print(f"   All emails preserved for compliance")
        return True
    else:
        print(f"❌ Failed to disable email: {result['error']['message']}")
        return False

# Example usage
offboard_employee("john.doe@ailabsafrica.com")
```

#### Use Case 3: Bulk User Creation

```python
import requests
import time

def bulk_create_emails(employees):
    """Create email accounts for multiple employees."""

    url = "https://developer.ailabsafrica.com/api/v1/email/accounts"
    headers = {"X-API-Key": "your_api_key_here", "Content-Type": "application/json"}

    results = []

    for employee in employees:
        try:
            response = requests.post(url, headers=headers, json={
                "first_name": employee["first_name"],
                "last_name": employee["last_name"],
                "quota_mb": employee.get("quota_mb", 512)
            })

            result = response.json()

            if result["success"]:
                results.append({
                    "name": f"{employee['first_name']} {employee['last_name']}",
                    "email": result["data"]["email"],
                    "password": result["data"]["password"],
                    "status": "success"
                })
                print(f"✅ Created: {result['data']['email']}")
            else:
                results.append({
                    "name": f"{employee['first_name']} {employee['last_name']}",
                    "error": result["error"]["message"],
                    "status": "failed"
                })
                print(f"❌ Failed: {result['error']['message']}")

            # Respect rate limits (10 per minute)
            time.sleep(6)

        except Exception as e:
            print(f"❌ Error processing {employee['first_name']} {employee['last_name']}: {str(e)}")
            results.append({
                "name": f"{employee['first_name']} {employee['last_name']}",
                "error": str(e),
                "status": "error"
            })

    return results

# Example usage
employees = [
    {"first_name": "Alice", "last_name": "Johnson", "quota_mb": 1024},
    {"first_name": "Bob", "last_name": "Williams", "quota_mb": 512},
    {"first_name": "Carol", "last_name": "Davis", "quota_mb": 2048}
]

results = bulk_create_emails(employees)

# Print summary
print(f"\n📊 Summary:")
print(f"   Total: {len(results)}")
print(f"   Success: {sum(1 for r in results if r['status'] == 'success')}")
print(f"   Failed: {sum(1 for r in results if r['status'] != 'success')}")
```

---

### Email Account Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                     Email Account Lifecycle                 │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐    POST /accounts    ┌──────────────┐
│   No Account │ ─────────────────────▶│    Active    │
│  (Available) │                       │   Account    │
└──────────────┘                       └──────┬───────┘
                                              │
                                              │ POST /disable
                                              ▼
                                       ┌──────────────┐
                                       │   Disabled   │
                                       │   Account    │
                                       │ (Data Kept)  │
                                       └──────┬───────┘
                                              │
                                              │ POST /enable
                                              ▼
                                       ┌──────────────┐
                                       │ Re-activated │
                                       │   Account    │
                                       └──────────────┘
```

---

### Error Handling

All endpoints follow the standard API error format:

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_CONFLICT",
    "message": "Email account already exists",
    "details": {
      "email": "john.doe@ailabsafrica.com",
      "suggestion": "Use john.doe2@ailabsafrica.com"
    }
  },
  "request_id": "req_xyz890"
}
```

**Common Error Codes:**

| Code | HTTP Status | Description | Solution |
|------|-------------|-------------|----------|
| VALIDATION_ERROR | 400 | Invalid request parameters | Check request format and required fields |
| RESOURCE_CONFLICT | 409 | Email already exists | Use different email or check suggestion |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests | Wait before retrying, respect rate limits |
| INTERNAL_ERROR | 500 | Server error | Contact support with request_id |

---

### Best Practices

#### 1. Secure Password Handling

```python
# ✅ GOOD: Immediately deliver password and clear from memory
password = result["data"]["password"]
send_welcome_email(employee_email, password)
del password  # Clear password from memory

# ❌ BAD: Storing passwords in logs or databases
logging.info(f"Created account with password: {password}")  # Don't do this!
```

#### 2. Rate Limit Management

```python
import time
from datetime import datetime

class RateLimiter:
    def __init__(self, requests_per_minute=10):
        self.rpm = requests_per_minute
        self.last_request_times = []

    def wait_if_needed(self):
        now = datetime.now()

        # Remove requests older than 1 minute
        self.last_request_times = [
            t for t in self.last_request_times
            if (now - t).seconds < 60
        ]

        # If at limit, wait
        if len(self.last_request_times) >= self.rpm:
            sleep_time = 60 - (now - self.last_request_times[0]).seconds
            time.sleep(sleep_time + 1)

        self.last_request_times.append(now)

# Usage
limiter = RateLimiter(requests_per_minute=10)

for employee in employees:
    limiter.wait_if_needed()
    create_email_account(employee)
```

#### 3. Idempotent Creation

```python
def create_email_safely(first_name, last_name):
    """Create email with duplicate check."""

    # First check if email exists
    check_response = requests.post(
        "https://developer.ailabsafrica.com/api/v1/email/accounts/check",
        headers=headers,
        json={"email": f"{first_name.lower()}.{last_name.lower()}@ailabsafrica.com"}
    )

    if check_response.json()["data"]["exists"]:
        print("Email already exists, skipping creation")
        return {"success": True, "status": "already_exists"}

    # Create if doesn't exist
    create_response = requests.post(
        "https://developer.ailabsafrica.com/api/v1/email/accounts",
        headers=headers,
        json={"first_name": first_name, "last_name": last_name}
    )

    return create_response.json()
```

---

### Integration with Other Systems

#### HR Information System (HRIS)

```python
# Example: Integrate with BambooHR
import requests

def sync_employee_from_bamboohr(employee_id):
    """Sync employee from BambooHR and create email account."""

    # Get employee details from BambooHR
    bamboo_api = "https://api.bamboohr.com/api/gateway.php/company/v1/"
    bamboo_headers = {"Authorization": f"Basic {bamboo_api_key}"}

    employee_data = requests.get(
        f"{bamboo_api}employees/{employee_id}",
        headers=bamboo_headers
    ).json()

    # Create email account via KasaAI
    kasaai_api = "https://developer.ailabsafrica.com/api/v1/email/accounts"
    kasaai_headers = {"X-API-Key": kasaai_api_key}

    email_result = requests.post(
        kasaai_api,
        headers=kasaai_headers,
        json={
            "first_name": employee_data["firstName"],
            "last_name": employee_data["lastName"],
            "quota_mb": 1024
        }
    ).json()

    if email_result["success"]:
        # Update BambooHR with email details
        requests.post(
            f"{bamboo_api}employees/{employee_id}",
            headers=bamboo_headers,
            json={"workEmail": email_result["data"]["email"]}
        )

        return email_result
```

---

### Testing

Use the sandbox environment for testing:

**Sandbox Base URL:** `https://dev-developer.ailabsafrica.com/api/v1/email`

**Test API Key:** Contact support for sandbox credentials

**Note:** Sandbox accounts are automatically cleaned up after 24 hours.

---

## ERP Partnership Management API

**Version:** v1.6.0 (2025-11-08)
**Base URL:** `https://dev-erp-api.ailabsafrica.com/api/v1/partnerships` (Dev)
**Production URL:** `https://erp-api.ailabsafrica.com/api/v1/partnerships` (Coming Soon)
**Status:** ✅ Fully Implemented (Dev Environment)

### Overview

The ERP Partnership Management API provides comprehensive tools for tracking and managing business partnerships throughout their entire lifecycle, from prospect to active partnership.

#### Key Features

🤝 **Partnership Lifecycle Management**
- Track partnerships from prospect stage through to active partnerships
- Support for multiple partnership types (Vendor, Technology, Strategic, Reseller, etc.)
- Stage-based workflow (Prospect → Discussion → Proposal → Agreement → Active)

📋 **Contact Management**
- Store primary and secondary contacts with full details
- Email, phone, and position tracking
- Multiple contacts per partnership

📁 **Document Management** (Cloud Storage)
- Upload proposals, contracts, and supporting documents
- Hetzner Storage Box integration (WebDAV)
- Organization-scoped storage (secure isolation)
- File download and listing capabilities

📊 **Interaction Tracking**
- Record emails, calls, meetings, and video calls
- Timestamped interaction history
- Notes and follow-up tracking

💰 **Financial Tracking**
- Expected revenue and actual revenue monitoring
- Payment terms and revenue share percentages
- Financial statistics and reporting

📈 **Statistics Dashboard**
- Partnership metrics by stage and type
- Revenue totals and trends
- Interaction counts and analytics

### Partnership Types

- **Vendor** - Suppliers and service providers
- **Technology** - Technology partnerships and integrations
- **Strategic** - Strategic alliances
- **Reseller** - Reseller and distribution partners
- **Distributor** - Distribution partners
- **Affiliate** - Affiliate marketing partners
- **Consulting** - Consulting partnerships

### Partnership Stages

1. **Prospect** - Initial identification
2. **Initial Contact** - First communication established
3. **Discussion** - Active discussions and exploration
4. **Proposal Sent** - Proposal submitted for review
5. **Negotiation** - Terms and conditions being negotiated
6. **Agreement Signed** - Contract signed, awaiting activation
7. **Active** - Partnership is active and operational
8. **On Hold** - Temporarily paused
9. **Inactive** - Not currently active
10. **Terminated** - Partnership ended

---

### Create Partnership

Create a new partnership record.

**Endpoint:** `POST /api/v1/partnerships/partnerships`

**Status:** ✅ Fully Implemented

**Request Body:**
```json
{
  "partner_name": "Tech Solutions Inc",
  "partnership_type": "Technology",
  "stage": "Prospect",
  "description": "Cloud infrastructure partnership for AI services",
  "primary_contact": {
    "name": "John Smith",
    "email": "john.smith@techsolutions.com",
    "phone": "+14155551234",
    "position": "VP of Partnerships"
  },
  "secondary_contact": {
    "name": "Jane Doe",
    "email": "jane.doe@techsolutions.com",
    "phone": "+14155555678",
    "position": "Account Manager"
  },
  "proposal_sent_date": "2025-11-01",
  "expected_revenue": 50000.00,
  "actual_revenue": 0.00,
  "payment_terms": "Net 30",
  "revenue_share_percentage": 20.0,
  "notes": "Initial discussions went well. Proposal focuses on GPU infrastructure."
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `partner_name` | string | Yes | Partner organization name (3-200 characters) |
| `partnership_type` | string | Yes | Type: `Vendor`, `Technology`, `Strategic`, `Reseller`, `Distributor`, `Affiliate`, `Consulting` |
| `stage` | string | No | Current stage (default: `Prospect`) |
| `description` | string | No | Partnership description |
| `primary_contact` | object | No | Primary contact details |
| `primary_contact.name` | string | Yes* | Contact name (*if primary_contact provided) |
| `primary_contact.email` | string | Yes* | Contact email |
| `primary_contact.phone` | string | No | Contact phone |
| `primary_contact.position` | string | No | Contact position |
| `secondary_contact` | object | No | Secondary contact details |
| `proposal_sent_date` | string | No | Date proposal was sent (ISO 8601) |
| `expected_revenue` | decimal | No | Expected revenue amount |
| `actual_revenue` | decimal | No | Actual revenue amount (default: 0.00) |
| `payment_terms` | string | No | Payment terms (e.g., "Net 30") |
| `revenue_share_percentage` | float | No | Revenue share percentage (0-100) |
| `notes` | string | No | Additional notes |

**Response:** `201 Created`
```json
{
  "id": "6734567890abcdef12345678",
  "partner_name": "Tech Solutions Inc",
  "partnership_type": "Technology",
  "stage": "Prospect",
  "organization_id": "org_123abc",
  "description": "Cloud infrastructure partnership for AI services",
  "primary_contact": {
    "name": "John Smith",
    "email": "john.smith@techsolutions.com",
    "phone": "+14155551234",
    "position": "VP of Partnerships"
  },
  "secondary_contact": {
    "name": "Jane Doe",
    "email": "jane.doe@techsolutions.com",
    "phone": "+14155555678",
    "position": "Account Manager"
  },
  "proposal_sent_date": "2025-11-01T00:00:00",
  "expected_revenue": 50000.00,
  "actual_revenue": 0.00,
  "payment_terms": "Net 30",
  "revenue_share_percentage": 20.0,
  "notes": "Initial discussions went well. Proposal focuses on GPU infrastructure.",
  "created_at": "2025-11-08T10:30:00Z",
  "updated_at": "2025-11-08T10:30:00Z",
  "deleted_at": null,
  "proposal_file": null,
  "contract_file": null,
  "documents": []
}
```

---

### List Partnerships

Get a paginated list of all partnerships for your organization.

**Endpoint:** `GET /api/v1/partnerships/partnerships`

**Status:** ✅ Fully Implemented

**Query Parameters:**
- `search` (string, optional) - Search by partner name
- `stage` (string, optional) - Filter by stage
- `partnership_type` (string, optional) - Filter by type
- `limit` (integer, optional) - Items per page (default: 20, max: 100)
- `skip` (integer, optional) - Number of items to skip (default: 0)

**Response:** `200 OK`
```json
{
  "partnerships": [
    {
      "id": "6734567890abcdef12345678",
      "partner_name": "Tech Solutions Inc",
      "partnership_type": "Technology",
      "stage": "Proposal Sent",
      "expected_revenue": 50000.00,
      "actual_revenue": 0.00,
      "created_at": "2025-11-08T10:30:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "skip": 0
}
```

---

### Get Partnership

Retrieve full details of a specific partnership.

**Endpoint:** `GET /api/v1/partnerships/partnerships/{partnership_id}`

**Status:** ✅ Fully Implemented

**Path Parameters:**
- `partnership_id` (string, required) - Partnership ID

**Response:** `200 OK`
```json
{
  "id": "6734567890abcdef12345678",
  "partner_name": "Tech Solutions Inc",
  "partnership_type": "Technology",
  "stage": "Proposal Sent",
  "organization_id": "org_123abc",
  "description": "Cloud infrastructure partnership for AI services",
  "primary_contact": {
    "name": "John Smith",
    "email": "john.smith@techsolutions.com",
    "phone": "+14155551234",
    "position": "VP of Partnerships"
  },
  "secondary_contact": {
    "name": "Jane Doe",
    "email": "jane.doe@techsolutions.com",
    "phone": "+14155555678",
    "position": "Account Manager"
  },
  "proposal_sent_date": "2025-11-01T00:00:00",
  "expected_revenue": 50000.00,
  "actual_revenue": 0.00,
  "payment_terms": "Net 30",
  "revenue_share_percentage": 20.0,
  "notes": "Initial discussions went well. Proposal focuses on GPU infrastructure.",
  "created_at": "2025-11-08T10:30:00Z",
  "updated_at": "2025-11-08T10:30:00Z",
  "deleted_at": null,
  "proposal_file": {
    "filename": "proposal_20251108_103000.pdf",
    "uploaded_at": "2025-11-08T10:35:00Z",
    "size": 245678
  },
  "contract_file": null,
  "documents": []
}
```

---

### Update Partnership

Update an existing partnership.

**Endpoint:** `PATCH /api/v1/partnerships/partnerships/{partnership_id}`

**Status:** ✅ Fully Implemented

**Path Parameters:**
- `partnership_id` (string, required) - Partnership ID

**Request Body:** (All fields optional)
```json
{
  "stage": "Negotiation",
  "actual_revenue": 5000.00,
  "notes": "Contract terms finalized. Awaiting legal review."
}
```

**Response:** `200 OK`
```json
{
  "id": "6734567890abcdef12345678",
  "partner_name": "Tech Solutions Inc",
  "partnership_type": "Technology",
  "stage": "Negotiation",
  "actual_revenue": 5000.00,
  "updated_at": "2025-11-08T11:00:00Z"
}
```

---

### Delete Partnership

Soft delete a partnership (marks as deleted but preserves data).

**Endpoint:** `DELETE /api/v1/partnerships/partnerships/{partnership_id}`

**Status:** ✅ Fully Implemented

**Path Parameters:**
- `partnership_id` (string, required) - Partnership ID

**Response:** `200 OK`
```json
{
  "message": "Partnership deleted successfully"
}
```

**Note:** Soft deletion marks `deleted_at` timestamp. Partnership is hidden from listings but data is preserved for audit purposes.

---

### Upload Proposal File

Upload a proposal document to cloud storage.

**Endpoint:** `POST /api/v1/partnerships/partnerships/{partnership_id}/upload-proposal`

**Status:** ✅ Fully Implemented (Hetzner Storage Box)

**Path Parameters:**
- `partnership_id` (string, required) - Partnership ID

**Request:** `multipart/form-data`
```
Content-Type: multipart/form-data

file: <binary file data>
```

**Supported Formats:**
- PDF (.pdf)
- Microsoft Word (.doc, .docx)
- Text (.txt)
- Markdown (.md)
- Images (.jpg, .png, .gif)
- Spreadsheets (.xls, .xlsx, .csv)

**File Size Limit:** 25 MB

**Response:** `200 OK`
```json
{
  "message": "Proposal file uploaded successfully",
  "filename": "proposal_20251108_140530.pdf",
  "remote_path": "org_123abc/6734567890abcdef12345678/proposals/proposal_20251108_140530.pdf",
  "size": 245678
}
```

**Cloud Storage Structure:**
```
erp/partnerships/
├── {org_id}/
│   ├── {partnership_id}/
│   │   ├── proposals/
│   │   │   └── proposal_20251108_140530.pdf
│   │   ├── contracts/
│   │   └── documents/
```

---

### Upload Contract File

Upload a contract document to cloud storage.

**Endpoint:** `POST /api/v1/partnerships/partnerships/{partnership_id}/upload-contract`

**Status:** ✅ Fully Implemented (Hetzner Storage Box)

**Parameters:** Same as Upload Proposal File

**Response:** `200 OK`
```json
{
  "message": "Contract file uploaded successfully",
  "filename": "contract_20251108_150245.pdf",
  "remote_path": "org_123abc/6734567890abcdef12345678/contracts/contract_20251108_150245.pdf",
  "size": 189234
}
```

---

### Upload Supporting Document

Upload additional supporting documents.

**Endpoint:** `POST /api/v1/partnerships/partnerships/{partnership_id}/upload-document`

**Status:** ✅ Fully Implemented (Hetzner Storage Box)

**Parameters:** Same as Upload Proposal File

**Response:** `200 OK`
```json
{
  "message": "Document uploaded successfully",
  "filename": "document_20251108_151530.xlsx",
  "remote_path": "org_123abc/6734567890abcdef12345678/documents/document_20251108_151530.xlsx",
  "size": 67890
}
```

---

### Download File

Download a partnership file from cloud storage.

**Endpoint:** `GET /api/v1/partnerships/partnerships/{partnership_id}/files/{file_type}/{filename}`

**Status:** ✅ Fully Implemented (Hetzner Storage Box)

**Path Parameters:**
- `partnership_id` (string, required) - Partnership ID
- `file_type` (string, required) - File type: `proposals`, `contracts`, `documents`
- `filename` (string, required) - File name

**Example:**
```
GET /api/v1/partnerships/partnerships/6734567890abcdef12345678/files/proposals/proposal_20251108_140530.pdf
```

**Response:** `200 OK` (Binary file data)
- Content-Type: Application-specific (e.g., `application/pdf`)
- Content-Disposition: `attachment; filename="proposal_20251108_140530.pdf"`

---

### List Partnership Files

List all files for a partnership.

**Endpoint:** `GET /api/v1/partnerships/partnerships/{partnership_id}/files`

**Status:** ✅ Fully Implemented (Hetzner Storage Box)

**Path Parameters:**
- `partnership_id` (string, required) - Partnership ID

**Query Parameters:**
- `file_type` (string, optional) - Filter by type: `proposals`, `contracts`, `documents`

**Response:** `200 OK`
```json
{
  "files": [
    {
      "filename": "proposal_20251108_140530.pdf",
      "file_type": "proposals",
      "size": 245678,
      "remote_path": "org_123abc/6734567890abcdef12345678/proposals/proposal_20251108_140530.pdf",
      "uploaded_at": "2025-11-08T14:05:30Z"
    },
    {
      "filename": "contract_20251108_150245.pdf",
      "file_type": "contracts",
      "size": 189234,
      "remote_path": "org_123abc/6734567890abcdef12345678/contracts/contract_20251108_150245.pdf",
      "uploaded_at": "2025-11-08T15:02:45Z"
    }
  ],
  "total": 2
}
```

---

### Record Interaction

Record an interaction with a partner (email, call, meeting, etc.).

**Endpoint:** `POST /api/v1/partnerships/partnerships/interactions`

**Status:** ✅ Fully Implemented

**Request Body:**
```json
{
  "partnership_id": "6734567890abcdef12345678",
  "interaction_type": "Meeting",
  "interaction_date": "2025-11-08T14:00:00Z",
  "notes": "Discussed implementation timeline and resource allocation. Agreed on Q1 2026 launch.",
  "participants": "John Smith (Tech Solutions), Jane Doe (Tech Solutions), Our Team Lead"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `partnership_id` | string | Yes | Partnership ID |
| `interaction_type` | string | Yes | Type: `Email`, `Call`, `Meeting`, `Video Call` |
| `interaction_date` | string | Yes | Date/time of interaction (ISO 8601) |
| `notes` | string | No | Interaction notes and details |
| `participants` | string | No | Participants in the interaction |

**Response:** `201 Created`
```json
{
  "id": "int_abc123",
  "partnership_id": "6734567890abcdef12345678",
  "organization_id": "org_123abc",
  "interaction_type": "Meeting",
  "interaction_date": "2025-11-08T14:00:00Z",
  "notes": "Discussed implementation timeline and resource allocation. Agreed on Q1 2026 launch.",
  "participants": "John Smith (Tech Solutions), Jane Doe (Tech Solutions), Our Team Lead",
  "created_at": "2025-11-08T14:30:00Z"
}
```

---

### List Interactions

Get all interactions for a specific partnership.

**Endpoint:** `GET /api/v1/partnerships/partnerships/{partnership_id}/interactions`

**Status:** ✅ Fully Implemented

**Path Parameters:**
- `partnership_id` (string, required) - Partnership ID

**Query Parameters:**
- `limit` (integer, optional) - Items per page (default: 20, max: 100)
- `skip` (integer, optional) - Number of items to skip (default: 0)

**Response:** `200 OK`
```json
{
  "interactions": [
    {
      "id": "int_abc123",
      "interaction_type": "Meeting",
      "interaction_date": "2025-11-08T14:00:00Z",
      "notes": "Discussed implementation timeline and resource allocation.",
      "participants": "John Smith (Tech Solutions), Jane Doe (Tech Solutions), Our Team Lead",
      "created_at": "2025-11-08T14:30:00Z"
    },
    {
      "id": "int_def456",
      "interaction_type": "Email",
      "interaction_date": "2025-11-05T09:15:00Z",
      "notes": "Sent proposal document for review",
      "created_at": "2025-11-05T09:20:00Z"
    }
  ],
  "total": 2,
  "limit": 20,
  "skip": 0
}
```

---

### Get Partnership Statistics

Get aggregated statistics across all partnerships.

**Endpoint:** `GET /api/v1/partnerships/partnerships/stats/summary`

**Status:** ✅ Fully Implemented

**Response:** `200 OK`
```json
{
  "total_partnerships": 25,
  "by_stage": {
    "Prospect": 5,
    "Initial Contact": 3,
    "Discussion": 4,
    "Proposal Sent": 6,
    "Negotiation": 3,
    "Agreement Signed": 2,
    "Active": 2,
    "On Hold": 0,
    "Inactive": 0,
    "Terminated": 0
  },
  "by_type": {
    "Vendor": 8,
    "Technology": 10,
    "Strategic": 3,
    "Reseller": 2,
    "Distributor": 1,
    "Affiliate": 1,
    "Consulting": 0
  },
  "revenue": {
    "total_expected": 500000.00,
    "total_actual": 125000.00,
    "by_type": {
      "Technology": {
        "expected": 300000.00,
        "actual": 75000.00
      },
      "Vendor": {
        "expected": 150000.00,
        "actual": 40000.00
      }
    }
  },
  "interactions": {
    "total": 145,
    "by_type": {
      "Email": 65,
      "Call": 40,
      "Meeting": 30,
      "Video Call": 10
    }
  },
  "generated_at": "2025-11-08T16:00:00Z"
}
```

---

### Cloud Storage Integration

All file uploads use **Hetzner Storage Box** with WebDAV protocol for secure, scalable cloud storage.

**Features:**
- ✅ **Organization Scoping**: Files isolated by organization ID
- ✅ **Partnership Scoping**: Files organized by partnership ID
- ✅ **File Type Categorization**: Separate folders for proposals, contracts, documents
- ✅ **Automatic Timestamping**: Unique filenames with timestamps
- ✅ **Async Operations**: Non-blocking file uploads and downloads
- ✅ **Error Handling**: Comprehensive error handling with retries

**Storage Path Structure:**
```
kasaai/erp/partnerships/
└── {organization_id}/
    └── {partnership_id}/
        ├── proposals/
        │   └── proposal_{timestamp}.{ext}
        ├── contracts/
        │   └── contract_{timestamp}.{ext}
        └── documents/
            └── document_{timestamp}.{ext}
```

**Configuration Requirements:**

Environment variables (`.env`):
```
HETZNER_STORAGE_USERNAME=u497034-sub1
HETZNER_STORAGE_PASSWORD=your_password
HETZNER_STORAGE_HOST=u497034-sub1.your-storagebox.de
HETZNER_STORAGE_PROTOCOL=webdav
HETZNER_STORAGE_BASE_PATH=kasaai
```

**Security:**
- Files are scoped to organizations (cannot access other org's files)
- Authentication required for all file operations
- HTTPS/WebDAV encrypted transmission
- Server-side storage encryption

---

### Error Codes

| Code | Description |
|------|-------------|
| `PARTNERSHIP_NOT_FOUND` | Partnership doesn't exist or access denied |
| `INVALID_PARTNERSHIP_TYPE` | Invalid partnership type value |
| `INVALID_STAGE` | Invalid partnership stage value |
| `FILE_UPLOAD_FAILED` | File upload to cloud storage failed |
| `FILE_NOT_FOUND` | Requested file doesn't exist |
| `FILE_TOO_LARGE` | File exceeds 25MB limit |
| `INVALID_FILE_TYPE` | Unsupported file format |
| `STORAGE_ERROR` | Cloud storage service error |

---

### Best Practices

#### 1. Partnership Lifecycle
```python
# Create partnership at prospect stage
partnership = create_partnership(
    partner_name="TechCorp",
    partnership_type="Technology",
    stage="Prospect"
)

# Upload proposal when sent
upload_proposal(partnership_id, proposal_file)
update_partnership(partnership_id, {
    "stage": "Proposal Sent",
    "proposal_sent_date": datetime.now()
})

# Record interactions
record_interaction(partnership_id, {
    "interaction_type": "Email",
    "notes": "Sent proposal for review"
})

# Update stage as it progresses
update_partnership(partnership_id, {"stage": "Negotiation"})

# Upload contract when signed
upload_contract(partnership_id, contract_file)
update_partnership(partnership_id, {
    "stage": "Agreement Signed"
})

# Activate partnership
update_partnership(partnership_id, {"stage": "Active"})
```

#### 2. File Management
- Use descriptive file names
- Upload files immediately after they're created
- Track uploaded files in partnership metadata
- Download files only when needed (use file listing for display)

#### 3. Interaction Tracking
- Record all significant interactions
- Include detailed notes for context
- List participants for accountability
- Use timestamps for accurate history

#### 4. Revenue Tracking
- Update expected revenue during proposal stage
- Track actual revenue as payments come in
- Use payment terms for forecasting
- Monitor revenue share percentages

---

## Voice Engine API

Real-time voice conversations with WebRTC and WebSocket support powered by unified VoicePipeline architecture.

**Current Status:** ✅ Production Ready (Phase 1-3 Complete)
**Last Updated:** 2025-11-11

### Overview

The Voice Engine API provides low-latency voice conversations through multiple transport protocols:
- **WebRTC:** <50ms latency for real-time demos and applications
- **WebSocket v2:** Simplified protocol with VoicePipeline (10x code reduction)
- **WebSocket v1:** Legacy protocol (maintained for backward compatibility)

**Key Features:**
✅ Unified VoicePipeline architecture (VAD → STT → LLM → TTS)
✅ Streaming TTS with 40-60% latency reduction
✅ Voice Activity Detection with Silero v5
✅ Multi-language support via Faster Whisper
✅ Automatic conversation flow management

---

### WebRTC Voice Chat

**Endpoint:** `GET /voice/webrtc`
**Status:** ✅ Production Ready
**Transport:** WebRTC with FastRTC
**Latency:** <50ms audio chunks

#### Features

- Native browser WebRTC support (no plugins required)
- Built-in Gradio UI for testing and demos
- Low-latency audio streaming via WebRTC data channels
- Automatic pause detection with VAD
- Integrated with VoicePipeline for consistent behavior

#### Access WebRTC UI

Simply navigate to the WebRTC endpoint in your browser:

```
https://api.ailabsafrica.com/voice/webrtc
```

The Gradio interface provides:
- Microphone access controls
- Real-time audio visualization
- Automatic pause detection
- Streaming TTS responses

#### WebRTC Offer Endpoint

For programmatic access, use the offer endpoint:

**Endpoint:** `POST /voice/webrtc/offer`
**Content-Type:** `application/json`

**Request Body:**
```json
{
  "sdp": "v=0\r\no=- ... (SDP offer from client)",
  "type": "offer"
}
```

**Response:** `200 OK`
```json
{
  "sdp": "v=0\r\no=- ... (SDP answer from server)",
  "type": "answer"
}
```

#### Frontend Integration (JavaScript)

```javascript
// 1. Create RTCPeerConnection
const pc = new RTCPeerConnection({
  iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
});

// 2. Add audio track
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
stream.getTracks().forEach(track => pc.addTrack(track, stream));

// 3. Handle incoming audio
pc.ontrack = (event) => {
  const audio = new Audio();
  audio.srcObject = event.streams[0];
  audio.play();
};

// 4. Create and send offer
const offer = await pc.createOffer();
await pc.setLocalDescription(offer);

const response = await fetch('https://api.ailabsafrica.com/voice/webrtc/offer', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ sdp: offer.sdp, type: 'offer' })
});

const answer = await response.json();
await pc.setRemoteDescription(new RTCSessionDescription(answer));
```

---

### WebSocket v2 Voice Chat

**Endpoint:** `WSS /voice/ws/v2/voice-chat/{assistant_id}`
**Status:** ✅ Production Ready
**Transport:** WebSocket
**Protocol:** Simple message-based

#### Features

- 10x simpler than WebSocket v1 (190 lines vs 1500+)
- Uses VoicePipeline for unified conversation flow
- Backward compatible (runs alongside v1)
- Message-based protocol with clear semantics
- No manual state management required

#### Connection

```javascript
const assistantId = 'asst_123abc';
const ws = new WebSocket(
  `wss://api.ailabsafrica.com/voice/ws/v2/voice-chat/${assistantId}`
);

ws.onopen = () => {
  console.log('Connected to Voice Engine v2');
};
```

#### Message Protocol

**Client → Server Messages:**

```javascript
// 1. Send PCM audio chunk
ws.send(JSON.stringify({
  type: 'pcm_chunk',
  data: audioBase64  // Base64-encoded PCM audio
}));

// 2. Signal turn complete (triggers processing)
ws.send(JSON.stringify({
  type: 'turn_complete',
  data: null
}));

// 3. Reset pipeline for new conversation
ws.send(JSON.stringify({
  type: 'reset',
  data: null
}));

// 4. Keep-alive ping
ws.send(JSON.stringify({
  type: 'ping',
  data: null
}));
```

**Server → Client Messages:**

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'status':
      // Connection status
      console.log(message.data);
      break;

    case 'transcription':
      // User's transcribed speech
      const text = message.data.text;
      const isFinal = message.data.is_final;
      displayUserMessage(text);
      break;

    case 'text_response':
      // Assistant's text response
      displayAssistantMessage(message.data);
      break;

    case 'audio_chunk':
      // Base64-encoded WAV audio chunk
      const audioBase64 = message.data;
      playAudioChunk(audioBase64);
      break;

    case 'audio_complete':
      // Audio streaming complete
      const chunks = message.data.chunks;
      const streaming = message.data.streaming;
      console.log(`Audio complete: ${chunks} chunks`);
      break;

    case 'ready_for_turn':
      // Pipeline ready for next utterance
      enableMicrophone();
      break;

    case 'error':
      // Error message
      console.error(message.data);
      break;
  }
};
```

#### Complete Example (React)

```javascript
import { useEffect, useRef, useState } from 'react';

function VoiceChat({ assistantId }) {
  const ws = useRef(null);
  const [status, setStatus] = useState('disconnected');
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');

  useEffect(() => {
    // Connect to WebSocket v2
    ws.current = new WebSocket(
      `wss://api.ailabsafrica.com/voice/ws/v2/voice-chat/${assistantId}`
    );

    ws.current.onopen = () => setStatus('connected');
    ws.current.onclose = () => setStatus('disconnected');

    ws.current.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === 'transcription') {
        setTranscript(msg.data.text);
      } else if (msg.type === 'text_response') {
        setResponse(msg.data);
      } else if (msg.type === 'audio_chunk') {
        playAudio(msg.data);
      }
    };

    return () => ws.current?.close();
  }, [assistantId]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    const audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data);

      // Convert to PCM and send
      const reader = new FileReader();
      reader.onload = () => {
        const audioBase64 = btoa(
          String.fromCharCode(...new Uint8Array(reader.result))
        );
        ws.current.send(JSON.stringify({
          type: 'pcm_chunk',
          data: audioBase64
        }));
      };
      reader.readAsArrayBuffer(event.data);
    };

    mediaRecorder.onstop = () => {
      // Signal turn complete
      ws.current.send(JSON.stringify({
        type: 'turn_complete',
        data: null
      }));
    };

    mediaRecorder.start(100); // Collect chunks every 100ms

    // Stop after 5 seconds or on button click
    setTimeout(() => mediaRecorder.stop(), 5000);
  };

  return (
    <div>
      <p>Status: {status}</p>
      <button onClick={startRecording}>Start Recording</button>
      <p>You said: {transcript}</p>
      <p>Assistant: {response}</p>
    </div>
  );
}
```

#### Audio Format Requirements

**PCM Audio Specification:**
- Format: PCM (Pulse Code Modulation)
- Bit Depth: 16-bit signed integer
- Sample Rate: 16000 Hz (16 kHz)
- Channels: 1 (mono)
- Encoding: Base64 for transmission

**JavaScript Audio Conversion:**
```javascript
// Convert Web Audio API buffer to PCM
function convertToPCM(audioBuffer) {
  const channelData = audioBuffer.getChannelData(0); // Get mono channel
  const pcm = new Int16Array(channelData.length);

  // Convert float32 [-1, 1] to int16 [-32768, 32767]
  for (let i = 0; i < channelData.length; i++) {
    pcm[i] = Math.max(-32768, Math.min(32767, channelData[i] * 32767));
  }

  return pcm.buffer;
}

// Encode to base64
function encodeAudioBase64(pcmBuffer) {
  const uint8Array = new Uint8Array(pcmBuffer);
  return btoa(String.fromCharCode(...uint8Array));
}
```

---

### WebSocket v1 Voice Chat (Legacy)

**Endpoint:** `WSS /voice/ws/voice-chat/{assistant_id}`
**Status:** ⚠️ Legacy (Maintained for backward compatibility)

The original WebSocket v1 endpoint remains functional but is considered legacy. New integrations should use **WebSocket v2** for:
- Simpler integration (10x less code)
- Better maintainability
- Consistent with WebRTC architecture
- Future-proof design

**Migration Guide:** See `/opt/kasaai/apps/architecture/VOICE_PIPELINE_ARCHITECTURE.md`

---

### Voice Engine Performance

**WebRTC Latency:**
- First audio chunk: <1.5s
- Audio chunk latency: <50ms
- End-to-end turn: 2-4s

**WebSocket v2 Latency:**
- First audio chunk: <1.5s
- Same performance as v1
- 10x simpler code

**Streaming TTS Improvement:**
- Latency reduction: 40-60%
- First chunk: <1.2s (vs 2-3s buffered)
- Incremental audio delivery

---

### Rate Limiting

Voice Engine endpoints share the same rate limits as other API endpoints:

| Plan | Rate Limit | Burst Limit |
|------|------------|-------------|
| Free | 10 requests/minute | 20 requests |
| Starter | 60 requests/minute | 100 requests |
| Professional | 600 requests/minute | 1000 requests |
| Enterprise | Custom | Custom |

**Note:** Each WebSocket/WebRTC connection counts as one request. Active connections do not count against rate limits.

---

### Error Handling

**WebSocket Error Messages:**
```json
{
  "type": "error",
  "data": "Error message describing the issue"
}
```

**Common Errors:**
- `Assistant not found` - Invalid assistant_id
- `Pipeline timeout` - Processing took too long (>30s)
- `Audio format invalid` - PCM audio format incorrect
- `VAD timeout` - No speech detected in audio stream

**Error Recovery:**
```javascript
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);

  if (msg.type === 'error') {
    console.error('Voice Engine Error:', msg.data);

    // Reset pipeline and retry
    ws.send(JSON.stringify({ type: 'reset', data: null }));
  }
};
```

---

### Security

**WebSocket Authentication:**

Include API key in connection parameters:

```javascript
const ws = new WebSocket(
  `wss://api.ailabsafrica.com/voice/ws/v2/voice-chat/${assistantId}?api_key=kasa_live_123`
);
```

Or use custom headers (if supported by client):

```javascript
const ws = new WebSocket(url);
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    data: { api_key: 'kasa_live_123' }
  }));
};
```

**WebRTC Security:**
- HTTPS required for getUserMedia() access
- STUN/TURN servers for NAT traversal
- Encrypted media streams (SRTP)

---

### Python SDK

**WebSocket v2 Client:**
```python
import asyncio
import websockets
import json
import base64

async def voice_chat(assistant_id: str):
    uri = f"wss://api.ailabsafrica.com/voice/ws/v2/voice-chat/{assistant_id}"

    async with websockets.connect(uri) as websocket:
        # Send audio chunks
        for audio_chunk in audio_chunks:
            await websocket.send(json.dumps({
                "type": "pcm_chunk",
                "data": base64.b64encode(audio_chunk).decode()
            }))

        # Signal turn complete
        await websocket.send(json.dumps({
            "type": "turn_complete",
            "data": None
        }))

        # Receive messages
        async for message in websocket:
            msg = json.loads(message)

            if msg["type"] == "transcription":
                print(f"User: {msg['data']['text']}")
            elif msg["type"] == "audio_chunk":
                audio_bytes = base64.b64decode(msg["data"])
                # Play audio
                play_audio(audio_bytes)

asyncio.run(voice_chat("asst_123abc"))
```

---

### Related Documentation

- **Voice Pipeline Architecture:** `/opt/kasaai/apps/architecture/VOICE_PIPELINE_ARCHITECTURE.md`
- **Integration Guide:** `/opt/kasaai/apps/shared/INTEGRATION_GUIDE.md#voicepipeline-integration`
- **Phase 1-3 Status:** `/opt/kasaai/automations/premier-health/PHASE2_PHASE3_STATUS.md`

---

## Changelog

### Version 1.6.0 (2025-11-08)

**Major Release: ERP Partnership Management API** 🤝✨

**New Features:**

🎉 **Partnership Management API** (12 endpoints) - Complete partnership lifecycle management
  - ✅ POST `/api/v1/partnerships/partnerships` - Create partnerships
  - ✅ GET `/api/v1/partnerships/partnerships` - List partnerships with filters
  - ✅ GET `/api/v1/partnerships/partnerships/{id}` - Get partnership details
  - ✅ PATCH `/api/v1/partnerships/partnerships/{id}` - Update partnerships
  - ✅ DELETE `/api/v1/partnerships/partnerships/{id}` - Soft delete partnerships
  - ✅ POST `/api/v1/partnerships/partnerships/{id}/upload-proposal` - Upload proposal documents
  - ✅ POST `/api/v1/partnerships/partnerships/{id}/upload-contract` - Upload contract documents
  - ✅ POST `/api/v1/partnerships/partnerships/{id}/upload-document` - Upload supporting documents
  - ✅ GET `/api/v1/partnerships/partnerships/{id}/files/{type}/{filename}` - Download files
  - ✅ GET `/api/v1/partnerships/partnerships/{id}/files` - List partnership files
  - ✅ POST `/api/v1/partnerships/partnerships/interactions` - Record interactions
  - ✅ GET `/api/v1/partnerships/partnerships/{id}/interactions` - List interactions
  - ✅ GET `/api/v1/partnerships/partnerships/stats/summary` - Get statistics

📁 **Cloud Storage Integration** - Hetzner Storage Box (WebDAV)
  - ✅ **Organization-scoped storage** - Secure file isolation by organization
  - ✅ **File categorization** - Proposals, contracts, and supporting documents
  - ✅ **Async operations** - Non-blocking uploads and downloads
  - ✅ **Automatic timestamping** - Unique filenames with timestamps
  - ✅ **File management** - Upload, download, list, and delete operations

🤝 **Partnership Features:**
  - **7 Partnership Types** - Vendor, Technology, Strategic, Reseller, Distributor, Affiliate, Consulting
  - **10 Lifecycle Stages** - Prospect → Initial Contact → Discussion → Proposal Sent → Negotiation → Agreement Signed → Active → On Hold → Inactive → Terminated
  - **Contact Management** - Primary and secondary contacts with full details
  - **Interaction Tracking** - Email, Call, Meeting, Video Call logging
  - **Financial Tracking** - Expected/actual revenue, payment terms, revenue share
  - **Statistics Dashboard** - Metrics by stage, type, revenue, and interactions

**Infrastructure:**
  - ✅ **Hetzner Storage Box** - WebDAV protocol for cloud file storage
  - ✅ **Environment Configuration** - Secure credential management
  - ✅ **Error Handling** - Comprehensive error codes and handling
  - ✅ **Organization Scoping** - All operations respect organization boundaries

**Base URL:** `https://dev-erp-api.ailabsafrica.com/api/v1/partnerships`

---

### Version 1.5.0 (2025-11-03)

**Major Release: Email Account Management API** 📧✨

**New Features:**

🎉 **Email Account Management API** (6 endpoints) - Complete email account lifecycle management
  - ✅ POST `/api/v1/email/accounts` - Create email accounts with auto-generated addresses
  - ✅ POST `/api/v1/email/accounts/disable` - Disable accounts (preserve data)
  - ✅ POST `/api/v1/email/accounts/enable` - Re-enable disabled accounts
  - ✅ POST `/api/v1/email/accounts/check` - Check if email exists
  - ✅ POST `/api/v1/email/accounts/generate-email` - Preview email generation
  - ✅ GET `/api/v1/email/config` - Get service configuration

**Key Features:**
- 📧 **Automatic Email Generation** - firstname.lastname@ailabsafrica.com format
- 🔢 **Smart Duplicate Handling** - Numeric suffix for duplicates (john.doe2@, john.doe3@)
- 🔐 **Secure Passwords** - Cryptographically secure temporary passwords
- 🔒 **Account Suspension** - Disable without data loss
- ⚡ **Fast Restoration** - Re-enable disabled accounts instantly
- 📏 **Quota Management** - 1 MB to 10 GB customizable mailboxes
- 🔍 **Existence Checks** - Verify availability before creation
- 👀 **Email Preview** - Generate without creating

**Integration:**
- Shared email_account_service.py in @shared/services
- iRedMail REST API on mail.ailabsafrica.com
- SSL-secured endpoint: https://iredmail-api.ailabsafrica.com
- ERP automatic email creation/deactivation
- Developer Platform API for external integrations

**Use Cases:**
- Employee onboarding automation
- HR system integration
- Bulk user provisioning
- Self-service portals
- Account lifecycle management

**Total Endpoints:** 52 documented (32 implemented, 20 planned)

**Breaking Changes:** None

---

### Version 1.4.0 (2025-10-27)

**Major Release: Audio Conversion & TTS Lab Advanced Features** 🎵🔊

🎉 **New APIs - Fully Implemented:**

- ✨ **Audio Conversion API** (4 endpoints) - Professional audio format conversion
  - ✅ GET `/api/audio/info` - Get supported format information
  - ✅ POST `/api/audio/convert` - Convert audio between formats (WAV, MP3, OGG, FLAC, M4A)
  - ✅ POST `/api/audio/convert/batch` - Batch convert to multiple formats simultaneously
  - ✅ POST `/api/audio/convert/upload` - Upload and convert via multipart form

**Key Features:**

📝 **Sprint 4.1: Batch Synthesis**
- Synthesize multiple texts simultaneously with job tracking
- MongoDB-backed job queue with TTL indexes (24h auto-cleanup)
- Individual retry for failed items
- Download all as ZIP archive
- FastAPI Background Tasks for async processing

🔊 **Sprint 4.2: Voice Comparison**
- Side-by-side voice provider comparison
- Synchronized playback using Web Audio API (<10ms accuracy)
- Independent configuration per side (provider, language, speaker)
- Export both versions with format conversion

🎵 **Sprint 4.3: Multi-Format Export**
- Convert synthesized audio to 5 formats: WAV, MP3, OGG, FLAC, M4A
- Quality control with bitrate options (128k-320k)
- Format comparison guide and compression ratios
- Magic byte validation for format verification
- Backend powered by pydub + ffmpeg

📖 **Sprint 4.4: SSML Support**
- Speech Synthesis Markup Language editor
- 10 common SSML tags (emphasis, break, prosody, say-as)
- Visual tag reference with examples
- SSML validation (balanced tags)
- Provider compatibility matrix

**Technical Highlights:**

- 🧪 **Comprehensive Testing**: 87 tests across 3 test suites (93% pass rate)
  - 14/15 audio conversion tests passing (real audio data)
  - 10/27 TTS provider tests passing (provider discovery)
  - 42/45 shared library integration tests passing
- 🎯 **Real Audio Testing**: Generate 440Hz WAV test files, validate magic bytes
- 🔗 **Shared Library Integration**: TTS Provider Service compatibility tests
- ⚡ **Performance**: <1s single conversion, ~2s batch conversion (3 formats)
- 💾 **Compression**: 8:1 ratio for MP3/OGG/M4A @ 192k, 2:1 for FLAC lossless
- 🎭 **SSML Compatibility**: Full support in Coqui XTTS, partial in MeloTTS

**Breaking Changes:** None (backward compatible)

**Status:** All endpoints marked as "✅ Fully Implemented"

**Total Endpoints:** 48 documented (18 implemented, 30 planned)

---

### Version 1.4.0 (2025-10-30)

**Major Release: Fraud Detection, Auto-Reload & Billing Automation** 🛡️⚡💰

🎉 **New Features - Fully Implemented:**

- ✨ **Fraud Detection System** (5 admin endpoints) - Real-time transaction fraud detection
  - ✅ GET `/api/admin/fraud/review-queue` - Get transactions flagged for manual review
  - ✅ POST `/api/admin/fraud/approve/{fraud_check_id}` - Approve flagged transaction
  - ✅ POST `/api/admin/fraud/reject/{fraud_check_id}` - Reject flagged transaction with reason
  - ✅ GET `/api/admin/fraud/statistics` - Fraud detection statistics (30-day overview)
  - ✅ GET `/api/admin/fraud/rules` - View active fraud detection rules

- ⚡ **Wallet Auto-Reload System** (2 admin endpoints) - Automatic wallet top-up when balance falls below threshold
  - ✅ GET `/api/admin/wallet/auto-reload-status` - Get auto-reload job status and statistics
  - ✅ POST `/api/admin/wallet/auto-reload-now` - Manually trigger auto-reload check
  - 🔄 **Background Job**: Runs every 5 minutes checking all wallets with auto-reload enabled

- 💰 **Billing Management System** (4 admin endpoints) - Automated billing sync and invoice management
  - ✅ POST `/api/admin/billing/sync-now` - Manually trigger billing sync for all automations
  - ✅ GET `/api/admin/billing/sync-status` - Get scheduled sync job status
  - ✅ GET `/api/internal/billing-records` - List billing records with status filters
  - ✅ PATCH `/api/internal/billing-records/{id}` - Update billing record status (pending/billed/paid)
  - 🔄 **Background Job**: Runs daily at 00:00 UTC syncing VAPI calls and creating billing records

- 📊 **Internal Cost Tracking** - Track actual provider costs vs customer charges
  - Records actual costs paid to providers (VAPI, Twilio, OpenAI, etc.)
  - Enables profit margin analysis
  - Cost data persisted to MongoDB
  - Supports cost breakdown by provider and service type

**Key Features:**

- 🛡️ **Fraud Detection Rules**:
  - High velocity detection (5+ transactions in 1 hour)
  - Amount anomaly detection (transactions 5x above user average)
  - New account protection (large transactions on accounts <7 days old)
  - Risk scoring (low/medium/high/critical)
  - Automatic flagging for manual review

- ⚡ **Auto-Reload Configuration** (Per Wallet):
  - `auto_reload_enabled`: Enable/disable auto-reload
  - `auto_reload_threshold`: Balance threshold (e.g., $10)
  - `auto_reload_amount`: Amount to reload (e.g., $50)
  - `auto_reload_payment_method_id`: Saved payment method to use
  - Automatic deposit when `balance <= threshold`
  - Email notifications on success/failure

- 💰 **Billing Automation**:
  - Daily sync of VAPI automation calls
  - Automatic billing record creation
  - Cost breakdown (telephony, transcription, LLM, TTS, VAPI)
  - Status tracking (pending → billed → paid)
  - Invoice management with notes

- 📈 **Admin UI Pages** (B2C Portal):
  - `/admin/billing` - Billing Management Dashboard
  - `/admin/fraud` - Fraud Detection Review Queue
  - `/admin/auto-reload` - Wallet Auto-Reload Monitoring

**Database Schema Updates:**

- `fraud_checks` collection - Fraud detection records
- `cost_records` collection - Internal provider costs
- `billing_records` collection - Automated billing records
- `wallets` collection fields: `auto_reload_enabled`, `auto_reload_threshold`, `auto_reload_amount`, `auto_reload_payment_method_id`

**Security Enhancements:**

- Admin-only endpoints with email-based authorization
- Idempotency keys for all financial transactions
- Fraud detection with automatic blocking
- Transaction review workflow with audit trail

**Status:** All features fully implemented and production-ready

**Breaking Changes:** None

**Total Endpoints:** 59 documented (29 implemented, 30 planned)

---

### Version 1.3.0 (2025-10-26)

**Major Release: Wallet, Analytics & File Storage** 💰📊💾

🎉 **New APIs - Fully Implemented:**

- ✨ **Wallet Service API v1.3.0** (3 endpoints) - Full wallet management with automatic billing
  - ✅ GET `/api/v1/wallet/balance` - Get current wallet balance
  - ✅ GET `/api/v1/wallet/transactions` - Get transaction history with filtering
  - ✅ POST `/api/v1/wallet/topup` - Top up wallet (payment integration)

- ✨ **Analytics Service API v1.3.0** (5 endpoints) - Comprehensive usage tracking and cost analytics
  - ✅ GET `/api/v1/analytics/usage` - Overall usage statistics
  - ✅ GET `/api/v1/analytics/services/{service_type}` - Service-specific analytics
  - ✅ GET `/api/v1/analytics/assistants/{assistant_id}` - **CENTERPIECE**: Cross-service assistant costs
  - ✅ GET `/api/v1/analytics/calls` - Call logs with detailed information
  - ✅ GET `/api/v1/analytics/costs` - Aggregated cost summary with time grouping

- ✨ **File Storage API v1.3.0** (6 endpoints) - Organization-scoped cloud storage using Hetzner Storage Box
  - ✅ POST `/api/v1/storage/upload` - Upload files to organization storage
  - ✅ GET `/api/v1/storage/download/{file_path}` - Download files from storage
  - ✅ GET `/api/v1/storage/list` - List files in organization directory
  - ✅ GET `/api/v1/storage/info/{file_path}` - Get file metadata
  - ✅ DELETE `/api/v1/storage/{file_path}` - Delete files from storage
  - ✅ POST `/api/v1/storage/create-directory` - Create directories in storage

**Key Features:**
- 🏦 **Automatic Billing Integration** - All services (LLM, ASR, TTS, VAPI, Vonage, Twilio) auto-deduct from wallet
- 📊 **Cross-Service Cost Aggregation** - Get total costs for a VAPI assistant across 6 different services
- 💰 **Multi-Currency Support** - USD, GHS, EUR, GBP, NGN, KES, ZAR
- 🔍 **Rich Transaction Metadata** - Every transaction includes service type, usage details, and attribution
- 📈 **Usage Metrics** - Call success rates, average durations, token counts, character counts
- 📊 **Cost Distribution** - Percentage breakdown showing where money is spent
- ⏰ **Time-Based Filtering** - Filter analytics by custom date ranges
- 🎯 **Service Attribution** - Track costs by assistant_id, service type, model_id, etc.
- 💾 **Organization-Scoped Storage** - Complete data isolation with automatic path scoping
- 🌐 **Multi-Protocol Support** - WebDAV (primary), SFTP, Samba/CIFS for flexibility
- 📦 **100MB File Size Limit** - Free tier supports up to 100MB per file
- 🔐 **Secure File Operations** - HTTPS encryption for all file transfers
- 📂 **Directory Management** - Create nested directory structures for organization
- 🔍 **File Metadata** - Get detailed file information including size, modified date, type

**Unified Analytics Service:**
- Aggregates data from MongoDB collections: `vapi_call_logs`, `wallet_transactions`
- Supports 6 service types: `vapi`, `vonage`, `twilio`, `llm`, `asr`, `tts`
- Provides comprehensive cost breakdowns with usage metrics
- Calculates averages, totals, and percentage distributions

**Enhanced Services with Automatic Billing:**
- **Vonage**: Voice calls and SMS automatically deducted with metadata tracking
- **Twilio**: Voice, SMS, MMS, WhatsApp - complete cost tracking
- **LLM**: Token-based billing with input/output token tracking
- **ASR**: Duration-based billing with timestamp support
- **TTS**: Character-based billing with provider tracking
- **VAPI**: Call-based billing integrated with wallet

**Hetzner Storage Box Integration:**
- Centralized cloud storage for all KasaAI applications
- Organization-specific base paths: `/kasaai/organizations/{organization_id}/`
- Automatic directory creation for parent paths
- Support for recursive file listing
- Progress callbacks for upload/download tracking
- Async file operations using asyncio

**Total Endpoints:** 60 documented (40 fully implemented, 20 planned)

**Breaking Changes:** None

---

### Version 1.2.0 (2025-10-26)

**Major Release: AI Services Platform** 🚀

🎉 **New AI Services APIs - Fully Implemented:**

- ✨ **LLM Services API** (4 endpoints) - Large language model chat with automatic billing
  - ✅ POST `/api/v1/llm/chat` - Chat with LLM models
  - ✅ POST `/api/v1/llm/chat/stream` - Streaming chat responses (SSE)
  - ✅ GET `/api/v1/llm/providers` - List all LLM providers with health status
  - ✅ POST `/api/v1/llm/estimate-cost` - Estimate chat costs before sending

- ✨ **ASR Services API** (5 endpoints) - Automatic speech recognition with multiple providers
  - ✅ POST `/api/v1/asr/transcribe` - Transcribe audio files (multipart upload)
  - ✅ GET `/api/v1/asr/providers` - List all ASR providers with health status
  - ✅ GET `/api/v1/asr/languages/{provider_id}` - Get supported languages
  - ✅ POST `/api/v1/asr/estimate-cost` - Estimate transcription costs

- ✨ **TTS Services API** (3 endpoints) - Text-to-speech with 10+ providers
  - ✅ GET `/api/v1/tts/providers` - List all TTS providers with capabilities
  - ✅ GET `/api/v1/tts/voices` - List available voice samples for cloning
  - ✅ GET `/api/v1/tts/voices/{filename}` - Download voice reference files

**Key Features:**
- 🏦 **Automatic Billing** - All AI services integrated with wallet system
- 📊 **Real-time Health Monitoring** - Provider status updated every 60 seconds
- 💰 **Cost Transparency** - Estimate and track costs for every request
- 🌍 **Multi-language Support** - 17+ languages for TTS, 99+ for ASR, multilingual LLMs
- ⚡ **Streaming Support** - Real-time LLM responses via Server-Sent Events
- 🎙️ **Voice Cloning** - TTS providers with voice cloning capabilities
- 📝 **Token Tracking** - Detailed usage metrics for LLM requests
- ⏱️ **Duration Tracking** - Accurate billing for audio transcription

**Code Examples:**
- Added comprehensive examples for Python, JavaScript, cURL, and PHP
- Includes LLM chat, ASR transcription, and TTS provider listing
- All examples include billing and cost tracking

**Total Endpoints:** 46 documented (26 fully implemented, 20 planned)

**Breaking Changes:** None

---

### Version 1.1.0 (2025-10-24)

**New Features**

🎉 **Added Shared Services APIs:**
- ✨ **RAG Service API** (4 endpoints) - Retrieval-Augmented Generation for intelligent Q&A
  - Initialize knowledge base
  - Query knowledge base with confidence scoring
  - List knowledge bases
  - Delete knowledge base
- ✨ **Document Processor API** (2 endpoints) - Multi-format document processing with chunking
  - Process single document (PDF, DOCX, TXT, HTML)
  - Batch process multiple documents
- ✨ **Wallet Service API** (6 endpoints) - Multi-currency wallet and payment management
  - Create wallet
  - Get wallet balance
  - Credit/debit operations with idempotency
  - Transaction history
  - Payment integration (Paystack, Stripe)
- ✨ **Usage Calculator API** (3 endpoints) - Tiered pricing calculations
  - Calculate RAG costs
  - Calculate voice call costs
  - Calculate document processing costs

**Status:** All new endpoints marked as "Coming Soon" (501 Not Implemented). Implementation planned for v1.2.0.

**Total Endpoints:** 34 documented (14 implemented, 20 planned)

---

### Version 1.0.1 (2025-10-23)

**Enhancements**

✅ **Implemented:**
- ✅ List workflows endpoint (GET /api/v1/workflows) - Fully functional with pagination
- ✅ List executions endpoint (GET /api/v1/executions) - Fully functional with filtering by workflow_id

**Status:** 14/19 endpoints now fully implemented (74%)

---

### Version 1.0.0 (2025-10-23)

**Initial Release**

✅ **Added:**
- Voice Assistants API (8 endpoints)
- Voice Calls API (3 endpoints)
- Workflows API (6 endpoints)
- Workflow Executions API (3 endpoints)
- Rate limiting
- Usage tracking
- Comprehensive error handling
- Multi-language support (17+ languages)

⚠️ **Not Yet Implemented:**
- Update assistant endpoint (PATCH /api/v1/assistants/{id})
- Delete assistant endpoint (DELETE /api/v1/assistants/{id})
- Update workflow endpoint (PATCH /api/v1/workflows/{id})
- Delete workflow endpoint (DELETE /api/v1/workflows/{id})
- Get execution details endpoint (GET /api/v1/executions/{id})

**Breaking Changes:** None (initial release)

---

## Support

### Documentation

- **API Reference:** [https://developer.ailabsafrica.com/docs](https://developer.ailabsafrica.com/docs)
- **Guides:** [https://developer.ailabsafrica.com/guides](https://developer.ailabsafrica.com/guides)
- **OpenAPI Spec:** [https://developer.ailabsafrica.com/openapi.json](https://developer.ailabsafrica.com/openapi.json)

### Community

- **GitHub:** [https://github.com/ailabsafrica/kasaai](https://github.com/ailabsafrica/kasaai)
- **Discord:** [https://discord.gg/kasaai](https://discord.gg/kasaai)
- **Stack Overflow:** Tag your questions with `kasaai`

### Contact

- **Email:** developers@ailabsafrica.com
- **Support Portal:** [https://support.ailabsafrica.com](https://support.ailabsafrica.com)
- **Status Page:** [https://status.ailabsafrica.com](https://status.ailabsafrica.com)

### Service Level Agreement (SLA)

| Plan | Uptime | Support Response |
|------|--------|------------------|
| Free | 99.0% | Community only |
| Starter | 99.5% | 48 hours |
| Professional | 99.9% | 24 hours |
| Enterprise | 99.95% | 4 hours |

---

**© 2025 AI Labs Africa. All rights reserved.**

---

## Voice Library API

**Base URL**: `https://api.ailabsafrica.com/api/voice-library`
**Version**: 1.0.0
**Status**: ✅ Production Ready
**Added**: November 8, 2025

### Overview

The Voice Library API provides centralized voice management across all KasaAI applications. Upload, manage, discover, and use voices for TTS, voice cloning, and voice conversion services.

**Key Features**:
- Centralized voice storage with automatic cloud backup
- Multi-level access control (public/organization/private/restricted)
- Voice preview and playback
- Favorites and rating system
- Advanced filtering and search
- Voice analytics and statistics
- Disaster recovery capabilities

### Authentication

All Voice Library API endpoints require authentication using Bearer tokens.

```bash
Authorization: Bearer {your_access_token}
```

### Base URL

```
https://api.ailabsafrica.com/api/voice-library
```

---

### Endpoints

#### 1. List Voices

Retrieve a paginated list of voices with optional filtering.

**Endpoint**: `GET /`

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `language` | string | No | Filter by language code (e.g., `en`, `es`, `fr`) |
| `gender` | string | No | Filter by gender (`male`, `female`, `neutral`) |
| `accent` | string | No | Filter by accent (e.g., `american`, `british`) |
| `categories` | string | No | Filter by categories (comma-separated) |
| `featured` | boolean | No | Filter featured voices |
| `verified` | boolean | No | Filter verified voices |
| `visibility` | string | No | Filter by access level (`public`, `organization`, `private`) |
| `search` | string | No | Search in voice names and descriptions |
| `skip` | integer | No | Pagination offset (default: 0) |
| `limit` | integer | No | Results per page (default: 100, max: 500) |

**Example Request**:
```bash
curl "https://api.ailabsafrica.com/api/voice-library/?language=en&gender=female&categories=Narration,Audiobook&limit=20" \
  -H "Authorization: Bearer {token}"
```

**Example Response**:
```json
{
  "voices": [
    {
      "voice_id": "akan_female_twi_001",
      "name": "Akan Female Twi Voice",
      "description": "Professional female Twi voice for narration",
      "characteristics": {
        "gender": "female",
        "language": "tw",
        "accent": "akan",
        "tone": "professional",
        "pace": "medium"
      },
      "metadata": {
        "tags": ["twi", "akan", "professional"],
        "categories": ["Narration", "Audiobook"],
        "featured": true,
        "verified": true
      },
      "access": {
        "visibility": "public",
        "owner_id": "system"
      },
      "files": {
        "original": {
          "url": "/voices/akan_female_twi_001/original.wav",
          "format": "wav",
          "size_bytes": 245678
        },
        "preview": {
          "url": "/voices/akan_female_twi_001/preview.wav",
          "format": "wav",
          "duration_seconds": 5.0
        }
      },
      "stats": {
        "views": 1523,
        "uses": 847,
        "favorites": 234,
        "rating": {
          "average": 4.8,
          "count": 156
        }
      },
      "status": "active",
      "created_at": "2025-11-08T10:00:00Z",
      "updated_at": "2025-11-08T10:00:00Z"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 20,
  "has_more": true
}
```

---

#### 2. Get Single Voice

Retrieve detailed information about a specific voice.

**Endpoint**: `GET /{voice_id}`

**Path Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `voice_id` | string | Yes | Unique voice identifier |

**Example Request**:
```bash
curl "https://api.ailabsafrica.com/api/voice-library/akan_female_twi_001" \
  -H "Authorization: Bearer {token}"
```

**Example Response**:
```json
{
  "voice_id": "akan_female_twi_001",
  "name": "Akan Female Twi Voice",
  "description": "Professional female Twi voice for narration and audiobooks",
  "characteristics": {
    "gender": "female",
    "language": "tw",
    "accent": "akan",
    "dialect": "asante",
    "tone": "professional",
    "pace": "medium"
  },
  "metadata": {
    "tags": ["twi", "akan", "professional", "narration"],
    "categories": ["Narration", "Audiobook", "Education"],
    "featured": true,
    "verified": true,
    "version": "1.0"
  },
  "access": {
    "visibility": "public",
    "owner_id": "system",
    "organization_ids": [],
    "allowed_user_ids": []
  },
  "files": {
    "original": {
      "url": "/voices/akan_female_twi_001/original.wav",
      "format": "wav",
      "size_bytes": 245678,
      "sample_rate": 44100,
      "bit_depth": 16
    },
    "preview": {
      "url": "/voices/akan_female_twi_001/preview.wav",
      "format": "wav",
      "duration_seconds": 5.0,
      "size_bytes": 44100
    }
  },
  "stats": {
    "views": 1523,
    "uses": 847,
    "favorites": 234,
    "rating": {
      "average": 4.8,
      "count": 156,
      "total": 749
    },
    "last_used": "2025-11-08T15:30:00Z"
  },
  "status": "active",
  "created_by": "system",
  "created_at": "2025-11-08T10:00:00Z",
  "updated_at": "2025-11-08T10:00:00Z"
}
```

---

#### 3. Create Voice

Upload a new voice to the library.

**Endpoint**: `POST /`

**Content-Type**: `multipart/form-data`

**Form Data**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audio_file` | file | Yes | Audio file (WAV, MP3, OGG, FLAC) |
| `name` | string | Yes | Voice name (1-100 characters) |
| `description` | string | No | Voice description (max 500 characters) |
| `characteristics` | JSON string | No | Voice characteristics object |
| `metadata` | JSON string | No | Voice metadata object |
| `visibility` | string | No | Access level (default: `private`) |

**Characteristics Object**:
```json
{
  "gender": "male|female|neutral",
  "language": "en|es|fr|tw|...",
  "accent": "american|british|akan|...",
  "dialect": "string",
  "tone": "professional|casual|warm|...",
  "pace": "slow|medium|fast"
}
```

**Metadata Object**:
```json
{
  "tags": ["tag1", "tag2"],
  "categories": ["Category1", "Category2"],
  "featured": false,
  "verified": false,
  "version": "1.0"
}
```

**Example Request**:
```bash
curl -X POST "https://api.ailabsafrica.com/api/voice-library/" \
  -H "Authorization: Bearer {token}" \
  -F "audio_file=@my_voice.wav" \
  -F "name=My Professional Voice" \
  -F "description=High-quality professional narration voice" \
  -F 'characteristics={"gender":"female","language":"en","accent":"american","tone":"professional","pace":"medium"}' \
  -F 'metadata={"tags":["professional","narration","corporate"],"categories":["Narration","Corporate"]}' \
  -F "visibility=private"
```

**Example Response**:
```json
{
  "voice_id": "voice_1234567890",
  "name": "My Professional Voice",
  "description": "High-quality professional narration voice",
  "characteristics": {
    "gender": "female",
    "language": "en",
    "accent": "american",
    "tone": "professional",
    "pace": "medium"
  },
  "metadata": {
    "tags": ["professional", "narration", "corporate"],
    "categories": ["Narration", "Corporate"],
    "featured": false,
    "verified": false
  },
  "access": {
    "visibility": "private",
    "owner_id": "user_id_here"
  },
  "files": {
    "original": {
      "url": "/voices/voice_1234567890/original.wav",
      "format": "wav",
      "size_bytes": 1245678
    },
    "preview": {
      "url": "/voices/voice_1234567890/preview.wav",
      "format": "wav",
      "duration_seconds": 5.0
    }
  },
  "stats": {
    "views": 0,
    "uses": 0,
    "favorites": 0,
    "rating": {
      "average": 0.0,
      "count": 0
    }
  },
  "status": "active",
  "created_by": "user_id_here",
  "created_at": "2025-11-08T18:30:00Z",
  "updated_at": "2025-11-08T18:30:00Z"
}
```

---

#### 4. Update Voice

Update voice metadata (does not update audio files).

**Endpoint**: `PUT /{voice_id}`

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "name": "Updated Voice Name",
  "description": "Updated description",
  "characteristics": {
    "gender": "female",
    "language": "en",
    "accent": "british"
  },
  "metadata": {
    "tags": ["updated", "professional"],
    "categories": ["Narration"],
    "featured": true,
    "verified": true
  }
}
```

**Example Request**:
```bash
curl -X PUT "https://api.ailabsafrica.com/api/voice-library/voice_1234567890" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Professional Voice",
    "metadata": {
      "featured": true,
      "categories": ["Narration", "Audiobook", "Corporate"]
    }
  }'
```

**Example Response**:
```json
{
  "voice_id": "voice_1234567890",
  "name": "Premium Professional Voice",
  "description": "High-quality professional narration voice",
  "characteristics": {
    "gender": "female",
    "language": "en",
    "accent": "american",
    "tone": "professional",
    "pace": "medium"
  },
  "metadata": {
    "tags": ["professional", "narration", "corporate"],
    "categories": ["Narration", "Audiobook", "Corporate"],
    "featured": true,
    "verified": false
  },
  "updated_at": "2025-11-08T19:00:00Z"
}
```

---

#### 5. Delete Voice

Permanently delete a voice and its associated files.

**Endpoint**: `DELETE /{voice_id}`

**Example Request**:
```bash
curl -X DELETE "https://api.ailabsafrica.com/api/voice-library/voice_1234567890" \
  -H "Authorization: Bearer {token}"
```

**Example Response**:
```json
{
  "message": "Voice deleted successfully",
  "voice_id": "voice_1234567890",
  "deleted_files": [
    "/voices/voice_1234567890/original.wav",
    "/voices/voice_1234567890/preview.wav"
  ]
}
```

---

#### 6. Add to Favorites

Mark a voice as favorite for quick access.

**Endpoint**: `POST /{voice_id}/favorite`

**Example Request**:
```bash
curl -X POST "https://api.ailabsafrica.com/api/voice-library/akan_female_twi_001/favorite" \
  -H "Authorization: Bearer {token}"
```

**Example Response**:
```json
{
  "message": "Voice added to favorites",
  "voice_id": "akan_female_twi_001",
  "favorites_count": 235
}
```

---

#### 7. Remove from Favorites

Remove a voice from favorites.

**Endpoint**: `DELETE /{voice_id}/favorite`

**Example Request**:
```bash
curl -X DELETE "https://api.ailabsafrica.com/api/voice-library/akan_female_twi_001/favorite" \
  -H "Authorization: Bearer {token}"
```

**Example Response**:
```json
{
  "message": "Voice removed from favorites",
  "voice_id": "akan_female_twi_001",
  "favorites_count": 234
}
```

---

#### 8. Get My Favorites

Retrieve all voices marked as favorites by the current user.

**Endpoint**: `GET /favorites`

**Example Request**:
```bash
curl "https://api.ailabsafrica.com/api/voice-library/favorites" \
  -H "Authorization: Bearer {token}"
```

**Example Response**:
```json
{
  "voices": [
    {
      "voice_id": "akan_female_twi_001",
      "name": "Akan Female Twi Voice",
      "characteristics": {...},
      "files": {...},
      "favorited_at": "2025-11-08T14:20:00Z"
    },
    {
      "voice_id": "voice_1234567890",
      "name": "My Professional Voice",
      "characteristics": {...},
      "files": {...},
      "favorited_at": "2025-11-08T18:45:00Z"
    }
  ],
  "total": 2
}
```

---

#### 9. Rate Voice

Submit a rating and optional comment for a voice.

**Endpoint**: `POST /{voice_id}/rate`

**Content-Type**: `application/json`

**Request Body**:
```json
{
  "rating": 5,
  "comment": "Excellent voice quality! Perfect for audiobook narration."
}
```

**Validations**:
- `rating`: Integer between 1 and 5 (required)
- `comment`: String, max 500 characters (optional)

**Example Request**:
```bash
curl -X POST "https://api.ailabsafrica.com/api/voice-library/akan_female_twi_001/rate" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 5,
    "comment": "Perfect for educational content in Twi!"
  }'
```

**Example Response**:
```json
{
  "message": "Rating submitted successfully",
  "voice_id": "akan_female_twi_001",
  "rating": {
    "average": 4.8,
    "count": 157,
    "your_rating": 5
  }
}
```

---

#### 10. Record Usage

Record that a voice was used (automatically increments usage statistics).

**Endpoint**: `POST /{voice_id}/usage`

**Example Request**:
```bash
curl -X POST "https://api.ailabsafrica.com/api/voice-library/akan_female_twi_001/usage" \
  -H "Authorization: Bearer {token}"
```

**Example Response**:
```json
{
  "message": "Usage recorded successfully",
  "voice_id": "akan_female_twi_001",
  "total_uses": 848
}
```

---

#### 11. Get Voice Analytics

Retrieve comprehensive analytics for the voice library.

**Endpoint**: `GET /analytics`

**Example Request**:
```bash
curl "https://api.ailabsafrica.com/api/voice-library/analytics" \
  -H "Authorization: Bearer {token}"
```

**Example Response**:
```json
{
  "total_voices": 150,
  "by_language": {
    "en": 80,
    "es": 30,
    "fr": 20,
    "tw": 20
  },
  "by_gender": {
    "male": 70,
    "female": 60,
    "neutral": 20
  },
  "by_visibility": {
    "public": 50,
    "organization": 30,
    "private": 70
  },
  "featured_count": 25,
  "verified_count": 40,
  "total_uses": 15847,
  "total_favorites": 1234,
  "total_ratings": 892,
  "average_rating": 4.6,
  "top_voices": [
    {
      "voice_id": "akan_female_twi_001",
      "name": "Akan Female Twi Voice",
      "uses": 847,
      "favorites": 234,
      "rating": 4.8
    }
  ]
}
```

---

#### 12. Restore Voice Files

Restore voice files from Hetzner Storage Box backup (disaster recovery).

**Endpoint**: `POST /{voice_id}/restore`

**Example Request**:
```bash
curl -X POST "https://api.ailabsafrica.com/api/voice-library/voice_1234567890/restore" \
  -H "Authorization: Bearer {token}"
```

**Example Response**:
```json
{
  "success": true,
  "voice_id": "voice_1234567890",
  "restore_status": {
    "original": true,
    "preview": true,
    "processed": false
  },
  "message": "Voice files restored successfully from backup"
}
```

---

### Error Responses

#### 400 Bad Request
```json
{
  "detail": "Invalid voice data: name is required"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Invalid token"
}
```

#### 403 Forbidden
```json
{
  "detail": "You don't have permission to access this voice"
}
```

#### 404 Not Found
```json
{
  "detail": "Voice not found"
}
```

#### 413 Payload Too Large
```json
{
  "detail": "Audio file size exceeds 50MB limit"
}
```

#### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "rating"],
      "msg": "ensure this value is between 1 and 5",
      "type": "value_error"
    }
  ]
}
```

---

### Integration Examples

#### Python Example

```python
import requests
from pathlib import Path

API_BASE = "https://api.ailabsafrica.com/api/voice-library"
TOKEN = "your_access_token_here"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# 1. List voices with filters
def list_voices():
    params = {
        "language": "en",
        "gender": "female",
        "categories": "Narration,Audiobook",
        "limit": 20
    }
    response = requests.get(f"{API_BASE}/", headers=headers, params=params)
    return response.json()

# 2. Upload a new voice
def create_voice():
    audio_file = Path("my_voice.wav")
    
    files = {
        "audio_file": ("voice.wav", open(audio_file, "rb"), "audio/wav")
    }
    
    data = {
        "name": "My Custom Voice",
        "description": "Professional narration voice",
        "characteristics": '{"gender":"female","language":"en","accent":"american"}',
        "metadata": '{"tags":["professional","narration"],"categories":["Narration"]}',
        "visibility": "private"
    }
    
    response = requests.post(f"{API_BASE}/", headers=headers, files=files, data=data)
    return response.json()

# 3. Add to favorites
def add_favorite(voice_id):
    response = requests.post(f"{API_BASE}/{voice_id}/favorite", headers=headers)
    return response.json()

# 4. Rate a voice
def rate_voice(voice_id, rating, comment):
    data = {
        "rating": rating,
        "comment": comment
    }
    response = requests.post(
        f"{API_BASE}/{voice_id}/rate",
        headers=headers,
        json=data
    )
    return response.json()

# Usage
voices = list_voices()
print(f"Found {voices['total']} voices")

new_voice = create_voice()
print(f"Created voice: {new_voice['voice_id']}")
```

#### JavaScript/TypeScript Example

```typescript
const API_BASE = "https://api.ailabsafrica.com/api/voice-library";
const TOKEN = "your_access_token_here";

const headers = {
  "Authorization": `Bearer ${TOKEN}`
};

// 1. List voices
async function listVoices() {
  const params = new URLSearchParams({
    language: "en",
    gender: "female",
    categories: "Narration,Audiobook",
    limit: "20"
  });
  
  const response = await fetch(`${API_BASE}/?${params}`, { headers });
  return await response.json();
}

// 2. Upload a new voice
async function createVoice(audioFile: File) {
  const formData = new FormData();
  formData.append("audio_file", audioFile);
  formData.append("name", "My Custom Voice");
  formData.append("description", "Professional narration voice");
  formData.append(
    "characteristics",
    JSON.stringify({
      gender: "female",
      language: "en",
      accent: "american"
    })
  );
  formData.append(
    "metadata",
    JSON.stringify({
      tags: ["professional", "narration"],
      categories: ["Narration"]
    })
  );
  formData.append("visibility", "private");
  
  const response = await fetch(`${API_BASE}/`, {
    method: "POST",
    headers,
    body: formData
  });
  
  return await response.json();
}

// 3. Add to favorites
async function addFavorite(voiceId: string) {
  const response = await fetch(`${API_BASE}/${voiceId}/favorite`, {
    method: "POST",
    headers
  });
  return await response.json();
}

// 4. Rate a voice
async function rateVoice(voiceId: string, rating: number, comment: string) {
  const response = await fetch(`${API_BASE}/${voiceId}/rate`, {
    method: "POST",
    headers: {
      ...headers,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ rating, comment })
  });
  return await response.json();
}

// Usage
const voices = await listVoices();
console.log(`Found ${voices.total} voices`);
```

---

### Best Practices

1. **Voice Upload**:
   - Use high-quality audio files (44.1kHz, 16-bit or higher)
   - Keep file sizes under 50MB
   - Provide descriptive names and accurate metadata
   - Test voice preview before making public

2. **Access Control**:
   - Use `private` visibility for personal voices
   - Use `organization` for team-shared voices
   - Use `public` only for verified, high-quality voices
   - Request verification for public voices

3. **Performance**:
   - Cache voice lists when possible
   - Use pagination for large result sets
   - Filter by language and category to reduce results
   - Load voice previews on-demand

4. **Error Handling**:
   - Always check response status codes
   - Handle 401/403 errors by refreshing tokens
   - Retry failed uploads with exponential backoff
   - Validate audio files before upload

5. **Usage Tracking**:
   - Call `/usage` endpoint when voice is actually used
   - Don't track preview playbacks as usage
   - Record usage for analytics and billing
   - Use favorites for quick access

---

### Rate Limits

- **List/Read Operations**: 100 requests/minute
- **Create/Update/Delete**: 20 requests/minute
- **Favorites/Ratings**: 50 requests/minute
- **File Uploads**: 10 requests/minute

Rate limit headers included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699468800
```

---

### Changelog

#### Version 1.0.0 (November 8, 2025)
- ✅ Initial release
- ✅ Voice CRUD operations
- ✅ Favorites management
- ✅ Rating system
- ✅ Usage tracking
- ✅ Analytics endpoint
- ✅ Disaster recovery (restore endpoint)
- ✅ Multi-level access control
- ✅ Automatic cloud backup (Hetzner Storage Box)

---

### Related Resources

- [Voice Library Architecture Documentation](../architecture/VOICE_LIBRARY_ARCHITECTURE.md)
- [Voice Library Integration Guide](../b2c-portal/src/components/voice-library/INTEGRATION_GUIDE.md)
- [Voice Library Service Implementation](../shared/services/voice_library_service.py)
- [Voice Library API Routes](../core_backend/backend/routes/voice_library.py)

---

