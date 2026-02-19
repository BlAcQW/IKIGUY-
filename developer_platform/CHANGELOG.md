# API Changelog

All notable changes to the KasaAI Developer Platform API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- v2 API with GraphQL support
- Real-time WebSocket connections for call monitoring
- Advanced analytics endpoints
- Batch operations support

---

## [1.0.0] - 2025-10-24

### 🎉 Initial Release

The first stable release of the KasaAI Developer Platform API v1.

### Added

#### Authentication & Authorization
- **API Key Authentication** - Secure API access with `X-API-Key` header
- **Multiple API Keys** - Create and manage multiple keys per account
- **Key Scopes** - Limit keys to specific endpoints and operations
- **Key Expiration** - Set expiration dates for enhanced security

#### Voice Assistant Endpoints
- `POST /api/v1/assistants` - Create AI voice assistants
  - Support for multiple AI models (GPT-4o, GPT-4o-mini)
  - Customizable voice selection (alloy, echo, fable, onyx, nova, shimmer)
  - Multi-language support
  - Custom system prompts and personalities
  - Configurable first/end call messages
- `GET /api/v1/assistants` - List all assistants with pagination
  - Query parameters: `limit`, `offset`
  - Returns total count and assistant metadata
- `GET /api/v1/assistants/{id}` - Get specific assistant details
- `PATCH /api/v1/assistants/{id}` - Update assistant configuration (Coming Soon)
- `DELETE /api/v1/assistants/{id}` - Delete assistant (Coming Soon)

#### Call Management Endpoints
- `POST /api/v1/calls` - Initiate outbound calls
  - Supports E.164 phone number format
  - Custom task/purpose per call
  - Real-time call initiation
- `GET /api/v1/calls` - List all calls with pagination
  - Filter by status, date range
  - Includes duration, timestamps, status
- `GET /api/v1/calls/{id}` - Get call details and status
  - Real-time status updates
  - Transcript URLs when available
  - Call duration and metadata

#### Workflow Automation Endpoints
- `POST /api/v1/workflows` - Create n8n workflows
  - Webhook triggers
  - HTTP request nodes
  - Email notification nodes
  - Database integration nodes
  - Custom JavaScript execution
- `GET /api/v1/workflows` - List workflows (Coming Soon)
- `GET /api/v1/workflows/{id}` - Get workflow details
- `PATCH /api/v1/workflows/{id}` - Update workflow (Coming Soon)
- `DELETE /api/v1/workflows/{id}` - Delete workflow (Coming Soon)
- `POST /api/v1/workflows/{id}/activate` - Activate workflow

#### Workflow Execution Endpoints
- `POST /api/v1/executions` - Execute workflow with data
  - Pass custom data payload
  - Async execution
- `GET /api/v1/executions` - List executions (Coming Soon)
- `GET /api/v1/executions/{id}` - Get execution status and results (Coming Soon)

#### Usage & Billing Endpoints
- `GET /api/v1/usage/quota` - Check quota and remaining credits
  - Real-time quota tracking
  - Usage breakdown by resource type
- `GET /api/v1/usage/rate-limit` - Check rate limit status
  - Per-endpoint limits
  - Reset timestamps
- `GET /api/v1/usage/stats` - Get usage statistics
  - Endpoint call counts
  - Success/error rates
  - Average response times
- `GET /api/v1/usage/summary` - Get usage summary
  - Credits consumed
  - Total requests
  - Cost analysis

#### Rate Limiting
- **Free Tier**: 10 requests/minute, 100/hour, 1,000/day
- **Starter Tier**: 60 requests/minute, 1,000/hour, 10,000/day
- **Professional Tier**: 300 requests/minute, 10,000/hour, 100,000/day
- **Enterprise Tier**: 1,000 requests/minute, 50,000/hour, 1,000,000/day
- Token bucket algorithm with Redis persistence
- Per-API-key tracking
- Graceful degradation
- `Retry-After` header on 429 responses
- Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

#### Usage Tracking
- Real-time tracking of all API calls
- Credit consumption per endpoint
- MongoDB persistence
- Aggregated metrics
- Billing-ready data export
- Historical usage data (30 days retention)

#### Documentation
- **Interactive API Documentation** - Swagger UI at `/docs`
- **API Reference** - ReDoc at `/redoc`
- **OpenAPI Specification** - Available at `/openapi.json`
- **Code Examples** - Python, JavaScript, cURL
  - Complete working examples
  - Error handling patterns
  - Best practices
- **Quickstart Guides**
  - "Create Your First Assistant in 5 Minutes"
  - "Trigger n8n Workflows via API"
  - "Handle Webhooks"
- **README Documentation** - Setup and usage guides

#### Error Handling
- Standardized error responses with HTTP status codes
- Detailed error messages with field-level validation
- Error codes for programmatic handling
- Request ID for debugging and support

### Response Formats

All endpoints return JSON with consistent structure:

```json
{
  "data": { /* response data */ },
  "error": null,
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2025-10-24T10:00:00Z"
  }
}
```

Error responses:

```json
{
  "detail": {
    "error": "Error type",
    "message": "Human-readable message",
    "field": "field_name",  // for validation errors
    "code": "ERROR_CODE"
  }
}
```

### HTTP Status Codes

- `200 OK` - Successful GET/PATCH request
- `201 Created` - Successful POST request
- `204 No Content` - Successful DELETE request
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Invalid/missing API key
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
- `501 Not Implemented` - Endpoint not yet implemented
- `503 Service Unavailable` - Service temporarily down

