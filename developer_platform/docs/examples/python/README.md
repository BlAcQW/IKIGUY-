# Python Examples for KasaAI Developer Platform

Complete Python examples demonstrating how to use the KasaAI API.

## Prerequisites

- Python 3.8 or higher
- `requests` library: `pip install requests`
- KasaAI API key (get one at [developer.ailabsafrica.com](https://developer.ailabsafrica.com))

## Setup

### 1. Install Dependencies

```bash
pip install requests
```

### 2. Set Your API Key

Set your API key as an environment variable:

```bash
export KASAAI_API_KEY="your_api_key_here"
```

Or add it to your `.bashrc` or `.zshrc` for persistence.

## Examples

### 1. Create Assistant (`create_assistant.py`)

Create a new AI voice assistant with custom personality and voice.

```bash
python create_assistant.py
```

**Features:**
- Configure assistant name and personality
- Choose voice and language
- Set custom greeting message

### 2. List Assistants (`list_assistants.py`)

List all your voice assistants and get details about a specific one.

```bash
python list_assistants.py
```

**Features:**
- List all assistants with pagination
- Get detailed info about a specific assistant

### 3. Initiate Call (`initiate_call.py`)

Make an outbound call using your voice assistant.

```bash
export ASSISTANT_ID="asst_abc123xyz"
export PHONE_NUMBER="+1234567890"
python initiate_call.py
```

**Features:**
- Initiate outbound calls
- Monitor call status in real-time
- Handle common errors

### 4. Create Workflow (`create_workflow.py`)

Create n8n workflows for automation.

```bash
python create_workflow.py
```

**Features:**
- Create simple webhook workflows
- Create call notification workflows
- Configure Slack integrations

### 5. Execute Workflow (`execute_workflow.py`)

Execute workflows and monitor their progress.

```bash
export WORKFLOW_ID="wf_xyz789abc"
python execute_workflow.py
```

**Features:**
- Execute workflows with custom data
- Monitor execution status
- List execution history

### 6. Check Usage (`check_usage.py`)

Check your API usage, quota, and billing information.

```bash
python check_usage.py
```

**Features:**
- View rate limits and current usage
- Get detailed usage statistics
- Check billing and credit information
- Receive warnings for approaching limits

## Error Handling

All examples include comprehensive error handling:

- **400 Bad Request**: Invalid parameters or malformed request
- **401 Unauthorized**: Invalid or missing API key
- **402 Payment Required**: Insufficient credits
- **404 Not Found**: Resource doesn't exist
- **429 Too Many Requests**: Rate limit exceeded

## Best Practices

1. **Store API keys securely**: Never hardcode API keys in your code
2. **Use environment variables**: Store sensitive data in environment variables
3. **Handle errors gracefully**: Always catch and handle HTTP errors
4. **Monitor usage**: Regularly check your quota and credits
5. **Use type hints**: All examples use Python type hints for clarity

## Additional Resources

- [Full API Documentation](../../API_DOCUMENTATION.md)
- [Quickstart Guide](../../quickstart/first_assistant.md)
- [JavaScript Examples](../javascript/)
- [cURL Examples](../curl/)

## Support

Need help? Contact us at:
- 📚 [Documentation](https://developer.ailabsafrica.com/docs)
- 💬 [Discord Community](https://discord.gg/kasaai)
- 📧 [Email Support](mailto:support@ailabsafrica.com)
