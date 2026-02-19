# EventPilot - Planning & Architecture

**Version:** 1.0
**Last Updated:** 2025-10-24
**Status:** Initial Planning

---

## 🎯 Vision

**EventPilot** is a mobile-first, AI-driven event management platform that automates event planning, task coordination, and team communication through voice AI and intelligent workflows.

**Tagline:** *Plan less. Celebrate more.*

**Core Value Proposition:**
- Automated voice calls to follow up with responsible persons
- Smart task generation and timeline management
- Pay-per-use pricing (credits for calls/messages)
- AI-powered recommendations and escalations
- Multi-channel notifications (voice, SMS, WhatsApp, push)

---

## 🏗️ System Architecture

### Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Mobile App** | React Native (Expo) | Cross-platform, shared codebase, fast development |
| **Web Dashboard** | Next.js / React | Event organizers need desktop access |
| **Backend API** | FastAPI (Python) | Consistent with KasaAI stack, async support, type-safe |
| **Database** | MongoDB | Flexible schema for events, tasks, wallet transactions |
| **Authentication** | Supabase Auth | Phone + OTP, consistent with KasaAI infrastructure |
| **Shared Services** | **✓ VAPI** (`apps/shared/integration/vapi.py`)<br>**✓ n8n** (`apps/shared/integration/n8n.py`)<br>**✓ Wallet** (`apps/shared/integration/wallet.py`)<br>**✓ UsageCalculator** (`apps/shared/integration/usage_calculator.py`)<br>**✓ RAG** (`apps/shared/integration/rag.py`) | Voice AI calling, workflow automation, payment processing, cost tracking, AI recommendations |
| **Notifications** | - Orchestration: **n8n workflows** (shared service)<br>- SMS: Twilio<br>- Voice: **VAPI** (shared service)<br>- Push: Firebase Cloud Messaging<br>- WhatsApp: Twilio WhatsApp API<br>- Email: SendGrid | Multi-channel automation via shared services |
| **AI Layer** | - Voice: **VAPI with GPT-4**<br>- Recommendations: **RAG service with Gemini/OpenAI**<br>- Task generation: LangChain + LLMs | Conversational AI, context-aware suggestions, intelligent planning |
| **File Storage** | Supabase Storage | Event documents, call recordings, profile images |
| **Hosting** | Backend: VPS (existing KasaAI infrastructure)<br>Mobile: Expo EAS | Cost-effective, controlled environment |

---

### Shared Services Integration

EventPilot maximizes reuse of KasaAI's shared services to accelerate development:

**✓ VAPI Service** (`apps/shared/integration/vapi.py`)
- Automated voice calls to responsible persons
- Interactive voice responses (IVR) for task confirmations
- Real-time transcription and conversation state
- Ideal for: Follow-up calls, status updates, escalations
- **1100+ lines** of production-ready code
- **Development time saved: 4-5 weeks**

**✓ n8n Workflow Service** (`apps/shared/integration/n8n.py`)
- Multi-channel reminder orchestration
- Conditional task escalation workflows
- Scheduled check-ins (e.g., "Call Ben in 2 days if no update")
- Integration with Twilio, VAPI, FCM, SendGrid
- **750+ lines** of production-ready code
- **Development time saved: 3-4 weeks**

**✓ Wallet Service** (`apps/shared/integration/wallet.py`)
- Pay-per-use credit system
- Multi-gateway support (Paystack, Stripe, MoMo)
- Idempotent transaction handling
- Real-time balance tracking
- Automatic low-balance alerts
- **900+ lines** of production-ready code
- **Development time saved: 3-4 weeks**

**✓ Usage Calculator** (`apps/shared/integration/usage_calculator.py`)
- Cost tracking for voice calls (per minute)
- Cost tracking for SMS/WhatsApp messages
- Tiered pricing support (Free, Basic, Premium, Enterprise)
- Detailed cost breakdowns per event
- **600+ lines** of production-ready code
- **Development time saved: 1-2 weeks**

**✓ RAG Service** (`apps/shared/integration/rag.py`)
- AI-powered event recommendations
- Semantic search over event templates and best practices
- Context-aware task suggestions
- Knowledge base for common event planning queries
- **750+ lines** of production-ready code
- **Development time saved: 3-4 weeks**

