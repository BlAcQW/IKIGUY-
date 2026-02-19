---
title: Get Usage Summary
description: Get comprehensive usage summary including quota, rate limits, and stats
---

# Get Usage Summary

Get comprehensive usage summary including quota, rate limits, and stats

<div class="api-endpoint">
  <div class="api-endpoint__header">
    <span class="method-badge method-get">GET</span>
    <span class="api-endpoint__path">/api/v1/usage/summary</span>
  </div>
</div>

## Authentication

This endpoint requires API key authentication via the `X-API-Key` header.

## Response

### Success Response (200 OK)

```json
{
  "quota": {
    "plan": "free",
    "daily": {},
    "monthly": {}
  },
  "rate_limit": {
    "tokens_remaining": 8,
    "tokens_capacity": 20
  },
  "stats": {
    "total_requests": 150,
    "total_cost": 125.5
  }
}
```

## Example Request

### cURL

```bash
curl -X GET https://developer.ailabsafrica.com/api/v1/usage/summary \
  -H "X-API-Key: your_api_key_here"
```

### Python

```python
import requests

url = "https://developer.ailabsafrica.com/api/v1/usage/summary"
headers = {"X-API-Key": "your_api_key_here"}

response = requests.get(url, headers=headers)
data = response.json()
print(data)
```

### JavaScript

```javascript
const response = await fetch("https://developer.ailabsafrica.com/api/v1/usage/summary", {
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
- [Get Usage Statistics](./get-stats)
