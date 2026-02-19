---
title: Get Quota Status
description: Retrieve current quota and usage limits for your API key
---

# Get Quota Status

Retrieve current quota and usage limits for your API key

<div class="api-endpoint">
  <div class="api-endpoint__header">
    <span class="method-badge method-get">GET</span>
    <span class="api-endpoint__path">/api/v1/usage/quota</span>
  </div>
</div>

## Authentication

This endpoint requires API key authentication via the `X-API-Key` header.

## Response

### Success Response (200 OK)

```json
{
  "plan": "free",
  "daily": {
    "limit": 100,
    "used": 45,
    "remaining": 55,
    "reset_at": "2025-10-24T00:00:00Z"
  },
  "monthly": {
    "limit": 1000,
    "used": 456,
    "remaining": 544,
    "reset_at": "2025-11-01T00:00:00Z"
  }
}
```

## Example Request

### cURL

```bash
curl -X GET https://developer.ailabsafrica.com/api/v1/usage/quota \
  -H "X-API-Key: your_api_key_here"
```

### Python

```python
import requests

url = "https://developer.ailabsafrica.com/api/v1/usage/quota"
headers = {"X-API-Key": "your_api_key_here"}

response = requests.get(url, headers=headers)
data = response.json()
print(data)
```

### JavaScript

```javascript
const response = await fetch("https://developer.ailabsafrica.com/api/v1/usage/quota", {
  method: "GET",
  headers: {
    "X-API-Key": "your_api_key_here"
  }
});

const data = await response.json();
console.log(data);
```

## Error Responses

### 401 Unauthorized

Invalid or missing API key.

```json
{
  "error": {
    "code": "AUTHENTICATION_ERROR",
    "message": "Invalid API key"
  }
}
```

### 429 Too Many Requests

Rate limit exceeded.

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again later.",
    "retry_after": 30
  }
}
```

## Related Endpoints

- [Get Rate Limit Status](./get-rate-limit)
- [Get Usage Statistics](./get-stats)
- [Get Usage Summary](./get-summary)