**Total Development Time Saved: 14-19 weeks (3.5-4.75 months)**

---

## 🎨 Core Modules

### 1. **Authentication & User Management**

**Features:**
- Phone number + OTP login
- User profiles with organization affiliation
- Role-based access (Event Organizer, Team Member, Viewer)
- Credit balance display

**Database Schema:**
```python
User:
  - id: ObjectId
  - phone: str (unique, indexed)
  - name: str
  - email: str (optional)
  - organization: str (optional)
  - roles: List[str]  # ['organizer', 'member', 'viewer']
  - wallet_id: str (ref: Wallet service)
  - created_at: datetime
  - last_active: datetime
  - profile_image_url: str (optional)
  - fcm_token: str (optional)
```

---

### 2. **Event Setup Wizard**

**Features:**
- Quick event creation (name, date, type, guests, location, budget)
- AI-powered task generation based on event type
- Responsible person assignment
- Timeline auto-generation (backward from event date)
- Document upload (schedules, checklists)

**Database Schema:**
```python
Event:
  - id: ObjectId
  - name: str  # "Impact 2025"
  - type: str  # "conference", "wedding", "concert", "outreach", "corporate"
  - date: datetime
  - location: str
  - venue_coordinates: GeoJSON Point (optional)
  - num_guests: int
  - budget_min: Decimal (optional)
  - budget_max: Decimal (optional)
  - status: str  # "planning", "active", "completed", "cancelled"
  - organizer_id: ObjectId (ref: User)
  - created_at: datetime
  - description: str
  - documents: List[str]  # URLs to uploaded files
  - tags: List[str]  # ["church", "youth", "public"]

ResponsiblePerson:
  - id: ObjectId
  - event_id: ObjectId (ref: Event)
  - name: str
  - phone: str
  - email: str (optional)
  - role: str  # "transport_lead", "catering_lead", "protocol", etc.
  - user_id: ObjectId (optional, if registered user)
  - created_at: datetime
```

**AI Task Generation:**
```python
from apps.shared.integration.rag import RAGService, create_rag_service_from_env

# Initialize RAG service for event recommendations
rag_service = await create_rag_service_from_env(ai_provider="gemini")

# Query knowledge base for event type
result = await rag_service.query_knowledge_base(
    collection_name="event_planning_templates",
    query=f"What tasks are needed for a {event.type} event with {event.num_guests} guests?",
    context={
        "event_type": event.type,
        "budget_range": f"{event.budget_min}-{event.budget_max}",
        "location": event.location
    }
)

# Generate tasks based on AI recommendations
suggested_tasks = parse_ai_response(result.answer)

# Auto-assign deadlines based on event date
for task in suggested_tasks:
    deadline = calculate_deadline(
        event_date=event.date,
        days_before=task["recommended_days_before"]
    )
    await create_task(event_id=event.id, task=task, deadline=deadline)
```

---

### 3. **Smart Task & Timeline Management**

**Features:**
- AI-generated to-do lists grouped by category
- Milestone tracking with color-coded progress
- Deadline auto-calculation
- Task dependencies (e.g., "Book venue" before "Send invitations")
- Real-time progress dashboard

**Database Schema:**
```python
Task:
  - id: ObjectId
  - event_id: ObjectId (ref: Event)
  - title: str  # "Book venue"
  - description: str
  - category: str  # "logistics", "marketing", "catering", "transport", "protocol"
  - priority: str  # "critical", "high", "medium", "low"
  - status: str  # "pending", "in_progress", "completed", "blocked"
  - assigned_to: ObjectId (ref: ResponsiblePerson)
  - deadline: datetime
  - created_at: datetime
  - completed_at: datetime (optional)
  - depends_on: List[ObjectId]  # Task dependencies
  - estimated_cost: Decimal (optional)
  - actual_cost: Decimal (optional)
  - notes: str
  - last_followup_at: datetime (optional)
  - followup_count: int  # Track number of reminders sent

TaskUpdate:
  - id: ObjectId
  - task_id: ObjectId (ref: Task)
  - update_text: str
  - status: str  # New status after update
  - updated_by: str  # "ai_call", "manual", "team_member"
  - source: str  # "voice_call", "sms", "app", "dashboard"
  - timestamp: datetime
  - call_recording_url: str (optional)
  - transcription: str (optional)
```

