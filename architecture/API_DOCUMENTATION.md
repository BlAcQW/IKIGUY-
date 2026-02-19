# KasaAI Platform API Documentation

**Version**: 2.0
**Last Updated**: 2025-10-24
**Status**: Living Document

---

## Table of Contents

1. [API Design Standards](#api-design-standards)
2. [Authentication & Authorization](#authentication--authorization)
3. [Request/Response Formats](#requestresponse-formats)
4. [Error Handling](#error-handling)
5. [Versioning Strategy](#versioning-strategy)
6. [AI Services API](#ai-services-api)
7. [RAG Services API](#rag-services-api)
8. [Document Management API](#document-management-api)
9. [Wallet Services API](#wallet-services-api)
10. [Code Examples](#code-examples)

---

## API Design Standards

### RESTful Principles

All APIs follow REST conventions:

| Method | Purpose | Example |
|--------|---------|---------|
| GET | Retrieve resource(s) | `GET /api/providers` |
| POST | Create new resource | `POST /api/providers` |
| PUT | Update entire resource | `PUT /api/providers/{id}` |
| PATCH | Partial update | `PATCH /api/providers/{id}` |
| DELETE | Remove resource | `DELETE /api/providers/{id}` |

### URL Structure

```
https://{domain}/api/v{version}/{resource}/{id}/{sub-resource}
```

**Examples**:
```
GET  https://api.ailabsafrica.com/api/v1/tts/providers
POST https://api.ailabsafrica.com/api/v1/tts/synthesize
GET  https://api.ailabsafrica.com/api/v1/knowledge-base/collections
POST https://api.ailabsafrica.com/api/v1/knowledge-base/premier_health/query
```

### Naming Conventions

- **Resources**: Plural nouns (`providers`, `documents`, `collections`)
- **Actions**: Verbs for non-CRUD operations (`synthesize`, `query`, `upload`)
- **IDs**: Use resource name + `_id` in request body (`provider_id`, `document_id`)
- **Case**: snake_case for API paths and JSON keys
- **Dates**: ISO 8601 format (`2025-10-24T10:30:00Z`)

---

## Authentication & Authorization

### Authentication Methods

#### 1. JWT Bearer Token (Primary)

All authenticated requests must include a JWT bearer token from Supabase:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Token Structure**:
```json
{
  "sub": "user_id_here",
  "email": "user@example.com",
  "role": "authenticated",
  "exp": 1735041600
}
```

**Backend Verification** (FastAPI):
```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from supabase import create_client

security = HTTPBearer()
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security)
) -> dict:
    """Verify JWT and return user info."""
    try:
        user = supabase.auth.get_user(credentials.credentials)
        return user.user.dict()
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
```

#### 2. API Key (Developer Platform Only)

Developer API uses API keys:

```http
X-API-Key: dev_key_1234567890abcdef
```

### Authorization Levels

| Level | Access | Verification |
|-------|--------|-------------|
| Public | No auth required | None |
| Authenticated | Valid JWT | `get_current_user()` |
| Organization | User in org | Check `user_id` in org members |
| Admin | Admin role | Check `role` in JWT claims |

---

## Request/Response Formats

### Standard Request Format

#### GET Request
```http
GET /api/v1/tts/providers HTTP/1.1
Host: api.ailabsafrica.com
Authorization: Bearer {jwt_token}
Accept: application/json
```

#### POST Request
```http
POST /api/v1/tts/synthesize HTTP/1.1
Host: api.ailabsafrica.com
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "provider_id": "coqui_xtts",
  "text": "Hello, world!",
  "language": "en",
  "voice_settings": {
    "speed": 1.0
  }
}
```

### Standard Response Format

#### Success Response (200 OK)
```json
{
  "success": true,
  "data": {
    "audio_url": "https://...",
    "duration_ms": 1500
  },
  "metadata": {
    "request_id": "req_abc123",
    "timestamp": "2025-10-24T10:30:00Z",
    "processing_time_ms": 234
  }
}
```

#### List Response (200 OK)
```json
{
  "success": true,
  "data": [
    {
      "id": "provider_1",
      "name": "Provider Name"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 150,
    "total_pages": 3
  }
}
```

#### Created Response (201 Created)
```json
{
  "success": true,
  "data": {
    "id": "newly_created_id",
    "created_at": "2025-10-24T10:30:00Z"
  }
}
```

#### No Content Response (204 No Content)
```
(Empty body)
```

---

## Error Handling

### Standard Error Response

All errors return this format:

```json
{
  "success": false,
  "error": {
    "code": "PROVIDER_OFFLINE",
    "message": "The selected AI provider is currently offline",
    "details": {
      "provider_id": "coqui_xtts",
      "last_checked": "2025-10-24T10:29:00Z"
    }
  },
  "request_id": "req_xyz789",
  "timestamp": "2025-10-24T10:30:00Z"
}
```

### HTTP Status Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| 200 | OK | Successful GET/PUT/PATCH/DELETE |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE (no response body) |
| 400 | Bad Request | Invalid input, validation error |
| 401 | Unauthorized | Missing or invalid auth token |
| 403 | Forbidden | Valid auth but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource already exists, state conflict |
| 422 | Unprocessable Entity | Valid JSON but semantic errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | AI service not responding |
| 503 | Service Unavailable | Service temporarily down |

### Error Codes

Application-specific error codes:

```python
class ErrorCode:
    # Authentication errors (1xxx)
    INVALID_TOKEN = "AUTH_1001"
    EXPIRED_TOKEN = "AUTH_1002"
    INSUFFICIENT_PERMISSIONS = "AUTH_1003"

    # Validation errors (2xxx)
    INVALID_INPUT = "VAL_2001"
    MISSING_REQUIRED_FIELD = "VAL_2002"
    INVALID_FORMAT = "VAL_2003"

    # Resource errors (3xxx)
    RESOURCE_NOT_FOUND = "RES_3001"
    RESOURCE_ALREADY_EXISTS = "RES_3002"
    RESOURCE_CONFLICT = "RES_3003"

    # AI Service errors (4xxx)
    PROVIDER_OFFLINE = "AI_4001"
    PROVIDER_TIMEOUT = "AI_4002"
    PROVIDER_ERROR = "AI_4003"
    UNSUPPORTED_LANGUAGE = "AI_4004"
    UNSUPPORTED_CAPABILITY = "AI_4005"

    # Wallet errors (5xxx)
    INSUFFICIENT_CREDITS = "WALLET_5001"
    INVALID_TRANSACTION = "WALLET_5002"

    # System errors (9xxx)
    INTERNAL_ERROR = "SYS_9001"
    DATABASE_ERROR = "SYS_9002"
    SERVICE_UNAVAILABLE = "SYS_9003"
```

### FastAPI Exception Handling

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import uuid

app = FastAPI()

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": getattr(exc, "error_code", "UNKNOWN"),
                "message": exc.detail,
                "details": getattr(exc, "details", {})
            },
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )

# Usage
raise HTTPException(
    status_code=400,
    detail="Provider is offline",
    headers={"error_code": "AI_4001"}
)
```

---

## Versioning Strategy

### URL Versioning

Version is included in URL path:

```
/api/v1/resource
/api/v2/resource
```

### Version Lifecycle

1. **v1.x** → Current stable version
2. **v2.x** → Next version (introduce breaking changes)
3. **Deprecation Period**: 6 months minimum before removing old version

### Breaking vs Non-Breaking Changes

**Non-Breaking** (same version):
- Adding new optional fields
- Adding new endpoints
- Adding new enum values
- Bug fixes

**Breaking** (new version):
- Removing fields
- Renaming fields
- Changing field types
- Changing response structure
- Removing endpoints

---

## AI Services API

### Overview

Unified API for Text-to-Speech (TTS), Large Language Models (LLM), and Automatic Speech Recognition (ASR).

### Base Endpoints

```
/api/v1/tts/*     - Text-to-Speech services
/api/v1/llm/*     - Large Language Model services
/api/v1/asr/*     - Speech Recognition services
```

---

### TTS API

#### List Providers

**Endpoint**: `GET /api/v1/tts/providers`

**Query Parameters**:
- `force_refresh` (boolean): Force provider health check

**Response**:
```json
{
  "success": true,
  "data": {
    "coqui_xtts": {
      "id": "coqui_xtts",
      "name": "Coqui XTTS v2",
      "provider_type": "tts",
      "endpoint": "https://coqui.ailabsafrica.com",
      "status": "online",
      "capabilities": {
        "voiceCloning": true,
        "multiLanguage": true,
        "speedControl": true,
        "pitchControl": false
      },
      "languages": 17,
      "languageList": ["en", "es", "fr", "de", ...],
      "description": "Multilingual TTS with voice cloning",
      "icon": "🎙️",
      "lastChecked": "2025-10-24T10:30:00Z",
      "responseTime": 123.45
    }
  }
}
```

#### Synthesize Speech

**Endpoint**: `POST /api/v1/tts/synthesize`

**Request**:
```json
{
  "provider_id": "coqui_xtts",
  "text": "Hello, this is a test of text-to-speech synthesis.",
  "language": "en",
  "voice_settings": {
    "speed": 1.0,
    "speaker": "default"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "audio_url": "https://api.ailabsafrica.com/storage/audio/abc123.wav",
    "audio_base64": "UklGRi4...",  // Optional
    "duration_ms": 2340,
    "provider_id": "coqui_xtts",
    "language": "en"
  },
  "metadata": {
    "request_id": "req_abc123",
    "processing_time_ms": 456,
    "credits_used": 5
  }
}
```

#### Clone Voice

**Endpoint**: `POST /api/v1/tts/clone-voice`

**Request** (multipart/form-data):
```
provider_id: coqui_xtts
text: "Text to synthesize with cloned voice"
language: en
audio_file: (binary audio file)
```

**Response**: Same as synthesize

#### Get Provider Health

**Endpoint**: `GET /api/v1/tts/providers/{provider_id}/health`

**Response**:
```json
{
  "success": true,
  "data": {
    "provider_id": "coqui_xtts",
    "status": "online",
    "response_time_ms": 45.2,
    "last_checked": "2025-10-24T10:30:00Z",
    "uptime_percentage": 99.5,
    "total_checks": 1440,
    "consecutive_failures": 0
  }
}
```

---

### LLM API

#### List Models

**Endpoint**: `GET /api/v1/llm/models`

**Response**:
```json
{
  "success": true,
  "data": {
    "llama_32_3b": {
      "id": "llama_32_3b",
      "name": "Llama 3.2 3B",
      "provider_type": "llm",
      "endpoint": "https://ollama.ailabsafrica.com",
      "status": "online",
      "capabilities": {
        "streaming": true,
        "reasoning": true,
        "functionCalling": false
      },
      "metadata": {
        "modelSize": "3B",
        "contextWindow": 8192,
        "parametersCount": "3000000000"
      }
    }
  }
}
```

#### Chat Completion

**Endpoint**: `POST /api/v1/llm/chat`

**Request**:
```json
{
  "model_id": "llama_32_3b",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Explain quantum computing in simple terms."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 500,
  "stream": false
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "message": {
      "role": "assistant",
      "content": "Quantum computing is..."
    },
    "finish_reason": "stop",
    "tokens_used": {
      "prompt": 25,
      "completion": 150,
      "total": 175
    }
  },
  "metadata": {
    "model_id": "llama_32_3b",
    "processing_time_ms": 1234,
    "credits_used": 2
  }
}
```

**Streaming Response** (when `stream: true`):

```
data: {"type": "token", "content": "Quantum"}
data: {"type": "token", "content": " computing"}
data: {"type": "token", "content": " is"}
data: {"type": "done", "tokens_used": 175}
```

---

### ASR API

#### List Providers

**Endpoint**: `GET /api/v1/asr/providers`

**Response**: Same structure as TTS providers

#### Transcribe Audio

**Endpoint**: `POST /api/v1/asr/transcribe`

**Request** (multipart/form-data):
```
provider_id: akan_whisper_giftmark
audio_file: (binary audio file)
language: tw
include_timestamps: true
```

**Response**:
```json
{
  "success": true,
  "data": {
    "text": "Yɛn nkɔ sukuu nnɛra",
    "language": "tw",
    "confidence": 0.95,
    "duration_ms": 2500,
    "segments": [
      {
        "text": "Yɛn nkɔ sukuu",
        "start_ms": 0,
        "end_ms": 1200,
        "confidence": 0.96
      },
      {
        "text": "nnɛra",
        "start_ms": 1200,
        "end_ms": 2500,
        "confidence": 0.94
      }
    ]
  },
  "metadata": {
    "provider_id": "akan_whisper_giftmark",
    "processing_time_ms": 678,
    "credits_used": 3
  }
}
```

---

### Voice Lab API

**New Unified API** for voice services combining ASR, TTS, and LLM chat.

**Base**: `/api/voice-lab/*`

#### Transcribe Audio (Speech-to-Text)

**Endpoint**: `POST /api/voice-lab/transcribe`

**Request**:
```json
{
  "audio_base64": "UklGRiQAAABXQVZF...",
  "language": "tw",
  "dialect": "asante",
  "model": "akan-whisper",
  "enhance_text": true,
  "return_timestamps": false,
  "enable_vad": false,
  "enable_streaming": false
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "text": "Yɛn nkɔ sukuu nnɛra",
    "enhanced_text": "Yɛn nkɔ sukuu nnɛ ara",
    "confidence": 0.95,
    "language": "tw",
    "dialect": "asante",
    "duration": 2.5,
    "processing_time": 0.678,
    "timestamps": null
  },
  "metadata": {
    "request_id": "req_abc123",
    "model_used": "akan-whisper",
    "timestamp": "2025-10-24T10:30:00Z"
  }
}
```

#### Synthesize Speech (Text-to-Speech)

**Endpoint**: `POST /api/voice-lab/synthesize`

**Request**:
```json
{
  "text": "Akwaaba",
  "model": "akan-mms",
  "voice_id": "default",
  "language": "tw",
  "speed": 1.0,
  "pitch": 0.0,
  "dialect": "asante",
  "enhance_text": true,
  "output_format": "wav"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "audio_base64": "UklGRiQAAABXQVZF...",
    "text": "Akwaaba",
    "voice_id": "default",
    "duration": 1.2,
    "processing_time": 0.456,
    "sample_rate": 22050,
    "model": "akan-mms"
  },
  "metadata": {
    "request_id": "req_xyz789",
    "credits_used": 2,
    "timestamp": "2025-10-24T10:30:00Z"
  }
}
```

#### Chat with LLM

**Endpoint**: `POST /api/voice-lab/chat`

**Request**:
```json
{
  "message": "What is the capital of Ghana?",
  "model": "gemini-2.5-flash",
  "mode": "general",
  "history": [
    {
      "role": "user",
      "content": "Hello"
    },
    {
      "role": "assistant",
      "content": "Hello! How can I help you?"
    }
  ],
  "language": "en",
  "dialect": "asante"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "response": "The capital of Ghana is Accra.",
    "model": "gemini-2.5-flash",
    "processing_time": 1.234
  },
  "metadata": {
    "request_id": "req_chat123",
    "mode": "general",
    "timestamp": "2025-10-24T10:30:00Z"
  }
}
```

#### Voice Assistant Management

**List Assistants**

**Endpoint**: `GET /api/voice/assistants/`

**Query Parameters**:
- `user_id` (string): Filter by user ID
- `active_only` (boolean): Show only active assistants (default: true)

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "asst_abc123",
      "name": "Healthcare Assistant",
      "system_prompt": "You are a helpful healthcare assistant...",
      "language": "en",
      "is_active": true,
      "transcribe_model": "akan-whisper",
      "llm_model": "gemini-2.5-flash",
      "tts_model": "akan-mms",
      "first_message": "Hello, how can I help you today?",
      "created_at": "2025-10-24T08:00:00Z",
      "updated_at": "2025-10-24T10:00:00Z"
    }
  ]
}
```

**Create Assistant**

**Endpoint**: `POST /api/voice/assistants/`

**Request**:
```json
{
  "name": "New Assistant",
  "system_prompt": "You are a helpful assistant.",
  "language": "en",
  "transcribe_model": "akan-whisper",
  "llm_model": "gemini-2.5-flash",
  "tts_model": "akan-mms",
  "first_message": "Hello!",
  "is_active": true
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "asst_new123",
    "name": "New Assistant",
    ...
  }
}
```

**Update Assistant**

**Endpoint**: `PUT /api/voice/assistants/{assistant_id}`

**Request**: Same as create (partial updates supported)

**Delete Assistant**

**Endpoint**: `DELETE /api/voice/assistants/{assistant_id}`

**Response**: `204 No Content`

**Activate/Deactivate Assistant**

**Endpoints**:
- `POST /api/voice/assistants/{assistant_id}/activate`
- `POST /api/voice/assistants/{assistant_id}/deactivate`

**Test Assistant**

**Endpoint**: `GET /api/voice/assistants/{assistant_id}/test`

**Query Parameters**:
- `test_input` (string): Test message (default: "Hello, how are you?")

**Response**:
```json
{
  "success": true,
  "data": {
    "assistant_id": "asst_abc123",
    "test_input": "Hello",
    "test_output": "Hello! How can I help you?",
    "status": "success",
    "response_time": 1.234
  }
}
```

#### WebSocket Voice Chat

**Endpoint**: `WS /voice/ws/voice-chat/{assistant_id}?token={jwt_token}`

**Message Types**:

Client → Server:
```json
{"type": "text", "data": "Hello"}
{"type": "audio", "data": "base64_audio_chunk"}
{"type": "end_audio", "data": null}
{"type": "barge_in", "data": null}
{"type": "config", "data": {"language": "tw", "dialect": "asante"}}
```

**Message Descriptions**:
- `text`: Send text message for processing (alternative to voice input)
- `audio`: Stream audio chunk for real-time transcription
- `end_audio`: Signal end of audio stream to finalize transcription
- `barge_in`: Interrupt assistant speech (stops current audio playback)
- `config`: Update assistant configuration (language, dialect, etc.)

Server → Client:
```json
{"type": "status", "data": "Connected"}
{"type": "transcription", "data": {"text": "hello", "is_final": false}}
{"type": "text_response", "data": "Hello! How can I help?"}
{"type": "audio_chunk", "data": "base64_audio_chunk"}
{"type": "audio_complete", "data": {"duration": 2.5}}
{"type": "error", "data": "Error message"}
```

---

## RAG Services API

### Overview

Retrieval-Augmented Generation API for semantic search over document collections.

**Base**: `/api/v1/knowledge-base/*`

---

### List Collections

**Endpoint**: `GET /api/v1/knowledge-base/collections`

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "collection_name": "premier_health_production",
      "display_name": "Premier Health Knowledge Base",
      "document_count": 1542,
      "total_chunks": 8923,
      "created_at": "2025-01-15T08:00:00Z",
      "last_updated": "2025-10-24T09:00:00Z"
    }
  ]
}
```

### Query Collection

**Endpoint**: `POST /api/v1/knowledge-base/{collection_name}/query`

**Request**:
```json
{
  "query": "What are the operating hours for the clinic in Accra?",
  "top_k": 5,
  "min_similarity": 0.7,
  "include_metadata": true
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "query": "What are the operating hours...",
    "results": [
      {
        "content": "The Accra Central Clinic operates Monday-Friday 8AM-6PM...",
        "similarity": 0.89,
        "chunk_id": "chunk_abc123",
        "document_id": "doc_xyz789",
        "metadata": {
          "title": "Accra Clinic Information",
          "page": 3,
          "source": "clinic_guide.pdf"
        }
      }
    ],
    "context": "The Accra Central Clinic operates...\n\n..."
  },
  "metadata": {
    "collection_name": "premier_health_production",
    "results_count": 5,
    "processing_time_ms": 234
  }
}
```

### Upload Document

**Endpoint**: `POST /api/v1/knowledge-base/{collection_name}/documents`

**Request** (multipart/form-data):
```
file: (binary file)
title: "Healthcare Providers in Accra"
metadata: {"category": "clinics", "region": "greater-accra"}
chunk_size: 500
chunk_overlap: 50
```

**Response**:
```json
{
  "success": true,
  "data": {
    "document_id": "doc_new123",
    "title": "Healthcare Providers in Accra",
    "chunks_created": 12,
    "status": "processing"
  }
}
```

### Delete Document

**Endpoint**: `DELETE /api/v1/knowledge-base/{collection_name}/documents/{document_id}`

**Response**: `204 No Content`

---

## Document Management API

### Overview

Universal document processing for PDF, DOCX, TXT, MD, HTML.

**Base**: `/api/v1/documents/*`

---

### Upload & Process Document

**Endpoint**: `POST /api/v1/documents/upload`

**Request** (multipart/form-data):
```
file: (binary file)
extract_metadata: true
chunk: true
chunk_size: 500
```

**Response**:
```json
{
  "success": true,
  "data": {
    "document_id": "doc_abc123",
    "filename": "report.pdf",
    "file_type": "pdf",
    "file_size_bytes": 245678,
    "page_count": 15,
    "extracted_text_length": 12345,
    "chunks": [
      {
        "chunk_id": "chunk_1",
        "text": "...",
        "start_page": 1,
        "end_page": 1
      }
    ],
    "metadata": {
      "author": "John Doe",
      "created_date": "2025-01-10",
      "title": "Annual Report"
    }
  }
}
```

### Get Document

**Endpoint**: `GET /api/v1/documents/{document_id}`

**Response**: Same as upload response

### List Documents

**Endpoint**: `GET /api/v1/documents`

**Query Parameters**:
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 50, max: 100)
- `file_type` (string): Filter by type (pdf, docx, txt)

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "document_id": "doc_abc123",
      "filename": "report.pdf",
      "uploaded_at": "2025-10-24T09:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 250,
    "total_pages": 5
  }
}
```

---

## Analytics Services API

### Overview

Comprehensive usage tracking and cost analytics across all services with unified cost aggregation for VAPI assistants.

**Base**: `/api/analytics/*` (Core Backend)

**Version**: v1.3.0 (Fully Implemented)

---

### Get Assistant Costs (Unified Analytics)

**THE CENTERPIECE ENDPOINT** - Aggregates costs from ALL services for a VAPI assistant.

**Endpoint**: `GET /api/analytics/assistants/{assistant_id}/costs`

**Authentication**: Bearer token or X-User-Id header

**Query Parameters**:
- `start_date` (ISO 8601, optional): Filter from date (default: 30 days ago)
- `end_date` (ISO 8601, optional): Filter to date (default: now)

**Response**:
```json
{
  "success": true,
  "data": {
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
}
```

**Data Sources**:
- **VAPI Calls**: MongoDB collection `vapi_call_logs`
- **Vonage Calls**: MongoDB collection `wallet_transactions` (metadata.service="vonage")
- **Twilio**: MongoDB collection `wallet_transactions` (metadata.service="twilio")
- **LLM**: MongoDB collection `wallet_transactions` (metadata.service="llm")
- **TTS**: MongoDB collection `wallet_transactions` (metadata.service="tts")
- **ASR**: MongoDB collection `wallet_transactions` (metadata.service="asr")

**Implementation**:
- Service: `/opt/kasaai/apps/shared/services/unified_analytics_service.py`
- Route: `/opt/kasaai/apps/core_backend/backend/routes/analytics.py`
- Method: `UnifiedAnalyticsService.get_assistant_costs()`

**Key Features**:
- ✅ Cross-service cost aggregation (6 services)
- ✅ Detailed usage metrics per service
- ✅ Percentage cost distribution
- ✅ Call success rate tracking
- ✅ Average cost and duration calculations
- ✅ Flexible date range filtering
- ✅ User-specific filtering (optional)

---

### Architecture: Unified Analytics Service

The `UnifiedAnalyticsService` in `@shared/services/unified_analytics_service.py` is the centralized service for cross-service analytics.

**Class**: `UnifiedAnalyticsService`

**Constructor**:
```python
def __init__(self, db: AsyncIOMotorDatabase):
    """
    Initialize with MongoDB database.

    Args:
        db: MongoDB database instance
    """
    self.db = db
    self.vapi_call_logs_collection = db["vapi_call_logs"]
    self.wallet_transactions_collection = db["wallet_transactions"]
```

**Core Methods**:

1. **`get_assistant_costs()`** - Main aggregation method
   - Aggregates costs from 6 services
   - Returns comprehensive breakdown with usage metrics
   - Filters by date range and user_id
   - Calculates percentages and averages

2. **`_get_vapi_costs()`** - VAPI call costs from call logs
   - Queries: `vapi_call_logs` collection
   - Filter: `assistant_id`, `created_at`
   - Aggregates: total_cost, call_count, duration, success_rate

3. **`_get_vonage_costs()`** - Vonage costs from wallet transactions
   - Queries: `wallet_transactions` collection
   - Filter: `metadata.service="vonage"`, `metadata.assistant_id`
   - Aggregates: total_cost, call_count, duration_seconds

4. **`_get_twilio_costs()`** - Twilio costs from wallet transactions
   - Queries: `wallet_transactions` collection
   - Filter: `metadata.service="twilio"`, `metadata.assistant_id`
   - Aggregates: total_cost, sms_count, voice_call_count, duration

5. **`_get_llm_costs()`** - LLM costs from wallet transactions
   - Queries: `wallet_transactions` collection
   - Filter: `metadata.service="llm"`, `metadata.assistant_id`
   - Aggregates: total_cost, request_count, total_tokens, input_tokens, output_tokens

6. **`_get_tts_costs()`** - TTS costs from wallet transactions
   - Queries: `wallet_transactions` collection
   - Filter: `metadata.service="tts"`, `metadata.assistant_id`
   - Aggregates: total_cost, request_count, total_characters

7. **`_get_asr_costs()`** - ASR costs from wallet transactions
   - Queries: `wallet_transactions` collection
   - Filter: `metadata.service="asr"`, `metadata.assistant_id`
   - Aggregates: total_cost, request_count, total_duration_seconds

**MongoDB Aggregation Pipeline Pattern**:
```python
pipeline = [
    {
        "$match": {
            "metadata.service": "vonage",
            "metadata.assistant_id": assistant_id,
            "created_at": {"$gte": start_date, "$lte": end_date}
        }
    },
    {
        "$group": {
            "_id": None,
            "total_cost": {"$sum": "$amount"},
            "call_count": {"$sum": 1},
            "total_duration_seconds": {"$sum": "$metadata.duration_seconds"}
        }
    }
]
```

**Transaction Metadata Structure**:

All wallet transactions include rich metadata for analytics:

```python
metadata = {
    "service": "vonage",  # Service type identifier
    "service_type": "voice_call",  # Sub-type (voice, sms, etc.)
    "assistant_id": "asst_123abc",  # VAPI assistant attribution
    "vapi_call_id": "call_xyz789",  # VAPI call reference
    "phone_number": "+14155551234",  # Contact number
    "destination": "US",  # Country/destination
    "duration_seconds": 120,  # Call/audio duration
    "model_id": "kasaai_llama_twi",  # LLM/ASR/TTS model
    "input_tokens": 25,  # LLM input tokens
    "output_tokens": 8,  # LLM output tokens
    "total_tokens": 33,  # LLM total tokens
    "timestamp": "2025-10-26T14:30:00Z"  # Transaction timestamp
}
```

---

### Automatic Billing Integration

All services now automatically deduct costs from user wallets with detailed transaction records:

**Services with Automatic Billing**:

1. **Vonage** (`VonageCostMonitoringService`)
   - Voice calls: Automatic wallet deduction with duration tracking
   - SMS: Per-message billing with destination tracking
   - Location: `/opt/kasaai/apps/core_backend/backend/services/vonage_cost_monitoring_service.py`

2. **Twilio** (`TwilioCostMonitoringService`)
   - Voice calls: Duration-based billing
   - SMS: Per-message billing
   - MMS: Media message billing
   - WhatsApp: Message billing
   - Location: `/opt/kasaai/apps/core_backend/backend/services/twilio_cost_monitoring_service.py`

3. **LLM** (`LLMProviderService`)
   - Token-based billing (input + output tokens)
   - Model-specific pricing
   - Location: `/opt/kasaai/apps/shared/integration/llm_services.py`

4. **ASR** (`ASRProviderService`)
   - Duration-based billing (per second of audio)
   - Provider-specific pricing
   - Location: `/opt/kasaai/apps/shared/integration/asr_services.py`

5. **TTS** (`TTSProviderService`)
   - Character-based billing
   - Provider-specific pricing
   - Location: `/opt/kasaai/apps/shared/integration/tts_services.py`

6. **VAPI** (Tracked in `vapi_call_logs`)
   - Call-based billing
   - Duration and status tracking

**Billing Pattern** (Example from Vonage):
```python
async def track_vapi_call_cost(
    self,
    vapi_call_id: str,
    phone_number: str,
    destination: str,
    duration: int,
    user_id: str,  # Required for wallet deduction
    assistant_id: Optional[str] = None,
    estimated_cost: Optional[Decimal] = None,
    auto_deduct: bool = True  # Enable automatic wallet deduction
) -> VonageCostRecord:
    """Track cost for a VAPI call with automatic wallet deduction."""

    # Create cost record
    cost_record = VonageCostRecord(...)

    # Automatically deduct from wallet if enabled
    if auto_deduct and self.wallet_service:
        await self._deduct_from_wallet(
            user_id=user_id,
            cost_record=cost_record,
            assistant_id=assistant_id
        )

    return cost_record

async def _deduct_from_wallet(
    self,
    user_id: str,
    cost_record: VonageCostRecord,
    assistant_id: Optional[str] = None
) -> None:
    """Deduct cost from user's wallet and create transaction record."""

    # Create rich metadata for analytics
    metadata = {
        "service": "vonage",
        "service_type": cost_record.service_type.value,
        "assistant_id": assistant_id,
        "vapi_call_id": cost_record.vapi_call_id,
        "phone_number": cost_record.phone_number,
        "destination": cost_record.destination,
        "duration_seconds": cost_record.duration,
        ...
    }

    # Deduct from wallet (creates transaction with metadata)
    wallet = await self.wallet_service.get_or_create_wallet(user_id, Currency.USD)
    await self.wallet_service.debit(
        wallet_id=wallet.id,
        amount=cost_record.cost_amount,
        description=f"Vonage voice call - {cost_record.duration}s",
        metadata=metadata,
        allow_negative=False  # Prevent overdrafts
    )
```

**Dual Authentication Support** (`/opt/kasaai/apps/core_backend/backend/auth.py`):

All analytics and wallet endpoints support two authentication methods:

1. **Bearer Token (JWT)** - Direct frontend calls
2. **X-User-Id Header** - Developer Platform API proxying

```python
async def get_user_from_header(
    authorization: str = Header(None),
    x_user_id: str = Header(None, alias="X-User-Id")
) -> dict:
    """Get user info from either Bearer token OR X-User-Id header.

    This supports two authentication patterns:
    1. Direct frontend calls: Bearer token with JWT authentication
    2. Developer Platform proxying: X-User-Id header with user context
    """
    if x_user_id:
        return {
            "user_id": x_user_id,
            "sub": x_user_id,
            "source": "developer_platform"
        }

    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        # ... JWT verification logic
        return user_data

    raise HTTPException(status_code=401, detail="Authentication required")
```

---

## Wallet Services API

### Overview

Credit-based usage tracking and billing with automatic deduction from all AI services.

**Base**: `/api/v1/wallet/*`

**Version**: v1.3.0 (Fully Implemented with Auto-Billing)

---

### Get Balance

**Endpoint**: `GET /api/v1/wallet/balance`

**Response**:
```json
{
  "success": true,
  "data": {
    "user_id": "user_abc123",
    "balance": 1250.50,
    "currency": "credits",
    "last_transaction_at": "2025-10-24T09:30:00Z"
  }
}
```

### List Transactions

**Endpoint**: `GET /api/v1/wallet/transactions`

**Query Parameters**:
- `start_date` (ISO 8601): Filter start
- `end_date` (ISO 8601): Filter end
- `transaction_type` (string): credit, debit, refund

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "transaction_id": "txn_abc123",
      "type": "debit",
      "amount": 5.0,
      "balance_after": 1245.50,
      "description": "TTS synthesis - Coqui XTTS",
      "metadata": {
        "provider_id": "coqui_xtts",
        "request_id": "req_xyz789"
      },
      "timestamp": "2025-10-24T09:30:00Z"
    }
  ],
  "pagination": {...}
}
```

### Add Credits

**Endpoint**: `POST /api/v1/wallet/credit`

**Request**:
```json
{
  "amount": 500.0,
  "payment_method": "stripe",
  "payment_id": "pi_abc123"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "transaction_id": "txn_new123",
    "new_balance": 1750.50
  }
}
```

---

## Code Examples

### Python (FastAPI Backend)

#### Using Shared AI Provider Service

```python
from fastapi import APIRouter, HTTPException, Depends
from apps.shared.integration.ai_services import (
    AIProviderService,
    ProviderRegistry,
    ProviderType,
    get_global_registry
)

router = APIRouter(prefix="/api/v1/tts")

# Initialize TTS service
tts_service = AIProviderService(provider_type=ProviderType.TTS)
registry = get_global_registry()

@router.get("/providers")
async def list_providers(force_refresh: bool = False):
    """List all TTS providers."""
    if force_refresh:
        await tts_service.refresh_providers(force=True)

    providers = tts_service.list_providers()

    return {
        "success": True,
        "data": {p.id: p.dict() for p in providers}
    }

@router.post("/synthesize")
async def synthesize_speech(
    provider_id: str,
    text: str,
    language: str = "en",
    current_user: dict = Depends(get_current_user)
):
    """Synthesize speech using specified provider."""
    # Get provider
    provider = registry.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    if provider.status != "online":
        raise HTTPException(
            status_code=502,
            detail="Provider is offline",
            headers={"error_code": "AI_4001"}
        )

    # Call provider API
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{provider.endpoint}/synthesize",
            json={"text": text, "language": language}
        ) as response:
            if response.status != 200:
                raise HTTPException(status_code=502, detail="Provider error")

            data = await response.json()

    # Deduct credits (assumed wallet service)
    await deduct_credits(current_user["id"], credits=5)

    return {
        "success": True,
        "data": data,
        "metadata": {
            "provider_id": provider_id,
            "credits_used": 5
        }
    }
```

### TypeScript (React Frontend)

#### Voice Lab Hooks

**Using Voice Transcription Hook**:

```typescript
// Using useVoiceTranscription hook
import { useVoiceTranscription } from '@/hooks/useVoiceTranscription';

function TranscriptionComponent() {
  const { transcribe, isTranscribing, result, error, clearResult } =
    useVoiceTranscription();

  const handleTranscribe = async (audioBlob: Blob) => {
    try {
      const transcriptionResult = await transcribe(audioBlob, {
        language: 'tw',
        dialect: 'asante',
        model: 'akan-whisper',
        enhanceText: true
      });

      console.log('Transcription:', transcriptionResult.text);
      console.log('Enhanced:', transcriptionResult.enhancedText);
      console.log('Confidence:', transcriptionResult.confidence);
    } catch (err) {
      console.error('Transcription failed:', err);
    }
  };

  return (
    <div>
      {isTranscribing && <p>Transcribing...</p>}
      {result && <p>Result: {result.text}</p>}
      {error && <p>Error: {error.message}</p>}
    </div>
  );
}
```

**Using Voice Synthesis Hook**:

```typescript
// Using useVoiceSynthesis hook
import { useVoiceSynthesis } from '@/hooks/useVoiceSynthesis';

function SynthesisComponent() {
  const { synthesize, play, stop, isSynthesizing, isPlaying, result } =
    useVoiceSynthesis();

  const handleSpeak = async () => {
    try {
      // Synthesize the text
      const synthesisResult = await synthesize('Akwaaba', {
        model: 'akan-mms',
        language: 'tw',
        speed: 1.0
      });

      // Play the audio
      await play(synthesisResult.audioBase64);
    } catch (err) {
      console.error('Synthesis failed:', err);
    }
  };

  return (
    <div>
      <button onClick={handleSpeak} disabled={isSynthesizing || isPlaying}>
        {isSynthesizing ? 'Synthesizing...' : isPlaying ? 'Playing...' : 'Speak'}
      </button>
      {isPlaying && <button onClick={stop}>Stop</button>}
    </div>
  );
}
```

**Using WebSocket Voice Chat Hook**:

```typescript
// Using useWebSocketChat hook
import { useWebSocketChat } from '@/hooks/useWebSocketChat';

function VoiceChatComponent({ assistantId }: { assistantId: string }) {
  const {
    isConnected,
    isRecording,
    connect,
    disconnect,
    sendTextMessage,
    startRecording,
    stopRecording,
    playAudio,
    updateConfig
  } = useWebSocketChat({
    assistantId,
    onTranscription: (text, isFinal) => {
      console.log('Transcription:', text, 'Final:', isFinal);
    },
    onTextResponse: (text) => {
      console.log('Assistant response:', text);
    },
    onAudioChunk: (audioData) => {
      // Audio chunk received for streaming playback
    },
    onAudioComplete: (metadata) => {
      console.log('Audio playback complete:', metadata);
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
    },
    onStatusChange: (status) => {
      console.log('Status:', status);
    }
  });

  return (
    <div>
      <p>Status: {isConnected ? 'Connected' : 'Disconnected'}</p>
      <button onClick={() => sendTextMessage('Hello')}>
        Send Text
      </button>
      <button
        onClick={isRecording ? stopRecording : startRecording}
      >
        {isRecording ? 'Stop Recording' : 'Start Recording'}
      </button>
    </div>
  );
}
```

**Using Audio Utilities**:

```typescript
// Using audio utilities
import {
  blobToBase64,
  base64ToBlob,
  playAudioBase64,
  downloadAudioBlob,
  getAudioDuration,
  formatDuration
} from '@/lib/audio-utils';

// Convert blob to base64
const base64 = await blobToBase64(audioBlob);

// Convert base64 back to blob
const blob = base64ToBlob(base64, 'audio/wav');

// Play audio from base64
await playAudioBase64(base64, {
  onEnded: () => console.log('Playback finished'),
  onError: (err) => console.error('Playback error:', err)
});

// Download audio
downloadAudioBlob(audioBlob, 'recording.wav');

// Get duration
const duration = await getAudioDuration(base64);
console.log('Duration:', formatDuration(duration)); // "2:34"
```

**Using Assistant API Client**:

```typescript
// Using Assistant API Client
import { assistantApiClient } from '@/services/assistant-api-client';

// Fetch all assistants
const assistants = await assistantApiClient.fetchAssistants({
  activeOnly: false
});

// Get a single assistant
const assistant = await assistantApiClient.getAssistant('asst_123');

// Create new assistant
const newAssistant = await assistantApiClient.createAssistant({
  name: 'My Assistant',
  system_prompt: 'You are a helpful assistant',
  language: 'en',
  transcribe_model: 'akan-whisper',
  llm_model: 'gemini-2.5-flash',
  tts_model: 'akan-mms'
});

// Update assistant
const updated = await assistantApiClient.updateAssistant('asst_123', {
  name: 'Updated Name'
});

// Delete assistant
await assistantApiClient.deleteAssistant('asst_123');

// Test assistant
const testResult = await assistantApiClient.testAssistant(
  'asst_123',
  'Hello, how are you?'
);
console.log('Response:', testResult.test_output);
```

#### Custom Hook for AI Provider

```typescript
// hooks/useAIProvider.ts
import { useState, useEffect, useCallback } from 'react';

interface AIProvider {
  id: string;
  name: string;
  status: 'online' | 'offline' | 'degraded';
  capabilities: Record<string, boolean>;
}

export function useAIProvider(providerType: 'tts' | 'llm' | 'asr') {
  const [providers, setProviders] = useState<Record<string, AIProvider>>({});
  const [selectedProvider, setSelectedProvider] = useState<AIProvider | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchProviders = useCallback(async (forceRefresh = false) => {
    setLoading(true);
    try {
      const response = await fetch(
        `https://api.ailabsafrica.com/api/v1/${providerType}/providers${
          forceRefresh ? '?force_refresh=true' : ''
        }`,
        {
          headers: {
            Authorization: `Bearer ${getToken()}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch providers');
      }

      const { data } = await response.json();
      setProviders(data);

      // Auto-select first online provider
      if (!selectedProvider) {
        const firstOnline = Object.values(data).find(
          (p: any) => p.status === 'online'
        );
        if (firstOnline) {
          setSelectedProvider(firstOnline as AIProvider);
        }
      }
    } catch (error) {
      console.error('Error fetching providers:', error);
    } finally {
      setLoading(false);
    }
  }, [providerType, selectedProvider]);

  useEffect(() => {
    fetchProviders();

    // Auto-refresh every 60 seconds
    const interval = setInterval(() => fetchProviders(false), 60000);
    return () => clearInterval(interval);
  }, [fetchProviders]);

  return {
    providers,
    selectedProvider,
    setSelectedProvider,
    loading,
    refetch: () => fetchProviders(true),
  };
}
```

#### Using the Hook

```typescript
// pages/TTSLab.tsx
import { useAIProvider } from '../hooks/useAIProvider';

export function TTSLab() {
  const { providers, selectedProvider, setSelectedProvider, loading } =
    useAIProvider('tts');

  const handleSynthesize = async () => {
    if (!selectedProvider) return;

    const response = await fetch('https://api.ailabsafrica.com/api/v1/tts/synthesize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getToken()}`,
      },
      body: JSON.stringify({
        provider_id: selectedProvider.id,
        text: 'Hello, world!',
        language: 'en',
      }),
    });

    const { data } = await response.json();
    // Handle audio playback
  };

  return (
    <div>
      <ProviderSidebar
        providers={providers}
        selectedId={selectedProvider?.id}
        onSelect={(id) => setSelectedProvider(providers[id])}
        loading={loading}
      />
      <button onClick={handleSynthesize}>Synthesize</button>
    </div>
  );
}
```

---

## Best Practices

### API Design

1. **Be consistent**: Follow naming and structure conventions
2. **Be explicit**: Clear parameter names and response structures
3. **Be defensive**: Validate all inputs, handle all errors
4. **Be documented**: Provide OpenAPI/Swagger documentation
5. **Be versioned**: Plan for future changes

### Performance

1. **Cache aggressively**: Provider status, static data
2. **Use async**: Non-blocking I/O for external calls
3. **Batch when possible**: Reduce round-trips
4. **Paginate lists**: Don't return massive datasets
5. **Stream large responses**: Use Server-Sent Events for real-time data

### Security

1. **Validate inputs**: Use Pydantic models
2. **Rate limit**: Prevent abuse
3. **Audit logs**: Track sensitive operations
4. **Encrypt in transit**: HTTPS only
5. **Minimize exposure**: Don't leak internal errors

---

## API Documentation Tools

### OpenAPI/Swagger

FastAPI auto-generates OpenAPI documentation:

```python
from fastapi import FastAPI

app = FastAPI(
    title="KasaAI Platform API",
    description="AI services for African languages",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)
```

**Access**:
- Swagger UI: `https://api.ailabsafrica.com/api/docs`
- ReDoc: `https://api.ailabsafrica.com/api/redoc`
- OpenAPI JSON: `https://api.ailabsafrica.com/api/openapi.json`

---

## Changelog

### Version 2.0 (2025-10-24)
- Added shared AI services API documentation
- Standardized error codes
- Added health monitoring endpoints
- Updated authentication patterns

### Version 1.0 (2024-01-15)
- Initial API documentation
- Core TTS/LLM/ASR endpoints
- Basic RAG and wallet services

---

**Questions or Suggestions?**

Keep this documentation updated as APIs evolve. When adding new endpoints or changing contracts, update this document immediately.
