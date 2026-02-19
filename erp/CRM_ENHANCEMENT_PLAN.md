# ERP CRM Enhancement Plan - Complete Workflow Implementation

## Executive Summary

This document outlines critical enhancements needed to transform the ERP CRM module from a basic contact manager into a complete sales workflow system with lead conversion, opportunity management, task tracking, and actionable dashboard insights.

---

## Current State Analysis

### ✅ What Works Well
- **CRUD Operations**: All entities (Customers, Leads, Opportunities, Contacts) have full CRUD
- **Data Models**: Well-structured with proper relationships
- **Organization Scoping**: Multi-tenant isolation works correctly
- **Search & Filtering**: Pagination and search functionality implemented
- **Bulk Import**: Contact bulk import from CSV/Excel
- **Status Tracking**: Lead statuses and opportunity stages defined
- **User Assignment**: Can assign leads and opportunities to team members

### ❌ Critical Gaps

#### 1. **NO Conversion Workflows**
- Cannot convert Lead → Opportunity
- Cannot convert Lead → Customer
- Cannot convert Opportunity → Customer (when deal closes)
- Manual copy-paste between entities required

#### 2. **NO Activity/Interaction Tracking**
- No call logs
- No email tracking
- No meeting notes
- No activity timeline
- No audit history

#### 3. **NO Follow-up Management**
- No follow-up dates on leads
- No follow-up reminders
- No scheduled task system for CRM
- Next steps exist but no dates attached

#### 4. **NO Dashboard Intelligence**
- Dashboard shows hardcoded fake data
- No real CRM metrics
- No sales pipeline visualization
- No conversion rate tracking
- No activity feed

#### 5. **NO Task/Todo Integration**
- Tasks exist in Projects module only
- No CRM-specific tasks
- No priority-based task dashboard
- No upcoming follow-ups view

---

## Enhancement Roadmap

### Phase 1: Core Conversion Workflows (HIGH PRIORITY)

#### 1.1 Lead to Opportunity Conversion

**Backend Implementation:**

```python
# File: erp/backend/app/api/routes/crm.py

@router.post("/leads/{lead_id}/convert-to-opportunity", response_model=OpportunityResponse)
async def convert_lead_to_opportunity(
    lead_id: str,
    request: LeadToOpportunityConversionRequest,
    org_scoped=Depends(OrganizationScoped)
):
    """
    Convert a qualified lead into an opportunity.

    Workflow:
    1. Validate lead exists and is qualified
    2. Create new opportunity with lead data
    3. Update lead status to CONVERTED
    4. Set lead.converted_at timestamp
    5. Link opportunity.lead_id to original lead
    6. Create activity log entry
    7. Return created opportunity
    """
```

**Request Schema:**
```python
class LeadToOpportunityConversionRequest(BaseModel):
    opportunity_name: str = Field(..., description="Deal name")
    amount: float = Field(..., description="Expected deal value")
    probability: int = Field(default=25, ge=0, le=100)
    stage: OpportunityStage = Field(default=OpportunityStage.PROSPECTING)
    expected_close_date: Optional[datetime] = None
    description: Optional[str] = None
    keep_lead_active: bool = Field(default=False, description="Don't mark lead as converted")
```

**Frontend:**
- Add "Convert to Opportunity" button on lead detail page
- Conversion modal with opportunity details form
- Pre-fill contact info from lead
- Show success message with link to new opportunity

---

#### 1.2 Lead to Customer Conversion

**Backend Implementation:**

```python
@router.post("/leads/{lead_id}/convert-to-customer", response_model=CustomerResponse)
async def convert_lead_to_customer(
    lead_id: str,
    request: LeadToCustomerConversionRequest,
    org_scoped=Depends(OrganizationScoped)
):
    """
    Convert a qualified lead directly into a customer.

    Use case: Quick conversions for small deals without opportunity tracking

    Workflow:
    1. Validate lead exists
    2. Create customer from lead data
    3. Create primary contact from lead
    4. Update lead status to CONVERTED
    5. Set lead.converted_to_customer_id
    6. Create activity log entry
    7. Return created customer
    """
```

