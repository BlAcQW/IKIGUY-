# B2C Portal - Shared Library Quick Reference Guide

**Quick lookup for commonly needed shared library features**

---

## 1. AUTHENTICATION (MUST USE)

### Protected Routes
```python
from fastapi import Depends
from apps.shared.auth.supabase_auth import get_current_user

@router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    return {
        "user_id": user["id"],
        "email": user["email"],
        "display_name": user.get("display_name", ""),
        "avatar_url": user.get("avatar_url", "")
    }
```

### Optional Authentication
```python
from fastapi import Depends
from typing import Optional
from apps.shared.auth.supabase_auth import get_current_user_optional

@router.get("/public-data")
async def get_public_data(user: Optional[dict] = Depends(get_current_user_optional)):
    if user:
        return {"data": "personalized", "user": user["email"]}
    return {"data": "public"}
```

### Token Verification (Non-FastAPI)
```python
from apps.shared.auth.supabase_auth import verify_supabase_token

user_info = await verify_supabase_token(token_string)
if user_info:
    print(f"Valid token for {user_info['email']}")
```

---

## 2. VOICE CHAT (HIGHEST IMPACT)

### Complete Voice Chat Pipeline
```python
from apps.shared.services.conversational_voice_service import (
    ConversationalVoiceService,
    VoiceConversationRequest
)

# Initialize once at app startup
voice_service = ConversationalVoiceService()
await voice_service.initialize()

# Use in route
@router.post("/api/voice-chat")
async def voice_chat(request: VoiceConversationRequest, user: dict = Depends(get_current_user)):
    result = await voice_service.process_voice_message(
        user_id=user["id"],
        request=request
    )
    
    return {
        "transcription": result.transcription,
        "response": result.response_text,
        "audio_base64": result.audio_base64,
        "duration": result.duration_seconds
    }
```

---

## 3. TEXT-TO-SPEECH

### Basic Synthesis
```python
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest
)

# Initialize once at startup
tts = TTSProviderService()
await tts.initialize()

# In route
@router.post("/api/tts")
async def synthesize(text: str, user: dict = Depends(get_current_user)):
    result = await tts.synthesize(
        user_id=user["id"],
        request=SynthesisRequest(
            provider_id="coqui_xtts",  # or another provider
            text=text,
            language="en",
            voice_id="nova"  # Optional
        )
    )
    
    return {
        "audio_base64": result.audio_base64,
        "duration": result.duration,
        "cost": result.cost,
        "transaction_id": result.transaction_id
    }
```

### Voice Cloning
```python
from apps.shared.services.tts_provider_service import VoiceCloneRequest

result = await tts.synthesize_with_voice_cloning(
    user_id=user["id"],
    request=VoiceCloneRequest(
        provider_id="f5tts",  # or "coqui_xtts"
        text="Custom text with cloned voice",
        reference_audio_base64=audio_samples,  # Reference voice
        language="en"
    )
)
```

### Available TTS Providers
- `coqui_xtts` - Self-hosted, voice cloning
- `elevenlabs` - High-quality English
- `openai_tts` - OpenAI TTS
- `google_tts` - Google Text-to-Speech
- `playht` - Play.ht
- `f5tts` - Voice cloning
- `indextts_2` - Advanced voice cloning
- `voxcpm` - Multilingual
- `bark` - Generative
- `glowts` - Fast synthesis

---

## 4. SPEECH-TO-TEXT

### Basic Transcription
```python
from apps.shared.services.asr_provider_service import (
    ASRProviderService,
    TranscriptionRequest
)

# Initialize once at startup
asr = ASRProviderService()
await asr.initialize()

# In route
@router.post("/api/transcribe")
async def transcribe(audio_base64: str, user: dict = Depends(get_current_user)):
    result = await asr.transcribe(
        user_id=user["id"],
        request=TranscriptionRequest(
            provider_id="whisper_large_v3",
            audio_base64=audio_base64,
            language="en"  # Optional, auto-detects
        )
    )
    
    return {
        "transcription": result.transcription,
        "language": result.language,
        "confidence": result.confidence,
        "duration": result.duration,
        "cost": result.cost
    }
```

### Available ASR Providers
- `whisper_large_v3` - OpenAI Whisper (best quality)
- `whisper_medium` - OpenAI Whisper (balanced)
- `whisper_base` - OpenAI Whisper (fast)
- `google_stt` - Google Speech-to-Text
- `assemblyai` - Assembly AI
- `deepgram` - Deepgram

---

## 5. LLM INTEGRATION

