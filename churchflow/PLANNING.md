# ChurchFlow - Planning & Architecture

**Version:** 1.0
**Last Updated:** 2025-10-23
**Status:** Initial Planning

---

## 🎯 Vision

**ChurchFlow** is a mobile-first church management and event coordination platform designed for conferences and large gatherings. It helps church members register for transportation, receive live updates, and feel personally connected through AI-powered voice and kiosk interactions.

**Tagline:** *Seamless movement. Warm connections.*

---

## 🏗️ System Architecture

### Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Mobile App** | React Native (Expo) | Cross-platform (iOS/Android), shared codebase, fast development |
| **Kiosk Interface** | React Web | Same component library as mobile, runs on tablets/iPads |
| **Backend API** | FastAPI (Python) | Consistent with KasaAI stack, async support, fast, type-safe |
| **Database** | MongoDB | Consistent with KasaAI apps, flexible schema for church data |
| **Authentication** | Supabase Auth | Phone number + OTP, consistent with KasaAI infrastructure |
| **Real-time Updates** | WebSockets (FastAPI) | Live bus tracking, notifications, kiosk updates |
| **Shared Services** | **✓ VAPI** (`apps/shared/integration/vapi.py`)<br>**✓ n8n** (`apps/shared/integration/n8n.py`)<br>**✓ Voice Lab** (TTS/STT) | Voice AI kiosk, workflow automation, notifications |
| **Notifications** | - Orchestration: **n8n workflows** (shared service)<br>- SMS: Twilio<br>- Push: Firebase Cloud Messaging<br>- WhatsApp: Twilio WhatsApp API<br>- Email: SendGrid | Multi-channel automation via shared n8n service |
| **Voice AI Kiosk** | **VAPI** (shared service) or **Voice Lab** (TTS/STT) | Voice interactions, personalized greetings, supports Twi/English |
| **Motion Detection** | Device camera + MediaPipe | Works on tablets/iPads without additional hardware |
| **File Storage** | Supabase Storage | Profile images, speaker photos, conference materials |
| **Hosting** | Backend: VPS (existing KasaAI infrastructure)<br>Mobile: Expo EAS | Cost-effective, controlled environment |

---

### Shared Services Integration

ChurchFlow leverages KasaAI's shared services for voice AI and workflow automation:

**✓ VAPI Service** (`apps/shared/integration/vapi.py`)
- Voice AI agent creation and management
- Inbound/outbound call handling
- Real-time transcription and conversation state
- Ideal for: AI kiosk voice interactions
- **1100+ lines** of production-ready code

**✓ n8n Workflow Service** (`apps/shared/integration/n8n.py`)
- Workflow orchestration for multi-channel notifications
- Conditional routing (SMS for urgent, email for receipts)
- Scheduled workflows (conference reminders)
- Integration with Twilio, FCM, SendGrid
- **750+ lines** of production-ready code

**✓ Voice Lab** (TTS/STT services)
- Text-to-speech in multiple languages (Twi, English, Ga)
- Speech-to-text via Whisper
- Custom voice cloning
- Low latency for real-time interactions

**Implementation Options for Voice Kiosk:**

1. **Option A: VAPI Integration** (Recommended for complex conversational AI)
   - Use shared VAPI service for full conversational agent
   - Automatic conversation flow management
   - Built-in context tracking
   - Webhook support for database lookups

2. **Option B: Voice Lab Direct** (Recommended for simple greetings)
   - Use Voice Lab TTS for pre-generated greetings
   - STT for basic name capture
   - Manual conversation state management
   - Lower latency for simple interactions

---

## 🎨 Core Modules

### 1. **Authentication & User Management**

**Features:**
- Phone number + OTP login
- User profiles with branch assignment
- Role-based access control (Super Admin, Branch Admin, Transport Coordinator, Conference Admin)
- Volunteer role tracking (choir, usher, media, etc.)

