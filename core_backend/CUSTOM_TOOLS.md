# Custom Tools Management System

## Overview

The Custom Tools Management System allows for dynamic registration, execution, and management of custom tool functions that can be integrated with VAPI (Voice AI Platform) for voice agent automation workflows. This system has been fully implemented and tested with comprehensive VAPI integration, analytics tracking, and robust error handling.

## Key Features

- ✅ **Tool Registration**: From Python files or direct database specification
- ✅ **VAPI Integration**: Automatic synchronization with VAPI platform
- ✅ **Tool Execution**: Runtime execution with analytics tracking
- ✅ **Search & Filtering**: Advanced tool discovery capabilities
- ✅ **Analytics & Monitoring**: Comprehensive execution metrics
- ✅ **Bulk Operations**: Efficient mass tool management
- ✅ **Async Operations**: Full MongoDB Motor integration for async operations

## Architecture

### Backend Components

#### Service Layer
- **Location**: `/opt/kasaai/apps/core_backend/backend/services/custom_tools_service.py`
- **Purpose**: Core business logic for tool management
- **Database**: MongoDB collections (`custom_tools`, `tool_clients`)

#### API Layer
- **Location**: `/opt/kasaai/apps/core_backend/backend/routes/custom_tools.py`
- **Purpose**: REST API endpoints for tool operations
- **Authentication**: Bearer token required

#### Database Schema
```javascript
{
  "_id": ObjectId,
  "name": String,                    // Tool name (unique per client)
  "client_id": String,              // Client identifier
  "industry": String,               // Industry category
  "category": String,               // Tool category
  "description": String,            // Tool description
  "schema": Object,                 // JSON schema for VAPI/N8N
  "endpoint": String,               // API endpoint URL
  "method": String,                 // HTTP method
  "source": String,                 // Registration source
  "code": String,                   // Optional Python code
  "function_name": String,          // Function reference
  "file_path": String,              // File path (for file-based tools)
  "version": String,                // Tool version
  "tags": [String],                 // Search tags
  "dependencies": [String],         // Required dependencies
  "active": Boolean,                // Tool status
  "created_at": DateTime,           // Creation timestamp
  "updated_at": DateTime,           // Last update
  "metadata": Object,               // Additional metadata

  // VAPI Integration Fields (NEW)
  "vapi_tool_id": String,           // VAPI-generated tool ID
  "server_url": String,             // Server URL for VAPI
  "vapi_sync_status": String,       // "synced|pending|error"
  "deployment_status": String,      // "active|inactive"
  "vapi_metadata": {
    "assistant_ids": [String],      // Associated VAPI assistants
    "last_synced": DateTime,        // Last sync timestamp
    "sync_errors": [String]         // Sync error history
  },

  // Analytics Fields (ENHANCED)
  "analytics": {
    "execution_count": Number,      // Total executions
    "last_executed": DateTime,      // Last execution time
    "average_response_time": Number, // Avg response time (seconds)
    "error_count": Number           // Total errors
  }
}
```

### Frontend Components

#### CustomToolsSelector
- **Location**: `/opt/kasaai/apps/b2c-portal/src/components/automation/CustomToolsSelector.tsx`
- **Purpose**: UI for tool selection and management
- **Features**: Search, filter, register, analytics viewing

#### Integration
- **AutomationDeploymentWizard**: Step 6 of automation creation workflow
- **VAPI Integration**: Tools added to voice agent function calls
- **N8N Integration**: Tools added as HTTP request nodes

## API Reference

### Base URL
```
https://api.ailabsafrica.com/custom-tools
```

### Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer <token>
```

### Endpoints

#### Tool Management

##### List Tools
```http
GET /
```
**Query Parameters:**
- `client_id` (optional): Filter by client
- `industry` (optional): Filter by industry
- `category` (optional): Filter by category
- `active_only` (boolean): Only active tools (default: true)

**Response:**
```json
{
  "tools": [
    {
      "id": "tool_id",
      "name": "tool_name",
      "client_id": "client_id",
      "industry": "healthcare",
      "category": "provider_search",
      "description": "Tool description",
      "endpoint": "/custom-tools/client/tool_name",
      "method": "POST",
      "schema": { ... },
      "active": true,
      "created_at": "2024-01-01T00:00:00Z",
      "metadata": { ... }
    }
  ],
  "count": 1
}
```

##### Search Tools
```http
GET /search?query=<search_term>
```
**Query Parameters:**
- `query` (required): Search term
- `client_id` (optional): Filter by client
- `industry` (optional): Filter by industry
- `category` (optional): Filter by category
- `limit` (optional): Max results (default: 50)

**Response:**
```json
{
  "tools": [ ... ],
  "count": 1,
  "query": "search_term",
  "filters": { ... }
}
```

##### Register Tool from File
```http
POST /register
```
**Request Body:**
```json
{
  "file_path": "/path/to/tool.py",
  "client_id": "client_id",
  "industry": "healthcare",
  "category": "provider_search",
  "description": "Tool description",
  "metadata": { ... }
}
```

##### Register Tool from Database
```http
POST /db/register
```
**Request Body:**
```json
{
  "name": "tool_name",
  "description": "Tool description",
  "schema": {
    "type": "function",
    "function": {
      "name": "tool_name",
      "description": "Tool description",
      "parameters": {
        "type": "object",
        "properties": {
          "param1": { "type": "string" }
        },
        "required": ["param1"]
      }
    }
  },
  "client_id": "client_id",
  "industry": "general",
  "category": "utility",
  "code": "def main(parameters): return {'result': 'success'}"
}
```

##### Bulk Register Tools
```http
POST /db/bulk-register
```
**Request Body:**
```json
{
  "tools": [
    {
      "name": "tool1",
      "description": "First tool",
      "schema": { ... }
    },
    {
      "name": "tool2",
      "description": "Second tool",
      "schema": { ... }
    }
  ],
  "client_id": "client_id",
  "source": "bulk_import"
}
```

#### Tool Execution

##### Execute by ID
```http
POST /execute/{tool_id}
```
**Request Body:**
```json
{
  "param1": "value1",
  "param2": "value2"
}
```

##### Execute by Name
```http
POST /{client_id}/{tool_name}
```
**Request Body:**
```json
{
  "param1": "value1",
  "param2": "value2"
}
```

**Response:**
```json
{
  "success": true,
  "result": { ... },
  "tool_name": "tool_name",
  "executed_at": "2024-01-01T00:00:00Z"
}
```

#### Analytics

##### Tool Analytics
```http
GET /analytics/{tool_id}
```
**Response:**
```json
{
  "analytics": {
    "execution_count": 150,
    "last_executed": "2024-01-01T00:00:00Z",
    "average_response_time": 0.245,
    "error_count": 3
  },
  "tool_name": "tool_name",
  "client_id": "client_id"
}
```

##### Client Summary
```http
GET /summary/{client_id}
```
**Response:**
```json
{
  "client_id": "client_id",
  "summary": {
    "total_tools": 10,
    "active_tools": 8,
    "total_executions": 1250,
    "total_errors": 15,
    "categories": ["provider_search", "communication"],
    "industries": ["healthcare"],
    "success_rate": 98.8
  }
}
```

#### Tool Management

##### Update Tool
```http
PUT /{tool_id}
```
**Request Body:**
```json
{
  "description": "Updated description",
  "active": false,
  "tags": ["tag1", "tag2"]
}
```

##### Deactivate Tool
```http
DELETE /{tool_id}
```

## Tool Categories

### Standard Categories
- **provider_search**: Healthcare provider location and search tools
- **communication**: Email, SMS, chat integration tools
- **data**: Data processing and transformation tools
- **security**: Authentication and security tools
- **utility**: General utility and helper tools

### Industry Classifications
- **healthcare**: Medical and healthcare-specific tools
- **finance**: Financial services and banking tools
- **retail**: E-commerce and retail tools
- **general**: Cross-industry utility tools

## Integration with Automation Workflows

### VAPI Integration
Custom tools are automatically added to VAPI voice agents as function calls:
```javascript
const customToolFunctions = selectedCustomTools.map(tool => ({
  type: 'function',
  function: {
    name: tool.name,
    description: tool.description,
    parameters: tool.schema?.function?.parameters || defaultSchema
  },
  server: {
    url: tool.endpoint,
    secret: process.env.VAPI_WEBHOOK_SECRET
  }
}));
```

### N8N Integration
Custom tools are added as HTTP request nodes in N8N workflows:
```javascript
const customToolNodes = selectedCustomTools.map((tool, index) => ({
  id: `custom-tool-${tool.name}`,
  name: `Custom Tool: ${tool.name}`,
  type: 'n8n-nodes-base.httpRequest',
  parameters: {
    url: tool.endpoint,
    method: tool.method || 'POST',
    sendBody: true,
    specifyBody: 'json'
  }
}));
```

## Current Implementation Status

### ✅ Completed Features

1. **Core Service Implementation**
   - Full `CustomToolsService` with async MongoDB operations using Motor
   - Tool registration from files and database specifications
   - Tool execution with analytics tracking
   - Comprehensive error handling and validation

2. **VAPI Integration**
   - Automatic tool synchronization with VAPI API
   - Correct schema formatting for VAPI function tools
   - Bulk sync operations for multiple tools
   - Sync status tracking and error reporting

3. **API Endpoints**
   - Complete REST API with 20+ endpoints
   - Authentication protection on all routes
   - Request/response validation with Pydantic models
   - Comprehensive error handling and logging

4. **Analytics and Monitoring**
   - Real-time execution tracking
   - Performance metrics (response time, success rate)
   - Client summary statistics
   - Error tracking and reporting

5. **Search and Discovery**
   - Text-based tool search
   - Multi-filter support (client, industry, category)
   - Tool categorization and tagging

6. **Testing Infrastructure**
   - Comprehensive test suite with 36+ test cases
   - Unit tests for all service methods
   - Integration tests for complete workflows
   - Async test support with pytest-asyncio

### ✅ Premier Health Integration

Successfully registered and synchronized 17 Premier Health tools:
- Healthcare provider search tools
- Emergency provider location
- Appointment scheduling (Calendly integration)
- Communication tools (SMS, Email)
- CRM integration (HubSpot)
- AI-powered features (transcript summarization, web search)

**Status**: All tools synced with VAPI and ready for production use.

### 🔧 Technical Implementation Details

#### Async MongoDB Operations
```python
# Updated mongo.py to use Motor for async operations
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorCollection

def get_collection(name: str) -> AsyncIOMotorCollection:
    """Return async MongoDB collection."""
    db_name = os.getenv("MONGODB_DB", "kasaai_core")
    return get_client()[db_name][name]
```

#### VAPI Schema Format
Corrected VAPI tool schema to match API requirements:
```python
def _prepare_vapi_tool_data(self, tool: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "server": {
            "url": tool.get("server_url", f"https://api.ailabsafrica.com{tool['endpoint']}")
        },
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": {
                "type": "object",
                "properties": parameters.get("properties", {}),
                "required": parameters.get("required", [])
            }
        }
    }
```

#### Testing Approach
```python
# Properly configured async tests with correct mocking
@pytest.mark.asyncio
async def test_tool_registration_from_database(self, service, sample_tool_data):
    """Test tool registration with proper async mocking."""
    with patch.object(service.tools_collection, 'insert_one') as mock_insert:
        mock_result = AsyncMock()
        mock_result.inserted_id = ObjectId()
        mock_insert.return_value = mock_result

        result = await service.register_tool_from_database(sample_tool_data)

        assert result["success"] is True
        assert "tool_id" in result
        mock_insert.assert_called_once()
```

## Tool Development Guide

### File-Based Tools
Create a Python file with tool functions:

```python
# /opt/kasaai/apps/automations/client/tools.py

class ClientTools:
    def __init__(self, config=None):
        self.config = config or {}

    def search_providers(self, location: str, specialty: str = None):
        """
        Search for healthcare providers by location and specialty.

        Args:
            location (str): Geographic location
            specialty (str): Medical specialty

        Returns:
            dict: Provider search results
        """
        # Implementation here
        return {
            "providers": [],
            "total": 0,
            "location": location,
            "specialty": specialty
        }