### Multi-Provider LLM
```python
from apps.shared.services.llm_provider_service import LLMProviderService

# Initialize once at startup
llm = LLMProviderService()
await llm.initialize()

# In route
@router.post("/api/chat")
async def chat(messages: List[dict], user: dict = Depends(get_current_user)):
    response = await llm.call(
        provider="openai",  # or "gemini", "anthropic", "mistral"
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )
    
    return {"response": response}
```

### Supported Providers
- `openai` - GPT-4, GPT-4o, GPT-3.5
- `gemini` - Google Gemini Pro
- `anthropic` - Claude 3 (Opus, Sonnet, Haiku)
- `mistral` - Mistral Large/Medium/Small

---

## 6. KNOWLEDGE BASE WITH RAG

### Index Documents
```python
from apps.shared.integration.rag import RAGService, RAGConfig, KnowledgeDocument

# Initialize once at startup
rag_config = RAGConfig(
    postgres_password="your_db_password",
    ai_provider="openai",
    api_key="sk-...",
    embedding_model="text-embedding-3-small",
    llm_model="gpt-4o-mini"
)
rag = RAGService(rag_config)

# Index documents (do once or when docs update)
@router.post("/api/kb/index")
async def index_documents(docs: List[dict], user: dict = Depends(get_current_user)):
    documents = [
        KnowledgeDocument(
            title=doc["title"],
            content=doc["content"],
            category=doc.get("category", "General"),
            tags=doc.get("tags", []),
            metadata={"org_id": user["org_id"]}
        )
        for doc in docs
    ]
    
    await rag.index_documents(
        f"b2c_kb_{user['org_id']}",  # Collection name
        documents
    )
    
    return {"status": "indexed", "count": len(documents)}
```

### Query Knowledge Base
```python
@router.post("/api/kb/query")
async def query_kb(query: str, user: dict = Depends(get_current_user)):
    result = await rag.query(
        f"b2c_kb_{user['org_id']}",
        query,
        filters={"org_id": user["org_id"]}
    )
    
    return {
        "response": result.response,
        "confidence": result.confidence_score,
        "sources": result.sources_used,
        "requires_escalation": result.requires_escalation
    }
```

---

## 7. BILLING & WALLET

### Get User Balance
```python
from apps.shared.integration.wallet import WalletService

wallet = WalletService()
await wallet.initialize()

@router.get("/api/balance")
async def get_balance(user: dict = Depends(get_current_user)):
    balance = await wallet.get_balance(user["id"])
    
    return {
        "balance": balance.amount,
        "currency": balance.currency,
        "last_updated": balance.updated_at
    }
```

### Create Transaction
```python
@router.post("/api/transaction")
async def create_transaction(
    amount: float,
    description: str,
    user: dict = Depends(get_current_user)
):
    transaction = await wallet.create_transaction(
        user_id=user["id"],
        amount=amount,
        currency="USD",
        description=description
    )
    
    return {
        "transaction_id": transaction.id,
        "status": transaction.status,
        "amount": transaction.amount
    }
```

---

## 8. EMAIL NOTIFICATIONS

### Send Email
```python
from apps.shared.integration.email import EmailIntegration

email = EmailIntegration(config_dict)
await email.initialize()

@router.post("/api/send-email")
async def send_email(to: str, subject: str, body: str):
    result = await email.send_email(
        to=to,
        subject=subject,
        body=body,
        html_body=f"<h1>{subject}</h1><p>{body}</p>"
    )
    
    return {"status": "sent", "message_id": result.message_id}
```

---

## 9. SMS NOTIFICATIONS

### Send SMS
```python
from apps.shared.integration.sms import SMSIntegration

sms = SMSIntegration(config_dict)
await sms.initialize()

@router.post("/api/send-sms")
async def send_sms(to: str, message: str):
    result = await sms.send_sms(
        to=to,
        message=message,
        from_number="+1234567890"
    )
    
    return {"status": "sent", "message_id": result.message_id}
```

---

## 10. ORGANIZATION & MULTI-TENANCY

### Get Organization
```python
from apps.shared.models.organization import Organization
from apps.shared.services.organization_service import OrganizationService

org_service = OrganizationService()

@router.get("/api/org/{org_id}")
async def get_org(org_id: str, user: dict = Depends(get_current_user)):
    org = await org_service.get_organization(org_id)
    
    return {
        "id": org.id,
        "name": org.display_name,
        "subscription": org.subscription_tier,
        "wallet_balance": org.wallet_balance,
        "logo_url": org.logo_url
    }
```

### Update Organization
```python
@router.put("/api/org/{org_id}")
async def update_org(
    org_id: str,
    updates: dict,
    user: dict = Depends(get_current_user)
):
    org = await org_service.update_organization(org_id, updates)
    return {"status": "updated", "org": org.dict()}
```

