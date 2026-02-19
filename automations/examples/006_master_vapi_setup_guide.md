# Master Vapi Integration Workflow Setup Guide

## 🎯 Overview

The **Master Vapi Integration Workflow** is a highly configurable voice assistant system that integrates with your existing Integration Service to support multiple business use cases. This workflow can be customized for sales, helpdesk, healthcare, lead generation, and more.

## 🏗️ Architecture

### **Integration Service Foundation**
- **Core Service**: `/opt/kasaai/apps/core_backend/backend/services/integration_service.py`
- **44+ Available Integrations**: Communication, CRM, Email, Search, Calendar, Support
- **Consolidated Services**: Dedicated service instances for major platforms
- **Webhook Routing**: Automatic routing via Integration Service

### **Workflow Components**
1. **Configuration Form**: Dynamic setup for any use case
2. **Personality Generator**: AI personality based on use case and industry
3. **Integration Tools Generator**: Dynamic tool creation based on selected integrations
4. **Vapi Assistant Creation**: Automated assistant setup with Claude 3.5 Sonnet
5. **Phone Number Provisioning**: Automatic phone line setup
6. **Testing Framework**: Comprehensive integration and voice testing

## 🚀 Quick Start

### **1. Prerequisites**
- n8n instance with MCP tools access
- Backend running at `https://api.ailabsafrica.com`
- Integration Service properly configured
- Required API keys in environment

### **2. Import Workflow**
```bash
curl -X POST https://your-n8n-instance.com/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @004_master_vapi_workflow.json
```

### **3. Configure for Your Use Case**
Run the workflow and fill out the configuration form:

#### **Sales Assistant Example:**
- **Use Case**: `sales`
- **Organization**: `TechCorp Solutions`
- **Industry**: `technology`
- **Active Integrations**: `hubspot_crm,resend_email,calendly_scheduling,tavily_search`
- **Personality**: `professional`

#### **Helpdesk Support Example:**
- **Use Case**: `helpdesk`
- **Organization**: `ServiceDesk Pro`
- **Industry**: `technology`
- **Active Integrations**: `freshdesk_support,resend_email,tavily_search,supabase_database`
- **Personality**: `empathetic`

## 🎛️ Configuration Options

### **Supported Use Cases**
| Use Case | Description | Key Integrations |
|----------|-------------|------------------|
| `sales` | Lead qualification and sales support | HubSpot, Email, Calendar, Search |
| `helpdesk` | Customer support and issue resolution | Freshdesk, Email, Search, Database |
| `healthcare` | HIPAA-compliant healthcare assistance | Calendar, Email, Search, CRM |
| `general_business` | Multi-purpose business assistant | CRM, Email, Calendar, Search |
| `lead_generation` | Focused B2B lead generation | CRM, Email, Calendar, Search |
| `customer_support` | Customer success and retention | CRM, Email, Support, Calendar |
| `appointment_booking` | Specialized scheduling service | Calendar, Email, SMS, CRM |
| `custom` | Flexible configuration for any need | User-selected integrations |

### **Available Integrations**
| Integration | Service | Description |
|-------------|---------|-------------|
| `hubspot_crm` | `hubspot_consolidated` | Contact and lead management |
| `resend_email` | `resend_consolidated` | Email notifications and follow-ups |
| `tavily_search` | `tavily_consolidated` | Web search and research |
| `calendly_scheduling` | `calendly_consolidated` | Appointment scheduling |
| `freshdesk_support` | `freshdesk_consolidated` | Support ticket management |
| `vonage_sms` | `vonage_consolidated` | SMS notifications |
| `firecrawl_scraping` | `firecrawl_consolidated` | Website content analysis |
| `brave_search` | `brave_consolidated` | Enhanced web search |
| `supabase_database` | Custom endpoint | Data storage and analytics |
| `vapi_advanced` | `vapi_consolidated` | Advanced Vapi features |

