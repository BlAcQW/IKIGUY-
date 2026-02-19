# Using Cloned Voices in Voice Studio

This guide shows how to use the cloned voices from `@voice-lab/clones/` in the B2C Portal Voice Studio.

## Overview

The cloned voices are now accessible via a RESTful API and can be:
1. Listed and previewed
2. Played directly from the voice-lab directory
3. Registered in the voice library for use in voice studio
4. Downloaded for offline use

## Quick Start

### 1. View Available Cloned Voices

```typescript
// In your React component
import { ClonedVoicesPanel } from '@/components/voice-studio/ClonedVoicesPanel';

function VoiceStudio() {
  const handleVoiceRegistered = (voice) => {
    console.log('Voice registered:', voice);
    // Refresh your voice library or show success message
  };

  return (
    <div>
      <ClonedVoicesPanel onVoiceRegistered={handleVoiceRegistered} />
    </div>
  );
}
```

### 2. Use the API Directly

#### List All Cloned Voices

```javascript
const response = await fetch('/api/cloned-voices/list');
const data = await response.json();

console.log(data.voices);
// Output:
// [
//   {
//     filename: "archbishop_1_f5tts_eng_20251109_222527.wav",
//     voice_name: "archbishop_1",
//     provider: "f5tts",
//     language: "eng",
//     timestamp: "20251109_222527",
//     file_size: 353843
//   },
//   ...
// ]
```

#### Filter by Provider or Language

```javascript
// Get only F5-TTS voices
const f5ttsVoices = await fetch('/api/cloned-voices/list?provider=f5tts');

// Get only English voices
const englishVoices = await fetch('/api/cloned-voices/list?language=eng');

// Get F5-TTS English voices
const filtered = await fetch('/api/cloned-voices/list?provider=f5tts&language=eng');
```

#### Play a Cloned Voice

```javascript
// Play directly from voice-lab
const audio = new Audio('/api/cloned-voices/play/f5tts/archbishop_1_f5tts_eng_20251109_222527.wav');
await audio.play();
```

#### Register in Voice Library

```javascript
const response = await fetch('/api/cloned-voices/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    filename: 'archbishop_1_f5tts_eng_20251109_222527.wav',
    name: 'Archbishop (F5-TTS) - English',  // Optional custom name
    description: 'Cloned voice using F5-TTS',  // Optional
    tags: ['f5tts', 'cloned', 'english', 'ghanaian'],  // Optional
    visibility: 'private'  // 'private' | 'internal' | 'public'
  })
});

const data = await response.json();
console.log('Registered voice:', data.voice);
```

#### Download a Cloned Voice

```javascript
// Create download link
const link = document.createElement('a');
link.href = '/api/cloned-voices/download/f5tts/archbishop_1_f5tts_eng_20251109_222527.wav';
link.download = 'archbishop_voice.wav';
link.click();
```

## API Endpoints

### `GET /api/cloned-voices/list`

List all available cloned voices.

**Query Parameters:**
- `provider` (optional): Filter by provider (e.g., `f5tts`)
- `voice_name` (optional): Filter by voice name
- `language` (optional): Filter by language (`eng`, `twi`)

**Response:**
```json
{
  "success": true,
  "message": "Found 10 cloned voices",
  "voices": [...],
  "total": 10
}
```

### `GET /api/cloned-voices/play/{provider}/{filename}`

Stream a cloned voice audio file for playback.

**Example:**
```
GET /api/cloned-voices/play/f5tts/archbishop_1_f5tts_eng_20251109_222527.wav
```

**Response:** Audio/WAV stream

### `POST /api/cloned-voices/register`

Register a cloned voice in the voice library.

**Request Body:**
```json
{
  "filename": "archbishop_1_f5tts_eng_20251109_222527.wav",
  "name": "Archbishop (F5-TTS) - English",
  "description": "Cloned voice using F5-TTS",
  "gender": "male",  // Optional: "male" | "female" | "neutral"
  "tags": ["f5tts", "cloned", "english"],
  "visibility": "private"  // "private" | "internal" | "public"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Cloned voice registered successfully",
  "voice": {
    "id": "voice_123",
    "name": "Archbishop (F5-TTS) - English",
    ...
  }
}
```

