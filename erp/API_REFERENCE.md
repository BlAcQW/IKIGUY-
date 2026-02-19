# KasaAI ERP - CRUD API Summary

**Base URL**: https://dev-erp-api.ailabsafrica.com
**API Version**: v1
**Prefix**: `/api/v1`

---

## 🏢 Organizations Module

**Base Path**: `/api/v1/organizations`

| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Organizations | `/organizations` | POST | ✅ Create | Create new organization (user becomes admin) |
| Organizations | `/organizations` | GET | ✅ Read | List user's organizations |
| Organization | `/organizations/{id}` | GET | ✅ Read | Get organization details |
| Organization | `/organizations/{id}` | PATCH | ✅ Update | Update organization (admin only) |
| Organization | `/organizations/{id}` | DELETE | ⚠️ Missing | Soft delete organization |
| **Members** | | | | |
| Members | `/organizations/{id}/users` | GET | ✅ Read | List organization members |
| Member | `/organizations/{id}/users/{user_id}` | PATCH | ✅ Update | Update member role |
| Member | `/organizations/{id}/users/{user_id}` | DELETE | ✅ Delete | Remove member from organization |

**CRUD Completeness**: 90% (Missing organization deletion)

---

## 👥 CRM Module

**Base Path**: `/api/v1/crm`

### Customers
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Customers | `/crm/customers` | POST | ✅ Create | Create new customer |
| Customers | `/crm/customers` | GET | ✅ Read | List customers (with search & pagination) |
| Customer | `/crm/customers/{id}` | GET | ✅ Read | Get customer by ID |
| Customer | `/crm/customers/{id}` | PATCH | ✅ Update | Update customer details |
| Customer | `/crm/customers/{id}` | DELETE | ✅ Delete | Soft delete customer |

**CRUD Completeness**: 100% ✅

### Leads
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Leads | `/crm/leads` | POST | ✅ Create | Create new lead |
| Leads | `/crm/leads` | GET | ✅ Read | List leads (with status filter) |
| Lead | `/crm/leads/{id}` | GET | ⚠️ Missing | Get lead by ID |
| Lead | `/crm/leads/{id}` | PATCH | ⚠️ Missing | Update lead |
| Lead | `/crm/leads/{id}` | DELETE | ⚠️ Missing | Delete lead |

**CRUD Completeness**: 40% (Missing read single, update, delete)

### Opportunities
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Opportunities | `/crm/opportunities` | POST | ✅ Create | Create new opportunity |
| Opportunities | `/crm/opportunities` | GET | ✅ Read | List opportunities |
| Opportunity | `/crm/opportunities/{id}` | GET | ⚠️ Missing | Get opportunity by ID |
| Opportunity | `/crm/opportunities/{id}` | PATCH | ⚠️ Missing | Update opportunity |
| Opportunity | `/crm/opportunities/{id}` | DELETE | ⚠️ Missing | Delete opportunity |

**CRUD Completeness**: 40% (Missing read single, update, delete)

### Contacts
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Contacts | `/crm/contacts` | POST | ✅ Create | Create new contact |
| Contacts | `/crm/contacts` | GET | ✅ Read | List contacts (filter by customer) |
| Contact | `/crm/contacts/{id}` | GET | ⚠️ Missing | Get contact by ID |
| Contact | `/crm/contacts/{id}` | PATCH | ⚠️ Missing | Update contact |
| Contact | `/crm/contacts/{id}` | DELETE | ⚠️ Missing | Delete contact |

**CRUD Completeness**: 40% (Missing read single, update, delete)

---

## 💼 HR Module

**Base Path**: `/api/v1/hr`

### Employees
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Employees | `/hr/employees` | POST | ✅ Create | Create new employee |
| Employees | `/hr/employees` | GET | ✅ Read | List employees |
| Employee | `/hr/employees/{id}` | GET | ✅ Read | Get employee by ID |
| Employee | `/hr/employees/{id}` | PATCH | ⚠️ Missing | Update employee |
| Employee | `/hr/employees/{id}` | DELETE | ⚠️ Missing | Delete employee |