**Request Schema:**
```python
class LeadToCustomerConversionRequest(BaseModel):
    customer_type: CustomerType = Field(default=CustomerType.INDIVIDUAL)
    company_name: Optional[str] = None
    create_contact: bool = Field(default=True, description="Create contact record")
    account_manager: Optional[str] = None  # User ID
    tags: List[str] = Field(default_factory=list)
```

---

#### 1.3 Opportunity to Customer Conversion

**Backend Implementation:**

```python
@router.post("/opportunities/{opportunity_id}/convert-to-customer", response_model=CustomerResponse)
async def convert_opportunity_to_customer(
    opportunity_id: str,
    request: OpportunityToCustomerConversionRequest,
    org_scoped=Depends(OrganizationScoped)
):
    """
    Convert a won opportunity into a customer.

    Workflow:
    1. Validate opportunity is CLOSED_WON
    2. Create/update customer
    3. Set opportunity.customer_id if creating
    4. Set closed_date to now
    5. Update lifetime_value
    6. Create activity log
    7. Optionally create invoice/project
    8. Return customer
    """
```

**Request Schema:**
```python
class OpportunityToCustomerConversionRequest(BaseModel):
    create_new_customer: bool = Field(
        default=True,
        description="False to link to existing customer"
    )
    existing_customer_id: Optional[str] = None
    customer_type: CustomerType = Field(default=CustomerType.BUSINESS)
    account_manager: Optional[str] = None
    create_invoice: bool = Field(default=False)
    create_project: bool = Field(default=False)
    project_name: Optional[str] = None
```

---

### Phase 2: Activity & Interaction Tracking (HIGH PRIORITY)

#### 2.1 CRM Activity Model

**New Model:**

```python
# File: erp/backend/app/models/crm.py

class ActivityType(str, Enum):
    """CRM activity types."""
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"
    TASK = "task"
    SMS = "sms"
    CONVERSION = "conversion"  # System-generated
    STATUS_CHANGE = "status_change"  # System-generated


class Activity(BaseModel):
    """
    Activity tracking for CRM entities.

    Records all interactions, notes, and system events for leads,
    opportunities, and customers.
    """

    # What entity does this activity relate to?
    entity_type: str = Field(..., description="lead, opportunity, customer, contact")
    entity_id: str = Field(..., description="ID of the entity")

    # Activity details
    activity_type: ActivityType
    subject: str = Field(..., description="Brief summary")
    description: Optional[str] = Field(None, description="Full details")

    # When and who
    activity_date: datetime = Field(default_factory=datetime.utcnow)
    created_by_user_id: str = Field(..., description="User who logged this")
    created_by_user_email: Optional[str] = None

    # Call-specific fields
    call_duration_minutes: Optional[int] = None
    call_outcome: Optional[str] = None  # "connected", "voicemail", "no_answer"

    # Email-specific fields
    email_subject: Optional[str] = None
    email_to: Optional[List[str]] = None
    email_cc: Optional[List[str]] = None

    # Follow-up tracking
    follow_up_required: bool = Field(default=False)
    follow_up_date: Optional[datetime] = None
    follow_up_completed: bool = Field(default=False)

    # Attachments
    attachment_urls: List[str] = Field(default_factory=list)

    # System metadata
    is_system_generated: bool = Field(
        default=False,
        description="True for automated activities (conversions, status changes)"
    )

    # Inherited from BaseModel: id, organization_id, created_at, updated_at, is_active
```

---

#### 2.2 Activity Endpoints

```python
# File: erp/backend/app/api/routes/crm.py

@router.post("/activities", response_model=ActivityResponse)
async def create_activity(
    request: ActivityCreate,
    current_user = Depends(get_current_user),
    org_scoped = Depends(OrganizationScoped)
):
    """Log a new CRM activity (call, email, meeting, note, etc.)"""

@router.get("/activities", response_model=List[ActivityResponse])
async def list_activities(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    activity_type: Optional[ActivityType] = None,
    user_id: Optional[str] = None,
    follow_up_required: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    org_scoped = Depends(OrganizationScoped)
):
    """List CRM activities with filtering"""

@router.get("/activities/timeline/{entity_type}/{entity_id}", response_model=List[ActivityResponse])
async def get_entity_activity_timeline(
    entity_type: str,
    entity_id: str,
    org_scoped = Depends(OrganizationScoped)
):
    """Get complete activity timeline for a lead, opportunity, or customer"""

@router.get("/activities/upcoming-follow-ups", response_model=List[ActivityResponse])
async def get_upcoming_follow_ups(
    user_id: Optional[str] = None,
    days_ahead: int = 7,
    org_scoped = Depends(OrganizationScoped)
):
    """Get activities requiring follow-up in the next N days"""
```

