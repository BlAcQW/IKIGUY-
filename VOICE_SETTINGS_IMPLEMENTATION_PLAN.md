# Voice Settings Implementation Plan
## InkWave & StudyFlow Voice Configuration System

**Date:** 2025-11-03
**Scope:** Add comprehensive voice settings to InkWave and StudyFlow applications
**Dependencies:** @shared/, @tts-deployment/, @core_backend/, @b2c-portal/

---

## Executive Summary

This plan outlines the implementation of a unified voice settings system for InkWave and StudyFlow, enabling users to:
- Select TTS providers, engines, and voices
- Configure ASR (Automatic Speech Recognition) providers
- Choose and configure LLM models
- Manage voice cloning and custom voices
- Set default preferences per organization/user

### Key Objectives
1. **Reusability**: Extract components from b2c-portal to @shared/ for use across all apps
2. **User Control**: Allow users to select and configure voice services
3. **Persistence**: Store user preferences in MongoDB
4. **Integration**: Leverage existing infrastructure from @shared/, @core_backend/, and @tts-deployment/

---

## Current State Analysis

### Existing Infrastructure

#### 1. **B2C Portal Components** (@b2c-portal/)
**Hooks:**
- `useTTSProvider.ts` - TTS provider management, synthesis, voice cloning
- `useASRProvider.ts` - ASR provider management, transcription
- `useLLMModel.ts` - LLM model management, chat
- `useClonedVoices.ts` - Voice cloning and management
- `useVoiceSynthesis.ts` - Voice synthesis wrapper
- `useVoiceTranscription.ts` - Transcription wrapper

**Lab Pages:**
- `TTSLab.tsx` - Full TTS testing interface with provider selection, synthesis, voice cloning, batch processing
- `ASRLab.tsx` - ASR testing with live transcription, file upload
- `LLMLab.tsx` - LLM chat interface with model selection
- `VoiceStudio.tsx` - Voice library management, cloning, batch operations
- `VoiceAgent.tsx` - Voice assistant creation and management

**Key Features:**
- Provider health monitoring
- Cost estimation
- Real-time synthesis/transcription
- Voice library browsing
- Batch voice cloning

#### 2. **Backend Services** (@shared/services/)
- `tts_provider_service.py` - TTS provider management with billing integration
- `asr_provider_service.py` - ASR provider management with billing
- `llm_provider_service.py` - LLM provider management with billing
- `voice_lab_service.py` - Voice library and cloning service
- `billing_service.py` - Wallet integration for all services

**Endpoints in Core Backend:**
```
/api/tts/providers           - List TTS providers
/api/tts/synthesize          - Synthesize speech
/api/tts/clone               - Clone voice
/api/asr/providers           - List ASR providers
/api/asr/transcribe/upload   - Transcribe audio
/api/llm/providers           - List LLM providers
/api/llm/chat                - Chat with LLM
/api/voice-lab/voices        - Voice library
```

#### 3. **InkWave & StudyFlow Current State**
**InkWave:**
- Has admin settings page: `/admin/settings`
- Uses `OrganizationSettings` component
- MongoDB collection: `inkwave`
- Backend: `/opt/kasaai/apps/inkwave/backend/`
- No voice settings currently

**StudyFlow:**
- Has settings page: `/settings`
- Has admin settings: `/admin/settings`
- MongoDB collection: `studyflow`
- Backend: `/opt/kasaai/apps/studyflow/backend/`
- No voice settings currently

---

## Implementation Plan

### Phase 1: Extract Reusable Components to @shared/

#### 1.1 Create Shared Frontend Library
**Location:** `/opt/kasaai/apps/shared/frontend/`

