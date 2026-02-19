# ERP System Planning Document

## Overview

A comprehensive, organization-scoped Enterprise Resource Planning system for managing all aspects of business operations.

## Core Requirements

### Multi-Tenancy
- All data scoped to organizations
- Users can belong to multiple organizations
- Universal admins can access all organizations
- Clear organization switching UX

### Modules

1. **Finance & Accounting**
   - General ledger with chart of accounts
   - Accounts payable/receivable
   - Invoicing system
   - Expense management
   - Financial reporting

2. **Human Resources**
   - Employee database
   - Payroll processing
   - Benefits administration
   - Recruitment tracking
   - Performance management

3. **CRM**
   - Customer management
   - Lead tracking
   - Opportunity pipeline
   - Contact management
   - Sales forecasting

4. **Project Management**
   - Project tracking
   - Task management
   - Resource allocation
   - Time tracking
   - Cost analysis

5. **Business Intelligence**
   - Custom reports
   - Dashboard builder
   - KPI tracking
   - Data visualization

6. **Integration & Automation**
   - Third-party integrations
   - Workflow automation
   - API access

7. **Security & Compliance**
   - Role-based access control
   - Audit logging
   - Data encryption
   - Compliance reporting

## Technology Stack

### Backend
- FastAPI (Python web framework)
- MongoDB (NoSQL database)
- Pydantic (Data validation)
- Supabase (Authentication)

### Frontend
- React 18 + TypeScript
- Tailwind CSS
- React Router
- Axios (HTTP client)

### Infrastructure
- Nginx (Reverse proxy)
- Systemd (Process management)
- Let's Encrypt (SSL)

## Security Model

### Authentication
- Supabase JWT tokens
- Secure password hashing
- Session management

### Authorization
- Organization membership required
- Role-based permissions (admin/user)
- Universal admin override
- API endpoint protection

### Data Isolation
- All queries filter by organization_id
- Middleware validates organization access
- No cross-organization data leakage

## Database Schema

All collections include:
- `organization_id` (required)
- `created_at`, `updated_at`
- `created_by`, `updated_by`
- `is_active` (soft delete flag)

## Deployment

### Ports
- Backend: 30034
- Frontend: Served by Nginx (443)

### URLs
- API: https://erp-api.ailabsafrica.com
- Frontend: https://erp.ailabsafrica.com

### Process Management
- Systemd service: kasaai-erp-backend
- Auto-restart on failure
- Journal logging

## Future Enhancements

1. Real-time notifications
2. Mobile apps
3. Advanced reporting
4. AI-powered insights
5. Multi-currency support
6. Advanced workflow builder
7. Email integration
8. Calendar integration
9. Document management
10. Asset management
