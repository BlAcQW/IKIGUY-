# Reference Audio Centralization - Implementation Guide

**Date**: 2025-11-29  
**Status**: ✅ Centralized in @shared

## Overview

The reference audio implementation has been moved to `@shared` to enable reuse across all KasaAI applications (InkWave, B2C Portal, StudyFlow, ChurchFlow, etc.).

---

## 📁 Shared Components

### Backend Services

**Location**: `/opt/kasaai/apps/shared/services/reference_audio_service.py`

- `ReferenceAudioService`: Centralized service for reference audio management
- `ReferenceAudio`: Pydantic model for reference audio documents
- `ReferenceAudioCreate`: Model for creating reference audio
- `ReferenceAudioUpdate`: Model for updating reference audio
- `ReferenceAudioFilters`: Model for filtering reference audio

**Features**:
- MongoDB storage for metadata
- Local file storage with Hetzner backup
- Audio duration detection using librosa
- File validation (format, size)
- User and organization scoping

### Backend Routes

**Location**: `/opt/kasaai/apps/shared/routes/reference_audio_routes.py`

- `create_reference_audio_router()`: Factory function for creating router
- Uses dependency injection for authentication
- Supports app-specific storage configuration

**Endpoints**:
- `POST /reference-audio/upload` - Upload reference audio
- `GET /reference-audio/` - List reference audio
- `GET /reference-audio/{id}` - Get reference audio metadata
- `GET /reference-audio/{id}/audio` - Serve audio file
- `PUT /reference-audio/{id}` - Update reference audio
- `DELETE /reference-audio/{id}` - Delete reference audio

### Frontend Components

**Location**: `/opt/kasaai/apps/shared/frontend/components/reference-audio/`

- `ReferenceAudioUpload.tsx`: Upload component with drag-and-drop
- `ReferenceAudioList.tsx`: List and manage reference audio files
- `index.ts`: Exports

**Integration**: Components accept `apiBaseUrl` and `getAuthHeaders` props for app-specific configuration.

---

## 🚀 Usage in Apps

### Backend Integration

#### 1. Include Router in Main App

```python
from apps.shared.routes.reference_audio_routes import create_reference_audio_router
from app.core.auth import get_current_user

# Create router with dependency injection
reference_audio_router = create_reference_audio_router(
    get_current_user_func=get_current_user,
    storage_config={
        "username": os.getenv("HETZNER_STORAGE_USERNAME"),
        "password": os.getenv("HETZNER_STORAGE_PASSWORD"),
        "host": os.getenv("HETZNER_STORAGE_HOST")
    },
    storage_base_path="reference_audio"  # App-specific path
)

# Include in FastAPI app
app.include_router(
    reference_audio_router,
    prefix="/api/v1",
    tags=["Reference Audio"]
)
```

#### 2. Use Service in TTS Service

```python
from apps.shared.services.reference_audio_service import get_reference_audio_service

# In your TTS service
service = get_reference_audio_service(
    storage_base_path="reference_audio"  # App-specific
)

# Check if voice_id is reference audio
if voice_id and voice_id.startswith("ref_audio_"):
    ref_audio = await service.get_reference_audio(voice_id, user_id)
    audio_bytes = await service.get_audio_file_bytes(voice_id, user_id)
    # Use for zero-shot TTS...
```

### Frontend Integration

#### 1. Use in Voice Settings

```typescript
import { VoiceSettingsPanel } from '@kasaai/shared-frontend/components/voice-settings';
import { ReferenceAudioList } from '@kasaai/shared-frontend/components/reference-audio';

// In your voice settings page
<VoiceSettingsPanel
  // ... other props
  showReferenceAudio={true}
  apiBaseUrl={API_BASE_URL}
  getAuthHeaders={getAuthHeaders}
/>
```

#### 2. Standalone Usage

```typescript
import { ReferenceAudioList } from '@kasaai/shared-frontend/components/reference-audio';

<ReferenceAudioList
  apiBaseUrl={API_BASE_URL}
  getAuthHeaders={getAuthHeaders}
  onSelect={(audio) => {
    // Handle selection
  }}
  showUpload={true}
/>
```

---

## 🔧 Configuration

### Environment Variables

```bash
# MongoDB (if not using default)
MONGODB_URL=mongodb://localhost:27017

# Storage
REFERENCE_AUDIO_STORAGE_PATH=/opt/kasaai/storage/reference_audio

# Hetzner Storage (optional)
HETZNER_STORAGE_USERNAME=your_username
HETZNER_STORAGE_PASSWORD=your_password
HETZNER_STORAGE_HOST=your_host
```

### Storage Paths

- **Local**: `/opt/kasaai/storage/reference_audio/{user_id}/{reference_audio_id}.{ext}`
- **Hetzner**: `{storage_base_path}/{user_id}/{reference_audio_id}.{ext}`

---

## 📊 Database Schema

### `reference_audio` Collection

```javascript
{
  reference_audio_id: "ref_audio_abc123",
  user_id: "user_123",
  organization_id: "org_456",
  name: "My Narration Voice",
  description: "Professional narration voice",
  audio_url: "/api/v1/reference-audio/ref_audio_abc123/audio",
  storage_path: "reference_audio/user_123/ref_audio_abc123.wav",
  file_size_bytes: 245678,
  duration_seconds: 8.5,
  format: "wav",
  compatible_providers: ["styletts2", "coqui_xtts", "openvoice", "f5tts"],
  voice_id: "voice_xyz789",  // Optional: linked voice library entry
  created_at: ISODate("2025-11-29T10:00:00Z"),
  updated_at: ISODate("2025-11-29T10:00:00Z")
}
```

---

## 🎯 Zero-Shot TTS Integration

### Supported Providers

- **StyleTTS2**: Expressive voice synthesis
- **Coqui XTTS**: High-quality multilingual TTS
- **OpenVoice**: Versatile voice cloning
- **F5-TTS**: Flow-matching based synthesis

### Usage Pattern

```python
# In TTS service
if voice_id.startswith("ref_audio_"):
    # Load reference audio
    ref_audio = await service.get_reference_audio(voice_id, user_id)
    audio_bytes = await service.get_audio_file_bytes(voice_id, user_id)
    
    # Convert to base64
    ref_audio_base64 = base64.b64encode(audio_bytes).decode()
    
    # Use with zero-shot TTS provider
    result = await tts_provider.synthesize_with_voice_cloning(
        VoiceCloneRequest(
            provider_id="f5tts",
            text=text,
            reference_audio_base64=ref_audio_base64,
            language=language,
            speed=speed
        )
    )
```

---

## ✅ Migration from InkWave

The InkWave-specific implementation has been replaced with the shared version:

1. **Backend**: Use `create_reference_audio_router()` instead of app-specific routes
2. **Frontend**: Use components from `@shared/frontend/components/reference-audio`
3. **Service**: Use `get_reference_audio_service()` instead of app-specific service

---

## 📝 Next Steps

1. **Update InkWave**: Replace app-specific implementation with shared version
2. **Add to Other Apps**: Integrate into B2C Portal, StudyFlow, ChurchFlow
3. **Testing**: Add unit tests for shared service and routes
4. **Documentation**: Update app-specific documentation

---

## 🔗 Related Files

- `/opt/kasaai/apps/shared/services/reference_audio_service.py`
- `/opt/kasaai/apps/shared/routes/reference_audio_routes.py`
- `/opt/kasaai/apps/shared/frontend/components/reference-audio/`
- `/opt/kasaai/apps/shared/frontend/components/voice-settings/VoiceSettingsPanel.tsx`

---

**Status**: ✅ Centralized | Ready for use across all apps