**Database Schema:**
```python
User:
  - id: ObjectId
  - phone: str (unique, indexed)
  - name: str
  - branch_id: ObjectId (ref: Branch)
  - roles: List[str]  # ['member', 'admin', 'transport_coordinator']
  - volunteer_roles: List[str]  # ['choir', 'usher', 'media']
  - created_at: datetime
  - last_active: datetime
  - profile_image_url: str (optional)

Branch:
  - id: ObjectId
  - name: str  # "Legon", "Tema", "Osu", "Madina"
  - location: GeoJSON Point
  - contact_person: str
  - contact_phone: str
  - created_at: datetime
```

---

### 2. **Bus Transportation Coordination**

**Features:**
- Bus route management by location
- Member registration for specific buses
- Capacity tracking and auto-assignment
- Real-time delay notifications (geo-filtered)
- Admin dashboard for route management

**Database Schema:**
```python
BusRoute:
  - id: ObjectId
  - name: str  # "Legon Bus #1"
  - pickup_location: str
  - pickup_coordinates: GeoJSON Point
  - departure_time: datetime
  - capacity: int
  - conference_id: ObjectId (ref: Conference)
  - driver_name: str
  - driver_phone: str
  - status: str  # "scheduled", "delayed", "departed", "arrived", "cancelled"
  - created_at: datetime

BusRegistration:
  - id: ObjectId
  - user_id: ObjectId (ref: User)
  - bus_route_id: ObjectId (ref: BusRoute)
  - conference_id: ObjectId (ref: Conference)
  - registration_status: str  # "confirmed", "waitlisted", "cancelled"
  - seat_number: int (optional)
  - checked_in: bool
  - checked_in_at: datetime (optional)
  - created_at: datetime

BusUpdate:
  - id: ObjectId
  - bus_route_id: ObjectId (ref: BusRoute)
  - message: str
  - update_type: str  # "delay", "departure", "arrival", "cancellation"
  - delay_minutes: int (optional)
  - sent_at: datetime
  - sent_by: ObjectId (ref: User)
```

**Business Logic:**
- When a bus reaches capacity, auto-assign registrants to next available bus for same pickup location
- Send notifications only to users registered for that specific bus route
- Allow transport coordinators to send targeted updates

---

### 3. **Conference Registration & Management**

**Features:**
- Conference creation and management
- Member registration
- Speaker profiles and session schedules
- QR code check-in
- Attendance tracking

**Database Schema:**
```python
Conference:
  - id: ObjectId
  - name: str  # "Impact 2025"
  - description: str
  - start_date: datetime
  - end_date: datetime
  - venue: str
  - venue_coordinates: GeoJSON Point
  - banner_image_url: str
  - registration_open: bool
  - max_capacity: int (optional)
  - created_at: datetime
  - created_by: ObjectId (ref: User)

Speaker:
  - id: ObjectId
  - conference_id: ObjectId (ref: Conference)
  - name: str
  - title: str  # "Pastor", "Bishop", "Guest Speaker"
  - bio: str
  - photo_url: str
  - session_topic: str (optional)
  - session_time: datetime (optional)

ConferenceRegistration:
  - id: ObjectId
  - user_id: ObjectId (ref: User)
  - conference_id: ObjectId (ref: Conference)
  - registration_date: datetime
  - checked_in: bool
  - check_in_time: datetime (optional)
  - check_in_method: str  # "qr_code", "phone", "kiosk"
  - qr_code: str (unique)
```

---

### 4. **AI Voice Kiosk System**

**Features:**
- Motion detection triggers greeting
- Voice input/output for interaction
- Database lookup for personalized greetings
- Display welcome animations
- Check-in integration

**Components:**
- Motion detection: Camera + MediaPipe or simple PIR sensor via web API
- Speech-to-text: Whisper API or KasaAI Voice Lab
- Text-to-speech: KasaAI Voice Lab (Twi/English voice)
- UI: Full-screen React web app with animations

**AI Assistant Persona - "Ama":**
```
Name: Ama
Tone: Warm, respectful, joyful, Ghanaian-accented English
Language: Primarily English, can greet in Twi
Context-aware: Knows user's name, branch, volunteer roles, attendance history
```

