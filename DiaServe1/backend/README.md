# EstateFlow Backend

Modern Real Estate Property Management SaaS Platform with AI-powered features, multi-currency support, and integrated communication campaigns.

## Overview

EstateFlow is a comprehensive property management solution designed for real estate companies to streamline operations, automate workflows, and enhance customer engagement through AI-powered features.

## Core Features

### 1. Property & Listing Management
- **Create and Manage Listings**: Full CRUD operations for property listings
- **Multi-Currency Support**:
  - Set prices in one base currency (e.g., USD)
  - Automatic conversion and display in local currencies
  - Real-time exchange rate updates
  - Currency preferences per organization
- **Rich Media Support**: Images, videos, virtual tours, floor plans
- **Property Categories**: Residential, commercial, land, rental, sale
- **Custom Fields**: Flexible property attributes and metadata

### 2. AI-Powered Features

#### Voice AI Agent for Real Estate
24/7 phone agent that can:
- Answer property questions
- Schedule property tours
- Provide detailed listing information
- Follow up with leads automatically
- Collect buyer requirements and preferences
- Intelligent handoff to human agents when needed
- Multi-language support

#### AI Chat Agent (Embedded in Listings)
Visitors can interact naturally with listings:
- "Is it close to a good school?"
- "Can I keep a dog?"
- "How much loan do I need?"
- "Is this neighborhood safe?"

AI responds instantly using:
- Structured listing data
- Neighborhood information
- General real estate knowledge
- Historical data and trends

#### AI Property Search Concierge
Natural language search that understands:
- "3-bedroom near a good school with a big kitchen under €1,500"
- "An apartment close to public transport that has a balcony and allows pets"

Features:
- NLP parsing to structured filters
- Intelligent scoring and ranking based on user intent
- Smart alternatives when exact matches don't exist
- Learning from user interactions

#### AI Listing Enhancer
Automatic marketing content generation:
- High-performing listing descriptions
- Title variants optimized for engagement
- Social media ad copy (Facebook, Instagram, LinkedIn)
- Blog posts about properties
- Email marketing campaigns
- WhatsApp broadcast messages

Audience-specific variants:
- Investor-focused copy
- Family-oriented descriptions
- Student housing messaging
- Luxury buyer positioning

#### AI Document Automation
Generate professional documents instantly:
- Lease agreements
- Offer letters
- Tenant screening summaries
- Rental applications
- Maintenance reports
- Move-in/out inspection checklists
- Property valuation reports

All with auto-populated variables from property and tenant profiles.

#### AI Property Manager Assistant
Automated property management:
- Auto-respond to tenant maintenance requests
- Classify request urgency (low, medium, high, emergency)
- Assign tasks to appropriate maintenance vendors
- Generate invoices automatically
- Follow up with tenants and vendors
- Notify landlord with executive summaries
- Track resolution time and satisfaction

### 3. Communication Campaigns

#### Multi-Channel Campaigns
- **Voice Campaigns**: Automated voice calls with natural speech
- **SMS Campaigns**: Bulk SMS with personalization
- **WhatsApp Campaigns**: Rich media messaging via WhatsApp Business
- **Email Campaigns**: Professional email marketing with templates

#### Campaign Features
- Segmentation by property type, location, buyer preferences
- A/B testing for messages
- Scheduling and automation
- Analytics and conversion tracking
- Drip campaign sequences
- Lead nurturing workflows

### 4. Integrations

#### Email Integration
- Gmail, Outlook, Exchange
- Two-way sync
- Email tracking
- Template management

#### Calendar Integration
- Google Calendar, Outlook Calendar
- Automated tour scheduling
- Availability management
- Reminder notifications

#### HubSpot Integration
- Contact synchronization
- Deal pipeline management
- Activity tracking
- Lead scoring

#### QuickBooks Integration
- Invoice synchronization
- Payment tracking
- Expense management
- Financial reporting
- Tax document generation

### 5. Booking & Scheduling
- Property tour scheduling
- Viewing appointment management
- Calendar sync across all channels
- Automated reminders (email, SMS, WhatsApp)
- Rescheduling and cancellation handling
- Waitlist management
- Agent availability tracking

