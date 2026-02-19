# Reference Audio Upload for Zero-Shot TTS - Implementation Summary

**Date**: 2025-11-29  
**Feature**: Reference Audio Upload for Zero-Shot TTS Providers

## Overview

Implemented a complete system for uploading and using reference audio files with zero-shot TTS providers (StyleTTS2, Coqui XTTS, OpenVoice, F5-TTS) for audiobook narration in InkWave.

---

## ✅ Completed Implementation

### Backend API Endpoints

**Location**: `/opt/kasaai/apps/inkwave/backend/app/api/routes/reference_audio.py`

#### 1. Upload Reference Audio
- **Endpoint**: `POST /api/v1/reference-audio/upload`
- **Description**: Upload reference audio file for zero-shot TTS providers
- **Features**:
  - File validation (size, format)
  - Audio duration detection
  - Optional voice library entry creation
  - Storage in local filesystem
  - MongoDB metadata storage
- **Supported Formats**: WAV, MP3, OGG, FLAC, M4A (max 10MB)

#### 2. List Reference Audio
- **Endpoint**: `GET /api/v1/reference-audio/`
- **Description**: List all reference audio files for the current user
- **Returns**: Array of reference audio metadata

#### 3. Get Reference Audio
- **Endpoint**: `GET /api/v1/reference-audio/{id}`
- **Description**: Get specific reference audio metadata

#### 4. Serve Audio File
- **Endpoint**: `GET /api/v1/reference-audio/{id}/audio`
- **Description**: Serve the actual audio file
- **Content-Type**: Based on file format (audio/wav, audio/mpeg, etc.)

#### 5. Delete Reference Audio
- **Endpoint**: `DELETE /api/v1/reference-audio/{id}`
- **Description**: Delete reference audio file and metadata

### TTS Service Integration

**Location**: `/opt/kasaai/apps/inkwave/backend/app/services/tts_service.py`

#### Reference Audio Support
- **Method**: `_narrate_with_reference_audio()`
- **Description**: Handles TTS synthesis using reference audio from database
- **How it works**:
  1. Detects `voice_id` starting with `ref_audio_` prefix
  2. Loads reference audio from database/storage
  3. Converts to base64
  4. Calls zero-shot TTS provider with reference audio
  5. Supports: StyleTTS2, Coqui XTTS, OpenVoice, F5-TTS

#### Usage Pattern
```python
# When voice_id starts with "ref_audio_", TTS service automatically:
# 1. Loads reference audio from database
# 2. Uses it for zero-shot TTS synthesis
result = await tts_service.narrate_chunk(
    voice_id="ref_audio_abc123",  # Reference audio ID
    provider_id="f5tts",  # Zero-shot provider
    ...
)
```

### Frontend Components

#### 1. Reference Audio Upload Component
**Location**: `/opt/kasaai/apps/inkwave/frontend/src/components/reference-audio/ReferenceAudioUpload.tsx`

- Drag-and-drop file upload
- Audio preview with play/pause
- File validation (format, size)
- Metadata form (name, description, tags)
- Optional voice library entry creation
- Real-time upload progress

#### 2. Reference Audio List Component
**Location**: `/opt/kasaai/apps/inkwave/frontend/src/components/reference-audio/ReferenceAudioList.tsx`

- Grid display of reference audio files
- Audio playback controls
- Delete functionality
- Upload modal integration
- Compatible providers display
- File metadata display

#### 3. Voice Settings Integration
**Location**: `/opt/kasaai/apps/inkwave/frontend/src/pages/VoiceSettingsPage.tsx`

- New "Reference Audio" tab in Voice Settings
- Integrated ReferenceAudioList component
- Easy access to upload and manage reference audio

### API Client Methods

**Location**: `/opt/kasaai/apps/inkwave/frontend/src/lib/api.ts`

```typescript
api.referenceAudio.upload(formData)    // Upload reference audio
api.referenceAudio.list()              // List all reference audio
api.referenceAudio.get(id)             // Get reference audio metadata
api.referenceAudio.getAudio(id)        // Get audio file blob
api.referenceAudio.delete(id)          // Delete reference audio
```

---

## 🔧 How It Works

### User Flow

1. **Upload Reference Audio**
   - User goes to Voice Settings → Reference Audio tab
   - Clicks "Upload Audio" button
   - Drops or selects audio file (WAV, MP3, etc.)
   - Fills in metadata (name, description)
   - Optionally creates voice library entry
   - Audio is validated, stored, and metadata saved

2. **Use Reference Audio for Narration**
   - User selects a reference audio as voice
   - Reference audio ID is passed as `voice_id` (e.g., `ref_audio_abc123`)
   - When generating audiobook narration:
     - TTS service detects `ref_audio_` prefix
     - Loads reference audio from database
     - Uses it with zero-shot TTS provider (StyleTTS2, F5-TTS, etc.)
     - Generates narration in that voice