### `GET /api/cloned-voices/download/{provider}/{filename}`

Download a cloned voice file.

**Example:**
```
GET /api/cloned-voices/download/f5tts/archbishop_1_f5tts_eng_20251109_222527.wav
```

**Response:** WAV file download

## Available Cloned Voices

Current cloned voices in `/opt/kasaai/apps/voice-lab/clones/f5tts/`:

| Voice Name | Provider | Languages | File Count |
|-----------|----------|-----------|------------|
| Archbishop 1 | F5-TTS | English, Twi | 2 |
| Archbishop 2 | F5-TTS | English, Twi | 2 |
| Juliet Bawuah | F5-TTS | English, Twi | 2 |
| Nana Aba | F5-TTS | English, Twi | 2 |
| Adom Okyere | F5-TTS | English, Twi | 2 |

**Total:** 10 cloned voices

## Filename Format

Cloned voices follow this naming convention:

```
{voice_name}_{provider}_{language}_{timestamp}.wav
```

**Examples:**
- `archbishop_1_f5tts_eng_20251109_222527.wav`
  - Voice: archbishop_1
  - Provider: f5tts
  - Language: eng (English)
  - Timestamp: 2025-11-09 22:25:27

- `juliet_bawuah_f5tts_twi_20251109_222414.wav`
  - Voice: juliet_bawuah
  - Provider: f5tts
  - Language: twi (Twi)
  - Timestamp: 2025-11-09 22:24:14

## Integration Example

Here's a complete example of integrating cloned voices into your voice selection UI:

```typescript
import React, { useState, useEffect } from 'react';

function VoiceSelector() {
  const [clonedVoices, setClonedVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState(null);

  useEffect(() => {
    // Fetch available cloned voices
    fetch('/api/cloned-voices/list?provider=f5tts&language=eng')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setClonedVoices(data.voices);
        }
      });
  }, []);

  const playVoice = (voice) => {
    const audio = new Audio(`/api/cloned-voices/play/${voice.provider}/${voice.filename}`);
    audio.play();
  };

  const selectVoice = async (voice) => {
    // Register voice in library first
    const response = await fetch('/api/cloned-voices/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: voice.filename,
        visibility: 'private'
      })
    });

    const data = await response.json();
    if (data.success) {
      setSelectedVoice(data.voice);
    }
  };

  return (
    <div>
      <h3>Available Cloned Voices</h3>
      {clonedVoices.map(voice => (
        <div key={voice.filename}>
          <span>{voice.voice_name} ({voice.provider})</span>
          <button onClick={() => playVoice(voice)}>Play</button>
          <button onClick={() => selectVoice(voice)}>Use Voice</button>
        </div>
      ))}
    </div>
  );
}
```

## Backend Implementation

The cloned voices API is implemented in:
- **Routes:** `/opt/kasaai/apps/core_backend/backend/routes/cloned_voices.py`
- **Clones Directory:** `/opt/kasaai/apps/voice-lab/clones/`

The API automatically:
1. Scans the clones directory for WAV files
2. Parses filenames to extract metadata
3. Serves audio files directly from disk
4. Integrates with the voice library service

## Notes

- All cloned voices are stored as WAV files (24kHz sample rate)
- File sizes range from ~330KB to ~1.5MB depending on text length
- F5-TTS provider achieved 100% success rate in testing
- Voices are automatically tagged with provider, language, and "cloned" tags
- Gender detection is automatic based on voice name patterns

## Next Steps

1. **Test the API**: Restart the backend and test the endpoints
2. **Use ClonedVoicesPanel**: Add it to your Voice Studio UI
3. **Register Voices**: Register your favorite cloned voices in the library
4. **Use in Production**: Use registered voices for TTS synthesis

## Troubleshooting

**Issue:** API returns 404
- **Solution:** Ensure backend has been restarted after adding the routes

**Issue:** Audio won't play
- **Solution:** Check that the voice file exists in `/opt/kasaai/apps/voice-lab/clones/{provider}/`

**Issue:** Registration fails
- **Solution:** Ensure user is authenticated and has proper permissions

For more help, check the backend logs:
```bash
sudo journalctl -u kasaai-core-backend -f
```