**CRUD Completeness**: 60% (Missing update, delete)

### Payroll
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Payroll | `/hr/payroll` | POST | ✅ Create | Create payroll record |
| Payroll | `/hr/payroll` | GET | ✅ Read | List payroll (filter by employee) |

**CRUD Completeness**: 40% (Create + Read only)

### Benefits
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Benefits | `/hr/benefits` | GET | ✅ Read | List benefits |

**CRUD Completeness**: 20% (Read only)

### Recruitment
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Recruitment | `/hr/recruitment` | POST | ✅ Create | Create job opening |
| Recruitment | `/hr/recruitment` | GET | ✅ Read | List job openings |

**CRUD Completeness**: 40% (Create + Read only)

---

## 💰 Finance Module

**Base Path**: `/api/v1/finance`

### Accounts
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Accounts | `/finance/accounts` | POST | ✅ Create | Create new account |
| Accounts | `/finance/accounts` | GET | ✅ Read | List accounts |

**CRUD Completeness**: 40% (Create + Read only)

### Transactions
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Transactions | `/finance/transactions` | POST | ✅ Create | Create new transaction |
| Transactions | `/finance/transactions` | GET | ✅ Read | List transactions |

**CRUD Completeness**: 40% (Create + Read only)

### Invoices
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Invoices | `/finance/invoices` | POST | ✅ Create | Create new invoice |
| Invoices | `/finance/invoices` | GET | ✅ Read | List invoices |

**CRUD Completeness**: 40% (Create + Read only)

### Expenses
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Expenses | `/finance/expenses` | POST | ✅ Create | Create new expense |
| Expenses | `/finance/expenses` | GET | ✅ Read | List expenses |

**CRUD Completeness**: 40% (Create + Read only)

---

## 📊 Projects Module

**Base Path**: `/api/v1/projects`

### Projects
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Projects | `/projects` | POST | ✅ Create | Create new project |
| Projects | `/projects` | GET | ✅ Read | List projects |

**CRUD Completeness**: 40% (Create + Read only)

### Tasks
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Tasks | `/projects/tasks` | POST | ✅ Create | Create new task |
| Tasks | `/projects/tasks` | GET | ✅ Read | List tasks |

**CRUD Completeness**: 40% (Create + Read only)

### Resources
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Resources | `/projects/resources` | POST | ✅ Create | Allocate resource |
| Resources | `/projects/resources` | GET | ✅ Read | List resources |

**CRUD Completeness**: 40% (Create + Read only)

### Timesheets
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Timesheets | `/projects/timesheets` | POST | ✅ Create | Create timesheet entry |
| Timesheets | `/projects/timesheets` | GET | ✅ Read | List timesheets |

**CRUD Completeness**: 40% (Create + Read only)

---

## 📈 Business Intelligence Module

**Base Path**: `/api/v1/bi`

### Reports
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Reports | `/bi/reports` | POST | ✅ Create | Create new report |
| Reports | `/bi/reports` | GET | ✅ Read | List reports |

**CRUD Completeness**: 40% (Create + Read only)

### Dashboards
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Dashboards | `/bi/dashboards` | POST | ✅ Create | Create new dashboard |
| Dashboards | `/bi/dashboards` | GET | ✅ Read | List dashboards |

**CRUD Completeness**: 40% (Create + Read only)

### KPIs
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| KPIs | `/bi/kpis` | POST | ✅ Create | Create new KPI |
| KPIs | `/bi/kpis` | GET | ✅ Read | List KPIs |

**CRUD Completeness**: 40% (Create + Read only)

---

## ⚙️ System Module

**Base Path**: `/api/v1/system`

### Integrations
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Integrations | `/system/integrations` | POST | ✅ Create | Create integration |
| Integrations | `/system/integrations` | GET | ✅ Read | List integrations |

**CRUD Completeness**: 40% (Create + Read only)

