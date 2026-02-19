# Insurance Claims Processing with Vapi Integration

## Overview
Complete n8n automation workflow for processing insurance claims with Vapi voice AI integration, providing multi-channel claim submission, automated processing, and intelligent voice interactions.

## Features

### 1. Multi-Channel Claim Intake
- **Web/Mobile API**: REST webhook endpoint for digital claim submissions
- **Voice Channel**: Vapi-powered voice assistant for phone-based claims
- **Email Processing**: Document intake and claim submission via email
- **SMS**: Two-way SMS communication for claim updates

### 2. Vapi Voice AI Integration
- **Inbound Call Handling**: AI assistant for claim filing via phone
- **Outbound Callbacks**: Automated follow-up calls for claim status
- **Voice Transcription**: Automatic transcription and analysis of voice claims
- **Interactive Voice Response**: Natural language understanding for claim queries
- **Function Calling**: Real-time database queries during calls

### 3. Claim Processing Pipeline
- **Validation Engine**: Automated validation of claim data
- **Document Processing**: OCR and document extraction
- **Fraud Detection**: Rule-based and ML-powered fraud checks
- **Auto-Adjudication**: Automated approval for simple claims
- **Escalation Logic**: Complex claims routed to human adjusters

### 4. Data Management
- **MongoDB**: Primary database for claim storage
- **Supabase**: Authentication and user management
- **Document Storage**: Cloud storage for claim documents
- **Audit Trail**: Complete history of all claim actions

### 5. Communication & Notifications
- **Email Notifications**: HTML-formatted claim confirmations
- **SMS Updates**: Real-time status updates via Twilio
- **Vapi Callbacks**: Scheduled voice follow-ups
- **Webhook Events**: Integration with external systems

## Workflow Components

### Entry Points
1. **Webhook - Claim Submission** (`/insurance-claim-submit`)
   - Receives new claims from web/mobile apps
   - Validates and processes claim data

2. **Webhook - Vapi Events** (`/vapi-webhook`)
   - Handles Vapi call events (start, end, transcript)
   - Processes voice interactions

3. **Webhook - Vapi Function Calls** (`/vapi-function-calls`)
   - Handles real-time function calls from Vapi assistant
   - Enables dynamic responses during calls

4. **Cron - Regular Claim Review**
   - Scheduled review of pending claims
   - Automatic escalation of aged claims

### Core Processing Nodes
1. **Code - Validate & Process Claim**
   - Input validation
   - Claim ID generation
   - Priority calculation

2. **MongoDB Operations**
   - Insert new claims
   - Query claim status
   - Update claim records

3. **Vapi Integration**
   - Assistant configuration
   - Outbound call initiation
   - Transcript processing

4. **Notification Services**
   - Email via SMTP
   - SMS via Twilio
   - Voice calls via Vapi

## Setup Instructions

### Prerequisites
1. n8n instance (v1.0+)
2. MongoDB database
3. Vapi account with API key
4. Twilio account (for SMS)
5. SMTP server (for email)
6. Supabase project (optional)

### Environment Variables
```bash
# Vapi Configuration
VAPI_API_KEY=your_vapi_api_key
VAPI_CLAIMS_ASSISTANT_ID=your_assistant_id
VAPI_PHONE_NUMBER_ID=your_phone_number_id

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# MongoDB
MONGODB_URI=mongodb://localhost:27017/insurance_claims

# n8n Webhooks
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_password

# Escalation Workflow
ESCALATION_WORKFLOW_ID=workflow_id_for_escalations
```

### Installation Steps

1. **Import Workflow**
   ```bash
   # Import the workflow JSON into n8n
   n8n import:workflow --input=insurance_claims_vapi_workflow.json
   ```

2. **Configure Credentials**
   - Add Vapi API credentials
   - Configure MongoDB connection
   - Set up Twilio credentials
   - Configure SMTP settings

3. **Setup Vapi Assistant**
   - Create assistant in Vapi dashboard
   - Configure system prompt for insurance claims
   - Set webhook URLs for events and functions
   - Enable required functions (checkClaimStatus, fileNewClaim, scheduleCallback)