---

## 11. FILE UPLOAD

### Upload File
```python
from apps.shared.services.file_upload_service import FileUploadService

upload_service = await FileUploadService()

@router.post("/api/upload")
async def upload_file(file: UploadFile, user: dict = Depends(get_current_user)):
    file_bytes = await file.read()
    
    upload_info = await upload_service.upload_file(
        file=file_bytes,
        filename=file.filename,
        organization_id=user["org_id"],
        file_category="documents"  # or "audio", "images", etc.
    )
    
    return {
        "file_id": upload_info.file_id,
        "url": upload_info.url,
        "path": upload_info.path
    }
```

---

## 12. PDF EXTRACTION (Receipts/Invoices)

### Extract from PDF
```python
from apps.shared.services.pdf_extraction_service import PDFExtractionService

pdf_service = PDFExtractionService(use_ocr=True)

@router.post("/api/extract-pdf")
async def extract_pdf(file: UploadFile):
    file_bytes = await file.read()
    
    result = await pdf_service.extract_from_pdf(file_bytes)
    
    return {
        "merchant": result.merchant,
        "amount": result.amount,
        "date": result.date,
        "tax": result.tax,
        "currency": result.currency,
        "category": result.category,
        "confidence": result.confidence
    }
```

---

## 13. FRONTEND COMPONENTS

### Voice Settings Panel
```tsx
import { VoiceSettingsPanel } from '@shared/frontend/components/voice-settings';

export function MySettings() {
    return (
        <VoiceSettingsPanel
            onSettingsChange={(settings) => {
                // Handle settings change
                console.log('New settings:', settings);
            }}
        />
    );
}
```

### Use Voice Settings Hook
```tsx
import { useVoiceSettings } from '@shared/frontend/hooks';

export function MyComponent() {
    const { settings, updateSettings, isLoading } = useVoiceSettings(orgId);
    
    if (isLoading) return <div>Loading...</div>;
    
    return (
        <div>
            <p>Current TTS: {settings.tts_provider}</p>
            <button onClick={() => updateSettings({ 
                tts_provider: "elevenlabs" 
            })}>
                Switch to ElevenLabs
            </button>
        </div>
    );
}
```

### Use TTS Provider Hook
```tsx
import { useTTSProvider } from '@shared/frontend/hooks';

export function TextToSpeech() {
    const { providers, synthesize, isLoading } = useTTSProvider();
    const [text, setText] = useState('');
    
    const handleSpeak = async () => {
        const audio = await synthesize(text, {
            voice_id: 'nova',
            language: 'en'
        });
        // Play audio...
    };
    
    return (
        <div>
            <input value={text} onChange={(e) => setText(e.target.value)} />
            <button onClick={handleSpeak} disabled={isLoading}>
                Speak
            </button>
        </div>
    );
}
```

---

## 14. COMMON PATTERNS

### Dependency Injection Pattern
```python
from fastapi import Depends

async def get_user_org(user: dict = Depends(get_current_user)) -> str:
    return user.get("org_id", "default_org")

@router.get("/data")
async def get_data(org_id: str = Depends(get_user_org)):
    # Now you have org_id injected
    return {"org_id": org_id}
```

### Error Handling
```python
from fastapi import HTTPException, status

@router.post("/api/risky-operation")
async def risky_operation(user: dict = Depends(get_current_user)):
    try:
        result = await some_service.do_something(user["id"])
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

### Async Context Manager
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_service():
    service = MyService()
    await service.initialize()
    try:
        yield service
    finally:
        await service.cleanup()

# Usage
async with get_service() as service:
    result = await service.do_something()
```

---

## 15. ENVIRONMENT VARIABLES NEEDED

```bash
# Authentication (MUST HAVE)
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_ANON_KEY=your_key_here
SUPABASE_KEY=your_key_here

# Voice Services
OPENAI_API_KEY=sk-...  # For TTS, ASR, LLM
GOOGLE_API_KEY=...     # For Google TTS, STT
ELEVENLABS_API_KEY=... # For ElevenLabs

# RAG/Knowledge Base
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_PASSWORD=your_password
POSTGRES_DB=kasaai_core

# Payment (if using wallet)
STRIPE_API_KEY=sk_...
STRIPE_SECRET_KEY=sk_...

# Email
SENDGRID_API_KEY=... # or SMTP credentials

# Storage (for file uploads)
HETZNER_USER=...
HETZNER_PASSWORD=...
```

---

## 16. IMPORT CHEAT SHEET