**Implementation Architecture:**

**Option A: VAPI-Powered Conversational Kiosk** (Recommended for rich interactions)
```python
from apps.shared.integration.vapi import VAPIService

# Initialize VAPI service
vapi = VAPIService()

# Create AI assistant for kiosk
assistant = await vapi.create_assistant(
    name="Ama - Church Kiosk",
    first_message="Good morning! Welcome to Impact 2025. What's your name and branch?",
    model="gpt-4o",
    voice="jennifer",  # Warm, professional voice
    server_url="https://church.kasaai.ailabsafrica.com/api/v1/kiosk/webhook",
    functions=[
        {
            "name": "lookup_member",
            "description": "Search for church member by name and branch",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "branch": {"type": "string"}
                }
            }
        },
        {
            "name": "check_in_member",
            "description": "Check in member for conference",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "conference_id": {"type": "string"}
                }
            }
        }
    ]
)

# When motion detected, start call
call = await vapi.create_web_call(
    assistant_id=assistant.id,
    metadata={"kiosk_id": "main_entrance", "conference_id": conference_id}
)
```

**Option B: Voice Lab Direct Integration** (Recommended for simple greetings)
```python
from apps.shared.integration.voice_lab import VoiceLabService

voice_lab = VoiceLabService()

# Pre-generate common greetings in Twi and English
greetings = {
    "morning_en": await voice_lab.text_to_speech(
        text="Good morning! Welcome to Impact 2025.",
        language="en",
        voice="female_ghanaian"
    ),
    "morning_twi": await voice_lab.text_to_speech(
        text="Maakye! Akwaaba Impact 2025.",
        language="tw",
        voice="female_ghanaian"
    )
}

# Listen for name
audio_input = await capture_audio()
transcription = await voice_lab.speech_to_text(
    audio_data=audio_input,
    language="en"
)

# Look up member
member = await db.users.find_one({"name": transcription.text})

# Generate personalized response
if member:
    greeting = generate_personalized_greeting(member)
    audio = await voice_lab.text_to_speech(greeting, "en", "female_ghanaian")
    await play_audio(audio)
```

**Interaction Flow:**
1. Motion detected → Display welcome animation
2. "Good morning! Welcome to [Conference Name]. What's your name and branch?"
3. User responds (voice or keypad)
4. System searches database:
   - **If found:** "Hi [Name] from [Branch] branch! It's great to see you again. [Personalized comment based on volunteer role]. Your bus departs at [time] from [location]."
   - **If new:** "Welcome! Please enter your name and branch so we can get to know you."
5. Offer to check in for conference
6. Display QR code or print badge

**Personalization Examples:**
```python
volunteer_role_greetings = {
    "choir": "Thank you for serving in the choir — you're such a blessing.",
    "usher": "Your service as an usher makes everyone feel welcome.",
    "media": "Thanks for capturing these special moments for us.",
    "protocol": "Thank you for helping things run smoothly.",
}

attendance_patterns = {
    "frequent": "It's always a joy to see you!",
    "returning": "Welcome back! We've missed you.",
    "first_time": "We're so glad you could join us!",
}

def generate_personalized_greeting(member: dict) -> str:
    """Generate contextual greeting based on member data."""
    greeting_parts = [f"Hi {member['name']} from {member['branch_name']} branch!"]

    # Add attendance pattern
    if member.get("attendance_count", 0) > 10:
        greeting_parts.append(attendance_patterns["frequent"])
    elif member.get("last_attendance"):
        greeting_parts.append(attendance_patterns["returning"])
    else:
        greeting_parts.append(attendance_patterns["first_time"])

    # Add volunteer role greeting
    if member.get("volunteer_roles"):
        role = member["volunteer_roles"][0]
        if role in volunteer_role_greetings:
            greeting_parts.append(volunteer_role_greetings[role])

    # Add bus info if registered
    if member.get("bus_registration"):
        bus = member["bus_registration"]
        greeting_parts.append(
            f"Your bus departs at {bus['departure_time']} from {bus['pickup_location']}."
        )

    return " ".join(greeting_parts)
```