**Structure:**
```
shared/
├── frontend/
│   ├── hooks/
│   │   ├── useTTSProvider.ts         (extracted from b2c-portal)
│   │   ├── useASRProvider.ts         (extracted from b2c-portal)
│   │   ├── useLLMModel.ts            (extracted from b2c-portal)
│   │   ├── useClonedVoices.ts        (extracted from b2c-portal)
│   │   ├── useVoiceSettings.ts       (new - manages user preferences)
│   │   └── index.ts
│   ├── components/
│   │   ├── voice-settings/
│   │   │   ├── TTSProviderSelector.tsx
│   │   │   ├── ASRProviderSelector.tsx
│   │   │   ├── LLMModelSelector.tsx
│   │   │   ├── VoiceLibrarySelector.tsx
│   │   │   ├── VoiceSettingsPanel.tsx
│   │   │   └── index.ts
│   │   └── index.ts
│   ├── services/
│   │   ├── voice-api-client.ts       (API client for voice services)
│   │   └── index.ts
│   ├── types/
│   │   ├── voice-settings.ts
│   │   └── index.ts
│   └── package.json
```

**Key Files to Create:**

**1.1.1 `useVoiceSettings.ts` - New Hook**
```typescript
/**
 * Hook for managing user voice preferences
 * Stores and retrieves TTS, ASR, and LLM settings per user/org
 */
interface VoiceSettings {
  tts: {
    defaultProvider: string;
    defaultVoice: string | null;
    speed: number;
    pitch: number;
  };
  asr: {
    defaultProvider: string;
    language: string;
    task: 'transcribe' | 'translate';
  };
  llm: {
    defaultModel: string;
    temperature: number;
    maxTokens: number;
  };
  voices: {
    favoriteVoices: string[];
    customVoices: string[];
  };
}

export const useVoiceSettings = (userId: string, orgId: string)
```

**1.1.2 Voice Settings Components**

**TTSProviderSelector.tsx**
```typescript
interface TTSProviderSelectorProps {
  selectedProviderId: string | null;
  onProviderChange: (providerId: string) => void;
  selectedVoiceId: string | null;
  onVoiceChange: (voiceId: string) => void;
  showAdvanced?: boolean;
}
```

**ASRProviderSelector.tsx**
```typescript
interface ASRProviderSelectorProps {
  selectedProviderId: string | null;
  onProviderChange: (providerId: string) => void;
  selectedLanguage: string;
  onLanguageChange: (language: string) => void;
}
```

**LLMModelSelector.tsx**
```typescript
interface LLMModelSelectorProps {
  selectedModelId: string | null;
  onModelChange: (modelId: string) => void;
  temperature: number;
  onTemperatureChange: (temp: number) => void;
  maxTokens: number;
  onMaxTokensChange: (tokens: number) => void;
}
```

**VoiceSettingsPanel.tsx** - Main container component
```typescript
interface VoiceSettingsPanelProps {
  userId: string;
  organizationId: string;
  onSave: (settings: VoiceSettings) => Promise<void>;
  onCancel: () => void;
}
```

#### 1.2 Package Configuration
Create `/opt/kasaai/apps/shared/frontend/package.json`:
```json
{
  "name": "@kasaai/shared-frontend",
  "version": "1.0.0",
  "type": "module",
  "main": "./index.ts",
  "exports": {
    "./hooks": "./hooks/index.ts",
    "./components": "./components/index.ts",
    "./services": "./services/index.ts",
    "./types": "./types/index.ts"
  },
  "peerDependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  }
}
```

---

### Phase 2: Backend Implementation

#### 2.1 Create Voice Settings Service in @shared/
**Location:** `/opt/kasaai/apps/shared/services/voice_settings_service.py`

