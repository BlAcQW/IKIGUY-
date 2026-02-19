# Integrated ERP System Enhancement Plan
## Complete Enterprise Resource Planning with CRM, Finance, HR, Projects, and Analytics Integration

**Created:** 2025-11-16
**Version:** 1.0
**Status:** Approved for Implementation

---

## 📋 EXECUTIVE SUMMARY

This comprehensive plan integrates the CRM Enhancement Plan with industry-standard ERP requirements to create a **fully integrated enterprise system** where all modules (CRM, Finance, HR, Projects, Analytics) work together with automated workflows, real-time dashboards, and centralized financial tracking.

**Current State:** 8 well-built but siloed modules (~40% integrated ERP)
**Target State:** Fully integrated enterprise system with automated workflows and real-time intelligence

**Total Estimated Timeline:** 16-20 weeks (4-5 months)
**Development Effort:** Backend (10 weeks) + Frontend (8 weeks) + Testing (2 weeks)

---

## 🔍 CURRENT STATE ANALYSIS

### Existing Modules (8 Total)

1. **Finance & Accounting** ✅ Well Developed
2. **Human Resources** ✅ Well Developed
3. **CRM** ✅ Well Developed
4. **Projects** ⚠️ Partially Developed
5. **Business Intelligence** ⚠️ Basic Structure Only
6. **Partnerships** ✅ Well Developed
7. **Legal/Documents** ✅ Well Developed
8. **Onboarding** ✅ Well Developed

### Critical Integration Gaps

❌ **NO Automated Workflows** between modules
❌ **NO Central Financial Ledger** integration
❌ **Dashboard shows FAKE DATA** (hardcoded values)
❌ **NO Conversion Workflows** (Lead→Opp, Opp→Customer)
❌ **NO Activity/Interaction Tracking** in CRM
❌ **NO Project-to-Finance** cost tracking
❌ **NO Payroll-to-Finance** integration
❌ **NO Cross-Module Analytics**

**Gap Assessment:** Currently at ~40% of a fully integrated enterprise ERP system. Strong individual modules but weak integration layer.

---

## 🎯 INTEGRATION PRIORITIES

### PHASE 1: Financial Integration Foundation (Weeks 1-4)
**Goal:** Make Finance the central hub - all revenue and costs flow through General Ledger

#### 1.1 Automatic Journal Entry Engine

**New Service:** `/opt/kasaai/apps/erp/backend/app/services/journal_entry_service.py`

Implement double-entry bookkeeping automation:

```python
class JournalEntryService:
    """
    Automated journal entry creation from source documents.
    Implements double-entry bookkeeping rules.
    """

    async def create_invoice_entries(self, invoice_id: str):
        """
        When invoice is created:
        DR Accounts Receivable (Asset) - invoice.total_amount
        CR Revenue (Revenue) - invoice.subtotal
        CR Sales Tax Payable (Liability) - invoice.tax_amount

        Tags transaction with: invoice_id, customer_id, invoice_number
        """
        pass

    async def create_expense_entries(self, expense_id: str):
        """
        When expense is approved:
        DR Expense Account (Expense) - expense.amount
        CR Cash or Accounts Payable (Asset/Liability) - expense.amount

        If reimbursement:
        DR Expense Account
        CR Employee Reimbursement Payable

        Tags transaction with: expense_id, employee_id, project_id
        """
        pass

    async def create_payroll_entries(self, payroll_id: str):
        """
        When payroll is processed:
        DR Payroll Expense (Expense) - gross_pay
        CR Employee Tax Payable (Liability) - tax deductions
        CR Employee Benefits Payable (Liability) - benefit deductions
        CR Retirement Contribution Payable (Liability) - retirement
        CR Cash (Asset) - net_pay

        Tags transaction with: payroll_id, employee_id, pay_period
        """
        pass

    async def create_project_cost_entries(self, project_id: str, period: str):
        """
        Monthly project cost accrual:
        DR Project Cost Account (Expense) - labor + expenses
        CR Accrued Labor Cost (Liability) - labor costs
        CR Cash (Asset) - expenses paid

        Tags transaction with: project_id, period
        """
        pass

    async def create_payment_entries(self, payment_id: str):
        """
        When payment received on invoice:
        DR Cash (Asset) - payment.amount
        CR Accounts Receivable (Asset) - payment.amount

        Tags transaction with: payment_id, invoice_id, customer_id
        """
        pass

    async def update_account_balance(self, account_id: str):
        """
        Recalculate account balance from all transactions.

        For Asset/Expense accounts:
        Balance = sum(debits) - sum(credits)

        For Liability/Equity/Revenue accounts:
        Balance = sum(credits) - sum(debits)

        Update Account.balance field and log balance change.
        """
        pass
```

#### 1.2 Real-Time Account Balance Updates

Implement automatic balance updates triggered by:
- Transaction creation
- Transaction deletion
- Transaction modification
- Period close/reopen

#### 1.3 Financial Reports with Real Data

**Update:** `/opt/kasaai/apps/erp/backend/app/api/routes/financial_reports.py`

Replace static calculations with real transaction aggregation:

```python
@router.get("/reports/profit-loss", response_model=ProfitLossResponse)
async def generate_profit_loss_statement(
    start_date: datetime,
    end_date: datetime,
    org_scoped = Depends(OrganizationScoped)
):
    """
    Generate P&L from actual transactions.

    Revenue:
      - Aggregate all Revenue account transactions in period
      - Group by revenue account (Sales, Service Revenue, etc.)

    Expenses:
      - Aggregate all Expense account transactions in period
      - Group by expense category (Payroll, Marketing, etc.)

    Net Income = Total Revenue - Total Expenses
    """
    pass

@router.get("/reports/balance-sheet", response_model=BalanceSheetResponse)
async def generate_balance_sheet(
    as_of_date: datetime,
    org_scoped = Depends(OrganizationScoped)
):
    """
    Generate Balance Sheet from account balances as of date.

    Assets = Liabilities + Equity

    Pull current balances from Account.balance for all accounts.
    """
    pass

@router.get("/reports/cash-flow", response_model=CashFlowResponse)
async def generate_cash_flow_statement(
    start_date: datetime,
    end_date: datetime,
    org_scoped = Depends(OrganizationScoped)
):
    """
    Generate Cash Flow Statement.

    Operating Activities:
      - Cash from customers (invoice payments)
      - Cash to suppliers (expense payments)
      - Cash for payroll

    Investing Activities:
      - Asset purchases/sales

    Financing Activities:
      - Loans, equity
    """
    pass
```

**Deliverables:**
- ✅ Journal entry automation engine
- ✅ Account balance auto-update service
- ✅ Real-time financial report endpoints
- ✅ Transaction audit logging
- ✅ Migration script for existing data

---

### PHASE 2: CRM-Finance Integration (Weeks 5-7)
**Goal:** Automate revenue recognition from sales pipeline

#### 2.1 Opportunity Won → Invoice Automation

**New Endpoint:** `POST /crm/opportunities/{opp_id}/mark-won`

```python
async def mark_opportunity_won(
    opportunity_id: str,
    request: MarkWonRequest,
    org_scoped = Depends(OrganizationScoped)
):
    """
    Mark opportunity as won and trigger invoice creation.

    Workflow:
    1. Update Opportunity.stage = CLOSED_WON
    2. Set Opportunity.closed_date = now
    3. If no customer_id, create Customer from opportunity data
    4. Create Invoice with amount from opportunity.amount
    5. Create journal entry (DR AR, CR Revenue)
    6. Update Customer.lifetime_value += opportunity.amount
    7. Log system activity: "Opportunity won"
    8. Optionally create Project if request.create_project = True
    9. Return created invoice and customer
    """
    pass
```

**Request Schema:**
```python
class MarkWonRequest(BaseModel):
    create_project: bool = Field(default=False)
    project_name: Optional[str] = None
    invoice_due_days: int = Field(default=30)
    invoice_notes: Optional[str] = None
```

#### 2.2 Lead/Opportunity Conversion Workflows

**A. Lead → Opportunity Conversion**

**Endpoint:** `POST /crm/leads/{lead_id}/convert-to-opportunity`

```python
class LeadToOpportunityConversionRequest(BaseModel):
    opportunity_name: str = Field(..., description="Deal name")
    amount: float = Field(..., description="Expected deal value")
    probability: int = Field(default=25, ge=0, le=100)
    stage: OpportunityStage = Field(default=OpportunityStage.PROSPECTING)
    expected_close_date: Optional[datetime] = None
    description: Optional[str] = None
    keep_lead_active: bool = Field(default=False)

async def convert_lead_to_opportunity(lead_id, request):
    """
    1. Validate lead exists and status allows conversion
    2. Create Opportunity with lead data
    3. Set opportunity.lead_id = lead.id
    4. Copy lead contact info to opportunity
    5. Update lead.status = CONVERTED (unless keep_lead_active)
    6. Set lead.converted_at = now
    7. Log system activity: "Converted to opportunity"
    8. Return created opportunity
    """
```

**B. Lead → Customer Conversion**

**Endpoint:** `POST /crm/leads/{lead_id}/convert-to-customer`

```python
class LeadToCustomerConversionRequest(BaseModel):
    customer_type: CustomerType = Field(default=CustomerType.INDIVIDUAL)
    company_name: Optional[str] = None
    create_contact: bool = Field(default=True)
    account_manager: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

async def convert_lead_to_customer(lead_id, request):
    """
    1. Validate lead exists
    2. Create Customer from lead data
    3. If create_contact, create Contact record
    4. Update lead.status = CONVERTED
    5. Set lead.converted_to_customer_id = customer.id
    6. Set lead.converted_at = now
    7. Log system activity: "Converted to customer"
    8. Return created customer
    """
```

**C. Opportunity → Customer Conversion**

**Endpoint:** `POST /crm/opportunities/{opp_id}/convert-to-customer`

```python
class OpportunityToCustomerConversionRequest(BaseModel):
    create_new_customer: bool = Field(default=True)
    existing_customer_id: Optional[str] = None
    customer_type: CustomerType = Field(default=CustomerType.BUSINESS)
    account_manager: Optional[str] = None
    create_invoice: bool = Field(default=True)
    create_project: bool = Field(default=False)

async def convert_opportunity_to_customer(opp_id, request):
    """
    1. Validate opportunity stage (should be CLOSED_WON)
    2. Create or link Customer
    3. Update opportunity.customer_id
    4. If create_invoice, generate invoice
    5. If create_project, create project record
    6. Update customer.lifetime_value
    7. Log system activity: "Created customer from won deal"
    8. Return customer (and invoice/project if created)
    """
```

#### 2.3 CRM Activity Tracking System

**New Model:** `/opt/kasaai/apps/erp/backend/app/models/crm.py`

