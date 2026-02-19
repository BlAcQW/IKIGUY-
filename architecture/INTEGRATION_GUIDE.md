# KasaAI Platform Integration Guide

**Version**: 2.1
**Last Updated**: 2025-10-26
**Audience**: Backend and Frontend Developers

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [AI Provider Services](#ai-provider-services)
3. [Centralized TTS Service](#centralized-tts-service) ⭐ NEW
4. [RAG Services](#rag-services)
5. [Document Processing](#document-processing)
6. [Wallet Services](#wallet-services)
7. [Health Monitoring](#health-monitoring)
8. [Complete Examples](#complete-examples)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

**Backend**:
```bash
# Install dependencies
pip install fastapi uvicorn pydantic aiohttp python-dotenv

# Environment variables - Self-hosted Supabase for Internal Apps
export MONGODB_URL="mongodb://admin:password@127.0.0.1:27017/kasaai_core?authSource=admin"
export SUPABASE_URL="https://supabase-api.ailabsafrica.com"
export SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvY2FsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzMjIwNzUsImV4cCI6MjA3NjY4MjA3NX0.bwOq689zcxepQnidP5k4pU7e_MOr_SP-00UVEQFz0eQ"
export SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvY2FsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTMyMjA3NSwiZXhwIjoyMDc2NjgyMDc1fQ.ncbP9EEe5v-3E7U9mhLNTfdq_VR-iUTxuNsaXn3HK2E"

# Supabase Dashboard: https://supabase.ailabsafrica.com
# Database: localhost:5433 (postgres/ciWfkEMFYnrYA6Ip665VbEps58SV5DY/)
```

**Frontend**:
```bash
# Install dependencies
npm install react react-router-dom

# Environment variables - Self-hosted Supabase for Internal Apps
VITE_API_URL=https://api.ailabsafrica.com
VITE_SUPABASE_URL=https://supabase-api.ailabsafrica.com
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxvY2FsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjEzMjIwNzUsImV4cCI6MjA3NjY4MjA3NX0.bwOq689zcxepQnidP5k4pU7e_MOr_SP-00UVEQFz0eQ
```

### Project Structure

```
your-app/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── ai_services.py    # Import shared services here
│   │   ├── services/
│   │   │   └── app_service.py        # Use shared services here
│   │   └── core/
│   │       └── config.py
│   └── requirements.txt
└── frontend/
    └── src/
        ├── hooks/
        │   └── useAIProvider.ts       # Import from @apps/shared/ui-hooks
        └── pages/
            └── AILab.tsx
```

---

## AI Provider Services

### Overview

The AI Provider Services module provides:
- Unified interface for TTS, LLM, ASR, Vision, Embedding models
- Centralized provider configuration
- Automated health monitoring
- Capability-based provider selection

**Location**: `@apps/shared/integration/ai_services/`

---

### Backend Integration

#### Step 1: Import Shared Services

```python
# In your service file (e.g., backend/services/tts_service.py)
from apps.shared.integration.ai_services import (
    AIProviderService,
    ProviderRegistry,
    HealthMonitorService,
    ProviderType,
    get_global_registry
)
```

#### Step 2: Initialize Provider Service

```python
# backend/services/tts_service.py
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class TTSService:
    """TTS service using shared AI Provider infrastructure."""

    def __init__(self):
        """Initialize TTS service with shared components."""
        # Get global provider registry
        self.registry = get_global_registry()

        # Register TTS providers from config
        from apps.shared.integration.ai_services.provider_registry import (
            get_default_tts_providers_config
        )
        self.registry.register_providers_from_config(
            get_default_tts_providers_config(),
            provider_type=ProviderType.TTS
        )

        # Initialize TTS provider service
        self.provider_service = AIProviderService(
            provider_type=ProviderType.TTS,
            cache_ttl=300,  # 5 minutes cache
            health_check_interval=60  # Check every 60 seconds
        )

        # Register all providers with the service
        for provider in self.registry.get_providers_by_type(ProviderType.TTS):
            self.provider_service.register_provider(provider)

        # Initialize health monitor
        self.health_monitor = HealthMonitorService(
            registry=self.registry,
            check_interval=60,
            timeout=5
        )

        # Register alert callback
        self.health_monitor.register_alert_callback(self._on_provider_alert)

        logger.info("TTSService initialized with shared AI services")

    async def _on_provider_alert(self, provider, result):
        """Handle provider health alerts."""
        if result.healthy:
            logger.info(f"Provider {provider.id} recovered!")
        else:
            logger.warning(
                f"Provider {provider.id} failed: {result.error}"
            )

    async def start(self):
        """Start background services."""
        await self.provider_service.start_auto_refresh()
        await self.health_monitor.start()
        logger.info("TTSService background tasks started")

    async def stop(self):
        """Stop background services."""
        await self.provider_service.stop_auto_refresh()
        await self.health_monitor.stop()
        logger.info("TTSService stopped")

    async def get_providers(self, force_refresh: bool = False) -> Dict:
        """Get all TTS providers."""
        await self.provider_service.refresh_providers(force=force_refresh)
        return self.provider_service.get_providers_dict()

    async def get_provider_by_id(self, provider_id: str):
        """Get specific provider by ID."""
        return self.registry.get_provider(provider_id)

    async def get_providers_with_capability(self, capability: str):
        """Get providers supporting specific capability."""
        return self.registry.get_providers_by_capability(
            capability,
            provider_type=ProviderType.TTS
        )

    async def synthesize(
        self,
        provider_id: str,
        text: str,
        language: str = "en",
        **kwargs
    ) -> Dict:
        """
        Synthesize speech using specified provider.

        Args:
            provider_id: Provider to use
            text: Text to synthesize
            language: Language code
            **kwargs: Provider-specific parameters

        Returns:
            Dict with audio_url, duration, etc.
        """
        # Get provider
        provider = self.registry.get_provider(provider_id)
        if not provider:
            raise ValueError(f"Provider {provider_id} not found")

        if provider.status != "online":
            raise ValueError(f"Provider {provider_id} is offline")

        # Make request to provider
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{provider.endpoint}/synthesize",
                json={"text": text, "language": language, **kwargs},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    raise Exception(f"Provider returned {response.status}")

                result = await response.json()

        return result

    async def get_health_report(self) -> Dict:
        """Get health report for all providers."""
        return await self.health_monitor.get_health_report()
```

#### Step 3: Create FastAPI Routes

```python
# backend/api/routes/tts_routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/api/v1/tts", tags=["TTS"])

# Dependency to get TTS service (initialized in main.py)
def get_tts_service():
    from app.main import tts_service
    return tts_service

class SynthesizeRequest(BaseModel):
    provider_id: str
    text: str
    language: str = "en"
    voice_settings: Optional[Dict[str, Any]] = None

@router.get("/providers")
async def list_providers(
    force_refresh: bool = False,
    service = Depends(get_tts_service)
):
    """List all TTS providers with health status."""
    providers = await service.get_providers(force_refresh=force_refresh)
    return {"success": True, "data": providers}

@router.get("/providers/capability/{capability}")
async def get_providers_by_capability(
    capability: str,
    service = Depends(get_tts_service)
):
    """Get providers supporting specific capability."""
    providers = await service.get_providers_with_capability(capability)
    return {
        "success": True,
        "data": {p.id: p.dict() for p in providers}
    }

@router.post("/synthesize")
async def synthesize_speech(
    request: SynthesizeRequest,
    service = Depends(get_tts_service)
):
    """Synthesize speech using specified provider."""
    try:
        result = await service.synthesize(
            provider_id=request.provider_id,
            text=request.text,
            language=request.language,
            **(request.voice_settings or {})
        )

        return {
            "success": True,
            "data": result,
            "metadata": {
                "provider_id": request.provider_id
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Provider error: {e}")

@router.get("/health")
async def get_health_report(service = Depends(get_tts_service)):
    """Get health report for all TTS providers."""
    report = await service.get_health_report()
    return {"success": True, "data": report}
```

#### Step 4: Initialize in main.py

```python
# backend/app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.services.tts_service import TTSService
from app.api.routes import tts_routes

# Global service instances
tts_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global tts_service

    # Startup
    tts_service = TTSService()
    await tts_service.start()
    yield

    # Shutdown
    await tts_service.stop()

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(tts_routes.router)
```

---

### Frontend Integration

#### Step 1: Create useAIProvider Hook

```typescript
// src/hooks/useAIProvider.ts
import { useState, useEffect, useCallback } from 'react';

export interface AIProvider {
  id: string;
  name: string;
  provider_type: string;
  endpoint: string;
  status: 'online' | 'offline' | 'degraded' | 'building' | 'maintenance';
  capabilities: Record<string, boolean>;
  languages: number;
  languageList: string[];
  description: string;
  icon: string;
  lastChecked?: string;
  responseTime?: number;
}

interface UseAIProviderReturn {
  providers: Record<string, AIProvider>;
  selectedProvider: AIProvider | null;
  setSelectedProvider: (provider: AIProvider | null) => void;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useAIProvider(
  providerType: 'tts' | 'llm' | 'asr'
): UseAIProviderReturn {
  const [providers, setProviders] = useState<Record<string, AIProvider>>({});
  const [selectedProvider, setSelectedProvider] = useState<AIProvider | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProviders = useCallback(
    async (forceRefresh = false) => {
      setLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem('supabase_token');
        const response = await fetch(
          `${import.meta.env.VITE_API_URL}/api/v1/${providerType}/providers${
            forceRefresh ? '?force_refresh=true' : ''
          }`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch providers: ${response.statusText}`);
        }

        const { data } = await response.json();
        setProviders(data);

        // Auto-select first online provider if none selected
        if (!selectedProvider && Object.keys(data).length > 0) {
          const firstOnline = Object.values(data).find(
            (p: any) => p.status === 'online'
          );
          if (firstOnline) {
            setSelectedProvider(firstOnline as AIProvider);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        console.error('Error fetching providers:', err);
      } finally {
        setLoading(false);
      }
    },
    [providerType, selectedProvider]
  );

  useEffect(() => {
    fetchProviders();

    // Auto-refresh every 60 seconds
    const interval = setInterval(() => fetchProviders(false), 60000);

    return () => clearInterval(interval);
  }, [fetchProviders]);

  return {
    providers,
    selectedProvider,
    setSelectedProvider,
    loading,
    error,
    refetch: () => fetchProviders(true),
  };
}
```

#### Step 2: Use in Component

```typescript
// src/pages/TTSLab.tsx
import React, { useState } from 'react';
import { useAIProvider } from '../hooks/useAIProvider';

export function TTSLab() {
  const {
    providers,
    selectedProvider,
    setSelectedProvider,
    loading,
    error,
    refetch,
  } = useAIProvider('tts');

  const [text, setText] = useState('');
  const [synthesizing, setSynthesizing] = useState(false);

  const handleSynthesize = async () => {
    if (!selectedProvider || !text) return;

    setSynthesizing(true);
    try {
      const token = localStorage.getItem('supabase_token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/tts/synthesize`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            provider_id: selectedProvider.id,
            text,
            language: 'en',
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Synthesis failed');
      }

      const { data } = await response.json();

      // Play audio
      const audio = new Audio(data.audio_url);
      audio.play();
    } catch (err) {
      console.error('Synthesis error:', err);
    } finally {
      setSynthesizing(false);
    }
  };

  return (
    <div>
      <h1>TTS Lab</h1>

      {/* Provider Selection */}
      <div>
        <h2>Select Provider</h2>
        {loading && <p>Loading providers...</p>}
        {error && <p>Error: {error}</p>}

        <select
          value={selectedProvider?.id || ''}
          onChange={(e) => {
            const provider = providers[e.target.value];
            setSelectedProvider(provider);
          }}
        >
          <option value="">Select a provider</option>
          {Object.values(providers).map((provider) => (
            <option key={provider.id} value={provider.id}>
              {provider.icon} {provider.name} ({provider.status})
            </option>
          ))}
        </select>

        <button onClick={refetch}>Refresh</button>
      </div>

      {/* Synthesize Section */}
      {selectedProvider && (
        <div>
          <h2>Synthesize Speech</h2>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Enter text to synthesize..."
            rows={5}
          />
          <button onClick={handleSynthesize} disabled={synthesizing || !text}>
            {synthesizing ? 'Synthesizing...' : 'Synthesize'}
          </button>
        </div>
      )}
    </div>
  );
}
```

---

## Centralized TTS Service

### Overview

The **Centralized TTS Provider Service** (`@apps/shared/services/tts_provider_service.py`) provides unified access to 10 self-hosted TTS providers with automatic billing, health monitoring, and voice cloning support.

**Key Features:**
- ✅ 10 TTS providers (Coqui XTTS, MeloTTS, F5-TTS, StyleTTS2, OpenVoice, Kokoro, Moshi, Akan MMS, etc.)
- ✅ Automatic wallet billing integration
- ✅ Provider health monitoring (30-second cache)
- ✅ Voice cloning support
- ✅ Multi-language support (17 languages)
- ✅ Automatic refunds on synthesis failure

**Why Use This (Not AI Provider Services)?**
- **Centralized billing**: Automatic cost calculation and wallet deductions
- **Business logic**: Orchestrates providers + wallet + usage calculator + health monitor
- **Consistent API**: Single interface for all TTS needs across all apps

### Architecture

```
Apps (Inkwave, StudyFlow, B2C Portal, etc.)
    ↓
TTSProviderService (@apps/shared/services/)
    ↓
├─> ProviderRegistry (provider discovery)
├─> HealthMonitor (status tracking)
├─> WalletService (automatic billing)
└─> UsageCalculator (cost calculation)
    ↓
TTS Provider Endpoints (self-hosted)
```

### Cost Model

- **Base**: $0.015 per 1000 characters
- **Voice Cloning**: +$0.05 per request
- **Premium Providers** (StyleTTS2, F5-TTS, OpenVoice): 2x base cost

**Example Costs:**
- Coqui XTTS, 500 chars: **$0.0075**
- MeloTTS, 1000 chars: **$0.0150**
- F5-TTS + voice cloning, 500 chars: **$0.0650**

### Quick Start (Backend)

#### Step 1: Import the Service

```python
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest
)
```

#### Step 2: Initialize (once at app startup)

```python
# In main.py or app initialization
class MyApp:
    def __init__(self):
        self.tts_service = TTSProviderService(
            enable_billing=True,  # Automatic wallet deductions
            enable_health_monitoring=True  # Track provider status
        )

    async def startup(self):
        """Initialize TTS service on app startup."""
        await self.tts_service.initialize()
        logger.info("TTS service initialized")
```

#### Step 3: Use for Synthesis

```python
# Basic synthesis
async def synthesize_speech(
    user_id: str,
    text: str,
    provider_id: str = "coqui_xtts",
    language: str = "en",
    speed: float = 1.0
):
    """
    Synthesize speech with automatic billing.

    Args:
        user_id: User ID for billing (wallet deduction)
        text: Text to synthesize
        provider_id: TTS provider to use
        language: Language code (en, fr, es, etc.)
        speed: Speech speed (0.5-2.0)

    Returns:
        Tuple of (audio_bytes, cost_usd, transaction_id)
    """
    # Create synthesis request
    request = SynthesisRequest(
        provider_id=provider_id,
        text=text,
        language=language,
        speed=speed
    )

    # Synthesize (automatic billing)
    result = await tts_service.synthesize(
        user_id=user_id,
        request=request
    )

    # Extract audio and cost info
    audio_bytes = base64.b64decode(result.audio_base64)
    cost_usd = result.cost
    transaction_id = result.transaction_id

    logger.info(f"Synthesized {len(text)} chars, cost=${cost_usd:.4f}, txn={transaction_id}")

    return audio_bytes, cost_usd, transaction_id
```

#### Step 4: Voice Cloning (Optional)

```python
# Synthesis with voice cloning
async def synthesize_with_voice_cloning(
    user_id: str,
    text: str,
    reference_audio_url: str,
    provider_id: str = "coqui_xtts"
):
    """
    Synthesize speech with voice cloning.

    Args:
        user_id: User ID for billing
        text: Text to synthesize
        reference_audio_url: URL to reference audio (10-30 seconds)
        provider_id: TTS provider (must support voice cloning)

    Returns:
        Tuple of (audio_bytes, cost_usd, transaction_id)
    """
    request = SynthesisRequest(
        provider_id=provider_id,
        text=text,
        language="en",
        voice_cloning=True,
        reference_audio=reference_audio_url
    )

    result = await tts_service.synthesize(
        user_id=user_id,
        request=request
    )

    audio_bytes = base64.b64decode(result.audio_base64)

    # Voice cloning costs more ($0.05 + base)
    logger.info(f"Voice cloning cost: ${result.cost:.4f}")

    return audio_bytes, result.cost, result.transaction_id
```

### FastAPI Integration

```python
# backend/api/routes/tts_routes.py
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1/tts", tags=["TTS"])

class SynthesizeRequest(BaseModel):
    text: str
    provider_id: str = "coqui_xtts"
    language: str = "en"
    speed: float = 1.0
    voice_cloning: bool = False
    reference_audio: Optional[str] = None

@router.post("/synthesize")
async def synthesize_speech(
    request: SynthesizeRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Synthesize speech with automatic billing.

    Returns MP3 audio file with cost headers.
    """
    try:
        # Synthesize using centralized service
        audio_bytes, cost, transaction_id = await synthesize_speech(
            user_id=current_user_id,
            text=request.text,
            provider_id=request.provider_id,
            language=request.language,
            speed=request.speed
        )

        # Return audio as MP3
        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "X-Audio-Cost": str(cost),
                "X-Transaction-ID": transaction_id
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"TTS synthesis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Synthesis failed")


@router.get("/providers")
async def list_tts_providers():
    """List available TTS providers with capabilities."""
    providers = await tts_service.get_available_providers()
    return {"providers": providers}


@router.get("/providers/{provider_id}/health")
async def get_provider_health(provider_id: str):
    """Get health status for a specific provider."""
    health = await tts_service.get_provider_health(provider_id)
    return health
```

### Provider Capabilities

| Provider | Languages | Voice Cloning | Multi-Speaker | Emotion Control |
|----------|-----------|---------------|---------------|-----------------|
| Coqui XTTS | 17 | ✅ | ❌ | ❌ |
| MeloTTS | 6 | ❌ | ✅ | ❌ |
| F5-TTS | 4 | ✅ | ❌ | ❌ |
| StyleTTS2 | 1 (EN) | ✅ | ❌ | ✅ |
| OpenVoice | 2 (EN, ZH) | ✅ | ❌ | ✅ |
| Kokoro | 1 (EN) | ❌ | ❌ | ❌ |
| Moshi | 1 (EN) | ❌ | ❌ | ❌ |
| Akan MMS | 1 (Twi) | ❌ | ✅ | ❌ |

### Educational Use Case (StudyFlow Example)

```python
# backend/services/pronunciation_service.py
from apps.shared.services.tts_provider_service import TTSProviderService

class PronunciationService:
    """Educational TTS service for StudyFlow."""

    _tts_service: Optional[TTSProviderService] = None
    _initialized: bool = False

    @classmethod
    async def get_tts_service(cls) -> TTSProviderService:
        """Get or create TTS service instance."""
        if cls._tts_service is None:
            cls._tts_service = TTSProviderService(
                enable_billing=True,
                enable_health_monitoring=True
            )

        if not cls._initialized:
            await cls._tts_service.initialize()
            cls._initialized = True

        return cls._tts_service

    @staticmethod
    async def synthesize_word_pronunciation(
        user_id: str,
        word: str,
        language: str = "en",
        provider_id: str = "coqui_xtts"
    ):
        """
        Get pronunciation audio for a word (slower speech for learning).

        Args:
            user_id: Student user ID
            word: Word to pronounce
            language: Language code
            provider_id: TTS provider

        Returns:
            Tuple of (audio_bytes, cost_usd, transaction_id)
        """
        tts = await PronunciationService.get_tts_service()

        # Use slower speed for educational purposes
        request = SynthesisRequest(
            provider_id=provider_id,
            text=word,
            language=language,
            speed=0.8  # Slower for learning
        )

        result = await tts.synthesize(
            user_id=user_id,
            request=request
        )

        audio_bytes = base64.b64decode(result.audio_base64)
        return audio_bytes, result.cost, result.transaction_id
```

### Error Handling

```python
from apps.shared.services.tts_provider_service import (
    TTSProviderService,
    SynthesisRequest,
    ProviderNotFoundError,
    ProviderOfflineError,
    InsufficientBalanceError
)

async def safe_synthesize(user_id: str, text: str):
    """Synthesize with comprehensive error handling."""
    try:
        result = await tts_service.synthesize(
            user_id=user_id,
            request=SynthesisRequest(
                provider_id="coqui_xtts",
                text=text,
                language="en"
            )
        )
        return result

    except ProviderNotFoundError:
        logger.error("Provider not found, using fallback")
        # Try fallback provider
        result = await tts_service.synthesize(
            user_id=user_id,
            request=SynthesisRequest(
                provider_id="melotts",  # Fallback
                text=text,
                language="en"
            )
        )
        return result

    except ProviderOfflineError as e:
        logger.error(f"Provider offline: {e}")
        raise HTTPException(
            status_code=503,
            detail="TTS service temporarily unavailable"
        )

    except InsufficientBalanceError:
        logger.warning(f"Insufficient balance for user {user_id}")
        raise HTTPException(
            status_code=402,
            detail="Insufficient wallet balance"
        )

    except Exception as e:
        logger.error(f"Unexpected TTS error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Synthesis failed"
        )
```

### Testing

```python
# tests/test_tts_service.py
import pytest
from apps.shared.services.tts_provider_service import TTSProviderService, SynthesisRequest

@pytest.mark.asyncio
async def test_tts_synthesis():
    """Test basic TTS synthesis."""
    tts = TTSProviderService(enable_billing=False)  # Disable billing for testing
    await tts.initialize()

    request = SynthesisRequest(
        provider_id="coqui_xtts",
        text="Hello world",
        language="en"
    )

    result = await tts.synthesize(
        user_id="test_user",
        request=request,
        skip_billing=True  # Skip billing for tests
    )

    assert result.audio_base64 is not None
    assert result.cost > 0
    assert result.provider_id == "coqui_xtts"


@pytest.mark.asyncio
async def test_voice_cloning():
    """Test voice cloning."""
    tts = TTSProviderService(enable_billing=False)
    await tts.initialize()

    request = SynthesisRequest(
        provider_id="coqui_xtts",
        text="This is a test",
        language="en",
        voice_cloning=True,
        reference_audio="https://example.com/reference.wav"
    )

    result = await tts.synthesize(
        user_id="test_user",
        request=request,
        skip_billing=True
    )

    assert result.audio_base64 is not None
    assert result.cost > 0.05  # Voice cloning adds $0.05
```

### Migration from Old TTS Pattern

**Before (AI Provider Services pattern):**
```python
# Old way - manual provider management
tts_service = TTSService()
await tts_service.start()
result = await tts_service.synthesize(
    provider_id="coqui_xtts",
    text="Hello",
    language="en"
)
# Manual billing required
await wallet_service.deduct_cost(user_id, cost)
```

**After (Centralized TTS Service):**
```python
# New way - automatic billing integrated
tts_service = TTSProviderService()
await tts_service.initialize()
result = await tts_service.synthesize(
    user_id=user_id,  # Billing automatic
    request=SynthesisRequest(
        provider_id="coqui_xtts",
        text="Hello",
        language="en"
    )
)
# Billing done automatically, transaction_id returned
```

### Documentation References

- **Service README**: `/opt/kasaai/apps/shared/services/README.md`
- **Implementation Summary**: `/opt/kasaai/CENTRALIZED_TTS_SERVICE_SUMMARY.md`
- **TASKS.md Phase 6**: `/opt/kasaai/apps/TASKS.md#phase-6-centralized-tts-service-integration`
- **Provider Registry**: `/opt/kasaai/apps/shared/integration/ai_services/provider_registry.py`

---

## RAG Services

### Overview

RAG (Retrieval-Augmented Generation) provides semantic search over document collections using vector embeddings.

**Location**: `@apps/shared/integration/rag_service/`

---

### Backend Integration

#### Step 1: Import RAG Service

```python
# backend/services/knowledge_base_service.py
from apps.shared.integration.rag_service import RAGService
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """Knowledge base service using shared RAG infrastructure."""

    def __init__(self, collection_name: str):
        """Initialize with specific collection."""
        self.rag = RAGService(collection_name=collection_name)
        logger.info(f"KnowledgeBaseService initialized for {collection_name}")

    async def query(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.7,
        include_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Query knowledge base with semantic search.

        Args:
            query: User query
            top_k: Number of results to return
            min_similarity: Minimum similarity threshold
            include_metadata: Include document metadata

        Returns:
            Dict with results and context
        """
        results = await self.rag.query(
            query=query,
            top_k=top_k,
            min_similarity=min_similarity
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result["content"],
                "similarity": result["similarity"],
                "chunk_id": result.get("chunk_id"),
                "document_id": result.get("document_id"),
                "metadata": result.get("metadata") if include_metadata else None
            })

        # Build context for LLM
        context = "\n\n".join([r["content"] for r in formatted_results])

        return {
            "query": query,
            "results": formatted_results,
            "context": context
        }

    async def add_document(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> Dict[str, Any]:
        """Add document to knowledge base."""
        document_id = await self.rag.add_document(
            text=text,
            metadata=metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        return {
            "document_id": document_id,
            "status": "added"
        }

    async def delete_document(self, document_id: str) -> bool:
        """Delete document from knowledge base."""
        return await self.rag.delete_document(document_id)

    async def list_documents(self, limit: int = 100) -> List[Dict]:
        """List all documents in collection."""
        return await self.rag.list_documents(limit=limit)
```

#### Step 2: Create API Routes

```python
# backend/api/routes/knowledge_base_routes.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter(prefix="/api/v1/knowledge-base", tags=["Knowledge Base"])

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    min_similarity: float = 0.7
    include_metadata: bool = True

class AddDocumentRequest(BaseModel):
    text: str
    metadata: Dict[str, Any]
    chunk_size: int = 500
    chunk_overlap: int = 50

@router.post("/{collection_name}/query")
async def query_knowledge_base(
    collection_name: str,
    request: QueryRequest
):
    """Query knowledge base with semantic search."""
    service = KnowledgeBaseService(collection_name=collection_name)

    try:
        result = await service.query(
            query=request.query,
            top_k=request.top_k,
            min_similarity=request.min_similarity,
            include_metadata=request.include_metadata
        )

        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{collection_name}/documents")
async def add_document(
    collection_name: str,
    request: AddDocumentRequest
):
    """Add document to knowledge base."""
    service = KnowledgeBaseService(collection_name=collection_name)

    try:
        result = await service.add_document(
            text=request.text,
            metadata=request.metadata,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )

        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{collection_name}/documents/{document_id}")
async def delete_document(
    collection_name: str,
    document_id: str
):
    """Delete document from knowledge base."""
    service = KnowledgeBaseService(collection_name=collection_name)

    try:
        deleted = await service.delete_document(document_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### Frontend Integration

```typescript
// src/hooks/useKnowledgeBase.ts
import { useState } from 'react';

interface QueryResult {
  content: string;
  similarity: number;
  chunk_id: string;
  document_id: string;
  metadata?: Record<string, any>;
}

export function useKnowledgeBase(collectionName: string) {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<QueryResult[]>([]);

  const query = async (
    queryText: string,
    options?: {
      top_k?: number;
      min_similarity?: number;
      include_metadata?: boolean;
    }
  ) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('supabase_token');
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/knowledge-base/${collectionName}/query`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            query: queryText,
            top_k: options?.top_k || 5,
            min_similarity: options?.min_similarity || 0.7,
            include_metadata: options?.include_metadata !== false,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Query failed');
      }

      const { data } = await response.json();
      setResults(data.results);

      return data;
    } catch (error) {
      console.error('Query error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return {
    query,
    results,
    loading,
  };
}
```

---

## Document Processing

### Backend Integration

```python
# backend/services/document_service.py
from apps.shared.integration.document_processor import DocumentProcessor
from fastapi import UploadFile
from typing import Dict, Any

class DocumentService:
    """Document processing service."""

    def __init__(self):
        self.processor = DocumentProcessor()

    async def process_document(
        self,
        file: UploadFile,
        extract_metadata: bool = True,
        chunk: bool = True,
        chunk_size: int = 500
    ) -> Dict[str, Any]:
        """
        Process uploaded document.

        Args:
            file: Uploaded file
            extract_metadata: Extract document metadata
            chunk: Split into chunks
            chunk_size: Size of each chunk

        Returns:
            Processed document data
        """
        # Read file content
        content = await file.read()

        # Process document
        result = await self.processor.process(
            content=content,
            filename=file.filename,
            extract_metadata=extract_metadata,
            chunk=chunk,
            chunk_size=chunk_size
        )

        return result
```

---

## Wallet Services

### Backend Integration

```python
# backend/services/wallet_service.py
from apps.shared.integration.wallet_service import WalletService, UsageCalculator
from typing import Dict, Any

class AppWalletService:
    """Wallet service for app-specific operations."""

    def __init__(self):
        self.wallet = WalletService()
        self.calculator = UsageCalculator()

    async def get_balance(self, user_id: str) -> Dict[str, Any]:
        """Get user wallet balance."""
        balance = await self.wallet.get_balance(user_id)
        return {
            "user_id": user_id,
            "balance": balance,
            "currency": "credits"
        }

    async def deduct_for_operation(
        self,
        user_id: str,
        operation: str,
        **params
    ) -> Dict[str, Any]:
        """
        Deduct credits for an operation.

        Args:
            user_id: User ID
            operation: Operation type (e.g., "tts_synthesis", "llm_chat")
            **params: Operation-specific parameters

        Returns:
            Transaction details
        """
        # Calculate cost
        cost = self.calculator.calculate_cost(operation, **params)

        # Deduct credits
        transaction = await self.wallet.deduct(
            user_id=user_id,
            amount=cost,
            description=f"{operation.replace('_', ' ').title()}"
        )

        return {
            "transaction_id": transaction.id,
            "amount_deducted": cost,
            "new_balance": transaction.balance_after
        }
```

---

## Health Monitoring

### Backend Integration

```python
# backend/services/monitoring_service.py
from apps.shared.integration.ai_services import (
    HealthMonitorService,
    ProviderRegistry,
    get_global_registry
)
import logging

logger = logging.getLogger(__name__)

class MonitoringService:
    """Centralized monitoring service."""

    def __init__(self):
        self.registry = get_global_registry()
        self.health_monitor = HealthMonitorService(
            registry=self.registry,
            check_interval=60,  # Check every minute
            timeout=5
        )

        # Register alert callbacks
        self.health_monitor.register_alert_callback(self._on_provider_alert)

    async def _on_provider_alert(self, provider, result):
        """Handle provider alerts."""
        if result.healthy:
            logger.info(f"✅ Provider {provider.id} recovered")
            # Could send notification, update dashboard, etc.
        else:
            logger.error(
                f"❌ Provider {provider.id} failed: {result.error}"
            )
            # Could send alert email, Slack notification, etc.

    async def start(self):
        """Start health monitoring."""
        await self.health_monitor.start()

    async def stop(self):
        """Stop health monitoring."""
        await self.health_monitor.stop()

    async def get_health_report(self):
        """Get comprehensive health report."""
        return await self.health_monitor.get_health_report()

    def get_metrics(self, provider_id: str = None):
        """Get provider metrics."""
        return self.health_monitor.get_metrics(provider_id=provider_id)
```

---

## Complete Examples

### Example 1: TTS Lab with All Features

**Backend** (complete FastAPI app):

```python
# backend/main.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from apps.shared.integration.ai_services import (
    AIProviderService,
    ProviderRegistry,
    HealthMonitorService,
    ProviderType,
    get_global_registry
)

# Global services
tts_service = None
monitoring_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown."""
    global tts_service, monitoring_service

    # Initialize services
    tts_service = TTSService()
    monitoring_service = MonitoringService()

    # Start background tasks
    await tts_service.start()
    await monitoring_service.start()

    yield

    # Cleanup
    await tts_service.stop()
    await monitoring_service.stop()

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Models
class SynthesizeRequest(BaseModel):
    provider_id: str
    text: str
    language: str = "en"
    speed: float = 1.0

# Routes
@app.get("/api/v1/tts/providers")
async def list_providers(force_refresh: bool = False):
    providers = await tts_service.get_providers(force_refresh)
    return {"success": True, "data": providers}

@app.post("/api/v1/tts/synthesize")
async def synthesize(request: SynthesizeRequest):
    try:
        result = await tts_service.synthesize(
            provider_id=request.provider_id,
            text=request.text,
            language=request.language,
            speed=request.speed
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tts/clone-voice")
async def clone_voice(
    provider_id: str,
    text: str,
    language: str,
    audio_file: UploadFile = File(...)
):
    try:
        result = await tts_service.clone_voice(
            provider_id=provider_id,
            text=text,
            language=language,
            audio_file=audio_file
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health")
async def health_report():
    report = await monitoring_service.get_health_report()
    return {"success": True, "data": report}
```

**Frontend** (complete React app):

```typescript
// src/App.tsx
import React from 'react';
import { TTSLab } from './pages/TTSLab';

function App() {
  return (
    <div className="App">
      <TTSLab />
    </div>
  );
}

export default App;

// src/pages/TTSLab.tsx
import React, { useState } from 'react';
import { useAIProvider } from '../hooks/useAIProvider';
import { ProviderSidebar } from '../components/ProviderSidebar';
import { SynthesizePanel } from '../components/SynthesizePanel';

export function TTSLab() {
  const {
    providers,
    selectedProvider,
    setSelectedProvider,
    loading,
    error,
    refetch,
  } = useAIProvider('tts');

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <ProviderSidebar
        providers={providers}
        selectedId={selectedProvider?.id}
        onSelect={(id) => setSelectedProvider(providers[id])}
        loading={loading}
        error={error}
        onRefresh={refetch}
      />

      {/* Main Panel */}
      <div className="flex-1 p-6">
        {selectedProvider ? (
          <SynthesizePanel provider={selectedProvider} />
        ) : (
          <div>Select a provider to get started</div>
        )}
      </div>
    </div>
  );
}

// src/components/SynthesizePanel.tsx
import React, { useState } from 'react';
import { AIProvider } from '../hooks/useAIProvider';

interface Props {
  provider: AIProvider;
}

export function SynthesizePanel({ provider }: Props) {
  const [text, setText] = useState('');
  const [synthesizing, setSynthesizing] = useState(false);

  const handleSynthesize = async () => {
    setSynthesizing(true);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/tts/synthesize`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('supabase_token')}`,
          },
          body: JSON.stringify({
            provider_id: provider.id,
            text,
            language: 'en',
          }),
        }
      );

      const { data } = await response.json();

      // Play audio
      const audio = new Audio(data.audio_url);
      audio.play();
    } catch (error) {
      console.error('Synthesis error:', error);
    } finally {
      setSynthesizing(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">
        {provider.icon} {provider.name}
      </h2>

      <div className="mb-4">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter text to synthesize..."
          className="w-full h-32 p-2 border rounded"
        />
      </div>

      <button
        onClick={handleSynthesize}
        disabled={synthesizing || !text}
        className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-400"
      >
        {synthesizing ? 'Synthesizing...' : 'Synthesize'}
      </button>
    </div>
  );
}
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'apps.shared'`

**Solution**:
```bash
# Add project root to PYTHONPATH
export PYTHONPATH=/opt/kasaai:$PYTHONPATH

# Or in code
import sys
sys.path.insert(0, '/opt/kasaai')
```

#### 2. Provider Always Offline

**Problem**: All providers show as offline

**Solution**:
- Check provider endpoints are accessible
- Verify health check endpoints (`{endpoint}/health`)
- Check network connectivity
- Review health monitor logs

#### 3. MongoDB Connection Errors

**Problem**: `pymongo.errors.ServerSelectionTimeoutError`

**Solution**:
```python
# Verify connection string format
MONGODB_URL = "mongodb://admin:password@127.0.0.1:27017/kasaai_core?authSource=admin"

# Test connection
from pymongo import MongoClient
client = MongoClient(MONGODB_URL)
client.server_info()  # Should not raise exception
```

#### 4. Supabase Auth Errors

**Problem**: `Invalid or expired token`

**Solution**:
```python
# Verify token format
import jwt

token = "your_jwt_token"
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)  # Should contain 'sub', 'email', 'exp'

# Check token expiration
import time
if decoded['exp'] < time.time():
    print("Token expired!")
```

---

## Best Practices

### Backend

1. **Always use shared services**: Don't duplicate provider management code
2. **Handle errors gracefully**: Provider might be offline, handle it
3. **Use dependency injection**: FastAPI's `Depends()` for service injection
4. **Log extensively**: Use Python's logging module
5. **Test thoroughly**: Unit tests for all service methods

### Frontend

1. **Use hooks for logic**: Separate logic from presentation
2. **Handle loading states**: Show spinners, disable buttons
3. **Error boundaries**: Catch and display errors gracefully
4. **Optimize renders**: Use `useCallback`, `useMemo` appropriately
5. **Accessibility**: ARIA labels, keyboard navigation

---

## Next Steps

1. **Read Architecture Docs**: `@apps/architecture/ARCHITECTURE.md`
2. **Review Component Patterns**: `@apps/architecture/COMPONENT_PATTERNS.md`
3. **Check API Docs**: `@apps/architecture/API_DOCUMENTATION.md`
4. **Explore Examples**: Look at `@apps/b2c-portal/` for real implementation
5. **Write Tests**: Create comprehensive unit tests

---

**Questions?**

If you encounter issues not covered here:
1. Check existing app implementations for reference
2. Review shared service source code
3. Update this document with your findings

This is a living document. Keep it updated as integration patterns evolve.