### Technical Flow

```
User Uploads Audio
    ↓
Backend validates & stores file
    ↓
MongoDB stores metadata
    ↓
User selects reference audio for narration
    ↓
TTS service detects ref_audio_ prefix
    ↓
Loads audio bytes from storage
    ↓
Converts to base64
    ↓
Calls zero-shot TTS provider with reference audio
    ↓
Generates narration in cloned voice
```

---

## 📊 Database Schema

### `reference_audio` Collection

```javascript
{
  reference_audio_id: "ref_audio_abc123",
  user_id: "user_123",
  name: "My Narration Voice",
  description: "Professional narration voice",
  audio_url: "/storage/reference_audio/user123/ref_audio_abc123.wav",
  storage_path: "reference_audio/user123/ref_audio_abc123.wav",
  file_size_bytes: 245678,
  duration_seconds: 8.5,
  format: "wav",
  compatible_providers: ["styletts2", "coqui_xtts", "openvoice", "f5tts"],
  voice_id: "voice_xyz789",  // Optional: linked voice library entry
  created_at: ISODate("2025-11-29T10:00:00Z"),
  organization_id: "org_123"
}
```

---

## 🎯 Zero-Shot TTS Provider Support

The system supports these zero-shot TTS providers:

1. **StyleTTS2** - Expressive voice synthesis
2. **Coqui XTTS** - High-quality multilingual TTS
3. **OpenVoice** - Versatile voice cloning
4. **F5-TTS** - Flow-matching based synthesis

All providers receive reference audio as base64-encoded audio data and generate speech in the cloned voice.

---

## 📁 File Storage

- **Local Storage**: `/opt/kasaai/apps/inkwave/backend/storage/reference_audio/{user_id}/`
- **File Naming**: `{reference_audio_id}{extension}`
- **Public URL Format**: `/api/v1/reference-audio/{id}/audio`

---

## 🔗 Integration Points

### Voice Library
- Reference audio can be linked to voice library entries
- Optional automatic voice library creation during upload
- Shared metadata (gender, language, tags)

### TTS Synthesis
- Seamlessly integrated with existing TTS service
- Automatic detection of reference audio IDs
- Fallback to default synthesis if reference audio not found

### Voice Settings
- New tab in Voice Settings page
- Easy upload and management interface
- Preview and playback functionality

---

## 🚀 Usage Examples

### Upload Reference Audio

```typescript
const formData = new FormData();
formData.append('audio_file', audioFile);
formData.append('name', 'My Voice');
formData.append('description', 'Professional narration voice');
formData.append('create_voice', 'true');
formData.append('gender', 'male');
formData.append('language', 'en');

const response = await api.referenceAudio.upload(formData);
// Returns: { reference_audio_id: "ref_audio_abc123", ... }
```

### Use Reference Audio for Narration

```typescript
// In audio generation request
const audioRequest = {
  provider_id: "f5tts",
  voice_id: "ref_audio_abc123",  // Reference audio ID
  speed: 1.0,
  language: "en"
};

await api.audio.generateChunkAudio(bookId, chunkIndex, audioRequest);
```

---

## ✨ Key Features

1. **Intuitive Upload Interface**
   - Drag-and-drop support
   - Real-time validation
   - Audio preview
   - Progress indicators

2. **Smart Integration**
   - Automatic voice library linking
   - Seamless TTS provider integration
   - Zero configuration needed

3. **User-Friendly Management**
   - Easy-to-use list view
   - Playback controls
   - Delete functionality
   - Metadata display

4. **Robust Error Handling**
   - File validation
   - Storage fallbacks
   - Graceful degradation

5. **Security**
   - User-scoped files
   - Authentication required
   - Organization isolation

---

## 📝 Next Steps (Optional Enhancements)

1. **Cloud Storage Integration**
   - Upload to Hetzner Storage Box
   - Automatic backup
   - CDN delivery

2. **Advanced Features**
   - Batch upload
   - Audio processing (normalization, trimming)
   - Quality scoring
   - Transcript generation

3. **Voice Library UI Enhancement**
   - Show reference audio options in voice selector
   - Filter by compatible providers
   - Preview integration

4. **Analytics**
   - Usage tracking
   - Popular reference audio
   - Cost analysis

---

## 🧪 Testing

### Manual Testing Checklist

- [x] Upload reference audio file
- [x] Validate file size and format
- [x] List reference audio files
- [x] Play reference audio preview
- [x] Delete reference audio
- [ ] Use reference audio in TTS synthesis
- [ ] Verify zero-shot TTS works with reference audio

---

## 📚 API Documentation

Full API documentation available at:
- `/api/docs` - Swagger UI
- `/api/redoc` - ReDoc

---

**Status**: ✅ Backend Complete | ✅ Frontend Complete | ⏳ Integration Testing Pending