```python
"""
Voice Settings Service

Manages user and organization voice preferences for TTS, ASR, and LLM services.
Stores preferences in MongoDB and provides CRUD operations.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase


class TTSSettings(BaseModel):
    """TTS preferences."""
    default_provider: str = "coqui_xtts"
    default_voice: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-1.0, le=1.0)


class ASRSettings(BaseModel):
    """ASR preferences."""
    default_provider: str = "whisper_local"
    language: str = "en"
    task: str = "transcribe"  # or "translate"


class LLMSettings(BaseModel):
    """LLM preferences."""
    default_model: str = "llama3.2"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=100000)


class VoicePreferences(BaseModel):
    """Voice library preferences."""
    favorite_voices: list[str] = Field(default_factory=list)
    custom_voices: list[str] = Field(default_factory=list)


class VoiceSettings(BaseModel):
    """Complete voice settings model."""
    user_id: str
    organization_id: str
    tts: TTSSettings = Field(default_factory=TTSSettings)
    asr: ASRSettings = Field(default_factory=ASRSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    voices: VoicePreferences = Field(default_factory=VoicePreferences)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class VoiceSettingsService:
    """Service for managing voice settings."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.voice_settings

    async def get_settings(
        self,
        user_id: str,
        organization_id: str
    ) -> VoiceSettings:
        """Get or create voice settings for a user."""
        pass

    async def update_settings(
        self,
        user_id: str,
        organization_id: str,
        settings: Dict[str, Any]
    ) -> VoiceSettings:
        """Update voice settings."""
        pass

    async def get_organization_defaults(
        self,
        organization_id: str
    ) -> VoiceSettings:
        """Get organization-wide default settings."""
        pass

    async def set_organization_defaults(
        self,
        organization_id: str,
        settings: Dict[str, Any]
    ) -> VoiceSettings:
        """Set organization-wide default settings."""
        pass
```

#### 2.2 Add API Routes to InkWave
**Location:** `/opt/kasaai/apps/inkwave/backend/app/api/routes/voice_settings.py`

```python
"""
Voice Settings API Routes for InkWave
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from apps.shared.services.voice_settings_service import (
    VoiceSettingsService,
    VoiceSettings
)
from app.core.deps import get_db, get_current_user

router = APIRouter(prefix="/api/voice-settings", tags=["voice-settings"])


@router.get("/my-settings", response_model=VoiceSettings)
async def get_my_voice_settings(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get current user's voice settings."""
    service = VoiceSettingsService(db)
    org_id = current_user.get("organization_id", "default")
    return await service.get_settings(current_user["id"], org_id)


@router.put("/my-settings")
async def update_my_voice_settings(
    settings: Dict[str, Any],
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update current user's voice settings."""
    service = VoiceSettingsService(db)
    org_id = current_user.get("organization_id", "default")
    return await service.update_settings(current_user["id"], org_id, settings)


@router.get("/organization-defaults", response_model=VoiceSettings)
async def get_organization_defaults(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get organization default voice settings."""
    service = VoiceSettingsService(db)
    org_id = current_user.get("organization_id", "default")
    return await service.get_organization_defaults(org_id)
```

**Register routes in** `/opt/kasaai/apps/inkwave/backend/app/main.py`:
```python
from app.api.routes import voice_settings

app.include_router(voice_settings.router)
```

#### 2.3 Add API Routes to StudyFlow
**Location:** `/opt/kasaai/apps/studyflow/backend/app/api/routes/voice_settings.py`

Same as InkWave implementation, register in `main.py`.

---

### Phase 3: Frontend Integration - InkWave

#### 3.1 Install Shared Frontend Package
Add to `/opt/kasaai/apps/inkwave/frontend/package.json`:
```json
{
  "dependencies": {
    "@kasaai/shared-frontend": "file:../../shared/frontend"
  }
}
```

#### 3.2 Create Voice Settings Page
**Location:** `/opt/kasaai/apps/inkwave/frontend/src/pages/VoiceSettingsPage.tsx`

```typescript
/**
 * Voice Settings Page for InkWave
 * Allows users to configure TTS, ASR, and LLM preferences
 */

import React, { useState, useEffect } from 'react';
import { VoiceSettingsPanel } from '@kasaai/shared-frontend/components';
import { useVoiceSettings } from '@kasaai/shared-frontend/hooks';
import { useAuthStore } from '../store/authStore';

export default function VoiceSettingsPage() {
  const { user } = useAuthStore();
  const {
    settings,
    isLoading,
    updateSettings,
    error
  } = useVoiceSettings(user?.id, user?.organization_id);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Voice Settings</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-12">Loading...</div>
      ) : (
        <VoiceSettingsPanel
          userId={user?.id}
          organizationId={user?.organization_id}
          initialSettings={settings}
          onSave={updateSettings}
          onCancel={() => window.history.back()}
        />
      )}
    </div>
  );
}
```