---

### Phase 3: Follow-up Date Management (HIGH PRIORITY)

#### 3.1 Update Lead Model

```python
# File: erp/backend/app/models/crm.py

class Lead(BaseModel):
    # ... existing fields ...

    # NEW FIELDS:
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
        description="Next action to take (e.g., 'Send proposal', 'Schedule demo')"
    )
```

---

#### 3.2 Update Opportunity Model

```python
# File: erp/backend/app/models/crm.py

class Opportunity(BaseModel):
    # ... existing fields ...

    # ENHANCE EXISTING:
    next_step: Optional[str]  # Already exists

    # NEW FIELDS:
    next_step_date: Optional[datetime] = Field(
        None,
        description="When the next step should be completed by"
    )
    last_activity_date: Optional[datetime] = Field(
        None,
        description="Last time there was activity on this opportunity"
    )
```

---

### Phase 4: Task/Todo System for CRM (HIGH PRIORITY)

#### 4.1 CRM Task Model

**Option A: Reuse Project Task Model**
- Add `entity_type` and `entity_id` fields to existing Task model
- Allow tasks to link to leads, opportunities, customers (not just projects)

**Option B: Create Dedicated CRM Task Model**

```python
# File: erp/backend/app/models/crm.py

class CRMTask(BaseModel):
    """
    Tasks/todos for CRM entities (leads, opportunities, customers).

    Different from Project tasks - these are sales activities.
    """

    # What entity is this task for?
    entity_type: str = Field(..., description="lead, opportunity, customer")
    entity_id: str = Field(..., description="ID of the entity")

    # Task details
    title: str = Field(..., description="Task title")
    description: Optional[str] = None
    task_type: str = Field(..., description="call, email, meeting, demo, proposal, follow_up")

    # Priority and status
    priority: TaskPriority  # LOW | MEDIUM | HIGH | URGENT (from existing enum)
    status: str = Field(
        default="pending",
        description="pending, in_progress, completed, cancelled"
    )

    # Scheduling
    due_date: datetime = Field(..., description="When task is due")
    reminder_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None

    # Assignment
    assigned_to: str = Field(..., description="User ID responsible for task")
    assigned_by: Optional[str] = None

    # Completion
    completed_by: Optional[str] = None
    completion_notes: Optional[str] = None

    # Inherited: id, organization_id, created_at, updated_at, is_active
```

---

#### 4.2 Task Dashboard View

**New Endpoint:**

```python
@router.get("/tasks/my-tasks", response_model=List[CRMTaskResponse])
async def get_my_crm_tasks(
    current_user = Depends(get_current_user),
    status: Optional[str] = Query(None, description="pending, in_progress, completed"),
    priority: Optional[TaskPriority] = None,
    overdue_only: bool = False,
    org_scoped = Depends(OrganizationScoped)
):
    """
    Get current user's CRM tasks.

    Returns tasks sorted by:
    1. Priority (URGENT > HIGH > MEDIUM > LOW)
    2. Due date (earliest first)
    """
```

---

### Phase 5: Enhanced Dashboard (HIGH PRIORITY)

#### 5.1 Real-Time CRM Metrics

**New Dashboard Endpoint:**

```python
# File: erp/backend/app/api/routes/dashboard.py

@router.get("/dashboard/crm-metrics", response_model=CRMMetricsResponse)
async def get_crm_metrics(
    user_id: Optional[str] = None,  # Filter for specific user
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    org_scoped = Depends(OrganizationScoped)
):
    """
    Get real CRM metrics for dashboard.

    Returns:
    - Lead metrics (total, new this month, by status, by source, conversion rate)
    - Opportunity metrics (total, by stage, total value, weighted value, win rate)
    - Customer metrics (total, new this month, lifetime value)
    - Activity metrics (calls, emails, meetings this week)
    - Task metrics (overdue, due today, due this week)
    - Top performers (by conversions, revenue)
    """
```

