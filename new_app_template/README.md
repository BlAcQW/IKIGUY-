# New App Template

This template provides a starting point for creating new internal applications that integrate with KasaAI's shared libraries (Vapi, n8n, RAG, etc.).

## 🚀 Quick Start

### 1. Copy This Template

```bash
cd /opt/kasaai/apps
cp -r new_app_template my_new_app
cd my_new_app
```

### 2. Update Configuration

```bash
# Rename files
mv backend/main_template.py backend/main.py

# Update app name in all files
find . -type f -exec sed -i 's/new_app_template/my_new_app/g' {} +
find . -type f -exec sed -i 's/NewApp/MyApp/g' {} +
```

### 3. Set Up Environment

```bash
# Create virtual environment (optional, or use shared venv)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Run the App

```bash
# Development
uvicorn backend.main:app --reload --port 8000

# Production (with systemd service)
# See DEPLOYMENT.md
```

---

## 📂 Project Structure

```
my_new_app/
├── backend/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── vapi_service.py       # Extends shared VAPIService
│   │   └── n8n_service.py        # Extends shared N8NIntegration
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── vapi.py               # Vapi-related endpoints
│   │   └── n8n.py                # n8n-related endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── app_models.py         # App-specific Pydantic models
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_vapi_service.py
│   │   └── test_n8n_service.py
│   ├── main.py                   # FastAPI application
│   └── config.py                 # Configuration management
├── frontend/                     # Optional frontend
│   └── README.md
├── .env.example                  # Environment variables template
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── DEPLOYMENT.md                 # Deployment instructions
```

---

## 🧩 Using Shared Integrations

### Vapi Integration

**Best Practice: Extend shared `VAPIService`**

```python
# backend/services/vapi_service.py
from shared.integration.vapi import VAPIService, VAPIAgent, VAPICall
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MyAppVapiService(VAPIService):
    """App-specific Vapi service - extends shared VAPIService."""

    def __init__(self, config, app_db):
        """
        Initialize MyAppVapiService.

        Args:
            config: Vapi configuration (API key, etc.)
            app_db: App-specific database connection
        """
        # Initialize parent class with shared configuration
        super().__init__(config)

        # Add app-specific attributes
        self.app_db = app_db
        self.logger = logging.getLogger(__name__)

    async def create_app_assistant(
        self,
        user_id: str,
        name: str,
        system_prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create assistant with app-specific business logic.

        This method demonstrates how to:
        1. Add app-specific validation
        2. Use inherited generic methods from VAPIService
        3. Add app-specific post-processing
        """
        # Step 1: App-specific validation
        user = await self.app_db.users.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User {user_id} not found")

        if await self._user_has_max_assistants(user_id):
            raise ValueError("User has reached max assistants limit")

        # Step 2: Use inherited method from VAPIService
        agent = VAPIAgent(
            name=name,
            system_prompt=system_prompt,
            voice=kwargs.get("voice", "alloy"),
            language=kwargs.get("language", "en"),
            model=kwargs.get("model", "gpt-4o-mini"),
            provider=kwargs.get("provider", "openai")
        )

        # Call parent's generic method
        vapi_response = await self.create_assistant(agent)

        # Step 3: App-specific post-processing
        # Store in app database
        app_assistant = {
            "user_id": user_id,
            "vapi_id": vapi_response["id"],
            "name": name,
            "created_at": datetime.utcnow(),
            "credits_used": 1
        }
        result = await self.app_db.assistants.insert_one(app_assistant)

        # Log to app analytics
        await self._log_assistant_creation(user_id, vapi_response["id"])

        return {
            **vapi_response,
            "app_assistant_id": str(result.inserted_id)
        }

    async def _user_has_max_assistants(self, user_id: str) -> bool:
        """Check if user has reached assistant limit."""
        count = await self.app_db.assistants.count_documents({"user_id": user_id})
        return count >= 10  # Example limit

    async def _log_assistant_creation(self, user_id: str, assistant_id: str):
        """Log assistant creation to analytics."""
        await self.app_db.analytics_events.insert_one({
            "event": "assistant_created",
            "user_id": user_id,
            "assistant_id": assistant_id,
            "timestamp": datetime.utcnow()
        })
```

**Key Principles:**
- ✅ **Extend, don't reimplement** - Use `super()` to call parent methods
- ✅ **Separation of concerns** - Generic operations in shared, business logic in your app
- ✅ **Add value** - Your service adds app-specific validation, database operations, analytics
- ❌ **Don't duplicate** - Never copy-paste methods from shared library

---

### n8n Integration

**Best Practice: Extend shared `N8NIntegration`**

```python
# backend/services/n8n_service.py
from shared.integration.n8n import N8NIntegration, N8NConfig, N8NWorkflow
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class MyAppN8NService(N8NIntegration):
    """App-specific n8n service - extends shared N8NIntegration."""

    def __init__(self, config: N8NConfig, app_db):
        """
        Initialize MyAppN8NService.

        Args:
            config: N8N configuration
            app_db: App-specific database connection
        """
        super().__init__(config)
        self.app_db = app_db

    async def create_app_workflow(
        self,
        user_id: str,
        workflow_name: str,
        nodes: List[Dict],
        connections: Dict
    ) -> Dict[str, Any]:
        """
        Create workflow with app-specific business logic.
        """
        # App-specific validation
        user = await self.app_db.users.find_one({"_id": user_id})
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Use inherited method from N8NIntegration
        workflow_data = {
            "name": f"{user['username']}-{workflow_name}",
            "nodes": nodes,
            "connections": connections,
            "tags": [f"user:{user_id}", "app:my_app"]
        }

        workflow = await self.create_workflow(
            name=workflow_data["name"],
            nodes=workflow_data["nodes"],
            connections=workflow_data["connections"],
            tags=workflow_data["tags"]
        )

        # App-specific post-processing
        app_workflow = {
            "user_id": user_id,
            "n8n_id": workflow.id,
            "name": workflow_name,
            "created_at": datetime.utcnow()
        }
        result = await self.app_db.workflows.insert_one(app_workflow)

        return {
            "id": workflow.id,
            "name": workflow.name,
            "app_workflow_id": str(result.inserted_id)
        }
```

---

## 🎯 Creating Routes

### Example Vapi Route

```python
# backend/routes/vapi.py
from fastapi import APIRouter, Depends, HTTPException
from backend.services.vapi_service import MyAppVapiService
from backend.models.app_models import CreateAssistantRequest, AssistantResponse
from backend.dependencies import get_vapi_service, get_current_user

router = APIRouter(prefix="/api/assistants", tags=["Assistants"])


@router.post("/", response_model=AssistantResponse)
async def create_assistant(
    request: CreateAssistantRequest,
    user=Depends(get_current_user),
    vapi_service: MyAppVapiService = Depends(get_vapi_service)
):
    """Create a new voice assistant."""
    try:
        result = await vapi_service.create_app_assistant(
            user_id=user["id"],
            name=request.name,
            system_prompt=request.system_prompt,
            voice=request.voice,
            language=request.language
        )
        return AssistantResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create assistant: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[AssistantResponse])
async def list_assistants(
    user=Depends(get_current_user),
    vapi_service: MyAppVapiService = Depends(get_vapi_service)
):
    """List user's assistants."""
    # Get from app database (with Vapi IDs)
    app_assistants = await vapi_service.app_db.assistants.find(
        {"user_id": user["id"]}
    ).to_list(length=100)

    # Enrich with Vapi data using inherited method
    enriched = []
    for app_assistant in app_assistants:
        vapi_data = await vapi_service.get_assistant(app_assistant["vapi_id"])
        enriched.append({
            **vapi_data,
            "app_assistant_id": str(app_assistant["_id"])
        })

    return enriched
```

---

## 🧪 Testing

### Testing Your Service

```python
# backend/tests/test_vapi_service.py
import pytest
from backend.services.vapi_service import MyAppVapiService
from shared.integration.vapi import VAPIService, VAPIConfig
from unittest.mock import AsyncMock, Mock


@pytest.fixture
def vapi_config():
    return VAPIConfig(api_key="test_key")


@pytest.fixture
def mock_app_db():
    db = Mock()
    db.users.find_one = AsyncMock(return_value={"_id": "user123", "username": "testuser"})
    db.assistants.count_documents = AsyncMock(return_value=5)
    db.assistants.insert_one = AsyncMock(return_value=Mock(inserted_id="app_asst_123"))
    db.analytics_events.insert_one = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_create_app_assistant(vapi_config, mock_app_db, monkeypatch):
    """Test app-specific assistant creation."""
    # Mock parent's create_assistant method
    mock_vapi_response = {
        "id": "vapi_asst_123",
        "name": "Test Assistant",
        "status": "active"
    }

    async def mock_create_assistant(self, agent):
        return mock_vapi_response

    monkeypatch.setattr(VAPIService, "create_assistant", mock_create_assistant)

    # Test your service
    service = MyAppVapiService(config=vapi_config, app_db=mock_app_db)

    result = await service.create_app_assistant(
        user_id="user123",
        name="Test Assistant",
        system_prompt="You are a helpful assistant"
    )

    # Verify
    assert result["id"] == "vapi_asst_123"
    assert result["app_assistant_id"] == "app_asst_123"

    # Verify database calls
    mock_app_db.users.find_one.assert_called_once()
    mock_app_db.assistants.insert_one.assert_called_once()
    mock_app_db.analytics_events.insert_one.assert_called_once()


@pytest.mark.asyncio
async def test_user_max_assistants_limit(vapi_config, mock_app_db):
    """Test assistant creation limit."""
    # Mock user at max limit
    mock_app_db.assistants.count_documents = AsyncMock(return_value=10)

    service = MyAppVapiService(config=vapi_config, app_db=mock_app_db)

    with pytest.raises(ValueError, match="max assistants limit"):
        await service.create_app_assistant(
            user_id="user123",
            name="Test",
            system_prompt="Test"
        )


@pytest.mark.asyncio
async def test_invalid_user(vapi_config, mock_app_db):
    """Test creation with invalid user."""
    mock_app_db.users.find_one = AsyncMock(return_value=None)

    service = MyAppVapiService(config=vapi_config, app_db=mock_app_db)

    with pytest.raises(ValueError, match="not found"):
        await service.create_app_assistant(
            user_id="invalid_user",
            name="Test",
            system_prompt="Test"
        )
```

### Run Tests

```bash
# Run all tests
pytest backend/tests/ -v

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Run specific test file
pytest backend/tests/test_vapi_service.py -v
```

---

## 📚 Documentation

See also:
- `INTEGRATION_GUIDE.md` - Detailed integration guide
- `@apps/architecture/INTEGRATION_GUIDE.md` - Architecture-level integration guide
- `@apps/shared/integration/` - Shared library source code
- `@apps/ARCHITECTURE_STRATEGY.md` - Overall architecture strategy

---

## 🚀 Deployment

See `DEPLOYMENT.md` for:
- Systemd service setup
- Nginx configuration
- Environment variables
- Monitoring and logging

---

## 💡 Best Practices

### DO ✅

1. **Extend shared classes**
   ```python
   class MyService(VAPIService):
       def __init__(self, config, app_db):
           super().__init__(config)
           self.app_db = app_db
   ```

2. **Use inherited methods**
   ```python
   result = await self.create_assistant(agent)  # From VAPIService
   ```

3. **Add app-specific value**
   ```python
   await self.app_db.assistants.insert_one(...)
   await self.log_analytics(...)
   ```

4. **Test your code**
   ```python
   @pytest.mark.asyncio
   async def test_my_feature():
       ...
   ```

5. **Document your decisions**
   - Why you added this feature
   - Why you chose this approach
   - What edge cases you handled

### DON'T ❌

1. **Don't copy-paste from shared library**
   ```python
   # ❌ BAD
   async def create_assistant(self, agent):
       # Copied entire implementation from shared
   ```

2. **Don't modify shared library for app-specific needs**
   - Keep app logic in your app
   - Shared library should remain generic

3. **Don't skip tests**
   - Always write tests for new features
   - Test both success and failure cases

4. **Don't hardcode configuration**
   ```python
   # ❌ BAD
   api_key = "sk-abc123..."

   # ✅ GOOD
   api_key = os.getenv("VAPI_API_KEY")
   ```

---

## 🆘 Getting Help

- **Architecture questions**: See `@apps/architecture/`
- **Shared library docs**: See `@apps/shared/integration/`
- **Examples**: See `@apps/core_backend/` and `@apps/developer_platform/`

---

## 📝 Checklist for New App

- [ ] Copied template to new directory
- [ ] Updated app name in all files
- [ ] Created `.env` from `.env.example`
- [ ] Extended shared `VAPIService` and `N8NIntegration`
- [ ] Created app-specific routes
- [ ] Added app-specific business logic
- [ ] Wrote unit tests (80%+ coverage)
- [ ] Created systemd service
- [ ] Configured nginx
- [ ] Tested in development
- [ ] Deployed to staging
- [ ] Deployed to production
- [ ] Updated `@apps/architecture/` documentation

---

**Created:** 2025-10-24
**Last Updated:** 2025-10-24
**Version:** 1.0
