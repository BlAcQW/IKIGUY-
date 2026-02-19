# Provision Phone Number

Create a new virtual phone number with automatic SIP registration and Asterisk integration.

## Endpoint

```
POST /api/phone-numbers/provision
```

## Request

### Headers

| Header | Value | Required |
|--------|-------|----------|
| `Content-Type` | `application/json` | Yes |
| `X-API-Key` | Your API key | Yes |

### Body Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | string | Yes | Provider: `kasaai`, `twilio`, `vonage` |
| `country_code` | string | Yes | E.164 country code (e.g., `+1`, `+233`, `+44`) |
| `area_code` | string | No | Area code for number selection |
| `plan` | string | Yes | Pricing plan: `basic`, `professional`, `enterprise` |
| `assistant_id` | string | No | Voice assistant ID for automatic linking |

### Example Request

```json
{
  "provider": "kasaai",
  "country_code": "+1",
  "area_code": "555",
  "plan": "professional",
  "assistant_id": "asst_123abc"
}
```

## Response

### Success Response

**Status Code:** `201 Created`

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

### Status Values

| Status | Description |
|--------|-------------|
| `active` | Number provisioned and ready |
| `pending` | Provisioning in progress |
| `suspended` | Number temporarily disabled |
| `error` | Provisioning failed |

### Error Responses

**400 Bad Request - Invalid Number Format**
```json
{
  "error": {
    "code": "INVALID_NUMBER_FORMAT",
    "message": "Phone number must be in E.164 format",
    "field": "country_code"
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

## Code Examples

### Python

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
```

### JavaScript

```javascript
async function provisionPhoneNumber(apiKey, assistantId) {
  const response = await fetch(
    'https://api.ailabsafrica.com/api/phone-numbers/provision',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey
      },
      body: JSON.stringify({
        provider: 'kasaai',
        country_code: '+1',
        area_code: '555',
        plan: 'professional',
        assistant_id: assistantId
      })
    }
  );

  return await response.json();
}

// Usage
const result = await provisionPhoneNumber(
  'kasa_live_1234567890abcdef',
  'asst_123abc'
);
console.log(`Provisioned: ${result.number}`);
```

### cURL

```bash
curl -X POST "https://api.ailabsafrica.com/api/phone-numbers/provision" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: kasa_live_1234567890abcdef" \
  -d '{
    "provider": "kasaai",
    "country_code": "+1",
    "area_code": "555",
    "plan": "professional",
    "assistant_id": "asst_123abc"
  }'
```

## Pricing

| Plan | Monthly Cost | Included Minutes | Per-Minute Rate |
|------|-------------|------------------|-----------------|
| **Basic** | $2/mo | 100 min | $0.05/min |
| **Professional** | $5/mo | 500 min | $0.03/min |
| **Enterprise** | Custom | Custom | $0.02/min |

## Related Endpoints

- [Import Phone Number](/api-reference/phone-numbers/import) - Import existing number
- [List Phone Numbers](/api-reference/phone-numbers/list) - Get all numbers
- [Delete Phone Number](/api-reference/phone-numbers/delete) - Remove number
