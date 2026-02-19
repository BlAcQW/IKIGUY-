# Demo Deployment API

This document describes the demo deployment functionality for ailabsafrica.com.

## Overview

The demo deployment API allows authorized users to deploy HTML demo files to the ailabsafrica.com server. Files are saved to `/var/www/ailabsafrica/demos/` directory and can be accessed via the web server.

## API Configuration

### Environment Variable

Set the API deploy key in your environment:

```bash
export API_DEPLOY_KEY="sk_live_v1_Xl7dThM7cCfYl0XU6sP5o7k8yFVR6s2z9FQvh1tbTzA"
```

## Endpoint

### POST https://api.ailabsafrica.com/deploy-demo

Deploys an HTML demo file to the server.

#### Request Headers

- `Content-Type: application/json`
- `Authorization: Bearer {API_DEPLOY_KEY}`

#### Request Body

```json
{
  "fileName": "asst_abc123-1703123456789.html",
  "html": "<!DOCTYPE html><html>...</html>",
  "demoId": "asst_abc123-1703123456789",
  "assistantName": "Customer Support Bot",
  "assistantType": "customer_support"
}
```

#### Parameters

- `fileName` (string, required): The filename for the demo (e.g., "asst_abc123-1703123456789.html")
- `html` (string, required): The HTML content to deploy
- `demoId` (string, required): Unique identifier for the demo
- `assistantName` (string, required): Name of the assistant
- `assistantType` (string, required): Type of assistant (e.g., "customer_support", "sales", "technical")

#### Response

**Success (200 OK):**
```json
{
  "success": true,
  "demoUrl": "https://ailabsafrica.com/demos/asst_abc123-1703123456789.html",
  "filePath": "/var/www/ailabsafrica/demos/asst_abc123-1703123456789.html"
}
```

**Error Response (200 OK with error):**
```json
{
  "success": false,
  "error": "Failed to create file: Permission denied"
}
```

**Authentication Error (401 Unauthorized):**
```json
{
  "detail": "Invalid API deploy key"
}
```

#### Security Features

1. **API Key Authentication**: Endpoint requires valid API deploy key via Bearer token
2. **Filename Validation**: Prevents directory traversal attacks by rejecting filenames containing ".." or "/"
3. **Error Handling**: Comprehensive error handling with appropriate HTTP status codes

#### File System

- **Target Directory**: `/var/www/ailabsafrica/demos/`
- **Directory Creation**: Automatically creates the target directory if it doesn't exist
- **File Encoding**: UTF-8 encoding for proper character handling
- **File Permissions**: Inherits system default permissions

#### Usage Examples

**cURL Example:**
```bash
curl -X POST "https://api.ailabsafrica.com/deploy-demo" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk_live_v1_Xl7dThM7cCfYl0XU6sP5o7k8yFVR6s2z9FQvh1tbTzA" \
  -d '{
    "fileName": "asst_abc123-1703123456789.html",
    "html": "<!DOCTYPE html><html><body><h1>My Demo</h1><p>This is a test demo.</p></body></html>",
    "demoId": "asst_abc123-1703123456789",
    "assistantName": "Customer Support Bot",
    "assistantType": "customer_support"
  }'
```

**JavaScript Example:**
```javascript
const response = await fetch('https://api.ailabsafrica.com/deploy-demo', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer sk_live_v1_Xl7dThM7cCfYl0XU6sP5o7k8yFVR6s2z9FQvh1tbTzA'
  },
  body: JSON.stringify({
    fileName: 'asst_abc123-1703123456789.html',
    html: '<!DOCTYPE html><html><body><h1>My Demo</h1></body></html>',
    demoId: 'asst_abc123-1703123456789',
    assistantName: 'Customer Support Bot',
    assistantType: 'customer_support'
  })
});

const result = await response.json();
if (result.success) {
  console.log('Demo deployed successfully:', result.demoUrl);
} else {
  console.error('Deployment failed:', result.error);
}
```

#### Testing

Run the test suite to verify the endpoint functionality:

```bash
cd apps/core_backend
pytest tests/test_demo_deploy.py -v
```

#### Future Enhancements

- File size limits
- Content validation (HTML structure)
- Version control integration
- Rollback functionality
- Preview generation
- Access control per demo
- Analytics tracking
- Rate limiting
- Demo metadata storage