### **Personality Types**
| Personality | Voice Characteristics | Best For |
|-------------|----------------------|----------|
| `professional` | Formal, business-focused | Sales, consulting |
| `friendly` | Warm, approachable | Customer support, general business |
| `empathetic` | Understanding, patient | Healthcare, sensitive issues |
| `authoritative` | Confident, decisive | Technical support, expert advice |
| `casual` | Relaxed, informal | Creative industries, startups |
| `technical` | Precise, analytical | IT support, technical sales |

## 🔧 Customization Guide

### **For Different Companies**

1. **Update Organization Details**:
   ```json
   {
     "organizationName": "Your Company Name",
     "industry": "your_industry",
     "primaryContactEmail": "admin@yourcompany.com",
     "supportEmail": "support@yourcompany.com",
     "targetLocationRegion": "Your Region"
   }
   ```

2. **Select Relevant Integrations**:
   - Choose from available integration list
   - Ensure API keys are configured in backend
   - Test each integration separately

3. **Customize Voice Personality**:
   - Match personality to brand voice
   - Consider target audience
   - Test different options

### **For Different Use Cases**

#### **Sales to Helpdesk Conversion**:
1. Change `useCase` from `sales` to `helpdesk`
2. Update integrations:
   - Remove: `hubspot_crm`, `calendly_scheduling`
   - Add: `freshdesk_support`, `supabase_database`
3. Change personality from `professional` to `empathetic`
4. Re-run workflow

#### **Healthcare Specialization**:
1. Set `useCase` to `healthcare`
2. Enable HIPAA compliance: `hipaaComplianceRequired: "Yes"`
3. Select healthcare-appropriate integrations
4. Use `empathetic` personality
5. Customize system prompts for medical context

### **Adding New Integrations**

1. **Check Integration Service**:
   ```bash
   curl https://api.ailabsafrica.com/integrations/capabilities
   ```

2. **Add to Form Options**:
   - Update `activeIntegrations` field options
   - Add integration to tool generation logic

3. **Create Tool Template**:
   ```javascript
   your_integration: {
     "function": {
       "name": "your_tool_name",
       "description": "Tool description",
       "parameters": {
         "integration_name": "your_integration_consolidated",
         "action": "your_action"
       }
     },
     "server": {
       "url": `${serverUrl}/integration-webhooks/execute`
     }
   }
   ```

4. **Test Integration**:
   ```bash
   curl -X POST https://api.ailabsafrica.com/integration-webhooks/execute \
     -H "Content-Type: application/json" \
     -d '{"integration_name": "your_integration_consolidated", "action": "test_connection"}'
   ```

## 🧪 Testing Framework

### **Automated Integration Tests**
The workflow includes comprehensive testing for all configured integrations:

1. **Connection Testing**: Verifies each integration service is available
2. **Functionality Testing**: Tests core actions for each integration
3. **Error Handling**: Validates error responses and fallbacks

### **Voice Conversation Testing**

#### **Sales Use Case Test Scripts**:
1. **Lead Qualification**:
   - Call: "Hi, I'm interested in your enterprise solution. Can you tell me about pricing?"
   - Expected: Contact saved to HubSpot, demo scheduled, follow-up email sent

2. **Information Request**:
   - Call: "Please send me your latest product brochure"
   - Expected: Web search for current info, email sent with details

#### **Helpdesk Use Case Test Scripts**:
1. **Technical Issue**:
   - Call: "I'm having trouble logging into your platform"
   - Expected: Support ticket created, troubleshooting provided, interaction logged

2. **Escalation**:
   - Call: "This is urgent - our entire system is down"
   - Expected: High-priority ticket, email notification, potential SMS alert

### **Performance Monitoring**
- Monitor integration response times
- Track conversation success rates
- Analyze tool usage patterns
- Review error logs for optimization

## 📊 Analytics and KPIs