**Response Schema:**

```python
class CRMMetricsResponse(BaseModel):
    # Lead Metrics
    total_leads: int
    new_leads_this_month: int
    qualified_leads: int
    lead_conversion_rate: float  # Percentage of leads converted to customers
    leads_by_status: Dict[str, int]  # {status: count}
    leads_by_source: Dict[str, int]  # {source: count}

    # Opportunity Metrics
    total_opportunities: int
    opportunities_by_stage: Dict[str, int]
    total_pipeline_value: float
    weighted_pipeline_value: float  # Sum of (amount * probability)
    won_opportunities_this_month: int
    lost_opportunities_this_month: int
    win_rate: float  # Percentage of closed deals that were won
    average_deal_size: float

    # Customer Metrics
    total_customers: int
    new_customers_this_month: int
    total_lifetime_value: float
    average_customer_value: float

    # Activity Metrics
    calls_this_week: int
    emails_this_week: int
    meetings_this_week: int
    activities_by_type: Dict[str, int]

    # Task Metrics
    overdue_tasks: int
    tasks_due_today: int
    tasks_due_this_week: int
    completed_tasks_this_week: int

    # Performance
    top_sales_reps: List[Dict[str, Any]]  # By revenue/conversions

    # Date range
    from_date: datetime
    to_date: datetime
```

---

#### 5.2 Sales Pipeline Visualization Data

**Endpoint:**

```python
@router.get("/dashboard/sales-pipeline", response_model=SalesPipelineResponse)
async def get_sales_pipeline(
    user_id: Optional[str] = None,
    org_scoped = Depends(OrganizationScoped)
):
    """
    Get sales pipeline data for funnel visualization.

    Returns opportunities grouped by stage with counts and values.
    """
```

**Response:**

```python
class PipelineStageMetrics(BaseModel):
    stage: OpportunityStage
    stage_name: str  # "Prospecting", "Qualification", etc.
    count: int
    total_value: float
    weighted_value: float
    average_deal_size: float
    oldest_opportunity_days: int  # Days in this stage

class SalesPipelineResponse(BaseModel):
    stages: List[PipelineStageMetrics]
    total_opportunities: int
    total_pipeline_value: float
    weighted_pipeline_value: float
    conversion_rates: Dict[str, float]  # From stage to stage
```

---

#### 5.3 Upcoming Tasks & Follow-ups Dashboard Widget

**Endpoint:**

```python
@router.get("/dashboard/upcoming-tasks", response_model=UpcomingTasksResponse)
async def get_upcoming_tasks_dashboard(
    current_user = Depends(get_current_user),
    org_scoped = Depends(OrganizationScoped)
):
    """
    Get upcoming tasks and follow-ups for dashboard widget.

    Returns:
    - Overdue tasks (HIGH PRIORITY)
    - Tasks due today
    - Tasks due this week
    - Activities requiring follow-up

    Sorted by: Overdue > Priority > Due date
    """
```

---

### Phase 6: Additional Enhancements (MEDIUM PRIORITY)

#### 6.1 Email Integration Hooks

```python
# File: erp/backend/app/api/routes/crm.py

@router.post("/activities/email-received", response_model=ActivityResponse)
async def log_email_received(
    request: EmailReceivedRequest,
    org_scoped = Depends(OrganizationScoped)
):
    """
    Webhook for email integration (Gmail, Outlook, etc.)

    Automatically creates activity when email is received from/to
    a lead, opportunity, or customer email address.
    """

@router.post("/activities/email-sent", response_model=ActivityResponse)
async def log_email_sent(
    request: EmailSentRequest,
    org_scoped = Depends(OrganizationScoped)
):
    """Log outbound emails to CRM entities"""
```

---

#### 6.2 Auto-update Opportunity Probability by Stage