```python
class ActivityType(str, Enum):
    """CRM activity types."""
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"
    SMS = "sms"
    TASK = "task"
    CONVERSION = "conversion"  # System-generated
    STATUS_CHANGE = "status_change"  # System-generated
    DOCUMENT = "document"
    PROPOSAL = "proposal"

class Activity(BaseModel):
    """
    Activity tracking for CRM entities.
    Records all interactions, notes, and system events.
    """

    # Entity linking
    entity_type: str = Field(..., description="lead, opportunity, customer, contact")
    entity_id: str = Field(..., description="ID of the entity")

    # Activity details
    activity_type: ActivityType
    subject: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    activity_date: datetime = Field(default_factory=datetime.utcnow)

    # User tracking
    created_by_user_id: str
    created_by_user_email: Optional[str] = None

    # Call-specific fields
    call_duration_minutes: Optional[int] = Field(None, ge=0)
    call_outcome: Optional[str] = None  # "connected", "voicemail", "no_answer", "busy"

    # Email-specific fields
    email_subject: Optional[str] = None
    email_to: Optional[List[str]] = Field(default_factory=list)
    email_cc: Optional[List[str]] = Field(default_factory=list)

    # Meeting-specific fields
    meeting_attendees: Optional[List[str]] = Field(default_factory=list)
    meeting_location: Optional[str] = None

    # Follow-up tracking
    follow_up_required: bool = Field(default=False)
    follow_up_date: Optional[datetime] = None
    follow_up_completed: bool = Field(default=False)
    follow_up_completed_at: Optional[datetime] = None

    # Attachments
    attachment_urls: List[str] = Field(default_factory=list)

    # System metadata
    is_system_generated: bool = Field(default=False)

    # Inherited from BaseModel:
    # id, organization_id, created_at, updated_at, is_active
```

**New Endpoints:**

```python
# Activity Management
POST /crm/activities  # Log new activity
GET /crm/activities  # List activities with filters
GET /crm/activities/{activity_id}  # Get activity details
PATCH /crm/activities/{activity_id}  # Update activity
DELETE /crm/activities/{activity_id}  # Delete activity

# Entity-specific
GET /crm/activities/timeline/{entity_type}/{entity_id}  # Full timeline
GET /crm/activities/upcoming-follow-ups  # Follow-ups due soon
PATCH /crm/activities/{activity_id}/complete-follow-up  # Mark follow-up done

# Statistics
GET /crm/activities/stats  # Activity statistics by type, user, period
```

#### 2.4 CRM Task/Todo System

**New Model:**

```python
class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class CRMTask(BaseModel):
    """
    Tasks and todos for CRM entities.
    Sales activities linked to leads, opportunities, customers.
    """

    # Entity linking
    entity_type: str = Field(..., description="lead, opportunity, customer")
    entity_id: str
    entity_name: Optional[str] = None  # Denormalized for display

    # Task details
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    task_type: str = Field(
        ...,
        description="call, email, meeting, demo, proposal, follow_up, other"
    )

    # Priority and status
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    status: str = Field(
        default="pending",
        description="pending, in_progress, completed, cancelled"
    )

    # Scheduling
    due_date: datetime
    reminder_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None

    # Assignment
    assigned_to: str  # User ID
    assigned_to_email: Optional[str] = None  # Denormalized
    assigned_by: Optional[str] = None

    # Completion
    completed_by: Optional[str] = None
    completion_notes: Optional[str] = None

    # Tracking
    estimated_duration_minutes: Optional[int] = None
    actual_duration_minutes: Optional[int] = None

    # Related entities
    related_activity_id: Optional[str] = None  # Link to activity if created from one

    # Inherited: id, organization_id, created_at, updated_at, is_active
```

**New Endpoints:**

```python
# Task Management
POST /crm/tasks  # Create task
GET /crm/tasks  # List tasks with filters
GET /crm/tasks/{task_id}  # Get task details
PATCH /crm/tasks/{task_id}  # Update task
DELETE /crm/tasks/{task_id}  # Delete task

# User-specific
GET /crm/tasks/my-tasks  # Current user's tasks
GET /crm/tasks/assigned-to/{user_id}  # Tasks assigned to specific user

# Actions
PATCH /crm/tasks/{task_id}/complete  # Mark complete
PATCH /crm/tasks/{task_id}/start  # Mark in progress
PATCH /crm/tasks/{task_id}/cancel  # Cancel task

# Entity-specific
GET /crm/tasks/for-entity/{entity_type}/{entity_id}  # All tasks for entity

# Statistics
GET /crm/tasks/stats  # Task completion rates, overdue count, etc.
```

#### 2.5 Enhanced Lead and Opportunity Models

**Lead Model Additions:**

```python
# Add to Lead model in crm.py
follow_up_date: Optional[datetime] = Field(
    None,
    description="Next scheduled follow-up date"
)
last_contacted: Optional[datetime] = Field(
    None,
    description="Last time contact was made"
)
next_action: Optional[str] = Field(
    None,
    max_length=200,
    description="Next action to take"
)
last_activity_id: Optional[str] = Field(
    None,
    description="Most recent activity ID"
)
activity_count: int = Field(
    default=0,
    description="Total number of activities logged"
)
```

**Opportunity Model Additions:**

```python
# Add to Opportunity model in crm.py
next_step_date: Optional[datetime] = Field(
    None,
    description="When the next step should be completed by"
)
last_activity_date: Optional[datetime] = Field(
    None,
    description="Last time there was activity on this opportunity"
)
activity_count: int = Field(
    default=0,
    description="Total number of activities logged"
)
days_in_current_stage: int = Field(
    default=0,
    description="Days in current stage (auto-calculated)"
)
```

**Deliverables:**
- ✅ 3 conversion endpoints implemented and tested
- ✅ Activity model, endpoints, and UI components
- ✅ CRM Task model, endpoints, and dashboard widget
- ✅ Automated invoice creation from won opportunities
- ✅ Customer lifetime value auto-calculation
- ✅ Activity timeline component
- ✅ Frontend conversion modals and workflows