#### 3.3 Add Route
In `/opt/kasaai/apps/inkwave/frontend/src/App.tsx`:
```typescript
import VoiceSettingsPage from './pages/VoiceSettingsPage';

// Add route
<Route path="/voice-settings" element={<VoiceSettingsPage />} />
```

#### 3.4 Add Navigation Link
Add to sidebar/navigation:
```typescript
<NavLink to="/voice-settings">
  <MicrophoneIcon className="w-5 h-5" />
  <span>Voice Settings</span>
</NavLink>
```

---

### Phase 4: Frontend Integration - StudyFlow

Same structure as InkWave:

#### 4.1 Install Package
```json
{
  "dependencies": {
    "@kasaai/shared-frontend": "file:../../shared/frontend"
  }
}
```

#### 4.2 Create Voice Settings Page
**Location:** `/opt/kasaai/apps/studyflow/frontend/src/pages/VoiceSettingsPage.tsx`

Same implementation as InkWave.

#### 4.3 Add Route and Navigation
Same as InkWave.

---

### Phase 5: Integration with Existing Features

#### 5.1 InkWave - Audio Book Player Integration
Modify `/opt/kasaai/apps/inkwave/frontend/src/pages/PlayerPage.tsx`:

```typescript
import { useVoiceSettings } from '@kasaai/shared-frontend/hooks';

// In player component
const { settings } = useVoiceSettings(user?.id, user?.organization_id);

// Use settings when synthesizing audio
const synthesizeChapter = async (text: string) => {
  return await ttsService.synthesize({
    text,
    provider_id: settings.tts.default_provider,
    voice_id: settings.tts.default_voice,
    speed: settings.tts.speed,
    pitch: settings.tts.pitch
  });
};
```

#### 5.2 StudyFlow - Material Reader Integration
Modify `/opt/kasaai/apps/studyflow/frontend/src/pages/MaterialDetails.tsx`:

```typescript
import { useVoiceSettings } from '@kasaai/shared-frontend/hooks';

// In material reader
const { settings } = useVoiceSettings(user?.id, user?.organization_id);

// Use for text-to-speech of study materials
const readMaterial = async (content: string) => {
  return await ttsService.synthesize({
    text: content,
    provider_id: settings.tts.default_provider,
    voice_id: settings.tts.default_voice,
    speed: settings.tts.speed
  });
};
```

#### 5.3 InkWave - Voice Search Integration
Add voice search capability using ASR settings:

```typescript
const { settings } = useVoiceSettings(user?.id, user?.organization_id);

const transcribeSearch = async (audio: Blob) => {
  return await asrService.transcribe({
    audio,
    provider_id: settings.asr.default_provider,
    language: settings.asr.language
  });
};
```

#### 5.4 StudyFlow - AI Tutor Integration
Use LLM settings for study assistant:

```typescript
const { settings } = useVoiceSettings(user?.id, user?.organization_id);

const askTutor = async (question: string) => {
  return await llmService.chat({
    model_id: settings.llm.default_model,
    messages: [{ role: 'user', content: question }],
    temperature: settings.llm.temperature,
    max_tokens: settings.llm.max_tokens
  });
};
```

---

## Database Schema