```python
# Default probability by stage
STAGE_DEFAULT_PROBABILITY = {
    OpportunityStage.PROSPECTING: 10,
    OpportunityStage.QUALIFICATION: 25,
    OpportunityStage.PROPOSAL: 50,
    OpportunityStage.NEGOTIATION: 75,
    OpportunityStage.CLOSED_WON: 100,
    OpportunityStage.CLOSED_LOST: 0,
}

# Auto-update probability when stage changes
# Can be overridden manually by user
```

---

#### 6.3 Relationship Map View

**Endpoint:**

```python
@router.get("/customers/{customer_id}/relationship-map", response_model=RelationshipMapResponse)
async def get_customer_relationship_map(
    customer_id: str,
    org_scoped = Depends(OrganizationScoped)
):
    """
    Get complete relationship overview for a customer.

    Returns:
    - All contacts
    - All opportunities (past and current)
    - All activities
    - Related leads (that converted to this customer)
    - Account manager details
    - Lifetime value breakdown
    """
```

---

## Frontend Implementation Plan

### 1. Conversion Workflows

**Lead Detail Page Enhancements:**
- Add "Convert" dropdown button with options:
  - "Convert to Opportunity"
  - "Convert to Customer"
- Conversion modals with forms
- Success notifications with links to created records

**Opportunity Detail Page Enhancements:**
- Add "Mark as Won" button (closes deal, prompts for customer creation)
- Add "Mark as Lost" button (prompts for loss reason)
- Conversion modal for won deals

---

### 2. Activity Timeline Component

```tsx
// File: erp/frontend/src/components/ActivityTimeline.tsx

interface ActivityTimelineProps {
  entityType: 'lead' | 'opportunity' | 'customer'
  entityId: string
}

/**
 * Displays activity timeline for CRM entities.
 *
 * Features:
 * - Chronological activity feed
 * - Activity type icons (call, email, meeting, note)
 * - Expandable activity details
 * - "Add Activity" quick button
 * - Filter by activity type
 * - System activities (conversions, status changes) marked differently
 */
export function ActivityTimeline({ entityType, entityId }: ActivityTimelineProps) {
  // Implementation
}
```

---

### 3. Task Management UI

**Dashboard Task Widget:**

```tsx
// File: erp/frontend/src/components/dashboard/TasksWidget.tsx

/**
 * Dashboard widget showing upcoming tasks and follow-ups.
 *
 * Sections:
 * - OVERDUE (red, urgent)
 * - DUE TODAY (orange)
 * - DUE THIS WEEK (blue)
 * - UPCOMING (gray)
 *
 * Features:
 * - Quick complete checkbox
 * - Click to view entity
 * - Filter by priority
 * - "Add Task" button
 */
```

**CRM Entity Task List:**

```tsx
// File: erp/frontend/src/components/TaskList.tsx

/**
 * Task list for specific CRM entity (lead, opportunity, customer).
 *
 * Features:
 * - Create new task
 * - Mark complete
 * - Edit task
 * - Delete task
 * - Sort by due date / priority
 * - Filter by status
 */
```

---

### 4. Enhanced Dashboard