---

### PHASE 3: Project-Finance Integration (Weeks 8-10)
**Goal:** Track project profitability and automate billing

#### 3.1 Timesheet → Invoice Automation

**New Endpoint:** `POST /projects/{project_id}/generate-invoice`

```python
class GenerateInvoiceRequest(BaseModel):
    period_start: datetime
    period_end: datetime
    include_expenses: bool = Field(default=True)
    invoice_due_days: int = Field(default=30)
    notes: Optional[str] = None

async def generate_project_invoice(project_id, request):
    """
    Generate invoice from approved billable timesheets.

    Workflow:
    1. Find all approved billable timesheets in date range
    2. Find all billable expenses in date range
    3. Create invoice line items:
       - Timesheet: "{employee_name} - {task_name}: {hours}h @ ${rate}/h"
       - Expense: "{category}: {description}"
    4. Calculate totals
    5. Create Invoice record
    6. Create journal entry (DR AR, CR Revenue)
    7. Mark timesheets as invoiced (set invoice_id)
    8. Mark expenses as invoiced
    9. Update project.revenue_recognized
    10. Return created invoice
    """
    pass
```

**Auto-Invoice on Approval:**

Update timesheet approval endpoint to optionally trigger invoicing:

```python
@router.patch("/timesheets/{timesheet_id}/approve")
async def approve_timesheet(
    timesheet_id: str,
    auto_invoice: bool = Query(default=False),
    org_scoped = Depends(OrganizationScoped)
):
    """
    Approve timesheet and optionally trigger invoice generation.

    If auto_invoice=True and project has auto_billing enabled:
    - Generate invoice for this timesheet immediately
    """
    pass
```

#### 3.2 Project Cost Tracking to Finance

**Update Project Model:**

```python
# Add to Project model in project.py
finance_account_id: Optional[str] = Field(
    None,
    description="GL account for project costs"
)
revenue_account_id: Optional[str] = Field(
    None,
    description="GL account for project revenue"
)
revenue_recognized: float = Field(
    default=0.0,
    description="Revenue posted to Finance from invoices"
)
cost_recognized: float = Field(
    default=0.0,
    description="Costs posted to Finance (labor + expenses)"
)
profit_margin: float = Field(
    default=0.0,
    description="(Revenue - Costs) / Revenue"
)
```

**New Service:** `ProjectCostService`

```python
class ProjectCostService:
    """Track and post project costs to Finance."""

    async def calculate_labor_costs(self, project_id: str, period: str):
        """
        Calculate labor costs for a project period.

        For each Resource allocation:
        1. Get employee's loaded cost (salary + overhead)
        2. Calculate: hours_worked × hourly_cost
        3. Sum all resource costs

        Returns total labor cost for period.
        """
        pass

    async def post_project_costs_to_gl(self, project_id: str, period: str):
        """
        Post project costs to General Ledger.

        Create journal entries:
        DR Project Cost Account (project.finance_account_id)
        CR Accrued Labor Cost (liability account)

        For expenses already posted via expense approval.

        Update project.cost_recognized
        """
        pass

    async def calculate_project_profitability(self, project_id: str):
        """
        Calculate project profitability.

        Revenue = sum(invoices where project_id = project.id)
        Labor Cost = sum(resource costs from timesheets)
        Expense Cost = sum(expenses where project_id = project.id)

        Gross Profit = Revenue - Labor Cost - Expense Cost
        Profit Margin = Gross Profit / Revenue

        Return profitability metrics.
        """
        pass
```

**New Endpoints:**

```python
GET /projects/{project_id}/costs  # Detailed cost breakdown
GET /projects/{project_id}/profitability  # Profit analysis
GET /projects/{project_id}/billable-time  # Unbilled time report
POST /projects/{project_id}/post-costs  # Post costs to GL for period
```

#### 3.3 Project Budget Integration

**Link Project Budgets to Finance Budgets:**

```python
# Update Project model
finance_budget_id: Optional[str] = Field(
    None,
    description="Link to Finance Budget record"
)

# When creating project with budget:
async def create_project_with_budget(project_data, budget_data):
    """
    1. Create Finance Budget record
    2. Create Budget line items for project cost/revenue accounts
    3. Create Project record with finance_budget_id link
    4. Return project with budget reference
    """
    pass
```

**Budget Variance Monitoring:**

```python
@router.get("/projects/{project_id}/budget-variance")
async def get_project_budget_variance(project_id: str):
    """
    Compare actual project costs vs budget.

    Returns:
    - Budget amounts (labor, expenses, total)
    - Actual amounts (from timesheets, expenses)
    - Variance (actual - budget)
    - Variance % (variance / budget)
    - Alerts if >80% or >100% of budget
    """
    pass
```

**Deliverables:**
- ✅ Timesheet-to-invoice automation
- ✅ Project cost posting to GL
- ✅ Project profitability calculation endpoint
- ✅ Budget integration and variance alerts
- ✅ Labor cost tracking service
- ✅ Billable time reporting

---

### PHASE 4: HR-Finance Integration (Weeks 11-12)
**Goal:** Track all people costs in Finance

#### 4.1 Payroll → GL Posting

**Update Payroll Processing:**