### 6. Invoicing & Receipting
- Professional invoice generation
- Recurring invoices for rentals
- Payment terms and schedules
- Automated receipt generation
- Multi-currency invoicing
- Tax calculations
- Payment reminders

### 7. Payment Processing
- **Direct Contract Integration**: Payments automatically update contract status
- **Multiple Payment Methods**:
  - Credit/Debit cards
  - Bank transfers
  - Digital wallets
  - Cryptocurrency (optional)
- **Payment Plans**: Installment and milestone-based payments
- **Security Deposits**: Automated handling and refunds
- **Commission Tracking**: Agent commission calculations

### 8. Multi-Tenancy & Organization Management
- **Organization Scoping**: All data isolated per organization
- **Role-Based Access Control**: Admin, Manager, Agent, Viewer roles
- **Universal Admin**: Can switch between organizations
- **Team Management**: User invitations and permissions
- **White-Labeling**: Custom branding per organization

## Technical Architecture

### Backend Stack
- **Framework**: FastAPI (Python 3.11+)
- **Database**: MongoDB (document storage)
- **Authentication**: Supabase Auth
- **Real-time**: WebSocket support
- **File Storage**: Local storage with S3 compatibility
- **Task Queue**: Background job processing

### API Structure
```
/api/v1/
├── properties/          # Property CRUD operations
├── listings/            # Listing management
├── campaigns/           # Communication campaigns
│   ├── voice/
│   ├── sms/
│   ├── whatsapp/
│   └── email/
├── bookings/            # Tour and viewing bookings
├── invoices/            # Invoice management
├── payments/            # Payment processing
├── contracts/           # Contract management
├── integrations/        # Third-party integrations
│   ├── email/
│   ├── calendar/
│   ├── hubspot/
│   └── quickbooks/
├── ai/                  # AI-powered features
│   ├── voice-agent/
│   ├── chat-agent/
│   ├── search/
│   ├── content-generator/
│   └── document-automation/
├── organizations/       # Organization management
├── users/               # User management
└── analytics/           # Reporting and analytics
```

### Shared Services
EstateFlow uses shared services from `@apps/shared/`:
- Organization service (multi-tenancy)
- Billing service (subscription management)
- TTS service (text-to-speech)
- ASR service (speech-to-text)
- LLM service (AI language models)
- Voice library (voice cloning)
- Provider management

## Installation & Setup

### Prerequisites
- Python 3.11+
- MongoDB
- Supabase account
- Node.js 18+ (for frontend)

### Backend Setup

1. **Install Dependencies**:
   ```bash
   cd /opt/kasaai/apps/estateflow/backend
   source /opt/kasaai/apps/venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   Create `/opt/kasaai/.env` with:
   ```env
   MONGODB_URL=mongodb://admin:password@127.0.0.1:27017/
   SUPABASE_URL=https://supabase.ailabsafrica.com
   SUPABASE_KEY=your_supabase_key
   SUPABASE_JWT_SECRET=your_jwt_secret
   OPENAI_API_KEY=your_openai_key
   ANTHROPIC_API_KEY=your_anthropic_key
   ```

3. **Run Development Server**:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 30037 --reload
   ```

### Production Deployment

1. **Install Nginx Configuration**:
   ```bash
   sudo cp /tmp/estateflow-api.ailabsafrica.com.conf /etc/nginx/sites-available/
   sudo cp /tmp/estateflow.ailabsafrica.com.conf /etc/nginx/sites-available/
   sudo ln -s /etc/nginx/sites-available/estateflow-api.ailabsafrica.com.conf /etc/nginx/sites-enabled/
   sudo ln -s /etc/nginx/sites-available/estateflow.ailabsafrica.com.conf /etc/nginx/sites-enabled/
   ```

2. **Obtain SSL Certificates**:
   ```bash
   sudo certbot --nginx -d estateflow-api.ailabsafrica.com
   sudo certbot --nginx -d estateflow.ailabsafrica.com
   ```

3. **Install Systemd Service**:
   ```bash
   sudo cp /tmp/kasaai-estateflow-backend.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable kasaai-estateflow-backend
   sudo systemctl start kasaai-estateflow-backend
   ```

4. **Test Nginx Configuration**:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Verify Installation