---

### 4. **Automated Voice & Messaging Assistant**

**Features:**
- Automated voice calls to responsible persons via VAPI
- Interactive voice response (IVR) for task confirmations
- SMS/WhatsApp reminders via n8n workflows
- Real-time transcription and dashboard updates
- Escalation logic for overdue tasks
- Daily summary reports to organizer

**AI Assistant Persona - "Ama":**
```
Name: Ama
Tone: Warm, polite, efficient, professional
Language: Ghanaian English
Context-aware: Knows event details, task history, person's role
```

**Implementation with VAPI:**

```python
from apps.shared.integration.vapi import VAPIService

vapi = VAPIService()

# Create VAPI assistant for event follow-ups
assistant = await vapi.create_assistant(
    name="Ama - Event Coordinator",
    first_message="Hello {{responsible_person.name}}, this is Ama calling about {{event.name}}. I'm checking if you've made progress on {{task.title}}?",
    model="gpt-4o",
    voice="jennifer",
    server_url="https://events.kasaai.ailabsafrica.com/api/v1/vapi/webhook",
    functions=[
        {
            "name": "update_task_status",
            "description": "Update task status based on person's response",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["completed", "in_progress", "blocked"]},
                    "notes": {"type": "string"},
                    "estimated_completion": {"type": "string"}
                }
            }
        },
        {
            "name": "request_callback",
            "description": "Schedule a callback for later",
            "parameters": {
                "type": "object",
                "properties": {
                    "callback_datetime": {"type": "string"},
                    "reason": {"type": "string"}
                }
            }
        }
    ]
)

# Initiate follow-up call
async def call_responsible_person(task: Task, person: ResponsiblePerson):
    """Make automated follow-up call via VAPI."""
    call = await vapi.create_phone_call(
        assistant_id=assistant.id,
        customer_number=person.phone,
        metadata={
            "task_id": str(task.id),
            "event_id": str(task.event_id),
            "person_id": str(person.id),
            "responsible_person_name": person.name,
            "task_title": task.title,
            "event_name": event.name,
            "deadline": task.deadline.isoformat()
        }
    )

    # Deduct call cost from organizer's wallet
    usage_calculator = UsageCalculator(tier=organizer.pricing_tier)
    call_cost = usage_calculator.calculate_voice_call_cost(
        duration_minutes=0,  # Will be updated after call
        direction="outbound",
        platform="vapi"
    )

    await wallet_service.debit(
        wallet_id=organizer.wallet_id,
        amount=call_cost.total_cost,
        description=f"Call: {person.name} - {task.title}",
        idempotency_key=f"call-{call.id}",
        metadata={"task_id": str(task.id), "call_id": call.id}
    )

    return call
```

**VAPI Webhook Handler:**
```python
# apps/event_manager/backend/app/api/routes/vapi.py
from fastapi import APIRouter, Request
from apps.shared.integration.vapi import VAPIWebhookEvent

router = APIRouter()

@router.post("/webhook")
async def handle_vapi_webhook(request: Request):
    """Handle VAPI function calls and call events."""
    data = await request.json()
    event = VAPIWebhookEvent(**data)

    if event.message.type == "function-call":
        function_name = event.message.function_call.name
        args = event.message.function_call.parameters
        task_id = event.call.metadata["task_id"]

        if function_name == "update_task_status":
            # Update task in database
            await db.tasks.update_one(
                {"_id": ObjectId(task_id)},
                {
                    "$set": {
                        "status": args["status"],
                        "last_followup_at": datetime.utcnow()
                    },
                    "$inc": {"followup_count": 1}
                }
            )

            # Log task update
            await db.task_updates.insert_one({
                "task_id": ObjectId(task_id),
                "update_text": args["notes"],
                "status": args["status"],
                "updated_by": "ai_call",
                "source": "voice_call",
                "timestamp": datetime.utcnow(),
                "transcription": event.message.transcript
            })

            # Send notification to organizer
            await notify_organizer(task_id, args["status"], args["notes"])

            return {"result": {"success": True, "message": "Task updated successfully"}}

        elif function_name == "request_callback":
            # Schedule callback in n8n
            await schedule_callback(task_id, args["callback_datetime"], args["reason"])
            return {"result": {"success": True, "message": "Callback scheduled"}}

    elif event.message.type == "call-ended":
        # Update call duration and cost
        duration_minutes = event.call.duration / 60
        await update_call_cost(event.call.id, duration_minutes)

    return {"status": "ok"}
```