```python
@router.post("/payroll/{payroll_id}/process")
async def process_payroll(
    payroll_id: str,
    org_scoped = Depends(OrganizationScoped)
):
    """
    Process payroll and create GL entries.

    Workflow:
    1. Validate payroll record
    2. Calculate all amounts (gross, deductions, net)
    3. Create journal entries:
       DR Payroll Expense - gross_pay
       CR Employee Tax Payable - tax deductions
       CR Benefits Payable - insurance, retirement
       CR Cash - net_pay
    4. Update Payroll.status = "processed"
    5. Tag entries with payroll_id, employee_id
    6. Return processed payroll with GL transaction IDs
    """
    pass
```

#### 4.2 Benefits Cost Tracking

**New Service:** `BenefitsCostService`

```python
class BenefitsCostService:
    """Track and post benefits costs to Finance."""

    async def calculate_monthly_benefits_cost(self, org_id: str):
        """
        Calculate total benefits cost for organization.

        For each active benefit:
        1. Get enrolled employee count
        2. Calculate: employee_count × employer_cost
        3. Sum all benefit costs
        """
        pass

    async def post_benefits_to_gl(self, org_id: str, period: str):
        """
        Post benefits costs to GL for period.

        DR Benefits Expense
        CR Benefits Payable

        Group by benefit type for clarity.
        """
        pass
```

**Automated Monthly Posting:**

Schedule monthly job to post benefits costs:
- Run on 1st of each month
- Post previous month's benefits
- Create journal entries
- Update benefit records with posting date

#### 4.3 Resource Cost Calculation

**Update Resource Model:**

```python
# Add to Resource model in project.py
employee_loaded_cost: float = Field(
    default=0.0,
    description="Employee salary + overhead per hour"
)
profit_margin_target: float = Field(
    default=0.3,
    description="Target profit margin (30% = 0.3)"
)
minimum_billing_rate: float = Field(
    default=0.0,
    description="Minimum rate to cover costs + margin"
)
```

**Resource Rate Validation:**

```python
async def validate_resource_rate(resource_id: str):
    """
    Ensure resource billing rate covers costs.

    1. Get Employee.salary
    2. Calculate hourly cost: salary / (52 weeks × 40 hours)
    3. Add overhead: hourly_cost × (1 + overhead_rate)
    4. Calculate minimum rate: loaded_cost × (1 + profit_margin)
    5. If resource.hourly_rate < minimum_rate: WARNING
    6. Return validation result with recommended rate
    """
    pass
```

#### 4.4 Capacity Planning

**New Endpoints:**

```python
GET /hr/employees/{employee_id}/capacity  # Availability vs allocation
GET /hr/capacity/team  # Team capacity overview
GET /hr/capacity/utilization  # Utilization metrics

# Response schema:
class EmployeeCapacity(BaseModel):
    employee_id: str
    employee_name: str
    standard_hours_per_week: int
    available_hours_this_week: int  # Standard - PTO - holidays
    allocated_hours: float  # Sum of project allocations
    utilization_percentage: float  # Allocated / available
    available_for_allocation: float  # Available - allocated
    overallocated: bool  # allocated > available
```

**Auto-Alert on Over-allocation:**

When creating or updating Resource allocation:
- Check employee capacity
- If allocation would cause over-allocation: return warning
- Optionally block allocation if strict mode enabled

**Deliverables:**
- ✅ Payroll GL posting automation
- ✅ Benefits cost tracking to Finance
- ✅ Resource cost validation
- ✅ Employee capacity planning endpoint
- ✅ Over-allocation warnings
- ✅ Monthly benefits posting schedule

---

### PHASE 5: Real-Time Dashboard & Analytics (Weeks 13-15)
**Goal:** Replace fake dashboard data with real-time intelligence

#### 5.1 Dashboard Metrics API

**New Endpoint:** `GET /dashboard/erp-overview`

```python
class ERPOverviewMetrics(BaseModel):
    """Comprehensive ERP metrics for dashboard."""

    # Finance Metrics
    finance: FinanceMetrics

    # CRM Metrics
    crm: CRMMetrics

    # HR Metrics
    hr: HRMetrics

    # Project Metrics
    projects: ProjectMetrics

    # Cross-Module Metrics
    cross_module: CrossModuleMetrics

    # Metadata
    as_of_date: datetime
    organization_id: str

class FinanceMetrics(BaseModel):
    monthly_revenue: float  # From invoices current month
    monthly_expenses: float  # From expenses + payroll current month
    net_income: float  # Revenue - expenses
    profit_margin: float  # Net income / revenue
    accounts_receivable: float  # Outstanding invoices
    accounts_payable: float  # Pending expenses
    cash_balance: float  # Cash account balance
    budget_vs_actual_variance: float  # Percent variance
    ytd_revenue: float
    ytd_expenses: float

class CRMMetrics(BaseModel):
    total_customers: int
    total_leads: int
    total_opportunities: int
    new_leads_this_month: int
    new_customers_this_month: int
    lead_conversion_rate: float  # Leads → customers %
    opportunity_win_rate: float  # Won / closed opps
    pipeline_value: float  # Sum of open opp amounts
    weighted_pipeline: float  # Sum of (amount × probability)
    average_deal_size: float
    sales_cycle_days: float  # Avg days to close

class HRMetrics(BaseModel):
    total_employees: int
    active_employees: int
    monthly_payroll_expense: float
    monthly_benefits_cost: float
    open_positions: int
    average_employee_cost: float
    turnover_rate: float  # Annual turnover %
    headcount_growth: float  # YTD growth %

class ProjectMetrics(BaseModel):
    active_projects: int
    total_projects: int
    completed_projects_this_month: int
    total_project_revenue: float
    total_project_costs: float
    average_profit_margin: float
    resource_utilization: float  # % of available hours allocated
    on_time_delivery_rate: float  # % of projects delivered on time
    overbudget_projects: int

class CrossModuleMetrics(BaseModel):
    revenue_per_employee: float  # Total revenue / employee count
    customer_lifetime_value: float  # Average LTV
    customer_acquisition_cost: float  # Sales/marketing cost / new customers
    project_roi: float  # (Revenue - costs) / costs
    employee_productivity: float  # Revenue / (payroll + benefits)
```

