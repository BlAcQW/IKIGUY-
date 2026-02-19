# Internal Developer Guide: Building Apps with KasaAI Shared Libraries

**Purpose:** Practical guide for internal developers building new apps
**Audience:** Backend developers, full-stack developers
**Version:** 1.0
**Date:** 2025-10-24

---

## Quick Start

### Create a New App in 30 Minutes

```bash
# 1. Copy template (2 minutes)
cd /opt/kasaai/apps
cp -r new_app_template my_new_app
cd my_new_app

# 2. Update app name (3 minutes)
find . -type f -exec sed -i 's/new_app_template/my_new_app/g' {} +
find . -type f -exec sed -i 's/NewApp/MyNewApp/g' {} +

# 3. Configure environment (5 minutes)
cp .env.example .env
nano .env  # Add your API keys

# 4. Install dependencies (5 minutes)
pip install -r requirements.txt
pip install -e ../shared

# 5. Run the app (1 minute)
uvicorn backend.main:app --reload --port 8003

# 6. Test (5 minutes)
curl http://localhost:8003/health

# 7. Create first feature (10 minutes)
# See examples below
```

**Total: ~30 minutes from zero to working app!**

---

## Understanding the Architecture

### The 3-Tier System

```
External Developers
        ↓
┌─────────────────────────────────────┐
│  Tier 3: Developer Platform          │  Port 30028
│  /api/v1/*                           │
│  • Versioned, stable APIs             │
│  • Rate limiting, billing             │
│  • Public documentation               │
└─────────────────────────────────────┘
        ↓ (read-only access)
┌─────────────────────────────────────┐
│  Tier 2: Your App                    │  Port 8003
│  /api/*                               │
│  • Your business logic                │
│  • User management                    │
│  • Fast iteration                     │
│  • Breaking changes OK                │
└─────────────────────────────────────┘
        ↓ (extends & uses)
┌─────────────────────────────────────┐
│  Tier 1: Shared Libraries             │
│  @apps/shared/integration/            │
│  • Generic API operations             │
│  • Vapi, n8n, RAG                     │
│  • Tested, reliable                   │
└─────────────────────────────────────┘
```

### Why This Architecture?

✅ **Separation of Concerns**
- Shared = Generic operations
- Your App = Business logic
- Developer Platform = Public API

✅ **DRY Principle**
- Write integration code once
- Use across all apps
- Update once, benefits all

✅ **Independent Scaling**
- Each app can scale independently
- Deploy without affecting others
- Different resource requirements

✅ **Fast Development**
- Don't rewrite Vapi/n8n integration
- Focus on your unique features
- New app in < 1 day

---

## Pattern: Extend Shared Services

### ✅ CORRECT Pattern

```python
# backend/services/vapi_service.py
from shared.integration.vapi import VAPIService, VAPIAgent

class MyAppVapiService(VAPIService):
    """Extend shared VAPIService with app-specific logic."""

    def __init__(self, config, app_db):
        # Initialize parent
        super().__init__(config)

        # Add app-specific attributes
        self.app_db = app_db
        self.logger = logging.getLogger(__name__)

    async def create_user_assistant(
        self,
        user_id: str,
        name: str,
        system_prompt: str
    ):
        """App-specific method that uses inherited functionality."""

        # 1. App-specific validation
        user = await self.app_db.users.find_one({"_id": user_id})
        if not user:
            raise ValueError("User not found")

        # 2. Use inherited method (from VAPIService)
        agent = VAPIAgent(name=name, system_prompt=system_prompt)
        vapi_result = await self.create_assistant(agent)  # ← Inherited!

        # 3. App-specific post-processing
        await self.app_db.user_assistants.insert_one({
            "user_id": user_id,
            "vapi_id": vapi_result["id"],
            "created_at": datetime.utcnow()
        })

        return vapi_result
```

**Why This Works:**
- ✅ Inherits all generic Vapi operations
- ✅ Adds user management (app-specific)
- ✅ Easy to test
- ✅ Easy to maintain

### ❌ WRONG Pattern

```python
# ❌ DON'T DO THIS!
class MyAppVapiService:
    def __init__(self, config, app_db):
        # Composition instead of inheritance ❌
        self.vapi = VAPIService(config)
        self.app_db = app_db

    async def create_user_assistant(self, ...):
        # Have to manually call vapi methods ❌
        result = await self.vapi.create_assistant(...)
```