### **Universal Metrics**
- **Call Volume**: Total conversations handled
- **Integration Usage**: Which tools are used most frequently
- **Success Rate**: Percentage of successful tool executions
- **Response Time**: Average time for integration responses

### **Use Case Specific Metrics**

#### **Sales Assistant**:
- Lead conversion rate
- Demo booking rate
- Contact capture completeness
- Follow-up email delivery

#### **Helpdesk Support**:
- First call resolution rate
- Ticket creation accuracy
- Customer satisfaction
- Escalation frequency

#### **Healthcare Assistant**:
- Appointment booking success
- HIPAA compliance score
- Provider search accuracy
- Patient satisfaction

## 🔒 Security and Compliance

### **Data Protection**
- All integrations use secure HTTPS endpoints
- API keys stored in environment variables
- No sensitive data logged in plain text
- Integration Service handles authentication

### **HIPAA Compliance** (Healthcare Use Case)
- Enable HIPAA mode in configuration
- No PHI in conversation logs
- Secure data transmission
- Patient consent mechanisms
- Audit trail maintenance

### **Integration Security**
- OAuth tokens for supported services
- API key rotation support
- Rate limiting protection
- Error message sanitization

## 🔄 Maintenance and Updates

### **Regular Maintenance Tasks**
1. **Monitor Integration Health**:
   ```bash
   curl https://api.ailabsafrica.com/integrations/health
   ```

2. **Update API Keys**: Rotate keys regularly for security

3. **Review Conversation Logs**: Optimize based on usage patterns

4. **Test New Features**: Validate after Integration Service updates

### **Scaling Considerations**
- **Horizontal Scaling**: Add more n8n instances
- **Integration Expansion**: Leverage all 44+ available integrations
- **Custom Tools**: Add business-specific tools via Integration Service
- **Multi-language Support**: Expand to additional languages

## 🆘 Troubleshooting

### **Common Issues**

#### **Tools Not Responding**
```bash
# Check Integration Service status
curl https://api.ailabsafrica.com/health

# Test specific integration
curl -X POST https://api.ailabsafrica.com/integration-webhooks/execute \
  -d '{"integration_name": "hubspot_consolidated", "action": "test_connection"}'
```

#### **Authentication Errors**
1. Verify API keys in environment
2. Check Integration Service initialization
3. Test individual service connections
4. Review error logs: `journalctl -u kasaai-core-backend.service`

#### **Voice Assistant Not Responding**
1. Check Vapi API key configuration
2. Verify webhook endpoint accessibility
3. Review assistant configuration in Vapi dashboard
4. Test phone number provisioning

### **Debug Commands**
```bash
# Integration Service capabilities
curl https://api.ailabsafrica.com/integrations/capabilities

# Specific integration test
curl -X POST https://api.ailabsafrica.com/integrations/test \
  -d '{"integration_name": "resend_consolidated"}'

# Webhook endpoint test
curl -X POST https://api.ailabsafrica.com/integration-webhooks/vapi-webhook \
  -d '{"test": true}'
```

## 🎯 Best Practices

1. **Start Simple**: Begin with 2-3 core integrations
2. **Test Thoroughly**: Validate each integration before going live
3. **Monitor Performance**: Track KPIs relevant to your use case
4. **Iterate Based on Data**: Optimize based on actual usage patterns
5. **Security First**: Regular key rotation and access reviews
6. **Documentation**: Keep configuration changes documented
7. **Backup Configurations**: Save working configurations for rollback

## 🔮 Future Enhancements

- **Multi-language Support**: Expand beyond English
- **Advanced Analytics**: ML-powered conversation insights
- **Custom Voice Models**: Branded voice personalities
- **Workflow Templates**: Pre-built industry-specific configurations
- **Real-time Monitoring**: Live dashboard for conversation metrics
- **A/B Testing**: Compare different personality and integration configurations

This master workflow provides a solid foundation for any voice-enabled business automation while leveraging your existing Integration Service infrastructure for maximum reliability and scalability.