**Implementation:**

```python
@router.get("/dashboard/erp-overview", response_model=ERPOverviewMetrics)
async def get_erp_overview(
    current_user = Depends(get_current_user),
    org_scoped = Depends(OrganizationScoped)
):
    """
    Generate real-time ERP metrics from live data.

    Queries:
    - Finance: Aggregate transactions, invoices, expenses for period
    - CRM: Count entities, calculate conversion rates
    - HR: Count employees, sum payroll
    - Projects: Calculate profitability, utilization
    - Cross-module: Join data for combined metrics

    Cache result for 5 minutes to improve performance.
    """
    pass
```

#### 5.2 Sales Pipeline Visualization

**New Endpoint:** `GET /dashboard/sales-pipeline`

```python
class SalesPipelineResponse(BaseModel):
    stages: List[PipelineStageMetrics]
    total_opportunities: int
    total_pipeline_value: float
    weighted_pipeline_value: float
    conversion_rates: Dict[str, float]  # Stage-to-stage conversion
    average_days_per_stage: Dict[str, float]

class PipelineStageMetrics(BaseModel):
    stage: OpportunityStage
    stage_name: str
    count: int
    total_value: float
    weighted_value: float  # Sum of (amount × probability)
    average_deal_size: float
    oldest_opportunity_days: int
    newest_opportunity_days: int
```

**Implementation:**

```python
async def get_sales_pipeline():
    """
    Aggregate opportunities by stage.

    For each stage:
    1. Count opportunities
    2. Sum amounts
    3. Calculate weighted value (amount × probability)
    4. Find oldest/newest
    5. Calculate conversion rate to next stage
    """
    pass
```

#### 5.3 Task Dashboard Widget

**New Endpoint:** `GET /dashboard/my-tasks`

```python
class MyTasksResponse(BaseModel):
    overdue: List[TaskSummary]  # Due date < today
    due_today: List[TaskSummary]
    due_this_week: List[TaskSummary]
    upcoming: List[TaskSummary]  # Due next week
    total_overdue_count: int
    total_pending_count: int

class TaskSummary(BaseModel):
    task_id: str
    title: str
    entity_type: str
    entity_id: str
    entity_name: str
    priority: TaskPriority
    due_date: datetime
    days_overdue: Optional[int]  # If overdue
    task_type: str
```

**Implementation:**

```python
async def get_my_tasks(user_id: str):
    """
    Get user's tasks sorted by priority.

    1. Query CRM tasks assigned to user
    2. Query Project tasks assigned to user (if implementing)
    3. Group by due date category
    4. Sort within each group: URGENT > HIGH > MEDIUM > LOW > due date
    5. Return categorized tasks
    """
    pass
```

#### 5.4 Activity Feed

**New Endpoint:** `GET /dashboard/activity-feed`

```python
class ActivityFeedResponse(BaseModel):
    activities: List[ActivityFeedItem]
    total_count: int

class ActivityFeedItem(BaseModel):
    activity_id: str
    activity_type: str  # "conversion", "deal_won", "new_customer", etc.
    title: str
    description: str
    timestamp: datetime
    user_id: str
    user_email: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    entity_name: Optional[str]
    icon: str  # Icon identifier for UI
    color: str  # Color code for UI
```

**Implementation:**

```python
async def get_activity_feed(limit: int = 20):
    """
    Recent significant events across all modules.

    Include:
    - CRM conversions (Lead→Opp, Opp→Customer)
    - Large deals won (>$10k)
    - New customers
    - Projects completed
    - Budget alerts
    - System activities

    Sort by timestamp descending.
    """
    pass
```

#### 5.5 Cross-Module Reports

**New Endpoints:**

```python
GET /reports/project-profitability-by-customer
GET /reports/revenue-by-sales-rep
GET /reports/employee-productivity
GET /reports/customer-acquisition-cost
GET /reports/department-budget-performance
```

**Example: Project Profitability by Customer**

```python
class ProjectProfitabilityByCustomer(BaseModel):
    customer_id: str
    customer_name: str
    total_projects: int
    active_projects: int
    total_revenue: float
    total_costs: float
    total_profit: float
    profit_margin: float
    projects: List[ProjectProfitabilitySummary]

async def get_project_profitability_by_customer():
    """
    Join Projects, Customers, Invoices, Timesheets, Expenses.

    For each customer:
    1. Find all projects
    2. Calculate revenue from invoices
    3. Calculate costs from timesheets + expenses
    4. Calculate profit = revenue - costs
    5. Calculate margin = profit / revenue
    """
    pass
```

**Deliverables:**
- ✅ Real-time dashboard API with all metrics
- ✅ Sales pipeline visualization endpoint
- ✅ Task dashboard widget with priority sorting
- ✅ Activity feed for recent events
- ✅ 5 cross-module analytics reports
- ✅ Frontend dashboard complete redesign
- ✅ Caching layer for performance

---

### PHASE 6: Advanced Workflows & Automation (Weeks 16-18)
**Goal:** Automate repetitive processes across modules

#### 6.1 Notification Service

**New Service:** `/opt/kasaai/apps/erp/backend/app/services/notification_service.py`