**Why This is Wrong:**
- ❌ Verbose (have to call `self.vapi.method()` everywhere)
- ❌ Doesn't show that your service IS-A VAPIService
- ❌ Can't override methods if needed
- ❌ More boilerplate code

---

## Common Patterns

### Pattern 1: Add Pre/Post Processing

```python
class MyService(VAPIService):
    async def create_assistant_with_analytics(self, user_id, agent):
        # Pre-processing
        await self._check_user_limit(user_id)
        await self._log_start("create_assistant", user_id)

        # Use inherited method
        result = await self.create_assistant(agent)

        # Post-processing
        await self._save_to_db(user_id, result)
        await self._log_success("create_assistant", user_id)
        await self._send_notification(user_id, "Assistant created!")

        return result
```

### Pattern 2: Add Business Rules

```python
class MyService(VAPIService):
    async def create_assistant_for_tier(self, user_id, tier, agent):
        """Create assistant based on user's subscription tier."""

        # Business rules
        if tier == "free":
            agent.model = "gpt-4o-mini"  # Free tier gets cheaper model
            agent.max_duration = 300      # 5 minute call limit
        elif tier == "pro":
            agent.model = "gpt-4o"
            agent.max_duration = 1800     # 30 minute limit
        elif tier == "enterprise":
            agent.model = "gpt-4o"
            agent.max_duration = None     # No limit

        # Use inherited method
        return await self.create_assistant(agent)
```

### Pattern 3: Add Caching

```python
class MyService(VAPIService):
    def __init__(self, config, app_db, cache):
        super().__init__(config)
        self.app_db = app_db
        self.cache = cache

    async def get_assistant_cached(self, assistant_id):
        """Get assistant with caching."""

        # Check cache first
        cached = await self.cache.get(f"assistant:{assistant_id}")
        if cached:
            return cached

        # Use inherited method
        result = await self.get_assistant(assistant_id)

        # Cache result
        await self.cache.set(
            f"assistant:{assistant_id}",
            result,
            expire=300  # 5 minutes
        )

        return result
```

### Pattern 4: Add Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class MyService(VAPIService):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def create_assistant_with_retry(self, agent):
        """Create assistant with automatic retries on failure."""
        return await self.create_assistant(agent)
```

---

## Real-World Examples

### Example 1: Healthcare App

```python
# healthcare_app/backend/services/vapi_service.py
from shared.integration.vapi import VAPIService, VAPIAgent

class HealthcareVapiService(VAPIService):
    """HIPAA-compliant Vapi service for healthcare."""

    async def create_patient_assistant(
        self,
        patient_id: str,
        doctor_id: str,
        specialty: str
    ):
        """Create HIPAA-compliant assistant for patient care."""

        # Validation
        patient = await self._get_patient(patient_id)
        doctor = await self._get_doctor(doctor_id)

        if not doctor.get("certified_for", []).contains(specialty):
            raise ValueError(f"Doctor not certified for {specialty}")

        # Create assistant with HIPAA-compliant prompt
        agent = VAPIAgent(
            name=f"Dr. {doctor['name']}'s Assistant",
            system_prompt=self._build_hipaa_prompt(specialty),
            voice="alloy",
            language=patient.get("preferred_language", "en")
        )

        result = await self.create_assistant(agent)

        # Log for HIPAA audit trail
        await self._log_hipaa_event(
            "assistant_created",
            patient_id=patient_id,
            doctor_id=doctor_id,
            assistant_id=result["id"]
        )

        return result

    def _build_hipaa_prompt(self, specialty):
        """Build HIPAA-compliant system prompt."""
        return f"""
        You are a medical assistant specialized in {specialty}.
        IMPORTANT HIPAA Guidelines:
        - Never share patient information with unauthorized individuals
        - Always verify caller identity before discussing medical details
        - Document all interactions for audit trail
        - Follow standard medical protocols
        """
```

### Example 2: Education App

```python
# education_app/backend/services/vapi_service.py
from shared.integration.vapi import VAPIService, VAPIAgent