**Webhook Handler for VAPI Function Calls:**
```python
# apps/church_manager/backend/app/api/routes/kiosk.py
from fastapi import APIRouter, Request
from apps.shared.integration.vapi import VAPIWebhookEvent

router = APIRouter()

@router.post("/webhook")
async def handle_vapi_webhook(request: Request):
    """Handle VAPI function calls from kiosk assistant."""
    data = await request.json()
    event = VAPIWebhookEvent(**data)

    if event.message.type == "function-call":
        function_name = event.message.function_call.name
        args = event.message.function_call.parameters

        if function_name == "lookup_member":
            # Search for member
            member = await db.users.find_one({
                "name": {"$regex": args["name"], "$options": "i"},
                "branch_name": {"$regex": args["branch"], "$options": "i"}
            })

            if member:
                # Return personalized data
                return {
                    "result": {
                        "found": True,
                        "name": member["name"],
                        "branch": member["branch_name"],
                        "volunteer_roles": member.get("volunteer_roles", []),
                        "bus_info": get_bus_info(member["_id"]),
                        "greeting": generate_personalized_greeting(member)
                    }
                }
            else:
                return {"result": {"found": False}}

        elif function_name == "check_in_member":
            # Check in member
            result = await check_in_service.check_in(
                user_id=args["user_id"],
                conference_id=args["conference_id"],
                method="kiosk"
            )
            return {"result": {"success": True, "qr_code": result.qr_code}}

    return {"status": "ok"}
```

---

### 5. **Notification System**

**Multi-channel notification routing:**

| Channel | Use Case | Priority |
|---------|----------|----------|
| **SMS** | Bus delays, urgent updates | High |
| **Push** | Conference reminders, general updates | Medium |
| **WhatsApp** | Rich media, session schedules | Medium |
| **Email** | Registration confirmations, receipts | Low |

**Database Schema:**
```python
NotificationTemplate:
  - id: ObjectId
  - name: str
  - template_type: str  # "bus_delay", "conference_reminder", "check_in_confirmation"
  - channels: List[str]  # ["sms", "push", "whatsapp", "email"]
  - message_template: str  # "Bus {bus_name} delayed by {delay} minutes. New ETA: {new_time}"
  - n8n_workflow_id: str (optional)  # For complex multi-channel workflows
  - created_at: datetime

NotificationLog:
  - id: ObjectId
  - user_id: ObjectId (ref: User)
  - template_id: ObjectId (ref: NotificationTemplate)
  - channel: str
  - message: str
  - sent_at: datetime
  - delivered: bool
  - delivered_at: datetime (optional)
  - error_message: str (optional)
```

**Implementation with n8n Workflow Orchestration:**

**Simple Direct Notification:**
```python
from apps.shared.integration.notification_service import NotificationService

notification_service = NotificationService()

# Send SMS to all users on a specific bus
await notification_service.send_sms(
    phone_numbers=[user.phone for user in bus_users],
    message=f"Bus {bus.name} delayed by {delay_minutes} minutes. New ETA: {new_eta}",
    sender_id="ChurchFlow"
)
```