```python
class NotificationService:
    """Send notifications via email and in-app."""

    async def send_invoice_reminder(self, invoice_id: str, days_overdue: int):
        """Send overdue invoice reminder to customer."""
        pass

    async def send_budget_alert(self, budget_id: str, variance_percent: float):
        """Alert when budget variance exceeds threshold."""
        pass

    async def send_task_reminder(self, task_id: str, days_until_due: int):
        """Remind assignee of upcoming task deadline."""
        pass

    async def send_approval_request(self, entity_type: str, entity_id: str, approver_id: str):
        """Request approval from designated approver."""
        pass
```

#### 6.2 Workflow Engine

**New Service:** `/opt/kasaai/apps/erp/backend/app/services/workflow_engine.py`

```python
class WorkflowEngine:
    """Trigger-based automation workflows."""

    async def register_trigger(self, trigger_type: str, entity_id: str, action: str):
        """Register a workflow trigger."""
        pass

    async def execute_workflow(self, trigger_type: str, entity_id: str):
        """Execute workflow when trigger fires."""
        pass

# Example workflows:
# - Opportunity stage = "Proposal" → Create task "Follow up in 3 days"
# - Invoice 30 days overdue → Send reminder email
# - Budget variance > 10% → Send alert to manager
# - Employee hired → Create onboarding checklist
# - Project 80% of budget → Send warning to PM
```

#### 6.3 Approval Routing System

**New Model:**

```python
class ApprovalWorkflow(BaseModel):
    """Multi-level approval configuration."""

    entity_type: str  # "expense", "invoice", "timesheet", "budget"
    approval_levels: List[ApprovalLevel]
    auto_approve_threshold: Optional[float]  # Auto-approve if under amount

class ApprovalLevel(BaseModel):
    level: int  # 1, 2, 3, etc.
    approver_role: str  # "manager", "finance", "executive"
    amount_threshold: Optional[float]  # This level only if amount > threshold
    required: bool

class ApprovalRequest(BaseModel):
    """Approval request instance."""

    entity_type: str
    entity_id: str
    requested_by: str
    current_level: int
    status: str  # "pending", "approved", "rejected"
    approvals: List[ApprovalAction]

class ApprovalAction(BaseModel):
    level: int
    approver_id: str
    action: str  # "approved", "rejected"
    timestamp: datetime
    comments: Optional[str]
```

**Deliverables:**
- ✅ Notification service (email + in-app)
- ✅ Workflow engine with triggers
- ✅ Approval routing system
- ✅ Automated alerts and reminders
- ✅ Scheduled job execution
- ✅ Webhook support for external integrations

---

### PHASE 7: Missing ERP Modules (Weeks 19-20+) - OPTIONAL
**Goal:** Add standard ERP modules currently missing

#### 7.1 Procurement Module

**New Models:**

```python
class PurchaseOrder(BaseModel):
    po_number: str
    vendor_id: str
    order_date: datetime
    expected_delivery_date: datetime
    line_items: List[PurchaseOrderLineItem]
    subtotal: float
    tax_amount: float
    total_amount: float
    status: str  # "draft", "sent", "acknowledged", "received", "closed"

class Vendor(BaseModel):
    vendor_name: str
    vendor_type: str
    email: str
    payment_terms: str
    tax_id: str
    rating: float

class GoodsReceipt(BaseModel):
    po_id: str
    received_date: datetime
    line_items: List[ReceivedLineItem]
    received_by: str
```

#### 7.2 Inventory Management

**New Models:**

```python
class InventoryItem(BaseModel):
    item_code: str
    item_name: str
    category: str
    unit_of_measure: str
    current_stock: float
    reorder_point: float
    unit_cost: float

class StockMovement(BaseModel):
    item_id: str
    movement_type: str  # "receipt", "issue", "transfer", "adjustment"
    quantity: float
    from_location: Optional[str]
    to_location: Optional[str]
    reference_type: str
    reference_id: str
```

---

## 📊 DATABASE SCHEMA CHANGES

### New Collections:

1. **`activities`** - CRM activity tracking
2. **`crm_tasks`** - CRM tasks and todos
3. **`approval_workflows`** - Approval configurations
4. **`approval_requests`** - Approval instances
5. **`notifications`** - Notification log

### Modified Collections:

1. **`leads`** - Add: `follow_up_date`, `last_contacted`, `next_action`, `last_activity_id`, `activity_count`
2. **`opportunities`** - Add: `next_step_date`, `last_activity_date`, `activity_count`, `days_in_current_stage`
3. **`projects`** - Add: `finance_account_id`, `revenue_account_id`, `revenue_recognized`, `cost_recognized`, `profit_margin`
4. **`employees`** - Add: `available_hours_per_week`, `overhead_rate`
5. **`resources`** - Add: `employee_loaded_cost`, `profit_margin_target`, `minimum_billing_rate`

### Required Indexes:

```python
# activities collection
db.activities.create_index("entity_type")
db.activities.create_index("entity_id")
db.activities.create_index([("entity_type", 1), ("entity_id", 1)])
db.activities.create_index("activity_type")
db.activities.create_index("activity_date")
db.activities.create_index("created_by_user_id")
db.activities.create_index([("follow_up_required", 1), ("follow_up_date", 1)])
db.activities.create_index("organization_id")

# crm_tasks collection
db.crm_tasks.create_index("entity_type")
db.crm_tasks.create_index("entity_id")
db.crm_tasks.create_index("assigned_to")
db.crm_tasks.create_index("due_date")
db.crm_tasks.create_index("priority")
db.crm_tasks.create_index("status")
db.crm_tasks.create_index([("assigned_to", 1), ("status", 1), ("due_date", 1)])
db.crm_tasks.create_index("organization_id")

# Compound indexes for dashboard queries
db.transactions.create_index([("organization_id", 1), ("transaction_date", 1)])
db.invoices.create_index([("organization_id", 1), ("status", 1)])
db.opportunities.create_index([("organization_id", 1), ("stage", 1)])
```

