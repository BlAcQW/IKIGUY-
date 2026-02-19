# TTS System Migration Guide

Complete guide for migrating from legacy TTS services to the unified `@shared/tts/` system.

**Migration Timeline:** 4 weeks (as of 2025-11-23)
**Status:** Week 3 Complete, Week 4 in Progress

---

## Table of Contents

1. [Why Migrate?](#why-migrate)
2. [Quick Start](#quick-start)
3. [Provider ID Changes](#provider-id-changes)
4. [Backend Migration](#backend-migration)
5. [Frontend Migration](#frontend-migration)
6. [Testing](#testing)
7. [Rollback Plan](#rollback-plan)
8. [FAQ](#faq)

---

## Why Migrate?

### Benefits of Unified System

**Cost Savings:**
- ✅ 40% reduction via MongoDB GridFS caching
- ✅ Automatic cache hit/miss tracking
- ✅ Idempotent billing prevents duplicate charges

**Developer Experience:**
- ✅ Single `AsyncTTSClient` for all providers
- ✅ TypeScript types auto-generated from Pydantic models
- ✅ Standardized provider IDs (snake_case)
- ✅ Comprehensive documentation and examples

**Reliability:**
- ✅ Provider health monitoring with email alerts
- ✅ Automatic refunds on synthesis failure
- ✅ 80%+ test coverage
- ✅ Real-time wallet balance tracking

**Features:**
- ✅ Unified API routes at `/api/tts`
- ✅ Voice cloning (2x cost multiplier)
- ✅ Cost estimation before synthesis
- ✅ Batch synthesis support
- ✅ Provider status monitoring

---

## Quick Start

### 1. Install Dependencies

```bash
# Already included in apps/venv
pip install motor pymongo aiohttp pydantic
```

### 2. Import New Client

**Before (DEPRECATED):**
```python
from apps.shared.integration.ai_services.tts_service import TTSService

tts = TTSService(provider="openai", api_key="...", voice="nova")
audio = await tts.synthesize("Hello world")
```

**After (RECOMMENDED):**
```python
from apps.shared.tts.client import AsyncTTSClient
from apps.shared.tts.models import TTSProvider, TTSRequest, AudioFormat

async with AsyncTTSClient() as client:
    response = await client.synthesize(
        text="Hello world",
        provider=TTSProvider.COQUI_XTTS,
        language="en",
        speaker="nova",
        output_format=AudioFormat.WAV
    )

    audio_bytes = response.audio
    cost = response.cost  # GHS 0.00001 per character
```

### 3. Add Billing Support

```python
from apps.shared.tts.billing import TTSBillingManager
from apps.shared.integration.wallet import WalletService, Currency
from apps.shared.integration.usage_calculator import PricingTier
from motor.motor_asyncio import AsyncIOMotorClient

# Initialize wallet service
client = AsyncIOMotorClient("mongodb://...")
wallet_service = WalletService(database=client.kasaai_core)

# Initialize billing manager
billing_manager = TTSBillingManager(
    wallet_service=wallet_service,
    pricing_tier=PricingTier.BASIC,
    currency=Currency.GHS
)

# Synthesize with automatic billing
response, transaction = await billing_manager.synthesize_with_billing(
    user_id="user_123",
    text="Hello world",
    provider=TTSProvider.COQUI_XTTS,
    language="en"
)

print(f"Cost: GHS {response.cost}")
print(f"Transaction ID: {transaction.id}")
```

---

## Provider ID Changes

All provider IDs now use **lowercase snake_case** format for consistency.

### Complete Mapping Table

| Legacy ID          | Canonical ID      | Notes                      |
|--------------------|-------------------|----------------------------|
| `XTTS`             | `coqui_xtts`      | Voice cloning supported    |
| `StyleTTS2`        | `styletts2`       | Emotion control            |
| `F5-TTS`           | `f5tts`           | Zero-shot voice cloning    |
| `Melo-TTS`         | `melotts`         | Multi-language             |
| `Open-Voice`       | `openvoice`       | Voice conversion           |
| `GPT-SoVITS`       | `gpt_sovits`      | High quality               |
| `Fish-Speech`      | `fish_speech`     | Streaming support          |
| `TTS-WebUI`        | `tts_webui`       | 20+ models                 |
| `Kokoro-TTS`       | `kokoro`          | Fast, natural prosody      |
| `VoxCPM`           | `voxcpm`          | Multilingual               |
| `Crawl4AI`         | `crawl4ai`        | Web scraping integration   |
| `IndexTTS`         | `indextts`        | Index-based synthesis      |
| `Chatterbox`       | `chatterbox`      | Conversational             |
| `Zonos`            | `zonos`           | Cloud TTS                  |
| `Moshi`            | `moshi`           | Real-time conversation     |

### Migration Script

Run the user preference migration script to update existing data:

```bash
# Dry run (preview changes)
python apps/shared/tts/scripts/migrate_user_preferences.py \
    --mongo-url "mongodb://admin:password@localhost:27017" \
    --database "kasaai_core"

# Execute migration
python apps/shared/tts/scripts/migrate_user_preferences.py \
    --mongo-url "mongodb://admin:password@localhost:27017" \
    --database "kasaai_core" \
    --execute
```

**What it does:**
- Scans MongoDB collections for legacy provider IDs
- Updates to canonical format
- Creates backup before migration
- Adds `migration_warnings` field to affected documents
- Generates migration report

---

## Backend Migration

### Step 1: Add Unified TTS Routes

**File:** `apps/<your_app>/backend/app/main.py`

```python
from apps.shared.routes.tts_routes import router as tts_router

# Include unified TTS routes
app.include_router(tts_router, prefix="/api/tts", tags=["TTS"])
```

**New Endpoints Available:**
- `POST /api/tts/synthesize` - Synthesize with billing
- `POST /api/tts/clone-voice` - Voice cloning (2x cost)
- `GET /api/tts/providers` - List providers with health status
- `GET /api/tts/providers/{id}` - Get specific provider
- `GET /api/tts/estimate-cost` - Cost estimation
- `GET /api/tts/cache/stats` - Cache statistics
- `DELETE /api/tts/cache` - Clear cache
- `GET /api/tts/health` - Health check

### Step 2: Replace Old TTS Service Calls

**Before (DEPRECATED):**
```python
from apps.shared.integration.ai_services.tts_service import TTSService

class VoiceService:
    async def generate_audio(self, text: str):
        tts = TTSService(provider="openai", voice="nova")
        return await tts.synthesize(text)
```

**After (RECOMMENDED):**
```python
from apps.shared.tts.client import AsyncTTSClient
from apps.shared.tts.models import TTSProvider, AudioFormat

class VoiceService:
    async def generate_audio(self, text: str):
        async with AsyncTTSClient() as client:
            response = await client.synthesize(
                text=text,
                provider=TTSProvider.COQUI_XTTS,
                language="en",
                output_format=AudioFormat.WAV
            )
            return response.audio
```

### Step 3: Add Caching (Optional but Recommended)

```python
from apps.shared.tts.cache import TTSAudioCache
from motor.motor_asyncio import AsyncIOMotorClient

# Initialize cache
client = AsyncIOMotorClient("mongodb://...")
cache = TTSAudioCache(
    database=client.tts_cache,
    default_ttl_hours=24,
    enable_metrics=True
)

await cache.ensure_indexes()

# Check cache before synthesis
cache_key = cache.generate_key(
    text="Hello world",
    provider="coqui_xtts",
    voice="nova",
    language="en"
)

cached_audio = await cache.get(cache_key)
if cached_audio:
    print("Cache hit!")
    return cached_audio

# Synthesize and cache
response = await client.synthesize(...)
await cache.set(cache_key, response.audio, ttl_hours=24)
```

---

## Frontend Migration

### Step 1: Use Enhanced Hook

**File:** `apps/<your_app>/frontend/src/components/VoiceSettings.tsx`

**Before (OLD):**
```typescript
import { useState } from 'react';

const VoiceSettings = () => {
  const [providers, setProviders] = useState([]);

  useEffect(() => {
    // Manual fetch
    fetch('/api/tts/providers')
      .then(res => res.json())
      .then(data => setProviders(data));
  }, []);

  return <select>{/* ... */}</select>;
};
```

**After (NEW):**
```typescript
import { useComprehensiveTTS } from '@shared/frontend/hooks/useComprehensiveTTS';

const VoiceSettings = () => {
  const {
    providers,
    loading,
    error,
    walletBalance,
    synthesize,
    estimateCost,
    refetch
  } = useComprehensiveTTS(
    'https://api.ailabsafrica.com',
    userId,
    { onlineOnly: true }
  );

  const handleSynthesize = async () => {
    const response = await synthesize({
      text: "Hello world",
      provider: "coqui_xtts",
      language: "en"
    });

    console.log(`Cost: GHS ${response.cost}`);
    console.log(`Balance: ${walletBalance?.formatted}`);
  };

  return (
    <div>
      <p>Balance: {walletBalance?.formatted}</p>
      <select>
        {providers.map(p => (
          <option key={p.id} value={p.id}>
            {p.name} ({p.status})
          </option>
        ))}
      </select>
      <button onClick={handleSynthesize}>Synthesize</button>
    </div>
  );
};
```

### Step 2: Use Generated TypeScript Types

**File:** `apps/<your_app>/frontend/src/services/tts.ts`

```typescript
import type {
  TTSProvider,
  TTSRequest,
  TTSResponse,
  AudioFormat,
  VoiceCloneRequest
} from '@shared/frontend/types/tts';

export const synthesizeAudio = async (
  request: TTSRequest
): Promise<TTSResponse> => {
  const response = await fetch('/api/tts/synthesize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    throw new Error('Synthesis failed');
  }

  return response.json();
};
```

### Step 3: Remove Static Provider Configs

Delete hardcoded provider lists:

```bash
# Remove old config files
rm apps/<your_app>/frontend/src/config/voice-agent-providers.ts
rm apps/<your_app>/frontend/src/config/tts-providers.json
```

Providers are now fetched dynamically from `/api/tts/providers`.

---

## Testing

### Backend Tests

```python
import pytest
from apps.shared.tts.billing import TTSBillingManager
from apps.shared.integration.wallet import WalletService

@pytest.mark.asyncio
async def test_synthesis_with_billing(mock_wallet_service):
    """Test synthesis with automatic billing."""
    billing_manager = TTSBillingManager(
        wallet_service=mock_wallet_service,
        pricing_tier=PricingTier.BASIC,
        currency=Currency.GHS
    )

    response, transaction = await billing_manager.synthesize_with_billing(
        user_id="test_user",
        text="Hello world",
        provider=TTSProvider.COQUI_XTTS,
        language="en"
    )

    assert response.audio is not None
    assert response.cost > 0
    assert transaction.id is not None
    assert transaction.amount == response.cost
```

### Frontend Tests

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useComprehensiveTTS } from '@shared/frontend/hooks/useComprehensiveTTS';

describe('useComprehensiveTTS', () => {
  it('fetches providers on mount', async () => {
    const { result } = renderHook(() =>
      useComprehensiveTTS('https://api.test.com', 'user_123')
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.providers.length).toBeGreaterThan(0);
    expect(result.current.error).toBeNull();
  });

  it('synthesizes audio with billing', async () => {
    const { result } = renderHook(() =>
      useComprehensiveTTS('https://api.test.com', 'user_123')
    );

    const response = await result.current.synthesize({
      text: "Test",
      provider: "coqui_xtts",
      language: "en"
    });

    expect(response.audio).toBeDefined();
    expect(response.cost).toBeGreaterThan(0);
    expect(response.transaction_id).toBeDefined();
  });
});
```

---

## Rollback Plan

If you encounter issues, you can rollback safely:

### 1. Keep Old Service Running

The deprecation warnings do NOT break existing code. Old services will continue to work during the migration grace period.

### 2. Restore from Backup

If you ran the migration script with `--execute`:

```bash
# List backup collections
mongosh "mongodb://admin:password@localhost:27017" --eval "
  use kasaai_core
  db.getCollectionNames().filter(n => n.includes('_backup_'))
"

# Restore from backup
mongosh "mongodb://admin:password@localhost:27017" --eval "
  use kasaai_core
  db.user_preferences.drop()
  db.user_preferences_backup_20251123_120000.renameCollection('user_preferences')
"
```

### 3. Remove Unified Routes

```python
# In apps/<your_app>/backend/app/main.py
# Comment out the unified routes
# app.include_router(tts_router, prefix="/api/tts", tags=["TTS"])
```

### 4. Revert Frontend Changes

```bash
git checkout HEAD~1 -- apps/<your_app>/frontend/src/components/VoiceSettings.tsx
```

---

## FAQ

### Q: Do I need to update all apps at once?

**A:** No! The migration can be done incrementally. Start with one app (e.g., StudyFlow) as a pilot, validate, then roll out to others.

### Q: Will existing user preferences break?

**A:** No. The migration script automatically converts legacy provider IDs to canonical format. Users will see no disruption.

### Q: What happens to my current TTS costs?

**A:** Costs will reduce by ~40% due to caching. Pricing per character remains the same (GHS 0.00001/char), but cache hits are free.

### Q: Can I still use the old TTSService?

**A:** Yes, during the grace period. However, you'll see deprecation warnings in logs. Plan to migrate within 4 weeks.

### Q: How do I monitor cache performance?

**A:** Use the `/api/tts/cache/stats` endpoint or call `cache.get_stats()` in Python:

```python
stats = await cache.get_stats()
print(f"Hit rate: {stats.hit_rate * 100:.1f}%")
print(f"Total size: {stats.total_size_mb:.2f} MB")
```

### Q: What if a provider goes offline?

**A:** The system will detect this via health checks and can send email alerts. Check provider status via `/api/tts/providers` endpoint.

### Q: How do I test without billing users?

**A:** Use the cost estimation endpoint first:

```python
estimated_cost = await billing_manager.estimate_cost(
    text="Hello world",
    provider=TTSProvider.COQUI_XTTS,
    voice_cloning=False
)
print(f"Estimated cost: GHS {estimated_cost}")
```

---

## Support

**Documentation:**
- Technical Docs: `apps/shared/tts/README.md`
- API Reference: `apps/shared/tts/docs/API.md`
- Provider Setup: `apps/shared/tts/docs/PROVIDERS.md`

**Code Examples:**
- Backend: `apps/shared/tts/examples/`
- Frontend: `apps/shared/frontend/hooks/useComprehensiveTTS.tsx`

**Issues:**
- GitHub: https://github.com/kasaai/tts-system/issues
- Slack: #tts-migration

---

**Last Updated:** 2025-11-23
**Version:** 1.0.0
**Author:** KasaAI Team