class EducationVapiService(VAPIService):
    """Vapi service for education/tutoring app."""

    async def create_tutor_assistant(
        self,
        student_id: str,
        subject: str,
        grade_level: int
    ):
        """Create AI tutor assistant for student."""

        # Get student profile
        student = await self.app_db.students.find_one({"_id": student_id})

        if not student:
            raise ValueError("Student not found")

        # Check parent consent (required for minors)
        if student["age"] < 13 and not student.get("parent_consent"):
            raise ValueError("Parent consent required for minors")

        # Create age-appropriate assistant
        agent = VAPIAgent(
            name=f"{subject} Tutor",
            system_prompt=self._build_tutor_prompt(subject, grade_level, student),
            voice="alloy",  # Friendly voice for students
            language=student.get("language", "en")
        )

        result = await self.create_assistant(agent)

        # Track for progress monitoring
        await self._track_tutor_assignment(student_id, result["id"], subject)

        return result

    def _build_tutor_prompt(self, subject, grade_level, student):
        """Build age-appropriate tutoring prompt."""
        learning_style = student.get("learning_style", "visual")

        return f"""
        You are a friendly {subject} tutor for grade {grade_level} students.

        Student Learning Profile:
        - Learning Style: {learning_style}
        - Current Level: {student.get("current_level", "beginner")}
        - Strengths: {", ".join(student.get("strengths", []))}
        - Areas to Improve: {", ".join(student.get("improvement_areas", []))}

        Teaching Guidelines:
        - Use age-appropriate language
        - Be encouraging and patient
        - Break down complex concepts into simple steps
        - Use {learning_style} learning techniques
        - Celebrate progress and effort
        """
```

### Example 3: E-commerce App

```python
# ecommerce_app/backend/services/vapi_service.py
from shared.integration.vapi import VAPIService, VAPIAgent

class EcommerceVapiService(VAPIService):
    """Vapi service for e-commerce customer support."""

    async def create_support_assistant(
        self,
        customer_id: str,
        department: str = "general"
    ):
        """Create personalized customer support assistant."""

        # Get customer history
        customer = await self._get_customer_with_history(customer_id)

        # Personalize based on customer tier
        tier = customer.get("tier", "standard")
        priority = {
            "vip": 1,
            "premium": 2,
            "standard": 3
        }.get(tier, 3)

        # Create assistant with customer context
        agent = VAPIAgent(
            name=f"{department.title()} Support",
            system_prompt=self._build_support_prompt(customer, department),
            voice="nova" if tier == "vip" else "alloy",
            language=customer.get("language", "en"),
            first_message=self._get_personalized_greeting(customer)
        )

        result = await self.create_assistant(agent)

        # Create support ticket
        await self._create_support_ticket(
            customer_id=customer_id,
            assistant_id=result["id"],
            priority=priority
        )

        return result

    def _build_support_prompt(self, customer, department):
        """Build support prompt with customer context."""
        recent_orders = customer.get("recent_orders", [])
        returns = customer.get("recent_returns", [])

        context = f"""
        You are a {department} support assistant for XYZ Store.

        Customer Profile:
        - Name: {customer["name"]}
        - Tier: {customer.get("tier", "standard")}
        - Account Age: {customer.get("account_age_days")} days
        - Total Orders: {customer.get("total_orders", 0)}
        - Recent Orders: {recent_orders}
        - Recent Returns: {returns}

        Guidelines:
        - Be friendly and helpful
        - Reference their order history when relevant
        - Offer proactive solutions
        - Escalate complex issues to human agent
        - Always ask if there's anything else you can help with
        """

        return context

    def _get_personalized_greeting(self, customer):
        """Get personalized greeting based on customer history."""
        if customer.get("tier") == "vip":
            return f"Hello {customer['name']}, thank you for being a valued VIP customer! How may I assist you today?"
        elif customer.get("recent_orders"):
            last_order = customer["recent_orders"][0]
            return f"Hello {customer['name']}! I see you recently ordered {last_order['product']}. How can I help you today?"
        else:
            return f"Hello {customer['name']}! How can I help you today?"
```

---

## Testing Your Services

### Unit Test Template

```python
# backend/tests/test_vapi_service.py
import pytest
from unittest.mock import AsyncMock, Mock, patch
from backend.services.vapi_service import MyAppVapiService
from shared.integration.vapi import VAPIService

@pytest.fixture
def mock_config():
    """Mock Vapi configuration."""
    config = Mock()
    config.api_key = "test_key"
    config.base_url = "http://test.com"
    return config