**Multi-Channel Reminders with n8n:**
```python
from apps.shared.integration.n8n import N8NService

n8n = N8NService()

# Create escalation workflow
workflow = await n8n.create_workflow(
    name=f"Task Escalation - {event.name}",
    nodes=[
        {
            "type": "n8n-nodes-base.webhook",
            "parameters": {"path": "task-escalation"}
        },
        {
            "type": "n8n-nodes-base.switch",
            "parameters": {
                "rules": [
                    {"field": "days_overdue", "operation": "greaterThan", "value": 3},
                    {"field": "days_overdue", "operation": "greaterThan", "value": 1}
                ]
            }
        },
        # If >3 days overdue: Call + SMS + notify organizer
        {
            "type": "n8n-nodes-base.httpRequest",
            "parameters": {
                "method": "POST",
                "url": "https://events.kasaai.ailabsafrica.com/api/v1/vapi/call",
                "body": {
                    "task_id": "={{$json.task_id}}",
                    "phone": "={{$json.phone}}"
                }
            }
        },
        # If 1-3 days overdue: SMS only
        {
            "type": "n8n-nodes-base.twilio",
            "parameters": {
                "operation": "send",
                "to": "={{$json.phone}}",
                "message": "Reminder: {{$json.task_title}} is overdue. Please provide an update. - {{$json.event_name}}"
            }
        }
    ]
)

# Trigger escalation for overdue tasks
for task in overdue_tasks:
    days_overdue = (datetime.utcnow() - task.deadline).days
    await n8n.execute_workflow(
        workflow_id=workflow.id,
        data={
            "task_id": str(task.id),
            "task_title": task.title,
            "phone": task.assigned_person.phone,
            "days_overdue": days_overdue,
            "event_name": event.name
        }
    )
```

---

### 5. **Wallet & Credit System**

**Features:**
- Pre-paid credit system (load via MoMo, Paystack, Stripe)
- Real-time cost deduction per action
- Low-balance alerts (< ₵10)
- Transaction history and usage reports
- Pricing tiers (Free, Basic, Premium, Enterprise)

**Pricing Table:**

| Action | Free Tier | Basic Tier | Premium Tier |
|--------|-----------|------------|--------------|
| Event creation | Free | Free | Free |
| AI task generation | 3/month | Unlimited | Unlimited |
| Voice call (per min) | N/A | ₵2.00 | ₵1.50 |
| SMS reminder | N/A | ₵0.20 | ₵0.15 |
| WhatsApp message | N/A | ₵0.30 | ₵0.25 |
| AI recommendations | 10/month | 100/month | Unlimited |

**Implementation with Shared Services:**
```python
from apps.shared.integration.wallet import WalletService, create_wallet_service_from_env
from apps.shared.integration.usage_calculator import UsageCalculator, PricingTier

# Initialize services
wallet_service = await create_wallet_service_from_env()
usage_calculator = UsageCalculator(tier=PricingTier.BASIC)

# Create wallet for new user
wallet = await wallet_service.create_wallet(
    user_id=str(user.id),
    currency="GHS",
    initial_balance=Decimal("50.00")  # Welcome bonus
)

# Top-up via Paystack
payment_response = await wallet_service.initiate_paystack_topup(
    wallet_id=wallet.wallet_id,
    amount=Decimal("100.00"),
    email=user.email,
    callback_url="https://events.kasaai.ailabsafrica.com/wallet/callback"
)

# Deduct cost for voice call
call_cost = usage_calculator.calculate_voice_call_cost(
    duration_minutes=2.5,
    direction="outbound",
    platform="vapi"
)

await wallet_service.debit(
    wallet_id=user.wallet_id,
    amount=call_cost.total_cost,
    description=f"Voice call: {person.name} - {task.title}",
    idempotency_key=f"call-{call_id}",
    allow_negative=False,  # Block call if insufficient balance
    metadata={
        "event_id": str(event.id),
        "task_id": str(task.id),
        "call_id": call_id,
        "duration_minutes": 2.5
    }
)

# Check balance before action
balance = await wallet_service.get_balance(user.wallet_id)
if balance < Decimal("10.00"):
    await send_low_balance_alert(user)
```