**New Dashboard Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│  ERP Dashboard                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  LEADS   │  │OPPORTUN. │  │CUSTOMERS │  │PIPELINE  │   │
│  │   245    │  │    48    │  │   189    │  │ $485K    │   │
│  │  ↑ 12%   │  │  ↑ 23%   │  │  ↑ 8%    │  │ Weighted │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
├──────────────────────────────┬───────────────────────────────┤
│ TASKS & FOLLOW-UPS           │ SALES PIPELINE               │
├──────────────────────────────┤                               │
│ ⚠️  3 OVERDUE                │  ┌─────────────────────┐     │
│ • Call John Smith (Lead)     │  │ Prospecting    $120K│     │
│ • Send proposal (Opp #42)    │  ├─────────────────────┤     │
│ • Follow up with Acme        │  │ Qualification  $95K │     │
│                               │  ├─────────────────────┤     │
│ 📅 5 DUE TODAY               │  │ Proposal       $180K│     │
│ • Demo for TechCorp          │  ├─────────────────────┤     │
│ • Pricing call with StartupX │  │ Negotiation    $90K │     │
│ • Send contract to ABC Ltd   │  └─────────────────────┘     │
│                               │                               │
│ [View All Tasks]             │  Conversion: 24% → 18% → ...  │
└──────────────────────────────┴───────────────────────────────┘
│                                                              │
│ RECENT ACTIVITY                                             │
│ • Jane Doe converted Lead #123 to Customer                 │
│ • Mike logged call with TechCorp (Opp #45)                 │
│ • Sarah sent proposal to StartupX                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema Changes

### New Collections:

1. **`activities`** - CRM activity/interaction tracking
2. **`crm_tasks`** - CRM-specific tasks and todos (or extend existing `tasks`)

### Modified Collections:

1. **`leads`** - Add fields:
   - `follow_up_date: datetime`
   - `last_contacted: datetime`
   - `next_action: str`

2. **`opportunities`** - Add fields:
   - `next_step_date: datetime`
   - `last_activity_date: datetime`

### Indexes Required:

```python
# activities collection
await db.activities.create_index("entity_type")
await db.activities.create_index("entity_id")
await db.activities.create_index([("entity_type", 1), ("entity_id", 1)])
await db.activities.create_index("activity_type")
await db.activities.create_index("activity_date")
await db.activities.create_index("created_by_user_id")
await db.activities.create_index([("follow_up_required", 1), ("follow_up_date", 1)])

# crm_tasks collection
await db.crm_tasks.create_index("entity_type")
await db.crm_tasks.create_index("entity_id")
await db.crm_tasks.create_index("assigned_to")
await db.crm_tasks.create_index("due_date")
await db.crm_tasks.create_index("priority")
await db.crm_tasks.create_index("status")
await db.crm_tasks.create_index([("assigned_to", 1), ("status", 1), ("due_date", 1)])
```

---

## Implementation Priority Matrix

| Feature | Priority | Effort | Impact | Dependencies |
|---------|----------|--------|--------|--------------|
| Lead → Opportunity Conversion | P0 | Medium | High | None |
| Lead → Customer Conversion | P0 | Medium | High | None |
| Opportunity → Customer Conversion | P0 | Medium | High | None |
| Activity/Interaction Model | P0 | High | High | None |
| Activity Logging UI | P0 | Medium | High | Activity Model |
| Follow-up Dates on Leads/Opps | P0 | Low | High | None |
| CRM Task Model | P0 | Medium | High | None |
| Task Dashboard Widget | P0 | Medium | High | Task Model |
| Real Dashboard Metrics Endpoint | P0 | Medium | High | None |
| Dashboard Frontend Redesign | P0 | High | High | Metrics Endpoint |
| Sales Pipeline Visualization | P1 | Medium | Medium | Metrics Endpoint |
| Activity Timeline Component | P1 | Medium | High | Activity Model |
| Email Integration Hooks | P2 | High | Medium | Activity Model |
| Relationship Map View | P2 | Medium | Low | None |
| Auto-update Opportunity Probability | P2 | Low | Low | None |

**P0** = Critical (Must have for complete CRM)
**P1** = Important (Should have soon)
**P2** = Nice to have (Can defer)

---

## Sample User Workflows

### Workflow 1: Lead to Customer Journey

```
1. Marketing generates lead from website form
   → Create Lead with source "Website - Contact Form"

2. Sales rep calls lead next day
   → Log Activity: "Call - Initial contact made"
   → Create Task: "Send product info" (due tomorrow)
   → Set follow_up_date: 3 days from now

3. Follow-up appears on dashboard
   → Sales rep calls again
   → Log Activity: "Call - Interested, wants demo"
   → Convert Lead → Opportunity
     - Name: "Acme Corp - Enterprise License"
     - Amount: $50,000
     - Probability: 25%
     - Stage: Qualification

4. Opportunity progresses
   → Create Task: "Schedule demo" (due this week)
   → Log Activity: "Demo completed"
   → Update stage to "Proposal"
   → Update probability to 60%
   → Create Task: "Send proposal" (due in 2 days)

5. Deal closes
   → Click "Mark as Won"
   → Convert Opportunity → Customer
   → Create invoice (optional)
   → Create project (optional)
   → Customer lifetime_value updated with deal amount
```

---

### Workflow 2: Dashboard Task Management

```
1. Sales manager logs in
   → Dashboard shows:
     - 3 overdue tasks (RED ALERT)
     - 5 tasks due today
     - 12 tasks due this week
     - Pipeline value: $485K
     - 8 new leads this week

2. Clicks overdue task
   → Opens lead detail page
   → Sees activity timeline
   → Makes call
   → Logs activity
   → Completes task
   → Creates new follow-up task

3. Views sales pipeline
   → Sees 12 opportunities in "Proposal" stage
   → Filters by assigned user
   → Clicks opportunity
   → Updates stage to "Negotiation"
   → Probability auto-updates to 75%
   → Sets next_step_date: Friday
```

---

## Testing Requirements

### Unit Tests:
- Lead conversion logic
- Opportunity conversion logic
- Activity creation and filtering
- Task priority sorting
- Dashboard metrics calculations

### Integration Tests:
- Full conversion workflow end-to-end
- Activity timeline retrieval
- Task dashboard data aggregation
- Multi-user task assignment

### Frontend Tests:
- Conversion modals
- Activity logging forms
- Task completion
- Dashboard widget rendering

---

## Documentation Requirements

1. **User Guide:**
   - How to convert leads to opportunities
   - How to convert opportunities to customers
   - How to log activities
   - How to manage tasks
   - How to read dashboard metrics

2. **API Documentation:**
   - All new conversion endpoints
   - Activity endpoints
   - Task endpoints
   - Dashboard metrics endpoint

3. **Developer Guide:**
   - Activity model usage
   - Task model usage
   - Extending activity types
   - Custom dashboard widgets

---

## Rollout Plan

### Sprint 1 (Week 1-2):
- ✅ Lead → Opportunity conversion (backend + frontend)
- ✅ Lead → Customer conversion (backend + frontend)
- ✅ Opportunity → Customer conversion (backend + frontend)
- ✅ Add follow_up_date fields to models

### Sprint 2 (Week 3-4):
- ✅ Activity model and endpoints
- ✅ Activity logging UI
- ✅ Activity timeline component

### Sprint 3 (Week 5-6):
- ✅ CRM Task model and endpoints
- ✅ Task dashboard widget
- ✅ Task management UI on CRM pages

### Sprint 4 (Week 7-8):
- ✅ Real dashboard metrics endpoint
- ✅ Dashboard frontend redesign
- ✅ Sales pipeline visualization

### Sprint 5 (Week 9-10):
- ✅ Polish and bug fixes
- ✅ Testing and QA
- ✅ Documentation
- ✅ User training materials

---

## Success Metrics

After implementation, measure:

1. **User Adoption:**
   - % of leads converted using conversion feature (target: >80%)
   - % of opportunities with logged activities (target: >90%)
   - % of users logging into dashboard daily (target: >70%)

2. **Data Quality:**
   - % of leads with follow-up dates (target: >80%)
   - % of opportunities with next_step_date (target: >90%)
   - Average activities per opportunity (target: >5)

3. **Sales Efficiency:**
   - Time from lead creation to conversion (track improvement)
   - % of follow-ups completed on time (target: >85%)
   - Opportunity conversion rate (track improvement)

4. **System Usage:**
   - Daily active users on CRM module
   - Activities logged per day
   - Tasks completed per day

---

## Conclusion

These enhancements will transform the ERP CRM from a basic contact manager into a complete sales workflow system with:

✅ **Complete conversion workflows** (Lead → Opportunity → Customer)
✅ **Full activity tracking** (calls, emails, meetings, notes)
✅ **Task/todo management** with priorities and due dates
✅ **Actionable dashboard** with real metrics and upcoming tasks
✅ **Sales pipeline visibility** with forecasting
✅ **Follow-up management** to never miss an opportunity

**Estimated Total Effort:** 10-12 weeks (2.5-3 months)
**Estimated Backend Development:** 6-7 weeks
**Estimated Frontend Development:** 4-5 weeks

**Next Steps:**
1. Review and approve enhancement plan
2. Prioritize features if needed
3. Assign development resources
4. Begin Sprint 1 implementation
