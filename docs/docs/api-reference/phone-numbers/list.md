# List Phone Numbers

Retrieve all provisioned phone numbers for your organization.

## Endpoint

```
GET /api/phone-numbers
```

## Request

### Headers

| Header | Value | Required |
|--------|-------|----------|
| `X-API-Key` | Your API key | Yes |

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Items per page (default: 20, max: 100) |
| `offset` | integer | No | Starting position (default: 0) |
| `provider` | string | No | Filter by provider (`kasaai`, `twilio`, `vonage`) |
| `status` | string | No | Filter by status (`active`, `pending`, `suspended`) |

### Example Request

```bash
GET /api/phone-numbers?limit=20&provider=kasaai&status=active
```

## Response

### Success Response

**Status Code:** `200 OK`

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

## Code Examples

### Python

```python
import httpx

async def list_phone_numbers(api_key: str, limit: int = 20, provider: str = None):
    """List all phone numbers"""
    params = {"limit": limit}
    if provider:
        params["provider"] = provider

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.ailabsafrica.com/api/phone-numbers",
            headers={"X-API-Key": api_key},
            params=params
        )
        response.raise_for_status()
        return response.json()

# Usage
result = await list_phone_numbers(
    "kasa_live_1234567890abcdef",
    limit=50,
    provider="kasaai"
)
print(f"Total numbers: {result['total']}")
for number in result['phone_numbers']:
    print(f"  {number['number']} - {number['provider']}")
```

### JavaScript

```javascript
async function listPhoneNumbers(apiKey, options = {}) {
  const { limit = 20, provider, status } = options;

  const params = new URLSearchParams({ limit: limit.toString() });
  if (provider) params.append('provider', provider);
  if (status) params.append('status', status);

  const response = await fetch(
    `https://api.ailabsafrica.com/api/phone-numbers?${params}`,
    {
      method: 'GET',
      headers: {
        'X-API-Key': apiKey
      }
    }
  );

  return await response.json();
}

// Usage
const result = await listPhoneNumbers(
  'kasa_live_1234567890abcdef',
  { limit: 50, provider: 'kasaai', status: 'active' }
);
console.log(`Total numbers: ${result.total}`);
```

### cURL

```bash
curl -X GET "https://api.ailabsafrica.com/api/phone-numbers?limit=20&provider=kasaai" \
  -H "X-API-Key: kasa_live_1234567890abcdef"
```

## Pagination

Use `limit` and `offset` parameters for pagination:

```javascript
// Get first page (0-19)
GET /api/phone-numbers?limit=20&offset=0

// Get second page (20-39)
GET /api/phone-numbers?limit=20&offset=20

// Get third page (40-59)
GET /api/phone-numbers?limit=20&offset=40
```

## Related Endpoints

- [Get Phone Number](/api-reference/phone-numbers/get) - Get specific number details
- [Provision Phone Number](/api-reference/phone-numbers/provision) - Create new number
- [Delete Phone Number](/api-reference/phone-numbers/delete) - Remove number
