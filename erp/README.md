# KasaAI ERP - Enterprise Resource Planning System

A comprehensive, organization-scoped ERP system built with FastAPI and React.

## Features

### Core Modules

1. **Finance & Accounting**
   - Chart of accounts
   - Transaction management
   - Invoicing
   - Expense tracking
   - Financial reporting

2. **Human Resources**
   - Employee management
   - Employee onboarding workflows (department-specific)
   - Payroll processing
   - Benefits administration
   - Recruitment tracking

3. **Customer Relationship Management (CRM)**
   - Customer database
   - Lead tracking
   - Opportunity management
   - Contact management

4. **Project Management**
   - Project tracking
   - Task management
   - Resource allocation
   - Time tracking

5. **Partnership Management**
   - Partnership tracking (vendor, technology, strategic, reseller, distributor, affiliate, consulting)
   - Partnership stages (prospect to active lifecycle)
   - Contact management (primary and secondary)
   - Proposal and contract management
   - Document uploads (proposals, contracts, supporting documents)
   - Interaction tracking (emails, calls, meetings, video calls)
   - Financial tracking (expected/actual revenue, payment terms, revenue share)
   - Statistics and reporting
   - Follow-up reminders

6. **Business Intelligence**
   - Custom reports
   - Dashboards
   - KPI tracking

7. **Integration & Automation**
   - Third-party integrations
   - Workflow automation
   - Audit logging

8. **Security & Compliance**
   - Organization-scoped data
   - Role-based access control
   - Audit trails

## Architecture

### Organization Management
- All data is scoped to organizations
- Users can belong to multiple organizations
- Universal admins can switch between any organization
- Regular users see only their organizations

### Tech Stack

**Backend:**
- FastAPI (Python)
- MongoDB (Database)
- Motor (Async MongoDB driver)
- Supabase (Authentication)
- Pydantic (Data validation)

**Frontend:**
- React 18
- TypeScript
- Tailwind CSS
- React Router
- Axios
- Zustand (State management)

## Installation

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv /opt/kasaai/apps/venv
source /opt/kasaai/apps/venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your API URL

# Run development server
npm run dev

# Build for production
npm run build
```

## Deployment

### Production Deployment

**Port:** 30034
**API URL:** https://erp-api.ailabsafrica.com
**Frontend URL:** https://erp.ailabsafrica.com
**Database:** MongoDB (`erp` database)

### Service Configuration

```bash
# Backend systemd service
sudo systemctl start kasaai-erp-backend
sudo systemctl enable kasaai-erp-backend

# View logs
sudo journalctl -u kasaai-erp-backend -f
```

## Usage

### Creating an Organization

1. Sign in with Supabase credentials
2. Navigate to Admin > Organizations tab
3. Click "New Organization"
4. Fill in organization details
5. You become the admin of the new organization

### Switching Organizations

1. Use the organization selector in the top navigation bar
2. Select the organization you want to work with
3. All data will be filtered to that organization

### Managing Users

1. Navigate to Admin > Users tab
2. View all users in the current organization
3. Admins can update user roles and permissions

## API Documentation

FastAPI provides interactive API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Security

### Authentication
- Supabase JWT-based authentication
- Tokens included in all API requests

### Authorization
- Organization-scoped data access
- Role-based permissions (admin/user)
- Universal admin role for platform administrators

### Data Isolation
- All database queries filter by organization_id
- Users can only access their organization's data
- Universal admins can access all organizations

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Project Structure

```
erp/
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Database, auth
│   │   ├── models/        # Data models
│   │   └── main.py        # FastAPI app
│   ├── tests/             # Unit tests
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/    # Reusable components
    │   ├── contexts/      # React contexts
    │   ├── pages/         # Page components
    │   ├── lib/           # Utilities
    │   └── App.tsx
    └── package.json
```

## Feature Highlights

### Partnership Management

The Partnership Management module provides comprehensive tools for tracking and managing business partnerships:

**Key Features:**
- **Partnership Lifecycle Management**: Track partnerships from prospect stage through to active partnerships
- **Contact Management**: Store primary and secondary contacts with full details
- **Document Management**: Upload and manage proposals, contracts, and supporting documents
- **Interaction Tracking**: Record all interactions (emails, calls, meetings, video calls)
- **Financial Tracking**: Monitor expected revenue, actual revenue, payment terms, and revenue share percentages
- **Statistics Dashboard**: View partnership metrics, revenue totals, and interaction counts

**Partnership Types:**
- Vendor
- Technology
- Strategic
- Reseller
- Distributor
- Affiliate
- Consulting

**Partnership Stages:**
- Prospect
- Initial Contact
- Discussion
- Proposal Sent
- Negotiation
- Agreement Signed
- Active
- On Hold
- Inactive
- Terminated

**Usage:**
1. Navigate to Partnerships page
2. Click "New Partnership" to create a partnership
3. Fill in partner details, contacts, and proposal information
4. Upload proposal and contract documents
5. Track interactions by clicking on a partnership and recording interactions
6. Monitor progress through the Statistics tab
7. Update partnership stage as it progresses

**API Endpoints:**
- `POST /api/v1/partnerships/partnerships` - Create partnership
- `GET /api/v1/partnerships/partnerships` - List partnerships (with search, stage, and type filters)
- `GET /api/v1/partnerships/partnerships/{id}` - Get partnership details
- `PATCH /api/v1/partnerships/partnerships/{id}` - Update partnership
- `DELETE /api/v1/partnerships/partnerships/{id}` - Delete partnership (soft delete)
- `POST /api/v1/partnerships/partnerships/{id}/upload-proposal` - Upload proposal file
- `POST /api/v1/partnerships/partnerships/{id}/upload-contract` - Upload contract file
- `POST /api/v1/partnerships/partnerships/{id}/upload-document` - Upload other documents
- `POST /api/v1/partnerships/partnerships/interactions` - Record interaction
- `GET /api/v1/partnerships/partnerships/{id}/interactions` - List interactions
- `GET /api/v1/partnerships/partnerships/stats/summary` - Get statistics

## Documentation

- **[Employee Onboarding Guide](./EMPLOYEE_ONBOARDING.md)** - Complete guide for the employee onboarding system
- **[Planning Document](./PLANNING.md)** - Architecture and planning details
- **[Tasks & Progress](./TASKS.md)** - Development progress tracker

## License

Proprietary - KasaAI / AI Labs Africa

## Support

For support, contact: support@ailabsafrica.com