### MongoDB Collection: `voice_settings`
```javascript
{
  "_id": ObjectId("..."),
  "user_id": "user_123",
  "organization_id": "org_456",
  "tts": {
    "default_provider": "coqui_xtts",
    "default_voice": "nana_aba_24bit",
    "speed": 1.0,
    "pitch": 0.0
  },
  "asr": {
    "default_provider": "whisper_local",
    "language": "en",
    "task": "transcribe"
  },
  "llm": {
    "default_model": "llama3.2",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "voices": {
    "favorite_voices": [
      "nana_aba",
      "juliet_bawuah"
    ],
    "custom_voices": [
      "custom_voice_id_1"
    ]
  },
  "created_at": ISODate("2025-11-03T00:00:00Z"),
  "updated_at": ISODate("2025-11-03T00:00:00Z")
}
```

### Indexes
```javascript
db.voice_settings.createIndex({ "user_id": 1, "organization_id": 1 }, { unique: true });
db.voice_settings.createIndex({ "organization_id": 1 });
db.voice_settings.createIndex({ "updated_at": -1 });
```

---

## Testing Strategy

### Unit Tests

#### Backend Tests
**Location:** `/opt/kasaai/apps/shared/services/tests/test_voice_settings_service.py`

```python
import pytest
from apps.shared.services.voice_settings_service import VoiceSettingsService

@pytest.mark.asyncio
async def test_get_settings_creates_default():
    """Test that get_settings creates defaults for new users."""
    pass

@pytest.mark.asyncio
async def test_update_settings():
    """Test updating user voice settings."""
    pass

@pytest.mark.asyncio
async def test_organization_defaults():
    """Test organization-wide defaults."""
    pass
```

#### Frontend Tests
**Location:** `/opt/kasaai/apps/shared/frontend/hooks/__tests__/useVoiceSettings.test.ts`

```typescript
import { renderHook } from '@testing-library/react-hooks';
import { useVoiceSettings } from '../useVoiceSettings';

describe('useVoiceSettings', () => {
  it('should load user settings', async () => {
    // Test implementation
  });

  it('should update settings', async () => {
    // Test implementation
  });
});
```

### Integration Tests

#### InkWave E2E Test
```python
async def test_inkwave_voice_settings_flow():
    """
    Test complete flow:
    1. User logs in
    2. Navigates to voice settings
    3. Updates TTS provider
    4. Settings persist
    5. Audio player uses new settings
    """
    pass
```

#### StudyFlow E2E Test
```python
async def test_studyflow_voice_settings_flow():
    """
    Test complete flow:
    1. User logs in
    2. Navigates to voice settings
    3. Updates ASR and LLM settings
    4. Settings persist
    5. Study assistant uses new settings
    """
    pass
```

---

## File Structure Summary

```
/opt/kasaai/apps/
├── shared/
│   ├── frontend/                          # NEW: Shared frontend library
│   │   ├── hooks/
│   │   │   ├── useTTSProvider.ts
│   │   │   ├── useASRProvider.ts
│   │   │   ├── useLLMModel.ts
│   │   │   ├── useClonedVoices.ts
│   │   │   ├── useVoiceSettings.ts       # NEW
│   │   │   └── index.ts
│   │   ├── components/
│   │   │   ├── voice-settings/
│   │   │   │   ├── TTSProviderSelector.tsx
│   │   │   │   ├── ASRProviderSelector.tsx
│   │   │   │   ├── LLMModelSelector.tsx
│   │   │   │   ├── VoiceLibrarySelector.tsx
│   │   │   │   ├── VoiceSettingsPanel.tsx
│   │   │   │   └── index.ts
│   │   │   └── index.ts
│   │   ├── services/
│   │   │   ├── voice-api-client.ts
│   │   │   └── index.ts
│   │   ├── types/
│   │   │   ├── voice-settings.ts
│   │   │   └── index.ts
│   │   └── package.json
│   └── services/
│       ├── voice_settings_service.py     # NEW
│       └── tests/
│           └── test_voice_settings_service.py  # NEW
├── inkwave/
│   ├── backend/
│   │   └── app/
│   │       └── api/
│   │           └── routes/
│   │               └── voice_settings.py  # NEW
│   └── frontend/
│       └── src/
│           ├── pages/
│           │   ├── VoiceSettingsPage.tsx # NEW
│           │   └── PlayerPage.tsx        # MODIFIED
│           └── package.json              # MODIFIED
├── studyflow/
│   ├── backend/
│   │   └── app/
│   │       └── api/
│   │           └── routes/
│   │               └── voice_settings.py  # NEW
│   └── frontend/
│       └── src/
│           ├── pages/
│           │   ├── VoiceSettingsPage.tsx # NEW
│           │   └── MaterialDetails.tsx   # MODIFIED
│           └── package.json              # MODIFIED
└── b2c-portal/
    └── src/
        ├── hooks/                         # EXTRACT TO shared/
        └── components/                    # EXTRACT TO shared/
```