---

### 6. **Organizer Dashboard**

**Features:**
- Overview of all active events
- Task progress visualization (pie charts, progress bars)
- Timeline view (Gantt-style)
- Responsible person directory
- Manual actions: "Call Now," "Remind," "Mark Complete," "Escalate"
- AI-generated daily summary
- Wallet balance and transaction history
- Usage analytics (calls made, messages sent, cost per event)

**Dashboard Metrics:**
```python
class EventDashboard:
    """Event dashboard with real-time metrics."""

    async def get_event_metrics(self, event_id: str) -> dict:
        """Get comprehensive event metrics."""
        event = await db.events.find_one({"_id": ObjectId(event_id)})
        tasks = await db.tasks.find({"event_id": ObjectId(event_id)}).to_list(None)

        # Task statistics
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t["status"] == "completed")
        overdue_tasks = sum(
            1 for t in tasks
            if t["deadline"] < datetime.utcnow() and t["status"] != "completed"
        )

        # Cost statistics
        usage_calculator = UsageCalculator(tier=organizer.pricing_tier)
        total_cost = Decimal("0.00")

        # Calculate costs from wallet transactions
        transactions = await wallet_service.get_transactions(
            wallet_id=organizer.wallet_id,
            filters={"metadata.event_id": str(event_id)}
        )
        total_cost = sum(t["amount"] for t in transactions if t["type"] == "debit")

        # Generate AI summary
        rag_service = await create_rag_service_from_env()
        summary = await rag_service.query_knowledge_base(
            collection_name="event_summaries",
            query=f"Summarize the current status and provide recommendations for {event['name']}",
            context={
                "total_tasks": total_tasks,
                "completed": completed_tasks,
                "overdue": overdue_tasks,
                "days_until_event": (event["date"] - datetime.utcnow()).days
            }
        )

        return {
            "event": event,
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "in_progress": sum(1 for t in tasks if t["status"] == "in_progress"),
                "pending": sum(1 for t in tasks if t["status"] == "pending"),
                "overdue": overdue_tasks,
                "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            "costs": {
                "total_spent": float(total_cost),
                "voice_calls": sum(1 for t in transactions if "call" in t.get("description", "").lower()),
                "messages_sent": sum(1 for t in transactions if "sms" in t.get("description", "").lower() or "whatsapp" in t.get("description", "").lower())
            },
            "ai_summary": summary.answer,
            "days_until_event": (event["date"] - datetime.utcnow()).days,
            "next_actions": await get_next_actions(event_id)
        }
```

---

### 7. **AI Recommendations Engine**

**Features:**
- Proactive task suggestions ("Order banners this week")
- Missing item detection ("No photographer assigned")
- Risk alerts ("Catering not confirmed 3 days before event")
- Best practices from knowledge base
- Personalized tips based on event type