### Security

- **HTTPS Only** - All API endpoints require HTTPS
- **API Key Authentication** - Secure key-based auth
- **Webhook Signature Verification** - HMAC-SHA256 signatures
- **Rate Limiting** - Protection against abuse
- **Input Validation** - Pydantic models with strict validation
- **CORS Support** - Configurable origins
- **Request Size Limits** - 10MB maximum payload

### Performance

- **Average Response Time**: < 200ms (95th percentile)
- **Availability**: 99.9% uptime SLA
- **Rate Limit**: Based on plan tier
- **Pagination**: Default 10 items, max 100 per request
- **Caching**: Redis caching for frequently accessed data

---

## API Stability Promise

**v1 API Stability Guarantee:**

The v1 API will **NOT** introduce breaking changes. All changes will be:
- ✅ **Backward compatible** - Existing code continues to work
- ✅ **Additive only** - New fields/endpoints may be added
- ✅ **Properly versioned** - Major changes get new API version

### What is a Breaking Change?

Breaking changes include:
- ❌ Removing endpoints
- ❌ Removing request/response fields
- ❌ Changing field types
- ❌ Changing authentication methods
- ❌ Changing error response formats

### What is NOT a Breaking Change?

Non-breaking changes include:
- ✅ Adding new endpoints
- ✅ Adding new optional fields
- ✅ Adding new error codes
- ✅ Improving error messages
- ✅ Performance improvements
- ✅ Bug fixes

### Deprecation Policy

When we need to introduce breaking changes:

1. **Announcement** - 6 months notice via:
   - Email to all API key holders
   - Changelog updates
   - Developer portal banner
   - API response headers

2. **Deprecation Period** - Minimum 6 months:
   - Old API continues to work
   - `Deprecation` header on responses
   - Documentation clearly marked

3. **Migration Guide** - Comprehensive guide with:
   - What's changing
   - Why it's changing
   - How to migrate
   - Code examples
   - Timeline

4. **v2 API Launch** - New version with:
   - All new features
   - Breaking changes
   - Parallel operation with v1

5. **v1 Sunset** - After 6 months:
   - Final reminder (30 days notice)
   - v1 API deprecated
   - Redirect to v2 documentation

---

## Version History

### Timeline

- **2025-10-23** - Development started
- **2025-10-24** - v1.0.0 released (Phase 3 complete)
- **2025-10-24** - Documentation complete (Phase 4)

### Planned Releases

- **v1.1.0** (Q4 2025)
  - WebSocket support for real-time call monitoring
  - Batch operations (create multiple assistants at once)
  - Advanced filtering and search
  - Call recording download endpoints

- **v1.2.0** (Q1 2026)
  - Advanced analytics endpoints
  - Custom model fine-tuning support
  - Multi-tenant management
  - Team collaboration features

- **v2.0.0** (Q2 2026)
  - GraphQL API
  - Real-time subscriptions
  - Enhanced webhook management
  - Advanced security features

---

## Migration Guides

### From Beta to v1.0.0

If you used the beta API, here's what changed:

#### Authentication
- **Before**: `Authorization: Bearer <token>`
- **After**: `X-API-Key: <api_key>`

#### Assistant Creation
- **Before**: `POST /assistants/create`
- **After**: `POST /api/v1/assistants`

#### Response Format
- **Before**: Inconsistent formats
- **After**: Standardized JSON with `data`, `error`, `meta`

#### Error Handling
- **Before**: Plain text error messages
- **After**: Structured JSON errors with codes

**Migration Steps:**

1. Update API key authentication
2. Update endpoint URLs (add `/api/v1/` prefix)
3. Update response parsing for new format
4. Update error handling for structured errors
5. Test thoroughly in sandbox environment

---

## Breaking Changes

This section will document any breaking changes in future releases.

### None Yet

v1.0.0 is the first stable release. No breaking changes yet!

---

## Support

### Getting Help

- **Documentation**: https://developer.ailabsafrica.com/docs
- **API Reference**: https://developer.ailabsafrica.com/api/v1/docs
- **Status Page**: https://status.ailabsafrica.com
- **Email**: support@ailabsafrica.com
- **GitHub Issues**: https://github.com/ailabsafrica/kasaai-issues

### Reporting Issues

When reporting issues, please include:

1. **API Version** - The version you're using
2. **Endpoint** - The specific endpoint
3. **Request ID** - From response headers
4. **Timestamp** - When the issue occurred
5. **Expected Behavior** - What should happen
6. **Actual Behavior** - What actually happened
7. **Code Sample** - Minimal reproducible example

### Stay Updated

Subscribe to changelog updates:

1. **Email Notifications**
   - Go to dashboard settings
   - Enable "Changelog Notifications"

2. **RSS Feed**
   - Subscribe to: https://developer.ailabsafrica.com/changelog.xml

3. **Webhook Notifications**
   - Set up webhook for `api.version.updated` events

---

## License

The KasaAI Developer Platform API is proprietary software.

Use of this API is governed by:
- [Terms of Service](https://ailabsafrica.com/terms)
- [Privacy Policy](https://ailabsafrica.com/privacy)
- [API Terms](https://developer.ailabsafrica.com/terms)

---

**Last Updated**: 2025-10-24
**Next Review**: Monthly (first Monday of each month)