**Complex Multi-Channel Workflow with n8n:**
```python
from apps.shared.integration.n8n import N8NService

n8n = N8NService()

# Create workflow for conference reminders
workflow = await n8n.create_workflow(
    name="Conference Reminder - Impact 2025",
    nodes=[
        {
            "type": "n8n-nodes-base.webhook",
            "parameters": {
                "path": "conference-reminder",
                "httpMethod": "POST"
            }
        },
        {
            "type": "n8n-nodes-base.switch",
            "parameters": {
                "rules": [
                    {"field": "hours_before", "operation": "lessThan", "value": 2},
                    {"field": "hours_before", "operation": "lessThan", "value": 24}
                ]
            }
        },
        {
            "type": "n8n-nodes-base.twilio",
            "parameters": {
                "operation": "send",
                "message": "Conference starts in {{hours_before}} hours! See you soon."
            }
        },
        {
            "type": "n8n-nodes-base.firebase",
            "parameters": {
                "operation": "sendNotification",
                "title": "Conference Reminder",
                "body": "Impact 2025 starts in {{hours_before}} hours!"
            }
        }
    ]
)

# Trigger workflow for all registered users
for user in conference_users:
    await n8n.execute_workflow(
        workflow_id=workflow.id,
        data={
            "user_id": str(user.id),
            "phone": user.phone,
            "fcm_token": user.fcm_token,
            "hours_before": calculate_hours_before(conference.start_date),
            "conference_name": conference.name,
            "venue": conference.venue
        }
    )
```

**Bus Delay Notification Workflow:**
```python
# apps/church_manager/backend/app/services/notification_service.py
from apps.shared.integration.n8n import N8NService
from typing import List

class ChurchNotificationService:
    """Church-specific notification service using n8n orchestration."""

    def __init__(self):
        self.n8n = N8NService()

    async def notify_bus_delay(
        self,
        bus_route_id: str,
        delay_minutes: int,
        new_eta: str,
        users: List[dict]
    ):
        """
        Send multi-channel notifications for bus delays.

        Routing logic:
        - <15 min delay: Push notification only
        - 15-30 min delay: Push + SMS
        - >30 min delay: Push + SMS + WhatsApp

        Args:
            bus_route_id: ID of delayed bus route
            delay_minutes: Minutes of delay
            new_eta: New estimated arrival time
            users: List of affected users
        """
        # Determine channels based on severity
        channels = ["push"]
        if delay_minutes >= 15:
            channels.append("sms")
        if delay_minutes >= 30:
            channels.append("whatsapp")

        # Get or create workflow
        workflow = await self._get_bus_delay_workflow()

        # Execute for each user
        for user in users:
            await self.n8n.execute_workflow(
                workflow_id=workflow.id,
                data={
                    "user_id": str(user["_id"]),
                    "phone": user["phone"],
                    "fcm_token": user.get("fcm_token"),
                    "delay_minutes": delay_minutes,
                    "new_eta": new_eta,
                    "bus_name": user["bus_name"],
                    "pickup_location": user["pickup_location"],
                    "channels": channels
                }
            )

            # Log notification
            await self._log_notification(
                user_id=user["_id"],
                channels=channels,
                message=f"Bus delayed by {delay_minutes} minutes"
            )

    async def _get_bus_delay_workflow(self) -> dict:
        """Get or create bus delay notification workflow."""
        # Check if workflow exists
        workflows = await self.n8n.list_workflows()
        existing = next(
            (w for w in workflows if w["name"] == "Bus Delay Notification"),
            None
        )

        if existing:
            return existing

        # Create new workflow
        return await self.n8n.create_workflow(
            name="Bus Delay Notification",
            nodes=[
                {
                    "type": "n8n-nodes-base.webhook",
                    "parameters": {"path": "bus-delay"}
                },
                {
                    "type": "n8n-nodes-base.switch",
                    "parameters": {
                        "rules": [
                            {"field": "channels", "operation": "contains", "value": "sms"},
                            {"field": "channels", "operation": "contains", "value": "whatsapp"}
                        ]
                    }
                },
                {
                    "type": "n8n-nodes-base.twilio",
                    "parameters": {
                        "operation": "send",
                        "to": "={{$json.phone}}",
                        "message": "Bus {{$json.bus_name}} delayed by {{$json.delay_minutes}} min. New ETA: {{$json.new_eta}}"
                    }
                },
                {
                    "type": "n8n-nodes-base.firebase",
                    "parameters": {
                        "operation": "sendNotification",
                        "token": "={{$json.fcm_token}}",
                        "title": "Bus Delay",
                        "body": "Your bus is delayed by {{$json.delay_minutes}} minutes"
                    }
                }
            ]
        )
```

