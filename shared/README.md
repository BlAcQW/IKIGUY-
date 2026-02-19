# KasaAI Shared Library

A comprehensive shared library for the KasaAI platform providing industry-specific modules, automation workflows, and integration capabilities.

## 🚀 Recent Updates

### 🎙️ Latest: TTS Provider Expansion (2025-11-09)

- **New TTS Providers Added**: IndexTTS 2.0 and VoxCPM now available in provider registry
  - **IndexTTS 2.0**: Advanced TTS with voice cloning, emotion control, and speech editing (EN, CN)
  - **VoxCPM**: Context-aware TTS from CPM family with voice cloning (EN, CN)
  - Both integrated into unified provider registry at `shared/integration/ai_services/provider_registry.py`
  - Total TTS providers: 11 (was 9)
  - Accessible through `/api/tts/providers` endpoint

- **TTS Lab Integration**: Both providers added to TTS Lab landing page (https://ttslab.ailabsafrica.com)
  - Total service count updated from 15+ to 17+
  - Individual provider cards with features and capabilities
  - Direct links to RunPod TTS-WebUI interface

### ✅ Phase 1: Foundation & Communication (Completed)

- **Enhanced Base Industry Modules** with automation workflows, integration points, and compliance frameworks
- **Automation Workflow Engine** with support for complex multi-step workflows
- **Industry Module Factory** for dynamic module creation and management
- **Standardized API Endpoints** for all industry modules
- **Complete Communication System**:
  - **Email Integration**: SMTP, SendGrid with template support and scheduling
  - **SMS Integration**: Twilio, MessageBird with bulk messaging and delivery tracking
  - **WhatsApp Business Integration**: Template messages, media, interactive buttons

### 🏠 Phase 2: High-Demand Industry Modules (Completed)

- **Real Estate Module**: Complete property management system with tenant services, maintenance requests, lead management, and automation workflows
- **Education Module**: ✅ Enhanced - Comprehensive student services and academic management with enrollment automation, grade tracking, event coordination, emergency communications, academic advising, student life management, orientation management, professional development, and administrative communications

### 🚀 Phase 3: Productivity Tools & Core Industries (Completed)

- **Google Workspace Integration**: Complete integration with Google Sheets, Calendar, and Docs APIs with authentication, error handling, and comprehensive testing
- **Professional Services Module**: Comprehensive legal and consulting services automation with case management, project tracking, client communications, and compliance frameworks
- **Automotive Module**: Vehicle service and sales automation with vehicle management, service records, customer management, sales leads, inventory management, warranty claims, recall management, and service reminders

### 🏥 Phase 4: Industry Systems & Remaining Modules (Completed)

- **Healthcare System Integrations**: ✅ **Completed**

  - EHR system integrations (Epic, Cerner, Allscripts, Custom)
  - Patient data management (CRUD operations)
  - Appointment scheduling and management
  - Lab results and prescription management
  - HIPAA compliance and security features
  - Comprehensive unit tests (43 tests passing)

- **Financial System Integrations**: ✅ **Completed**
  - Core banking system integrations (Fiserv, FIS, Jack Henry, Custom)
  - Account management and balance retrieval
  - Transaction history and transfer capabilities
  - Loan status tracking and customer management
  - PCI DSS compliance and security features
  - Comprehensive unit tests (49 tests passing)

### 🔧 Phase 5: Enhanced Integration Framework (Completed)

- **Extended Integration Types**: ✅ **Completed**

  - 20 integration types including CRM, ERP, Payment, Email, SMS, WhatsApp, Calendar, Storage, Productivity, Industry, Custom, Database, Document, Notification, Analytics, Security, Compliance, Monitoring, Backup, and API

- **Integration Workflow Engine**: ✅ **Completed**
  - Complex workflow execution with dependencies and topological sorting
  - Multiple step types: Integration, Transform, Validate, Condition, Delay, Notification, Custom
  - Retry logic with configurable attempts and delays
  - Rollback capabilities for failed workflows
  - Workflow scheduling and status tracking
  - Comprehensive validation and error handling
  - Complete unit test coverage (50+ tests)

### 📊 Phase 6: Automation Implementation Status Analysis (Completed)

- **Comprehensive Analysis**: ✅ **Completed**

  - Complete audit of all industry automation processes from `industry-automation-processes.md`
  - Detailed comparison with actual implementations across all modules
  - Identification of 217 missing automations out of 325 total (33.2% completion rate)
  - Priority categorization: High (0% complete), Medium (36-45% complete), Low (72-100% complete)

- **Missing Automation Documentation**: ✅ **Completed**
  - Created `automation-implementation-status.md` with detailed breakdown
  - Updated `comprehensive-implementation-task-list.md` with 13 new tasks for missing automations
  - Prioritized implementation roadmap for Manufacturing, Logistics & Transportation, and Telecom modules
  - Identified enhancement opportunities for existing modules with 36-45% completion rates

## 📦 Core Components

### 🏗️ Industry Modules

- **Base Module System**: Enhanced with automation workflows and integration points
- **Module Factory**: Dynamic creation and management of industry modules
- **Standardized APIs**: Consistent endpoints across all modules

### 🔄 Automation Workflows

- **Workflow Engine**: Multi-step automation with dependencies and retry logic
- **Step Types**: Capability execution, integrations, conditions, delays, loops, parallel execution
- **Execution Tracking**: Real-time status monitoring and error handling

### 🔧 Enhanced Integration Framework

- **Integration Types**: 20 comprehensive integration types for different systems and platforms
- **Workflow Engine**: Complex integration workflows with dependencies and topological sorting
- **Step Types**: Integration, Transform, Validate, Condition, Delay, Notification, Custom
- **Retry & Rollback**: Configurable retry logic and rollback capabilities for failed workflows
- **Scheduling**: Workflow scheduling and status tracking
- **Validation**: Comprehensive validation and error handling

### 📧 Communication Integrations

- **Email System**: Multi-provider support (SMTP, SendGrid) with templates and scheduling
- **SMS System**: Multi-provider support (Twilio, MessageBird) with bulk messaging
- **WhatsApp Business**: Template messages, media sharing, interactive buttons
- **Google Workspace**: Comprehensive integration with Google Sheets, Calendar, and Docs APIs

### 🏥 Healthcare System Integrations

- **EHR Systems**: Epic, Cerner, Allscripts, and Custom EHR integrations
- **Patient Management**: Complete CRUD operations for patient data
- **Appointment Management**: Scheduling, updates, and status tracking
- **Lab Results**: Retrieval and management of laboratory test results
- **Prescription Management**: Creation and tracking of prescriptions
- **HIPAA Compliance**: Built-in security and compliance features

### 💰 Financial System Integrations

- **Core Banking Systems**: Fiserv, FIS, Jack Henry, and Custom banking integrations
- **Account Management**: Balance retrieval and account information
- **Transaction Processing**: History tracking and transfer capabilities
- **Loan Management**: Status tracking and loan information
- **Customer Management**: Customer data updates and management
- **PCI DSS Compliance**: Built-in security and compliance features

### 🏥 Industry-Specific Modules

- **Healthcare**: ✅ **Enhanced** - HIPAA-compliant patient management and appointment automation with appointment management, medication management, lab results processing, claims processing, patient registration, staff coordination, and comprehensive analytics
- **Financial**: ✅ **Enhanced** - PCI-compliant banking and payment processing with fraud detection, loan default automation, KYC verification, risk assessment, transaction monitoring, default prediction, and alert systems
- **Retail**: ✅ **Enhanced** - E-commerce integration and customer service automation with inventory management, customer analytics, order processing, supply chain management, loyalty programs, inventory monitoring, and demand forecasting
- **Manufacturing**: ✅ **Completed** - Production monitoring and quality control automation with equipment maintenance, quality control, supply chain management, inventory management, safety management, and employee communications
- **Logistics & Transportation**: ✅ **Completed** - Package management and fleet automation with route optimization, customer communication, fleet management, driver management, delivery confirmations, and real-time tracking
- **Telecom**: Call management and customer support
- **Insurance**: Claims processing and policy management
- **Real Estate**: Property management, tenant services, and lead management automation
- **Education**: Student services, academic management, and educational workflow automation
- **Professional Services**: Legal and consulting services with case management, project tracking, and compliance
- **Automotive**: Vehicle service and sales automation with maintenance tracking, customer service, and sales management
- **Hospitality**: ✅ **Completed** - Guest services and booking management automation with room management, guest experience, staff coordination, and operational workflows
- **Utilities**: ✅ **Completed** - Customer service and infrastructure management automation with meter reading, billing management, outage management, and energy efficiency
- **Government**: ✅ **Completed** - Citizen services and administrative automation with application processing, emergency management, citizen registration, policy management, and compliance monitoring

## 🚀 Quick Start

### Basic Usage

```python
from shared.modules import create_module, get_available_industries
from shared.integration import EmailIntegration, SMSIntegration, WhatsAppIntegration

# Create an industry module
healthcare_module = create_module("healthcare", "tenant_123")

# Initialize with settings
await healthcare_module.initialize("tenant_123", {
    "ehr_system": "epic",
    "compliance_level": "hipaa"
})

# Execute a capability
result = await healthcare_module.execute_capability("schedule_appointment", {
    "patient_id": "12345",
    "doctor_id": "67890",
    "date": "2024-01-15",
    "time": "14:30"
})

# Execute an automation workflow
workflow_result = await healthcare_module.execute_workflow("appointment_reminder_workflow", {
    "patient_id": "12345",
    "appointment_id": "apt_789"
})
```

### Communication Integrations

```python
# Email Integration
email_config = {
    "providers": {
        "smtp": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "your-email@gmail.com",
            "password": "your-password"
        },
        "sendgrid": {
            "api_key": "your-sendgrid-api-key"
        }
    },
    "default_provider": "sendgrid"
}

email_integration = EmailIntegration(email_config)

# Send email
result = await email_integration.send_email(
    to="customer@example.com",
    subject="Appointment Reminder",
    body="Your appointment is tomorrow at 2:30 PM",
    html_body="<h1>Appointment Reminder</h1><p>Your appointment is tomorrow at 2:30 PM</p>"
)

# SMS Integration
sms_config = {
    "providers": {
        "twilio": {
            "account_sid": "your-account-sid",
            "auth_token": "your-auth-token"
        }
    },
    "default_provider": "twilio"
}

sms_integration = SMSIntegration(sms_config)

# Send SMS
result = await sms_integration.send_sms(
    to="+1234567890",
    message="Your appointment is tomorrow at 2:30 PM",
    from_number="+0987654321"
)

# WhatsApp Integration
whatsapp_config = {
    "phone_number_id": "your-phone-number-id",
    "access_token": "your-access-token",
    "verify_token": "your-verify-token"
}

whatsapp_integration = WhatsAppIntegration(whatsapp_config)

# Send WhatsApp message
result = await whatsapp_integration.send_template_message(
    template_name="appointment_reminder",
    to="1234567890",
    variables={
        "patient_name": "John Doe",
        "appointment_time": "2:30 PM",
        "appointment_date": "tomorrow"
    }
)

# Google Workspace Integration
from shared.integration import GoogleWorkspaceIntegration, GoogleWorkspaceConfig

# Configure Google Workspace integration
workspace_config = GoogleWorkspaceConfig(
    sheets=GoogleSheetsConfig(
        spreadsheet_id="your-spreadsheet-id",
        credentials_path="/path/to/service-account.json"
    ),
    calendar=GoogleCalendarConfig(
        calendar_id="primary",
        credentials_path="/path/to/service-account.json"
    ),
    docs=GoogleDocsConfig(
        credentials_path="/path/to/service-account.json"
    )
)

# Initialize integration
workspace_integration = GoogleWorkspaceIntegration(workspace_config)

# Google Sheets operations
spreadsheet = await workspace_integration.sheets.create_spreadsheet("Sales Report")
data = await workspace_integration.sheets.read_range("spreadsheet_id", "A1:D10")
await workspace_integration.sheets.write_range("spreadsheet_id", "A1:D10", [["Data", "Here"]])

# Google Calendar operations
event = await workspace_integration.calendar.create_event("primary", {
    "summary": "Team Meeting",
    "start": {"dateTime": "2024-01-15T10:00:00Z"},
    "end": {"dateTime": "2024-01-15T11:00:00Z"}
})

# Google Docs operations
document = await workspace_integration.docs.create_document("Project Report", "Initial content")
await workspace_integration.docs.update_document("document_id", [
    {"insertText": {"location": {"index": 1}, "text": "Updated content"}}
])
```

## 🏗️ Architecture

### Module Structure

```
shared/
├── modules/
│   ├── base.py              # Enhanced base module with automation workflows
│   ├── workflow.py          # Automation workflow engine
│   ├── factory.py           # Industry module factory
│   ├── api.py               # Standardized API endpoints
│   ├── healthcare.py        # Healthcare industry module
│   ├── financial.py         # Financial industry module
│   ├── retail.py            # Retail industry module
│   ├── manufacturing.py     # Manufacturing industry module
│   ├── telecom.py           # Telecom industry module
│   └── insurance.py         # Insurance industry module
├── integration/
│   ├── email.py             # Email integration system
│   ├── sms.py               # SMS integration system
│   ├── whatsapp.py          # WhatsApp Business integration
│   ├── google_workspace.py  # Google Workspace integration (Sheets, Calendar, Docs)
│   └── integration_manager.py # Integration management
├── ai/                      # AI-powered features
├── analytics/               # Business intelligence
├── config/                  # Configuration management
├── events/                  # Event system
├── license/                 # License management
├── monitoring/              # System monitoring
├── security/                # Security features
├── speech/                  # Speech processing
├── storage/                 # Data storage
├── telephony/               # Telephony adapters
├── tenant/                  # Multi-tenant management
└── usage/                   # Usage tracking
```

### API Endpoints

All industry modules expose standardized endpoints:

```
/api/v1/modules/{industry}/
├── /initialize              # Initialize module for tenant
├── /capabilities            # List available capabilities
├── /capabilities/{capability}/execute  # Execute capability
├── /workflows               # List automation workflows
├── /workflows/{workflow}/execute  # Execute workflow
├── /analytics               # Get industry-specific analytics
├── /compliance              # Get compliance information
├── /integrations            # List integration points
└── /health                  # Health check
```

## 🔧 Configuration

### Environment Variables

```bash
# Email Configuration
EMAIL_PROVIDER=smtp
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-password

# SMS Configuration
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token

# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_ACCESS_TOKEN=your-access-token
WHATSAPP_VERIFY_TOKEN=your-verify-token
```

### Module Configuration

```python
module_config = {
    "industry": "healthcare",
    "tenant_id": "tenant_123",
    "settings": {
        "ehr_system": "epic",
        "compliance_level": "hipaa",
        "automation_enabled": True,
        "integrations": {
            "email": True,
            "sms": True,
            "whatsapp": True
        }
    }
}
```

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
python -m pytest shared/tests/

# Run specific module tests
python -m pytest shared/tests/test_healthcare_module.py

# Run integration tests
python -m pytest shared/tests/test_integration.py
```

### Integration Tests

```bash
# Test communication integrations
python -m pytest shared/tests/test_communication_integrations.py

# Test automation workflows
python -m pytest shared/tests/test_workflows.py
```

## 📚 Documentation

- [Industry Automation Processes Guide](../docs/industry-automation-processes.md)
- [Shared Library Capabilities Mapping](../docs/shared-library-capabilities-mapping.md)
- [Current Access Patterns](../docs/current-access-patterns.md)
- [Frontend Integration Guide](../docs/frontend-integration-guide.md)
- [Comprehensive Implementation Task List](../docs/comprehensive-implementation-task-list.md)

## 🤝 Contributing

1. Follow the established architecture patterns
2. Add comprehensive unit tests for new features
3. Update documentation for any API changes
4. Ensure compliance with industry standards (HIPAA, PCI, etc.)

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For support and questions:

- Check the documentation in the `docs/` directory
- Review the comprehensive task list for implementation status
- Contact the development team for specific issues