@pytest.fixture
def mock_db():
    """Mock database."""
    db = Mock()
    db.users.find_one = AsyncMock(return_value={
        "_id": "user123",
        "name": "Test User",
        "tier": "pro"
    })
    db.assistants.insert_one = AsyncMock(return_value=Mock(inserted_id="asst_app_123"))
    return db

@pytest.mark.asyncio
async def test_create_user_assistant_success(mock_config, mock_db, monkeypatch):
    """Test successful assistant creation."""

    # Mock parent's create_assistant method
    async def mock_create_assistant(self, agent):
        return {
            "id": "asst_vapi_123",
            "name": agent.name,
            "status": "active"
        }

    monkeypatch.setattr(
        VAPIService,
        "create_assistant",
        mock_create_assistant
    )

    # Test your service
    service = MyAppVapiService(mock_config, mock_db)

    result = await service.create_user_assistant(
        user_id="user123",
        name="Test Assistant",
        system_prompt="You are a test assistant"
    )

    # Verify result
    assert result["id"] == "asst_vapi_123"
    assert result["name"] == "Test Assistant"

    # Verify database calls
    mock_db.users.find_one.assert_called_once_with({"_id": "user123"})
    mock_db.assistants.insert_one.assert_called_once()

    # Verify insert was called with correct data
    insert_call = mock_db.assistants.insert_one.call_args[0][0]
    assert insert_call["user_id"] == "user123"
    assert insert_call["vapi_id"] == "asst_vapi_123"

@pytest.mark.asyncio
async def test_create_user_assistant_user_not_found(mock_config, mock_db):
    """Test assistant creation with invalid user."""

    # Mock user not found
    mock_db.users.find_one = AsyncMock(return_value=None)

    service = MyAppVapiService(mock_config, mock_db)

    with pytest.raises(ValueError, match="User not found"):
        await service.create_user_assistant(
            user_id="invalid_user",
            name="Test",
            system_prompt="Test"
        )
```

### Integration Test Template

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_vapi_integration():
    """Test with real Vapi API."""

    # Skip if no API key
    if not os.getenv("VAPI_API_KEY"):
        pytest.skip("VAPI_API_KEY not set")

    # Real configuration
    config = VAPIConfig(
        api_key=os.getenv("VAPI_API_KEY"),
        base_url="https://api.vapi.ai"
    )

    service = VAPIService(config)

    # Create real assistant
    agent = VAPIAgent(
        name="Integration Test Assistant",
        system_prompt="You are a test assistant for integration testing.",
        voice="alloy",
        language="en"
    )

    assistant = await service.create_assistant(agent)

    try:
        # Verify
        assert "id" in assistant
        assert assistant["name"] == "Integration Test Assistant"

        # Test get assistant
        retrieved = await service.get_assistant(assistant["id"])
        assert retrieved["id"] == assistant["id"]

    finally:
        # Cleanup
        await service.delete_assistant(assistant["id"])
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (`pytest backend/tests/ -v`)
- [ ] Environment variables configured (`.env`)
- [ ] Database migrations run
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Shared library installed (`pip install -e ../shared`)
- [ ] Systemd service created
- [ ] Nginx configuration created
- [ ] SSL certificate obtained

### Deployment Steps

```bash
# 1. Create systemd service
sudo nano /etc/systemd/system/my-app-backend.service

# 2. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable my-app-backend
sudo systemctl start my-app-backend

# 3. Verify service
sudo systemctl status my-app-backend
sudo journalctl -u my-app-backend -f

# 4. Configure Nginx
sudo nano /etc/nginx/sites-available/my-app-api.conf
sudo ln -s /etc/nginx/sites-available/my-app-api.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 5. SSL certificate
sudo certbot --nginx -d my-app-api.ailabsafrica.com

# 6. Test
curl https://my-app-api.ailabsafrica.com/health
```

### Post-Deployment

- [ ] Service running (`systemctl status my-app-backend`)
- [ ] Health endpoint responding (`curl /health`)
- [ ] Logs look clean (`journalctl -u my-app-backend`)
- [ ] Database connected
- [ ] Vapi/n8n integrations working
- [ ] Monitoring configured
- [ ] Backup strategy in place

---

## Common Pitfalls

### Pitfall 1: Modifying Shared Library

❌ **WRONG:**
```python
# In @apps/shared/integration/vapi.py
class VAPIService:
    async def create_assistant(self, agent, tenant_id=None):  # ❌ Adding tenant_id
        # Now ALL apps have to deal with tenant_id ❌