```bash
# Check service status
sudo systemctl status kasaai-estateflow-backend

# View logs
sudo journalctl -u kasaai-estateflow-backend -f

# Test API endpoint
curl https://estateflow-api.ailabsafrica.com/health
```

## Infrastructure

### Live Server (148.251.0.46)
- **Backend**: Port 30039
- **Service**: kasaai-estateflow-backend.service
- **API URL**: https://estateflow-api.ailabsafrica.com
- **Frontend URL**: https://estateflow.ailabsafrica.com
- **Database**: MongoDB (estateflow)

### API Endpoints
- **Docs**: https://estateflow-api.ailabsafrica.com/docs
- **ReDoc**: https://estateflow-api.ailabsafrica.com/redoc
- **OpenAPI**: https://estateflow-api.ailabsafrica.com/openapi.json
- **Health**: https://estateflow-api.ailabsafrica.com/health

## Development

### Adding New Features

1. **Create Router Module**: `app/api/[feature]/router.py`
2. **Create Service Module**: `app/services/[feature]/service.py`
3. **Create Models**: `app/models/[feature].py`
4. **Add Tests**: `tests/test_[feature].py`
5. **Update API Router**: Include in `app/api/__init__.py`

### Code Organization

```
backend/
├── app/
│   ├── api/                 # API routers
│   │   ├── properties/
│   │   ├── listings/
│   │   ├── campaigns/
│   │   └── ...
│   ├── services/            # Business logic
│   │   ├── property_service.py
│   │   ├── campaign_service.py
│   │   └── ...
│   ├── models/              # Pydantic models
│   │   ├── property.py
│   │   ├── listing.py
│   │   └── ...
│   ├── core/                # Core functionality
│   │   ├── database.py
│   │   ├── auth.py
│   │   └── config.py
│   └── main.py              # Application entry point
├── tests/                   # Unit and integration tests
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Testing

EstateFlow has a comprehensive test suite with **68+ tests** covering all critical functionality.

#### Test Coverage
- ✅ **Agent Management**: CRUD operations, auto-assignment, availability (15 tests)
- ✅ **Booking System**: Lifecycle, status transitions, reminders (33 tests)
- ✅ **Notifications**: Email templates and delivery (10 tests)
- ✅ **Reminder Worker**: Scheduling and processing (10 tests)
- ✅ **Property Management**: CRUD, search, filters (existing tests)

#### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test modules
pytest tests/test_agents.py -v
pytest tests/test_bookings.py -v
pytest tests/test_notifications.py -v
pytest tests/test_reminders.py -v

# Run by category
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests only
pytest -m "not slow"     # Skip slow tests
```

#### Test Documentation
See [tests/README.md](tests/README.md) for comprehensive testing documentation including:
- Test structure and organization
- Writing new tests
- Fixtures and utilities
- Troubleshooting guide
- Coverage goals

## Currency Management

EstateFlow implements sophisticated multi-currency support:

1. **Base Currency**: Each organization sets a base currency (USD, EUR, etc.)
2. **Exchange Rates**: Real-time rates from external API
3. **Automatic Conversion**: Prices displayed in visitor's preferred currency
4. **Historical Tracking**: Rate changes logged for audit purposes
5. **Manual Overrides**: Ability to set custom rates for specific properties

## Security

- **Authentication**: Supabase-based JWT authentication
- **Authorization**: Role-based access control (RBAC)
- **Data Isolation**: Organization-scoped data access
- **Input Validation**: Pydantic models for all inputs
- **SQL Injection Prevention**: MongoDB parameterized queries
- **CORS**: Configured for specific domains only
- **Rate Limiting**: API rate limits per organization
- **Audit Logging**: All actions logged with user attribution

## Monitoring & Logging

- **Application Logs**: Structured logging to stdout/journald
- **Nginx Logs**: Access and error logs in `/var/log/nginx/`
- **Health Checks**: `/health` endpoint for monitoring
- **Metrics**: Response times, error rates, resource usage

## Support & Documentation

- **API Documentation**: Available at `/docs` endpoint
- **User Guide**: Coming soon
- **Developer Guide**: This README
- **Issue Tracking**: Internal ticketing system

## License

Proprietary - AI Labs Africa

## Version

**v1.0.0** - Initial release with core features

---

**Last Updated**: December 11, 2025
