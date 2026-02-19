# Premier Health Vapi Voice Assistant Setup Guide

## Overview

This optimized n8n workflow creates a comprehensive voice assistant for Premier Health that integrates with:

- **Custom Premier Health API Tools** from `/backend/routes/premier_health.py`
- **Integration API Keys** from the configuration file
- **Freshdesk Escalation** for complex queries
- **Location Services** optimized for Greater Accra region

## Features

### Core Capabilities
1. **Healthcare Provider Search** - Find doctors, hospitals, clinics, pharmacies by location/specialty
2. **Emergency Provider Lookup** - Urgent care and emergency services
3. **Information Delivery** - Send provider details via email or SMS
4. **Support Escalation** - Create Freshdesk tickets for complex queries
5. **Call Analytics** - Structured data extraction and reporting

### Advanced Features
- **Smart Location Recognition** - Optimized for Greater Accra and surrounding areas
- **Multi-channel Communication** - Voice, email, SMS integration
- **Contextual Understanding** - Healthcare-specific conversation patterns
- **Escalation Intelligence** - Automatic support routing when needed

## Setup Instructions

### Prerequisites

1. **Vapi Account** with API access
2. **API Keys** configured in environment:
   ```bash
   VAPI_API_KEY=your-vapi-api-key
   RESEND_API=your-resend-api-key
   VONAGE_API_KEY=your-vonage-api-key
   VONAGE_API_SECRET=your-vonage-secret
   FRESHDESK_URL=your-freshdesk-url
   ```

3. **Backend Services** running at `https://api.ailabsafrica.com`

### Deployment Steps

1. **Import Workflow**
   ```bash
   # Import the JSON workflow into your n8n instance
   curl -X POST https://your-n8n-instance.com/api/v1/workflows \
     -H "Content-Type: application/json" \
     -d @premier_health_vapi_optimized_workflow.json
   ```

2. **Configure Credentials**
   - Create "Vapi AI Authentication" HTTP Header Auth credential
   - Add `Authorization: Bearer YOUR_VAPI_API_KEY`

3. **Run Setup Workflow**
   - Execute the workflow
   - Fill in the form with:
     - **Server URL**: `https://api.ailabsafrica.com`
     - **Organization Name**: `Premier Health Ghana`
     - **Service Area**: `Greater Accra`
     - **Support Email**: `support@premierhealth.com`

4. **Verify Setup**
   - Check the generated summary for:
     - Assistant ID and Phone Number
     - Tool IDs (should be 5 tools)
     - Webhook endpoint configuration

## Tool Integration Details

### Healthcare Search Tool
```json
{
  "name": "search_healthcare_providers",
  "endpoint": "/premier-health/vapi-webhook",
  "parameters": {
    "query": "Search description",
    "location": "Geographic area",
    "specialty": "Medical specialty",
    "provider_type": "doctor|hospital|clinic|pharmacy",
    "max_results": 5
  }
}
```

### Emergency Provider Tool
```json
{
  "name": "get_emergency_providers",
  "endpoint": "/premier-health/vapi-webhook",
  "parameters": {
    "location": "Emergency location",
    "max_results": 5
  }
}
```

### Communication Tools
- **Email Tool**: `send_provider_info_email` - Uses Resend API
- **SMS Tool**: `send_provider_info_sms` - Uses Vonage API

### Support Escalation Tool
```json
{
  "name": "escalate_to_support",
  "endpoint": "/premier-health/vapi-webhook",
  "parameters": {
    "customer_name": "Customer name",
    "customer_email": "Email for followup",
    "customer_phone": "Phone number",
    "search_query": "What they searched for",
    "location_searched": "Area searched",
    "issue_description": "Problem description"
  }
}
```

## Backend API Integration

The workflow integrates with these Premier Health backend endpoints:

- `POST /premier-health/search` - Healthcare provider search
- `POST /premier-health/emergency-providers` - Emergency services
- `POST /premier-health/send-email` - Email provider information
- `POST /premier-health/send-sms` - SMS provider information
- `POST /premier-health/escalate-to-support` - Freshdesk escalation
- `POST /premier-health/vapi-webhook` - Main webhook handler

## Voice Assistant Configuration

### Personality & Tone
- **Professional and Empathetic** - Healthcare-focused communication
- **Location-Aware** - Understands Greater Accra geography
- **Action-Oriented** - Guides users to solutions quickly

### Conversation Flow
1. **Greeting** - Introduce capabilities
2. **Intent Recognition** - Understand healthcare needs
3. **Location Clarification** - Confirm service area
4. **Search Execution** - Find relevant providers
5. **Information Delivery** - Present results clearly
6. **Follow-up Actions** - Email/SMS or escalation

### Analytics & Reporting
- **Call Scoring** - 1-10 effectiveness rating
- **Intent Tracking** - Customer healthcare needs
- **Location Analytics** - Popular search areas
- **Escalation Monitoring** - Support ticket creation
- **Success Metrics** - Resolution rate tracking

## Testing & Validation

### Test Scenarios
1. **Basic Search**: "Find a cardiologist in Accra"
2. **Emergency Query**: "I need an emergency hospital near East Legon"
3. **Email Request**: "Send me the clinic information by email"
4. **Escalation**: "I can't find what I'm looking for"

### Monitoring
- Check `/premier-health/health` endpoint for service status
- Monitor Freshdesk for escalated tickets
- Review call analytics in Vapi dashboard

## Troubleshooting

### Common Issues
1. **Tools Not Loading** - Verify server URL is accessible
2. **Authentication Errors** - Check Vapi API key
3. **No Search Results** - Verify database connectivity
4. **Email/SMS Fails** - Confirm Resend/Vonage credentials

### Debug Commands
```bash
# Test backend health
curl https://api.ailabsafrica.com/premier-health/health

# Test webhook endpoint
curl -X POST https://api.ailabsafrica.com/premier-health/vapi-webhook \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Check available areas
curl https://api.ailabsafrica.com/premier-health/areas
```

## Next Steps

1. **Performance Optimization** - Monitor response times
2. **Content Enhancement** - Add more healthcare specialties
3. **Geographic Expansion** - Add more regions beyond Greater Accra
4. **Analytics Dashboard** - Build reporting interface
5. **Staff Training** - Train support team on escalation handling

## Support

For technical issues with this setup:
- Check the backend logs: `journalctl -u kasaai-core-backend.service`
- Review n8n workflow execution logs
- Contact the development team with specific error messages