```

✅ **CORRECT:**
```python
# In @apps/my_app/backend/services/vapi_service.py
class MyAppVapiService(VAPIService):
    async def create_assistant_for_tenant(self, agent, tenant_id):  # ✅
        # Tenant logic in YOUR app ✅
        result = await self.create_assistant(agent)  # ✅ Use inherited method
        await self._link_to_tenant(tenant_id, result)
        return result
```

### Pitfall 2: Not Using Inheritance

❌ **WRONG:**
```python
class MyService:
    def __init__(self, config):
        self.vapi = VAPIService(config)  # ❌ Composition

    async def create(self, agent):
        return await self.vapi.create_assistant(agent)  # ❌ Verbose
```

✅ **CORRECT:**
```python
class MyService(VAPIService):  # ✅ Inheritance
    async def create(self, agent):
        return await self.create_assistant(agent)  # ✅ Direct access
```

### Pitfall 3: Duplicating Generic Logic

❌ **WRONG:**
```python
class MyService(VAPIService):
    async def create_assistant(self, agent):
        # Re-implementing parent's logic ❌
        response = requests.post(...)
        return response.json()
```

✅ **CORRECT:**
```python
class MyService(VAPIService):
    async def create_app_assistant(self, user_id, agent):
        # Add app logic, use inherited for API ✅
        await self._validate_user(user_id)
        result = await self.create_assistant(agent)  # ✅ Use inherited
        await self._save_to_db(user_id, result)
        return result
```

---

## Quick Reference

### Shared Services

| Service | Import | Purpose |
|---------|--------|---------|
| `VAPIService` | `from shared.integration.vapi import VAPIService` | Voice AI assistants |
| `N8NIntegration` | `from shared.integration.n8n import N8NIntegration` | Workflow automation |
| `RAGService` | `from shared.integration.rag import RAGService` | Document search |
| `TTSClient` | `from shared.tts import TTSClient, AsyncTTSClient` | Text-to-Speech (15+ providers) |
| `ASRService` | `from shared.integration.ai_services import ASRService` | Speech-to-Text |
| `LLMService` | `from shared.integration.ai_services import LLMService` | Large Language Models |

### TTS Lab - Unified Hub

**🌟 NEW:** Access all TTS services through a consolidated web interface:

- **URL:** https://ttslab.ailabsafrica.com
- **Providers:** 15+ TTS services (RunPod GPU + Local Infrastructure)
- **Features:** Modern UI, status indicators, Gradio interfaces

**Available Services:**
- RunPod GPU: TTS-WebUI (20+ models), GPT-SoVITS, Fish Speech, Zonos, F5-TTS, StyleTTS2
- Local: Coqui XTTS, MeloTTS, OpenVoice, Kokoro, F5-TTS API

### Common Methods

#### VAPIService
- `create_assistant(agent)` - Create voice assistant
- `get_assistant(id)` - Get assistant details
- `initiate_call(assistant_id, phone)` - Start outbound call
- `get_call(call_id)` - Get call details

#### N8NIntegration
- `create_workflow(name, nodes, connections)` - Create workflow
- `activate_workflow(id)` - Activate workflow
- `trigger_workflow(id, data)` - Execute workflow
- `get_execution(id)` - Get execution status

#### TTSClient / AsyncTTSClient
- `synthesize(text, provider, language, speed)` - Convert text to speech
- `clone_voice(text, reference_audio, provider)` - Voice cloning
- `synthesize_batch(texts, provider, parallel)` - Batch processing
- `get_provider_status(provider)` - Check provider availability
- **Providers:** `F5TTS`, `STYLETTS2`, `COQUI_XTTS`, `MELOTTS`, `OPENVOICE`, `KOKORO`, `TTS_WEBUI`, `FISH_SPEECH`, `ZONOS`

---

## Next Steps

1. ✅ Copy template
2. ✅ Create your first service (extend VAPIService or N8NIntegration)
3. ✅ Add app-specific routes
4. ✅ Write tests
5. ✅ Deploy

**Need help?** Check:
- Template: `@apps/new_app_template/`
- Examples: `@apps/core_backend/`
- Architecture: `@apps/architecture/`

---

**Document Version:** 1.0
**Last Updated:** 2025-10-24
**Maintainer:** KasaAI Engineering Team