---

## Implementation Phases - Timeline

### Week 1: Foundation
**Days 1-2:**
- [ ] Create `@shared/frontend/` directory structure
- [ ] Extract hooks from b2c-portal to shared
- [ ] Create `voice_settings_service.py` in @shared/services/
- [ ] Write unit tests for voice settings service

**Days 3-4:**
- [ ] Create shared voice settings components
- [ ] Create `VoiceSettingsPanel.tsx`
- [ ] Create selector components (TTS, ASR, LLM, Voice)
- [ ] Write component tests

**Day 5:**
- [ ] Package configuration and build setup
- [ ] Documentation for shared components
- [ ] Review and refactoring

### Week 2: InkWave Integration
**Days 1-2:**
- [ ] Add voice settings routes to InkWave backend
- [ ] Create MongoDB indexes
- [ ] Write backend integration tests

**Days 3-4:**
- [ ] Create VoiceSettingsPage in InkWave frontend
- [ ] Add navigation and routing
- [ ] Integrate with audio player
- [ ] Add voice search capability

**Day 5:**
- [ ] End-to-end testing
- [ ] Bug fixes
- [ ] Documentation

### Week 3: StudyFlow Integration
**Days 1-2:**
- [ ] Add voice settings routes to StudyFlow backend
- [ ] Create MongoDB indexes
- [ ] Write backend integration tests

**Days 3-4:**
- [ ] Create VoiceSettingsPage in StudyFlow frontend
- [ ] Add navigation and routing
- [ ] Integrate with material reader
- [ ] Integrate with AI tutor

**Day 5:**
- [ ] End-to-end testing
- [ ] Bug fixes
- [ ] Documentation

### Week 4: Polish & Deployment
**Days 1-2:**
- [ ] Cross-app testing
- [ ] Performance optimization
- [ ] Security audit

**Days 3-4:**
- [ ] User acceptance testing
- [ ] Final bug fixes
- [ ] Deployment preparation

**Day 5:**
- [ ] Deploy to dev server
- [ ] Monitor and fix issues
- [ ] Deploy to production

---

## Success Criteria

### Functional Requirements
- [ ] Users can select TTS providers and voices
- [ ] Users can configure ASR providers and languages
- [ ] Users can select LLM models and parameters
- [ ] Settings persist across sessions
- [ ] Settings apply to voice features in both apps
- [ ] Organization defaults can be set by admins

### Non-Functional Requirements
- [ ] Settings page loads in < 2 seconds
- [ ] Settings update in < 1 second
- [ ] All changes are reflected immediately
- [ ] 90%+ test coverage
- [ ] Mobile responsive design
- [ ] Accessible (WCAG 2.1 AA)

### Integration Requirements
- [ ] InkWave audio player uses TTS settings
- [ ] InkWave voice search uses ASR settings
- [ ] StudyFlow material reader uses TTS settings
- [ ] StudyFlow AI tutor uses LLM settings
- [ ] Voice features gracefully fallback to defaults

---

## Risk Mitigation

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes to existing features | High | Comprehensive testing before deployment |
| Performance degradation | Medium | Load testing, caching strategies |
| Provider incompatibility | Medium | Fallback to default providers |
| Settings sync issues | Medium | Optimistic updates with retry logic |

