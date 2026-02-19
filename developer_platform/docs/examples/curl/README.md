# cURL Examples for KasaAI Developer Platform

Complete cURL/shell script examples demonstrating how to use the KasaAI API.

## Prerequisites

- `curl` command-line tool (pre-installed on most Unix systems)
- `jq` for JSON formatting: `sudo apt install jq` (Ubuntu/Debian) or `brew install jq` (macOS)
- KasaAI API key (get one at [developer.ailabsafrica.com](https://developer.ailabsafrica.com))

## Setup

1. **Set your API key as an environment variable:**

```bash
export KASAAI_API_KEY=your_api_key_here
```

Add this to your `~/.bashrc` or `~/.zshrc` to make it permanent.

2. **Make scripts executable:**

```bash
chmod +x *.sh
```

## Available Examples

### 1. Create an Assistant

Create a new voice assistant with custom configuration.

```bash
./create_assistant.sh
```

**What it does:**
- Creates a customer service assistant
- Creates a sales assistant with custom settings
- Displays the created assistant details

### 2. List Assistants

Retrieve a list of all your voice assistants.

```bash
./list_assistants.sh
```

**What it does:**
- Lists all assistants
- Gets details for the first assistant
- Demonstrates pagination

### 3. Initiate a Call

Start an outbound call using your assistant.

```bash
./initiate_call.sh <assistant_id> <phone_number>
```

**Example:**
```bash
./initiate_call.sh asst_123abc +1234567890
```

**What it does:**
- Initiates an outbound call
- Monitors call status in real-time
- Displays call details when completed

## Using cURL Directly

If you prefer to use cURL directly without scripts:

### Create an Assistant

```bash
curl -X POST "https://developer.ailabsafrica.com/api/v1/assistants" \
  -H "X-API-Key: $KASAAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Assistant",
    "system_prompt": "You are a helpful assistant.",
    "voice": "alloy",
    "language": "en",
    "model": "gpt-4o-mini",
    "provider": "openai"
  }' | jq '.'
```

### List Assistants

```bash
curl -X GET "https://developer.ailabsafrica.com/api/v1/assistants" \
  -H "X-API-Key: $KASAAI_API_KEY" | jq '.'
```

### Get Specific Assistant

```bash
curl -X GET "https://developer.ailabsafrica.com/api/v1/assistants/<assistant_id>" \
  -H "X-API-Key: $KASAAI_API_KEY" | jq '.'
```

### Initiate a Call

```bash
curl -X POST "https://developer.ailabsafrica.com/api/v1/calls" \
  -H "X-API-Key: $KASAAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "asst_123abc",
    "phone_number": "+1234567890",
    "task": "Make a friendly call"
  }' | jq '.'
```

### Check Call Status

```bash
curl -X GET "https://developer.ailabsafrica.com/api/v1/calls/<call_id>" \
  -H "X-API-Key: $KASAAI_API_KEY" | jq '.'
```

## Response Handling

All examples use `jq` to format JSON responses. If you don't have `jq`, remove `| jq '.'` from the commands.

### Success Responses

- **201 Created** - Resource created successfully
- **200 OK** - Request successful

### Error Responses

- **400 Bad Request** - Invalid input
- **401 Unauthorized** - Invalid API key
- **404 Not Found** - Resource not found
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server error

## Checking Your Rate Limits

```bash
curl -X GET "https://developer.ailabsafrica.com/api/v1/usage/rate-limit" \
  -H "X-API-Key: $KASAAI_API_KEY" | jq '.'
```

## Checking Your Usage

```bash
curl -X GET "https://developer.ailabsafrica.com/api/v1/usage/summary" \
  -H "X-API-Key: $KASAAI_API_KEY" | jq '.'
```

## Tips

1. **Save responses to files:**
   ```bash
   curl ... > response.json
   ```

2. **Pretty print JSON without jq:**
   ```bash
   curl ... | python -m json.tool
   ```

3. **Include response headers:**
   ```bash
   curl -i ...
   ```

4. **Verbose output for debugging:**
   ```bash
   curl -v ...
   ```

5. **Silence curl progress:**
   ```bash
   curl -s ...
   ```

## Troubleshooting

### "curl: command not found"
Install curl:
- Ubuntu/Debian: `sudo apt install curl`
- macOS: `brew install curl`
- Windows: Download from https://curl.se/windows/

### "jq: command not found"
Install jq:
- Ubuntu/Debian: `sudo apt install jq`
- macOS: `brew install jq`
- Windows: Download from https://stedolan.github.io/jq/download/

### "Permission denied" when running scripts
Make scripts executable:
```bash
chmod +x *.sh
```

### "API key not set" error
Set your API key:
```bash
export KASAAI_API_KEY=your_api_key_here
```

## Next Steps

- Check out the [Python examples](../python/) for more complex integrations
- Read the [API documentation](https://developer.ailabsafrica.com/docs)
- Explore the [quickstart guide](../../quickstart/)

## Support

- Documentation: https://developer.ailabsafrica.com/docs
- API Reference: https://developer.ailabsafrica.com/api/v1/docs
- Email: support@ailabsafrica.com