**Conference Reminder Scheduler:**
```python
# Send reminders at specific intervals using n8n scheduling
async def schedule_conference_reminders(conference_id: str):
    """Schedule automated reminders for conference."""
    conference = await db.conferences.find_one({"_id": ObjectId(conference_id)})
    users = await get_registered_users(conference_id)

    n8n = N8NService()

    # Create scheduled workflow
    workflow = await n8n.create_workflow(
        name=f"Conference Reminders - {conference['name']}",
        schedule={
            "triggers": [
                {"type": "cron", "expression": "0 8 * * *"},  # Daily at 8 AM
            ]
        },
        nodes=[
            # Check if conference is within reminder window
            {
                "type": "n8n-nodes-base.function",
                "parameters": {
                    "functionCode": """
                    const conferenceDate = new Date('{{$json.conference_date}}');
                    const now = new Date();
                    const hoursUntil = (conferenceDate - now) / (1000 * 60 * 60);

                    // Send reminders at 7 days, 3 days, 1 day, 3 hours
                    const reminderWindows = [168, 72, 24, 3];
                    const shouldSend = reminderWindows.some(h =>
                        Math.abs(hoursUntil - h) < 1
                    );

                    return { shouldSend, hoursUntil };
                    """
                }
            },
            # Send push notifications
            {
                "type": "n8n-nodes-base.firebase",
                "parameters": {
                    "operation": "sendNotification",
                    "title": "Conference Reminder",
                    "body": "{{$json.conference_name}} starts in {{$json.hours_until}} hours!"
                }
            }
        ]
    )

    # Activate workflow
    await n8n.activate_workflow(workflow.id)
```

---

### 6. **Admin Dashboard**

**Role-based views:**

**Super Admin:**
- Manage all branches, users, buses, conferences
- System-wide analytics
- Configure notification templates
- Manage admin roles

**Branch Admin:**
- Manage members in their branch
- View branch-specific analytics
- Assign volunteer roles

**Transport Coordinator:**
- Create and manage bus routes
- Send delay notifications
- Track registrations and capacity
- Check-in passengers

**Conference Admin:**
- Create and manage conferences
- Manage speakers and sessions
- View registration stats
- Configure kiosk settings

---

## 📱 Mobile App Structure

### Navigation

```
TabNavigator:
├── Home
│   ├── Conference banner
│   ├── Quick actions (Register, View Bus, Check-in)
│   └── Upcoming events
├── Bus
│   ├── My Routes
│   ├── Select/Change Route
│   └── Live Updates
├── Conference
│   ├── Event Details
│   ├── Speakers
│   ├── Schedule
│   └── My Registration
├── Notifications
│   ├── All Notifications
│   └── Filter by type
└── Profile
    ├── Personal Info
    ├── Branch
    ├── Volunteer Roles
    └── Settings
```

### Key Screens

1. **Onboarding Flow**
   - Welcome → Phone Entry → OTP Verification → Branch Selection → Permission Requests

2. **Home Screen**
   - Conference card with registration status
   - Bus assignment card (if registered)
   - Quick actions
   - Recent notifications

3. **Bus Registration Flow**
   - Select Conference → Select Pickup Location → View Available Buses → Confirm Registration → Confirmation

4. **Conference Registration Flow**
   - View Details → Review Speakers/Schedule → Confirm Registration → QR Code Display

5. **Kiosk Mode** (Tablet/iPad)
   - Full-screen welcome interface
   - Motion detection indicator
   - Large text for visibility
   - Voice interaction prompts
   - Check-in confirmation

---

## 🔐 Security & Privacy

### Authentication
- Phone number verified via OTP
- JWT tokens for API authentication
- Session management via Supabase
- Role-based access control (RBAC)

### Data Privacy
- Collect minimal required data (name, phone, branch)
- No sensitive personal data stored
- Voice interactions not recorded by default
- Option to opt-out of personalized greetings
- GDPR-compliant data export/deletion