### Workflows
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Workflows | `/system/workflows` | POST | ✅ Create | Create workflow |
| Workflows | `/system/workflows` | GET | ✅ Read | List workflows |

**CRUD Completeness**: 40% (Create + Read only)

### Audit Logs
| Resource | Endpoint | Method | CRUD | Description |
|----------|----------|--------|------|-------------|
| Audit Logs | `/system/audit-logs` | GET | ✅ Read | List audit logs (read-only) |

**CRUD Completeness**: 20% (Read only - expected for audit logs)

---

## 📊 Overall CRUD Summary

### By Completeness Level

**100% Complete (Full CRUD)**:
- ✅ CRM Customers (5/5 operations)

**90%+ Complete**:
- ✅ Organizations (7/8 operations)

**60% Complete**:
- ⚠️ HR Employees (3/5 operations)

**40% Complete** (Create + Read only):
- ⚠️ CRM Leads, Opportunities, Contacts
- ⚠️ HR Payroll, Recruitment
- ⚠️ Finance Accounts, Transactions, Invoices, Expenses
- ⚠️ Projects, Tasks, Resources, Timesheets
- ⚠️ BI Reports, Dashboards, KPIs
- ⚠️ System Integrations, Workflows

**20% Complete** (Read only):
- ℹ️ HR Benefits
- ℹ️ System Audit Logs (intentionally read-only)

---

## 🔐 Authentication & Authorization

All endpoints require:
- **Authentication**: Supabase JWT token via `Authorization: Bearer <token>` header
- **Organization Context**: Most endpoints require `X-Organization-ID` header
- **Role-Based Access**: Some operations restricted to organization admins

---

## 🔍 Common Features Across Endpoints

### Pagination
Most list endpoints support:
- `skip`: Number of records to skip (default: 0)
- `limit`: Max records to return (default: 100, max: 1000)

### Filtering
- Organization-scoped by default
- Soft delete support (`is_active: true` filter)
- Resource-specific filters (e.g., `customer_id` for contacts)

### Search
- Regex-based search on key fields (where implemented)
- Case-insensitive matching

### Sorting
- Default: Newest first (`created_at: -1`)
- Resource-specific sorting (e.g., payroll by `pay_date`)

---

## 📝 Next Steps for Full CRUD Coverage

**High Priority** (Most Used Resources):
1. ✅ Add UPDATE/DELETE to CRM Leads
2. ✅ Add UPDATE/DELETE to CRM Opportunities
3. ✅ Add UPDATE/DELETE to CRM Contacts
4. ✅ Add UPDATE/DELETE to HR Employees
5. ✅ Add GET single to Finance resources

**Medium Priority**:
6. ✅ Add full CRUD to Projects
7. ✅ Add full CRUD to Tasks
8. ✅ Add full CRUD to Finance resources

**Low Priority**:
9. ✅ Add UPDATE/DELETE to BI resources
10. ✅ Add UPDATE/DELETE to System resources

---

## 🚀 Testing the APIs

### Get Access Token
```bash
curl -X POST 'https://supabase-api.ailabsafrica.com/auth/v1/token?grant_type=password' \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@ailabsafrica.com","password":"Admin@2024!"}'
```

### Create Organization
```bash
curl -X POST 'https://dev-erp-api.ailabsafrica.com/api/v1/organizations' \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Acme Corp",
    "description": "A test organization",
    "settings": {}
  }'
```

### Create Customer
```bash
curl -X POST 'https://dev-erp-api.ailabsafrica.com/api/v1/crm/customers' \
  -H 'Authorization: Bearer <token>' \
  -H 'X-Organization-ID: <org-id>' \
  -H 'Content-Type: application/json' \
  -d '{
    "company_name": "Client Corp",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@clientcorp.com",
    "phone": "+1234567890"
  }'
```

---

**Documentation Generated**: 2025-11-02
**API Status**: ✅ Operational
**Frontend**: https://dev-erp.ailabsafrica.com
**Backend**: https://dev-erp-api.ailabsafrica.com
**Swagger UI**: https://dev-erp-api.ailabsafrica.com/docs