**Implementation:**
```python
from apps.shared.integration.rag import RAGService

class EventRecommendationEngine:
    """AI-powered recommendation engine using RAG service."""

    def __init__(self):
        self.rag = await create_rag_service_from_env(ai_provider="gemini")

    async def get_recommendations(self, event_id: str) -> List[dict]:
        """Get AI recommendations for event."""
        event = await db.events.find_one({"_id": ObjectId(event_id)})
        tasks = await db.tasks.find({"event_id": ObjectId(event_id)}).to_list(None)

        days_until_event = (event["date"] - datetime.utcnow()).days

        # Query RAG for recommendations
        result = await self.rag.query_knowledge_base(
            collection_name="event_best_practices",
            query=f"What should I focus on for a {event['type']} event that is {days_until_event} days away?",
            context={
                "event_type": event["type"],
                "days_remaining": days_until_event,
                "num_guests": event.get("num_guests"),
                "completed_tasks": [t["title"] for t in tasks if t["status"] == "completed"],
                "pending_tasks": [t["title"] for t in tasks if t["status"] == "pending"],
                "overdue_tasks": [
                    t["title"] for t in tasks
                    if t["deadline"] < datetime.utcnow() and t["status"] != "completed"
                ]
            }
        )

        # Parse AI recommendations
        recommendations = self._parse_recommendations(result.answer)

        # Add rule-based recommendations
        recommendations.extend(await self._detect_missing_tasks(event, tasks))
        recommendations.extend(await self._detect_risks(event, tasks, days_until_event))

        return recommendations

    async def _detect_missing_tasks(self, event: dict, tasks: List[dict]) -> List[dict]:
        """Detect common missing tasks based on event type."""
        task_titles = {t["title"].lower() for t in tasks}
        recommendations = []

        # Essential tasks by event type
        essential_tasks = {
            "conference": ["venue", "sound", "catering", "transport", "program"],
            "wedding": ["venue", "catering", "photography", "decoration", "invitations"],
            "concert": ["venue", "sound", "security", "ticketing", "promotion"]
        }

        for essential in essential_tasks.get(event["type"], []):
            if not any(essential in title for title in task_titles):
                recommendations.append({
                    "type": "missing_task",
                    "priority": "high",
                    "message": f"Consider adding: {essential.title()}",
                    "action": "create_task"
                })

        return recommendations

    async def _detect_risks(
        self,
        event: dict,
        tasks: List[dict],
        days_until_event: int
    ) -> List[dict]:
        """Detect potential risks based on timeline."""
        recommendations = []

        # Critical tasks not completed near event date
        critical_categories = ["venue", "transport", "catering"]

        for task in tasks:
            if task["status"] != "completed" and any(
                cat in task["category"].lower() for cat in critical_categories
            ):
                if days_until_event <= 7:
                    recommendations.append({
                        "type": "risk_alert",
                        "priority": "critical",
                        "message": f"URGENT: {task['title']} not completed - only {days_until_event} days left",
                        "action": "escalate",
                        "task_id": str(task["_id"])
                    })
                elif days_until_event <= 14:
                    recommendations.append({
                        "type": "risk_alert",
                        "priority": "high",
                        "message": f"WARNING: {task['title']} should be completed soon",
                        "action": "remind",
                        "task_id": str(task["_id"])
                    })

        return recommendations
```

---

## 📱 Mobile App Structure

### Navigation

```
TabNavigator:
├── Home
│   ├── Active events list
│   ├── Quick stats
│   ├── Wallet balance
│   └── Recent activity
├── Events
│   ├── All Events
│   ├── Event Details
│   │   ├── Overview
│   │   ├── Tasks
│   │   ├── Timeline
│   │   ├── Team
│   │   └── Budget
│   └── Create Event
├── Tasks
│   ├── My Tasks (if team member)
│   ├── Filter by status/category
│   └── Task details with updates
├── Wallet
│   ├── Balance & transactions
│   ├── Top-up
│   └── Usage analytics
└── Profile
    ├── Personal info
    ├── Settings
    └── Notification preferences
```

---

## 🔐 Security & Privacy

### Authentication
- Phone number verified via OTP
- JWT tokens for API authentication
- Session management via Supabase
- Role-based access control (RBAC)

### Data Privacy
- Minimal data collection (name, phone, email)
- Call recordings encrypted and auto-deleted after 30 days
- User consent for voice recording
- GDPR-compliant data export/deletion
- Responsible persons can opt-out of calls

### API Security
- HTTPS only
- Rate limiting on endpoints
- Input validation and sanitization
- MongoDB injection prevention
- CORS configuration
- API key rotation for external services

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│                   Users                         │
│  (Mobile App + Web Dashboard)                   │
└──────────────────┬──────────────────────────────┘
                   │
                   │ HTTPS
                   │
┌──────────────────▼──────────────────────────────┐
│          Nginx Reverse Proxy                    │
│      events.kasaai.ailabsafrica.com             │
└──────────────────┬──────────────────────────────┘
                   │
                   │
┌──────────────────▼──────────────────────────────┐
│        FastAPI Backend (Python)                 │
│    - REST API                                   │
│    - Business Logic                             │
│    - Integration Layer                          │
└──────┬──────────┬──────────┬───────────────────┘
       │          │          │
       │          │          │
  ┌────▼───┐ ┌───▼────┐ ┌──▼─────────┐
  │MongoDB │ │Supabase│ │Shared      │
  │        │ │Auth    │ │Services    │
  │        │ │Storage │ │(VAPI, n8n, │
  │        │ │        │ │Wallet, RAG)│
  └────────┘ └────────┘ └────────────┘