# Optional: Define schemas for better integration
TOOL_SCHEMAS = {
    "search_providers": {
        "type": "function",
        "function": {
            "name": "search_providers",
            "description": "Search for healthcare providers",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Geographic location"
                    },
                    "specialty": {
                        "type": "string",
                        "description": "Medical specialty"
                    }
                },
                "required": ["location"]
            }
        }
    }
}
```

### Database-Registered Tools
Register tools directly via API with inline Python code:

```python
tool_data = {
    "name": "calculate_bmi",
    "description": "Calculate Body Mass Index",
    "client_id": "healthcare-client",
    "category": "utility",
    "industry": "healthcare",
    "schema": {
        "type": "function",
        "function": {
            "name": "calculate_bmi",
            "description": "Calculate BMI from height and weight",
            "parameters": {
                "type": "object",
                "properties": {
                    "height_cm": {"type": "number"},
                    "weight_kg": {"type": "number"}
                },
                "required": ["height_cm", "weight_kg"]
            }
        }
    },
    "code": """
def main(parameters):
    height_cm = parameters.get('height_cm')
    weight_kg = parameters.get('weight_kg')

    if height_cm <= 0 or weight_kg <= 0:
        return {'error': 'Invalid height or weight'}

    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)

    if bmi < 18.5:
        category = 'Underweight'
    elif bmi < 25:
        category = 'Normal'
    elif bmi < 30:
        category = 'Overweight'
    else:
        category = 'Obese'

    return {
        'bmi': round(bmi, 1),
        'category': category,
        'height_cm': height_cm,
        'weight_kg': weight_kg
    }
"""
}
```

## Frontend Usage

### Basic Tool Selection
```typescript
import CustomToolsSelector from '@/components/automation/CustomToolsSelector';

function MyComponent() {
  const [selectedTools, setSelectedTools] = useState([]);

  return (
    <CustomToolsSelector
      selectedTools={selectedTools}
      onToolsChange={setSelectedTools}
      industry="healthcare"
      clientId="my-client"
    />
  );
}
```

### Tool Registration
The CustomToolsSelector includes a registration dialog accessible via the "Register Tool" button. Users can:
- Enter tool name and description
- Select category and industry
- Write inline Python code
- Define JSON schema
- Preview and register the tool

### Analytics Viewing
Click the analytics icon (📊) on any tool card to view:
- Total executions
- Average response time
- Error count and success rate
- Last execution timestamp

## Best Practices

### Security
- Always validate input parameters
- Sanitize user inputs before processing
- Use environment variables for sensitive data
- Implement proper error handling

### Performance
- Keep tool functions lightweight
- Use async operations for I/O bound tasks
- Cache frequently accessed data
- Monitor execution times via analytics

### Documentation
- Provide clear function docstrings
- Include parameter descriptions in schemas
- Add usage examples in metadata
- Use descriptive tool names and categories

### Testing
- Test tools independently before registration
- Validate schema compatibility with VAPI/N8N
- Monitor analytics for performance issues
- Use staging environment for new tools

## Troubleshooting

### Common Issues

#### Authentication Errors
```
Command insert requires authentication
```
**Solution**: Ensure MongoDB is properly configured with authentication.

#### Import Errors
```
ModuleNotFoundError: No module named 'tool_module'
```
**Solution**: Check file path and ensure all dependencies are installed.

#### Schema Validation Errors
```
Invalid schema format
```
**Solution**: Validate JSON schema format and required fields.

#### Execution Timeouts
```
Tool execution timed out
```
**Solution**: Optimize tool code or increase timeout limits.

### Debugging
- Check tool analytics for execution patterns
- Review error logs in MongoDB
- Test tools independently via API
- Validate schemas with online validators

## Support

For issues or questions:
- Review API documentation above
- Check MongoDB logs for database issues
- Test tools via direct API calls
- Contact development team for integration issues