---

## 🎯 SUCCESS METRICS

**Integration Completeness:**
- % of invoices auto-created from won opportunities: >90%
- % of timesheets auto-invoiced: >80%
- % of payroll with GL entries: 100%
- Account balance accuracy: 100%
- Dashboard showing real data: Yes

**User Adoption:**
- % of CRM conversions using conversion feature: >85%
- % of users logging activities: >70%
- Daily dashboard visits: >80% of users
- Task completion rate: >85%
- Follow-up completion rate: >80%

**Data Quality:**
- % of opportunities with follow-up dates: >90%
- % of projects with budget tracking: 100%
- Activity logging frequency: avg >5 per opportunity
- Task overdue rate: <15%

**Business Insights:**
- Can generate real-time P&L: Yes
- Can calculate project profitability: Yes
- Can forecast sales pipeline: Yes
- Can track employee productivity: Yes
- Can calculate customer acquisition cost: Yes

---

## 📅 IMPLEMENTATION TIMELINE

### Month 1 (Weeks 1-4): Financial Foundation
- Week 1-2: Journal entry engine and account balance automation
- Week 3-4: Real financial reports and testing

### Month 2 (Weeks 5-8): CRM & Project Integration
- Week 5-6: CRM conversions, activities, tasks
- Week 7-8: Project-Finance integration and billing automation

### Month 3 (Weeks 9-12): HR & Analytics
- Week 9-10: HR-Finance integration and capacity planning
- Week 11-12: Dashboard redesign and cross-module reports

### Month 4 (Weeks 13-16): Workflows & Polish
- Week 13-14: Notification service and workflow engine
- Week 15-16: Testing, bug fixes, documentation

### Month 5 (Weeks 17-20): Optional Enhancements
- Week 17-18: Procurement module (if needed)
- Week 19-20: Final polish, training, deployment

---

## 🚀 DEPLOYMENT STRATEGY

1. **Staging Deployment (Week 16)**
   - Deploy to dev server first
   - User acceptance testing
   - Performance testing
   - Bug fixes

2. **Production Deployment (Week 18)**
   - Deploy to production during low-traffic period
   - Run data migration scripts
   - Monitor for issues
   - Gradual rollout by module

3. **User Training (Week 19)**
   - Create user documentation
   - Video tutorials
   - Live training sessions
   - Q&A support

4. **Monitoring & Optimization (Week 20)**
   - Monitor performance metrics
   - Gather user feedback
   - Optimize slow queries
   - Fine-tune automations

---

## 📚 DOCUMENTATION REQUIREMENTS

1. **API Documentation**
   - All new endpoints with examples
   - Request/response schemas
   - Error codes and handling

2. **User Guides**
   - CRM conversion workflows
   - Activity logging best practices
   - Task management
   - Dashboard interpretation
   - Financial reporting

3. **Developer Documentation**
   - Architecture overview
   - Service integrations
   - Database schema
   - Workflow engine usage
   - Adding new automations

4. **Admin Documentation**
   - Configuration settings
   - Approval workflow setup
   - User role management
   - Data migration procedures

---

## 💡 BENEFITS SUMMARY

**For Sales Team:**
- ✅ One-click conversions (no data re-entry)
- ✅ Never miss follow-ups (automated reminders)
- ✅ Complete interaction history
- ✅ Visual sales pipeline
- ✅ Accurate revenue forecasting

**For Finance Team:**
- ✅ Real-time financial position
- ✅ Automated journal entries
- ✅ Accurate revenue recognition
- ✅ Project profitability tracking
- ✅ Budget variance alerts

**For Project Managers:**
- ✅ Automated client billing
- ✅ Real-time project costs
- ✅ Resource utilization tracking
- ✅ Budget monitoring
- ✅ Profitability by project/customer

**For HR Team:**
- ✅ Automated payroll posting
- ✅ Resource capacity planning
- ✅ Employee cost tracking
- ✅ Benefits administration integration

**For Executives:**
- ✅ Real-time dashboard with accurate metrics
- ✅ Cross-module analytics
- ✅ Data-driven decision making
- ✅ Complete business visibility
- ✅ Forecasting and planning tools

---

## 🎯 CONCLUSION

This integrated enhancement plan transforms the ERP system from **8 siloed modules operating independently** into a **unified enterprise platform** where:

- 💰 **Finance is the central hub** - all revenue and costs flow through the General Ledger
- 🔄 **Workflows are automated** - won opportunities create invoices, approved timesheets generate bills, payroll posts to GL
- 📊 **Dashboards show real data** - no more mock numbers, all metrics calculated from live transactions
- 🎯 **Teams collaborate seamlessly** - sales, projects, finance, and HR all connected
- 📈 **Business insights are actionable** - profitability by project/customer, resource utilization, sales forecasting

**Estimated Total Effort:** 16-20 weeks
**Estimated ROI:** 300%+ through automation savings, improved accuracy, and better decision making

**Next Steps:**
1. ✅ Review and approve plan
2. ✅ Allocate development resources
3. ✅ Begin Phase 1 implementation
4. ✅ Weekly progress reviews
5. ✅ Adjust timeline as needed

---

*This document integrates the CRM Enhancement Plan (/opt/kasaai/apps/erp/CRM_ENHANCEMENT_PLAN.md) with comprehensive ERP industry standards to create a complete roadmap for a fully integrated enterprise system.*