```

**Services:**
- Backend API: systemd service `kasaai-event-manager.service`
- Nginx config: `events.kasaai.ailabsafrica.com.conf`
- MongoDB: Existing KasaAI MongoDB instance
- Supabase: Existing KasaAI Supabase project

---

## 🎯 Development Principles

### Code Quality
- Follow PEP 8 for Python, ESLint/Prettier for JavaScript/TypeScript
- Type hints everywhere (Python), TypeScript for frontend
- Maximum 500 lines per file
- Comprehensive docstrings (Google style)
- Unit tests for all business logic (pytest)
- Integration tests for API endpoints

### File Structure
```
/opt/kasaai/apps/event_manager/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth.py
│   │   │   │   ├── events.py
│   │   │   │   ├── tasks.py
│   │   │   │   ├── wallet.py
│   │   │   │   ├── vapi.py
│   │   │   │   └── recommendations.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── event.py
│   │   │   ├── task.py
│   │   │   └── responsible_person.py
│   │   ├── schemas/
│   │   │   └── (Pydantic models for API)
│   │   ├── services/
│   │   │   ├── event_service.py
│   │   │   ├── task_service.py
│   │   │   ├── call_service.py
│   │   │   ├── recommendation_service.py
│   │   │   └── dashboard_service.py
│   │   └── main.py
│   ├── tests/
│   │   ├── test_events.py
│   │   ├── test_tasks.py
│   │   ├── test_calls.py
│   │   └── test_recommendations.py
│   ├── requirements.txt
│   └── .env
├── mobile/
│   ├── src/
│   │   ├── screens/
│   │   ├── components/
│   │   ├── navigation/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── contexts/
│   │   └── utils/
│   ├── app.json
│   ├── package.json
│   └── tsconfig.json
├── web/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── lib/
│   │   └── styles/
│   ├── package.json
│   └── next.config.js
├── docs/
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── USER_GUIDE.md
├── PLANNING.md
├── TASK.md
└── README.md
```

### Testing Strategy
- Unit tests for all services and utilities
- Integration tests for API endpoints with real MongoDB test database
- Mock VAPI/n8n calls in tests (use shared test utilities)
- E2E tests for critical flows (event creation, call workflow, payment)
- Test coverage minimum: 80%

### Git Workflow
- Branch: `dev` for active development
- Main branch: `main` for production
- Commit after each feature/task completion
- Descriptive commit messages following conventional commits

---

## 📊 Success Metrics

### User Engagement
- Daily active users
- Events created per user
- Task completion rate
- Call/message success rate
- Wallet top-up frequency

### Operational Efficiency
- Average time to complete event planning
- Reduction in manual follow-ups
- Task overdue rate
- Call answer rate
- Average cost per event

### Revenue Metrics
- Monthly recurring revenue (MRR)
- Average revenue per user (ARPU)
- Credit consumption rate
- Wallet balance churn

### User Satisfaction
- App rating
- Net Promoter Score (NPS)
- Feature usage patterns
- Support ticket volume

---

## 🔮 Future Expansion

### Phase 2 Features
- Vendor marketplace (photographers, caterers, venues)
- Budget tracker with invoice reminders
- WhatsApp bot for low-data users
- Calendar integrations (Google Calendar, Outlook)
- Multi-language support (Twi, Ga, French)

### Phase 3 Features
- Team collaboration (chat, file sharing)
- Event templates library
- Analytics dashboard (cost vs. timeline, success patterns)
- Voice kiosk for on-site check-ins
- Integration with booking platforms

### Revenue Model
- Freemium: 3 events/month, limited calls
- Basic: ₵30/month, unlimited events, pay-per-use calls
- Premium: ₵80/month, discounted calls, priority support
- Enterprise: Custom pricing, multi-org, API access

---

## 📝 Notes

- **Reliability first:** Voice calls and reminders are critical
- **Mobile-first:** Most users will access via phone
- **Simple UX:** Keep it intuitive for non-technical users
- **Cost transparency:** Show real-time cost in dashboard
- **Offline capabilities:** Cache events and tasks for offline viewing
- **Voice quality:** Test Ama's voice in various network conditions

---

**Document Version History:**
- v1.0 (2025-10-24): Initial planning document created with shared services integration