### Operational Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| User confusion | Medium | Clear UI, onboarding tooltips |
| Migration complexity | Low | Gradual rollout, backward compatibility |
| Support burden | Low | Documentation, FAQ, video tutorials |

---

## Future Enhancements

### Phase 2 Features (Post-MVP)
1. **Voice Profiles**: Multiple saved configurations
2. **A/B Testing**: Compare different voice settings
3. **Usage Analytics**: Track which settings perform best
4. **Smart Recommendations**: AI-suggested optimal settings
5. **Voice Cloning UI**: Simplified voice cloning workflow
6. **Batch Operations**: Update settings for multiple users
7. **API Access**: Allow external apps to read user preferences

### Integration Opportunities
1. **Mobile Apps**: Export settings to mobile versions
2. **Browser Extensions**: Share settings across platforms
3. **Third-party Apps**: OAuth-based settings sharing

---

## Appendix

### A. Component API Reference

#### VoiceSettingsPanel Props
```typescript
interface VoiceSettingsPanelProps {
  userId: string;
  organizationId: string;
  initialSettings?: VoiceSettings;
  onSave: (settings: VoiceSettings) => Promise<void>;
  onCancel: () => void;
  showAdvanced?: boolean;
  readonly?: boolean;
}
```

#### TTSProviderSelector Props
```typescript
interface TTSProviderSelectorProps {
  selectedProviderId: string | null;
  onProviderChange: (providerId: string) => void;
  selectedVoiceId: string | null;
  onVoiceChange: (voiceId: string) => void;
  speed: number;
  onSpeedChange: (speed: number) => void;
  pitch: number;
  onPitchChange: (pitch: number) => void;
  showAdvanced?: boolean;
}
```

### B. API Endpoint Reference

#### GET /api/voice-settings/my-settings
**Response:**
```json
{
  "user_id": "user_123",
  "organization_id": "org_456",
  "tts": {
    "default_provider": "coqui_xtts",
    "default_voice": "nana_aba_24bit",
    "speed": 1.0,
    "pitch": 0.0
  },
  "asr": {
    "default_provider": "whisper_local",
    "language": "en",
    "task": "transcribe"
  },
  "llm": {
    "default_model": "llama3.2",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "voices": {
    "favorite_voices": ["nana_aba"],
    "custom_voices": []
  }
}
```

#### PUT /api/voice-settings/my-settings
**Request Body:**
```json
{
  "tts": {
    "default_provider": "f5tts",
    "speed": 1.2
  }
}
```

**Response:** Updated settings object

### C. Migration Guide

#### Updating Existing Code
**Before:**
```typescript
// Direct hardcoded values
const synthesize = () => {
  return ttsService.synthesize({
    provider_id: 'coqui_xtts',
    voice_id: 'default',
    speed: 1.0
  });
};
```

**After:**
```typescript
// Using user settings
import { useVoiceSettings } from '@kasaai/shared-frontend/hooks';

const { settings } = useVoiceSettings(userId, orgId);

const synthesize = () => {
  return ttsService.synthesize({
    provider_id: settings.tts.default_provider,
    voice_id: settings.tts.default_voice,
    speed: settings.tts.speed
  });
};
```

---

## Conclusion

This implementation plan provides a comprehensive roadmap for adding voice settings to InkWave and StudyFlow. By:

1. **Extracting reusable components** to @shared/frontend/
2. **Creating a unified settings service** in @shared/services/
3. **Implementing settings UI** in both applications
4. **Integrating with existing features** for seamless user experience

We will create a maintainable, scalable voice configuration system that enhances user experience across the KasaAI platform.

**Next Steps:**
1. Review and approve this plan
2. Create detailed task breakdown in TASK.md
3. Begin Phase 1 implementation
4. Weekly progress reviews

---

**Document Version:** 1.0
**Last Updated:** 2025-11-03
**Author:** Claude (AI Assistant)
**Status:** Draft - Awaiting Review
