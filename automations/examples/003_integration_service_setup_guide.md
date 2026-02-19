# Premier Health Vapi Integration Service Workflow Setup Guide (v002)

## Overview

This updated workflow leverages the existing **Integration Service** architecture in `/opt/kasaai/apps/core_backend/backend/services/integration_service.py` for a more robust and maintainable implementation.

## Key Architectural Improvements

### 1. **Integration Service Architecture**
- Uses the consolidated `IntegrationService` class that manages 44+ integrations
- Leverages dedicated consolidated services:
  - `hubspot_consolidated` - CRM and contact management
  - `resend_consolidated` - Email notifications
  - `tavily_consolidated` - Web search and research
  - `calendly_consolidated` - Appointment scheduling
  - Custom `premier_health` - Healthcare provider search

### 2. **Webhook Routing**
```
Integration Tools → /integration-webhooks/execute → IntegrationService.execute_integration()
Premier Health → /premier-health/vapi-webhook → Custom healthcare tools
```

### 3. **Tool Configuration**
Each tool now properly routes through the Integration Service:

```json
{
  "integration_name": "resend_consolidated",
  "action": "send_email",
  "recipient_email": "user@example.com",
  "subject": "Healthcare Provider Information",
  "content": "Provider details..."
}
```

## Workflow Components

### **Tool 1: Healthcare Provider Search**
- **Endpoint**: `/premier-health/vapi-webhook`
- **Function**: `search_healthcare_providers`
- **Purpose**: Find doctors, hospitals, clinics, pharmacies in Greater Accra
- **Integration**: Custom Premier Health API

### **Tool 2: Email Notifications**
- **Endpoint**: `/integration-webhooks/execute`
- **Integration**: `resend_consolidated`
- **Action**: `send_email`
- **Purpose**: Send provider information via email

### **Tool 3: Web Health Search**
- **Endpoint**: `/integration-webhooks/execute`
- **Integration**: `tavily_consolidated`
- **Action**: `search`
- **Purpose**: Search for current health information and guidelines

### **Tool 4: Contact Management**
- **Endpoint**: `/integration-webhooks/execute`
- **Integration**: `hubspot_consolidated`
- **Action**: `create_contact`
- **Purpose**: Save patient information in CRM

### **Tool 5: Appointment Scheduling**
- **Endpoint**: `/integration-webhooks/execute`
- **Integration**: `calendly_consolidated`
- **Action**: `create_event`
- **Purpose**: Schedule healthcare appointments

### **Tool 6: Support Escalation**
- **Endpoint**: `/premier-health/vapi-webhook`
- **Function**: `escalate_to_support`
- **Purpose**: Create Freshdesk tickets for complex queries

## Setup Instructions

### 1. **Import Workflow**
```bash
# Import into n8n
curl -X POST https://your-n8n-instance.com/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @002_comprehensive_vapi_integration_service_workflow.json
```

### 2. **Configure API Keys**
Ensure these keys are configured in the Integration Service:
```bash
VAPI_API_KEY=your-vapi-api-key
RESEND_API=your-resend-api-key
HUBSPOT_ACCESS_TOKEN=your-hubspot-token
TAVILY_API_KEY=your-tavily-key
CALENDLY_ACCESS_TOKEN=your-calendly-token
```

### 3. **Run Setup Workflow**
Execute with these form values:
- **Server URL**: `https://api.ailabsafrica.com`
- **Organization Name**: `Premier Health Ghana`
- **Service Area**: `Greater Accra`
- **Support Email**: `support@premierhealth.com`
- **Test Email**: `ailabsafrica@gmail.com`

## Testing Comprehensive Integration

### **Voice Conversation Test Script**

1. **Call the generated phone number**

2. **Test Healthcare Search + Email:**
   - Say: *"I need a cardiologist in Accra and want the information sent to my email"*
   - Provide email: `ailabsafrica@gmail.com`
   - **Expected**: Provider search + email via Resend integration

3. **Test Contact Saving:**
   - Say: *"Please save my contact information for follow-up"*
   - Provide: Name, email, phone, healthcare needs
   - **Expected**: HubSpot contact creation

4. **Test Appointment Scheduling:**
   - Say: *"I'd like to schedule an appointment with the cardiologist"*
   - Provide: Preferred date/time
   - **Expected**: Calendly appointment creation

5. **Test Web Search:**
   - Say: *"Can you find current heart health guidelines for Ghana?"*
   - **Expected**: Tavily search with health-focused results

6. **Test Support Escalation:**
   - Say: *"I can't find a specialist for my rare condition"*
   - **Expected**: Freshdesk ticket creation

### **Expected Integration Flow**
```
Voice Request → Vapi Assistant → Tool Selection → Integration Service →
Consolidated Service (hubspot/resend/tavily/calendly) → External API → Response
```

## Integration Service Benefits

### **1. Unified Architecture**
- Single service manages all 44+ integrations
- Consistent error handling and logging
- Standardized authentication flow

### **2. Scalability**
- Easy to add new integrations
- Auto-generated consolidated services
- MCP server support for advanced integrations

### **3. Maintainability**
- Centralized configuration
- Dedicated service instances
- Comprehensive integration testing

### **4. Robustness**
- Automatic fallback handling
- Integration health monitoring
- Detailed capability reporting

## Monitoring and Validation

### **Backend Health Checks**
```bash
# Test Integration Service health
curl https://api.ailabsafrica.com/health

# Test specific integration
curl -X POST https://api.ailabsafrica.com/integration-webhooks/execute \
  -H "Content-Type: application/json" \
  -d '{"integration_name": "resend_consolidated", "action": "test_connection"}'
```

### **Integration Service Stats**
- **Total Integrations**: 44+
- **Consolidated Services**: 13+ dedicated services
- **MCP Enabled**: Multiple integrations with MCP server support
- **Categories**: Communication, Business Tools, Payment Systems, etc.

## Troubleshooting

### **Common Issues**

1. **Tool Not Responding**
   - Check Integration Service status
   - Verify endpoint URLs are accessible
   - Review integration-specific logs

2. **Authentication Errors**
   - Verify API keys in environment
   - Check Integration Service initialization
   - Test individual service connections

3. **No Results from Search**
   - Check Premier Health database connectivity
   - Verify location is within Greater Accra region
   - Review search parameters

### **Debug Commands**
```bash
# Check Integration Service capabilities
curl https://api.ailabsafrica.com/integrations/capabilities

# Test specific integration
curl -X POST https://api.ailabsafrica.com/integrations/test \
  -d '{"integration_name": "hubspot_consolidated"}'

# Check logs
journalctl -u kasaai-core-backend.service -f
```

## Next Steps

1. **Performance Monitoring**: Track integration response times
2. **Enhanced Error Handling**: Implement retry mechanisms
3. **Advanced Analytics**: Build reporting dashboard
4. **Geographic Expansion**: Add more regions beyond Greater Accra
5. **Integration Expansion**: Add more healthcare-specific integrations

This updated architecture provides a solid foundation for scalable voice-enabled healthcare assistance while leveraging existing infrastructure for maximum reliability and maintainability.