4. **Database Setup**
   ```javascript
   // MongoDB collection schema
   {
     claimId: String,
     customerName: String,
     customerPhone: String,
     customerEmail: String,
     claimType: String,
     description: String,
     amount: Number,
     status: String,
     priority: String,
     submittedAt: Date,
     vapiCallId: String,
     transcription: String,
     recordingUrl: String,
     documents: Array,
     notes: Array,
     assignedTo: String,
     resolvedAt: Date
   }
   ```

5. **Activate Workflow**
   - Enable the workflow in n8n
   - Test webhook endpoints
   - Verify Vapi integration

## API Documentation

### Submit New Claim
```bash
POST /webhook/insurance-claim-submit
Content-Type: application/json

{
  "customerName": "John Doe",
  "customerPhone": "+1234567890",
  "customerEmail": "john@example.com",
  "claimType": "auto",
  "description": "Rear-end collision on Highway 101",
  "amount": 5000,
  "urgent": false,
  "attachments": []
}

Response:
{
  "success": true,
  "claimId": "CLM-1234567890-ABC123",
  "status": "pending_review"
}
```

### Vapi Function Calls

#### Check Claim Status
```javascript
{
  "function": "checkClaimStatus",
  "parameters": {
    "claimId": "CLM-1234567890-ABC123"
  }
}
```

#### File New Claim
```javascript
{
  "function": "fileNewClaim",
  "parameters": {
    "customerName": "Jane Doe",
    "claimType": "health",
    "description": "Emergency room visit"
  }
}
```

#### Schedule Callback
```javascript
{
  "function": "scheduleCallback",
  "parameters": {
    "claimId": "CLM-1234567890-ABC123",
    "preferredTime": "2024-01-15T14:00:00Z"
  }
}
```

## Testing

### Test Scenarios
1. **Submit Valid Claim**: Test with all required fields
2. **Invalid Phone Number**: Test validation logic
3. **High-Value Claim**: Test priority escalation
4. **Vapi Call Flow**: Test voice interaction end-to-end
5. **Database Operations**: Test CRUD operations
6. **Notification Delivery**: Verify email/SMS delivery

### Sample Test Script
```bash
# Test claim submission
curl -X POST https://your-n8n.com/webhook/insurance-claim-submit \
  -H "Content-Type: application/json" \
  -d '{
    "customerName": "Test User",
    "customerPhone": "+1234567890",
    "customerEmail": "test@example.com",
    "claimType": "auto",
    "description": "Test claim",
    "amount": 1000
  }'
```

## Monitoring & Maintenance

### Key Metrics
- Claim submission rate
- Average processing time
- Vapi call success rate
- Notification delivery rate
- Error rate by node

### Maintenance Tasks
- Regular database cleanup
- Transcript archive management
- Credential rotation
- Workflow version control
- Performance optimization

## Troubleshooting

### Common Issues

1. **Vapi Connection Failed**
   - Verify API key
   - Check assistant configuration
   - Validate webhook URLs

2. **MongoDB Connection Error**
   - Check connection string
   - Verify database permissions
   - Ensure indexes are created

3. **SMS Not Sending**
   - Verify Twilio credentials
   - Check phone number format
   - Review Twilio account balance

4. **Webhook Not Responding**
   - Check n8n webhook URL
   - Verify workflow is active
   - Review execution logs

## Security Considerations

1. **Data Protection**
   - Encrypt sensitive claim data
   - Use secure credential storage
   - Implement access controls

2. **API Security**
   - Use API key rotation
   - Implement rate limiting
   - Validate all inputs

3. **Compliance**
   - HIPAA compliance for health claims
   - PCI compliance for payment data
   - GDPR for EU customers

## Support & Resources

- [n8n Documentation](https://docs.n8n.io)
- [Vapi Documentation](https://docs.vapi.ai)
- [MongoDB Documentation](https://docs.mongodb.com)
- [Twilio Documentation](https://www.twilio.com/docs)

## License
Proprietary - Premier Health Insurance

## Version History
- v1.0.0 - Initial release with basic claim processing
- v1.1.0 - Added Vapi voice integration
- v1.2.0 - Enhanced validation and fraud detection
- v1.3.0 - Added auto-adjudication for simple claims