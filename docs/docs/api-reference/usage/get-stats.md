---
title: Get Usage Statistics
description: Retrieve detailed usage analytics for your API key
---

# Get Usage Statistics

Retrieve detailed usage analytics for your API key

<div class="api-endpoint">
  <div class="api-endpoint__header">
    <span class="method-badge method-get">GET</span>
    <span class="api-endpoint__path">/api/v1/usage/stats</span>
  </div>
</div>

## Authentication

This endpoint requires API key authentication via the `X-API-Key` header.

## Parameters

| Parameter | Type | Location | Required | Description |
|-----------|------|----------|----------|-------------|
| `days` | integer | query | No | Number of days to include (1-90) (default: `30`) |

## Response

### Success Response (200 OK)

```json
{
  "total_requests": 150,
  "total_cost": 125.5,
  "avg_response_time_ms": 245.3,
  "requests_by_endpoint": {
    "/api/v1/assistants": 50,
    "/api/v1/calls": 100
  },
  "requests_by_status": {
    "200": 145,
    "201": 5
  },
  "daily_usage": [
    {
      "date": "2025-10-20",
      "requests": 30,
      "cost": 25.0
    },
    {
      "date": "2025-10-21",
      "requests": 45,
      "cost": 37.5
    }
  ]
}
```

## Example Request

### cURL

```bash
curl -X GET https://developer.ailabsafrica.com/api/v1/usage/stats \
  -H "X-API-Key: your_api_key_here" \
  "?days=30"
```

### Python

```python
import requests

url = "https://developer.ailabsafrica.com/api/v1/usage/stats"
headers = {"X-API-Key": "your_api_key_here"}

response = requests.get(url, headers=headers)
data = response.json()
print(data)
```

### JavaScript

```javascript
const response = await fetch("https://developer.ailabsafrica.com/api/v1/usage/stats", {
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

- [Get Quota Status](./get-quota)
- [Get Rate Limit Status](./get-rate-limit)
- [Get Usage Summary](./get-summary)