### API Security
- HTTPS only
- Rate limiting on endpoints
- Input validation and sanitization
- MongoDB injection prevention
- CORS configuration

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│                   Users                         │
│  (Mobile App + Kiosk Tablets)                   │
└──────────────────┬──────────────────────────────┘
                   │
                   │ HTTPS
                   │
┌──────────────────▼──────────────────────────────┐
│          Nginx Reverse Proxy                    │
│      church.kasaai.ailabsafrica.com             │
└──────────────────┬──────────────────────────────┘
                   │
                   │
┌──────────────────▼──────────────────────────────┐
│        FastAPI Backend (Python)                 │
│    - REST API + WebSockets                      │
│    - Business Logic                             │
│    - Integration Layer                          │
└──────┬──────────┬──────────┬───────────────────┘
       │          │          │
       │          │          │
  ┌────▼───┐ ┌───▼────┐ ┌──▼─────┐
  │MongoDB │ │Supabase│ │KasaAI  │
  │        │ │Auth    │ │Voice   │
  │        │ │Storage │ │Lab API │
  └────────┘ └────────┘ └────────┘
```

**Services:**
- Backend API: systemd service `kasaai-church-manager.service`
- Nginx config: `church.kasaai.ailabsafrica.com.conf`
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
/opt/kasaai/apps/church_manager/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth.py
│   │   │   │   ├── buses.py
│   │   │   │   ├── conferences.py
│   │   │   │   ├── users.py
│   │   │   │   └── notifications.py
│   │   │   └── deps.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── bus.py
│   │   │   ├── conference.py
│   │   │   └── notification.py
│   │   ├── schemas/
│   │   │   └── (Pydantic models for API)
│   │   ├── services/
│   │   │   ├── bus_service.py
│   │   │   ├── conference_service.py
│   │   │   ├── notification_service.py
│   │   │   └── voice_service.py
│   │   └── main.py
│   ├── tests/
│   │   ├── test_buses.py
│   │   ├── test_conferences.py
│   │   └── test_notifications.py
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
├── kiosk/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── App.tsx
│   ├── package.json
│   └── tsconfig.json
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
- E2E tests for critical user flows (registration, bus sign-up)
- Test coverage minimum: 80%

### Git Workflow
- Branch: `dev` for active development
- Main branch: `main` for production
- Commit after each feature/task completion
- Descriptive commit messages following conventional commits

---

## 🌍 Localization (Future)

### Languages
- English (primary)
- Twi (for voice greetings)
- Ga (for voice greetings)

### Cultural Considerations
- Ghanaian naming conventions
- Local time formats
- Currency (Ghana Cedis) for future payment features
- Mobile-first design (limited data considerations)

---

## 📊 Success Metrics

### User Engagement
- Daily active users
- Bus registration rate
- Conference check-in rate
- Kiosk interaction rate

### Operational Efficiency
- Notification delivery rate
- Bus capacity utilization
- Check-in speed (avg time)
- Admin task completion time

### User Satisfaction
- App rating
- Post-event surveys
- Feature usage patterns
- Support ticket volume

---

## 🔮 Future Expansion

### Phase 2 Features
- Volunteer management module
- GPS bus tracking
- Branch chat groups
- Feedback/survey system

### Phase 3 Features
- Attendance analytics dashboard
- Multi-church support (SaaS model)
- WhatsApp/SMS chatbot
- Donation/payment integration (MoMo, Paystack)

### Revenue Model (if SaaS)
- Subscription per church: ₵300-₵500/month
- Event-based license: ₵500 per conference
- Custom branding/white-label: ₵2,000 setup + monthly fee
- Enterprise features (analytics, multi-site): Premium tier

---

## 📝 Notes

- This is an internal church tool first, with potential to scale to SaaS
- Prioritize reliability over features (SMS notifications critical)
- Keep UX simple - many users are not tech-savvy
- Voice AI should feel warm and personal, not robotic
- Offline capabilities for mobile app (future consideration)

---

**Document Version History:**
- v1.0 (2025-10-23): Initial planning document created