```python
# AUTHENTICATION (ALWAYS NEEDED)
from apps.shared.auth.supabase_auth import (
    get_current_user,
    get_current_user_optional,
    verify_supabase_token,
    get_supabase_client
)

# VOICE SERVICES (MOST COMMON)
from apps.shared.services.conversational_voice_service import (
    ConversationalVoiceService,
    VoiceConversationRequest
)
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest,
    VoiceCloneRequest
)
from apps.shared.services.asr_provider_service import (
    ASRProviderService,
    TranscriptionRequest
)

# AI/LLM
from apps.shared.services.llm_provider_service import LLMProviderService
from apps.shared.integration.rag import RAGService, RAGConfig, KnowledgeDocument

# PAYMENT & BILLING
from apps.shared.integration.wallet import WalletService
from apps.shared.services.billing_service import BillingService

# COMMUNICATION
from apps.shared.integration.email import EmailIntegration
from apps.shared.integration.sms import SMSIntegration
from apps.shared.integration.whatsapp_business import WhatsAppIntegration

# DATA & MODELS
from apps.shared.models.organization import Organization, OrganizationRole
from apps.shared.services.organization_service import OrganizationService

# FILE OPERATIONS
from apps.shared.services.file_upload_service import FileUploadService
from apps.shared.services.pdf_extraction_service import PDFExtractionService

# FRONTEND (TYPESCRIPT)
import { useVoiceSettings } from '@shared/frontend/hooks';
import { VoiceSettingsPanel } from '@shared/frontend/components/voice-settings';
import { OrganizationManagement } from '@shared/frontend/admin-components';
```

---

## 17. TESTING SHARED LIBRARY CHANGES

If you need to test changes to shared library before using them:

```bash
# Install shared library in editable mode
cd /opt/kasaai/apps/shared
pip install -e .

# Run tests
pytest tests/ -v

# Or from b2c-portal
cd /opt/kasaai/apps/b2c-portal
pytest tests/ -v

# With coverage
pytest --cov=shared tests/
```

---

## 18. COMMON GOTCHAS

### ❌ Wrong Way: Direct API calls
```python
# Don't do this!
async def bad_tts(text: str):
    url = "https://coqui.ailabsafrica.com/api/tts"
    # hardcoded endpoint, no billing, no failover
```

### ✅ Right Way: Use service
```python
# Do this instead!
from apps.shared.services.tts_provider_service import TTSProviderService

tts = TTSProviderService()
await tts.initialize()
result = await tts.synthesize(user_id, request)
# auto billing, failover, cost tracking
```

### ❌ Wrong Way: Recreate models
```python
# Don't do this!
class MyOrganization:
    def __init__(self, name):
        self.name = name
```

### ✅ Right Way: Use shared models
```python
# Do this instead!
from apps.shared.models.organization import Organization
```

### ❌ Wrong Way: Hardcode environment variables
```python
# Don't do this!
API_KEY = "sk-12345..."
```

### ✅ Right Way: Use environment
```python
# Do this instead!
import os
api_key = os.getenv("OPENAI_API_KEY")
```

---

## 19. GETTING HELP

### Documentation Files
- `SHARED_LIBRARY_OVERVIEW.md` - Full technical reference (this directory)
- `/opt/kasaai/apps/shared/README.md` - Shared library main docs
- `/opt/kasaai/apps/shared/QUICK_REFERENCE.md` - Architecture overview
- `/opt/kasaai/apps/shared/INTEGRATION_GUIDE.md` - Integration patterns

### Code Examples
- `/opt/kasaai/apps/core_backend/` - Production usage examples
- `/opt/kasaai/apps/shared/tests/` - Test examples
- `/opt/kasaai/apps/shared/integration/ai_services/examples/` - Usage patterns

### Common Services
- **TTS**: `/opt/kasaai/apps/shared/services/tts_provider_service.py`
- **ASR**: `/opt/kasaai/apps/shared/services/asr_provider_service.py`
- **RAG**: `/opt/kasaai/apps/shared/integration/rag.py`
- **Wallet**: `/opt/kasaai/apps/shared/integration/wallet/wallet_service.py`

---

## 20. QUICK START CHECKLIST

For a new B2C feature requiring voice:

- [ ] 1. Import `get_current_user` for auth
- [ ] 2. Import voice service (ConversationalVoiceService, TTSProviderService, or ASRProviderService)
- [ ] 3. Initialize service once at app startup
- [ ] 4. Create route that uses Depends(get_current_user)
- [ ] 5. Call service with user_id
- [ ] 6. Return results to frontend
- [ ] 7. Test with real audio data
- [ ] 8. Monitor costs via wallet/billing service
- [ ] 9. Check logs for errors
- [ ] 10. Add tests

---

**Last Updated**: 2025-11-11  
**Status**: Ready to use
