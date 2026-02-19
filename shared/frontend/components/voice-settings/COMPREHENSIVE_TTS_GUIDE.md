# Comprehensive TTS Provider Selector - Usage Guide

## Overview

The `ComprehensiveTTSSelector` component provides a **unified, reusable interface** for selecting TTS providers across **all KasaAI applications**. It automatically fetches and displays all 14+ TTS providers configured in `@shared/tts/config.py`.

### ✨ Key Features

- **14+ TTS Providers** (F5-TTS, StyleTTS2, Kokoro, TTS-WebUI, etc.)
- **Automatic capability detection** (voice cloning, multilingual, streaming, etc.)
- **Multi-model support** (TTS-WebUI with 20+ models)
- **Voice/Speaker selection** (Kokoro has 11 voices!)
- **Advanced controls** (speed, pitch, language)
- **Status indicators** (online, offline, degraded)
- **Deployment badges** (RunPod GPU, Local Docker, Cloud)
- **Preview functionality**
- **Compact & Detailed views**

---

## Quick Start

### 1. Installation

The component is already available in `@kasaai/shared-frontend`:

```tsx
import { ComprehensiveTTSSelector, useComprehensiveTTS } from '@kasaai/shared-frontend';
```

### 2. Basic Usage

```tsx
import React, { useState } from 'react';
import { ComprehensiveTTSSelector, useComprehensiveTTS } from '@kasaai/shared-frontend';

function MyVoiceSettings() {
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [selectedVoice, setSelectedVoice] = useState<string | null>(null);

  // Fetch all TTS providers from backend
  const { providers, loading, error } = useComprehensiveTTS(
    'https://api.ailabsafrica.com'
  );

  return (
    <ComprehensiveTTSSelector
      providers={providers}
      selectedProviderId={selectedProvider}
      onSelectProvider={setSelectedProvider}
      selectedVoice={selectedVoice}
      onSelectVoice={setSelectedVoice}
      showAdvanced={true}
      showOnlineOnly={true}
    />
  );
}
```

### 3. With All Controls

```tsx
import React, { useState } from 'react';
import { ComprehensiveTTSSelector, useComprehensiveTTS } from '@kasaai/shared-frontend';

function AdvancedVoiceSettings() {
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [selectedVoice, setSelectedVoice] = useState<string | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(0.0);

  const { providers, loading } = useComprehensiveTTS(
    'https://api.ailabsafrica.com'
  );

  const handlePreview = async (text: string) => {
    // Your preview logic here
    console.log('Previewing:', text);
  };

  return (
    <ComprehensiveTTSSelector
      providers={providers}
      selectedProviderId={selectedProvider}
      onSelectProvider={setSelectedProvider}

      // Model selection (for TTS-WebUI)
      selectedModel={selectedModel}
      onSelectModel={setSelectedModel}

      // Voice selection
      selectedVoice={selectedVoice}
      onSelectVoice={setSelectedVoice}

      // Language selection
      selectedLanguage={selectedLanguage}
      onSelectLanguage={setSelectedLanguage}

      // Voice controls
      speed={speed}
      onSpeedChange={setSpeed}
      pitch={pitch}
      onPitchChange={setPitch}

      // Preview
      onPreview={handlePreview}

      // Display options
      showAdvanced={true}
      showOnlineOnly={false}
      isLoading={loading}
    />
  );
}
```

---

## Usage in Different Apps

### 🎙️ Voice Agent (@b2c-portal)

```tsx
// In AssistantConfiguration.tsx
import { ComprehensiveTTSSelector, useComprehensiveTTS } from '@kasaai/shared-frontend';
import { API_BASE_URL } from '@/config/api-config';

const AssistantConfiguration = ({ assistant, onConfigurationChange }) => {
  const { providers, loading } = useComprehensiveTTS(API_BASE_URL);

  return (
    <div>
      <h3>TTS Provider</h3>
      <ComprehensiveTTSSelector
        providers={providers}
        selectedProviderId={assistant?.tts_provider}
        onSelectProvider={(provider) => onConfigurationChange({ tts_provider: provider })}
        selectedVoice={assistant?.tts_voice}
        onSelectVoice={(voice) => onConfigurationChange({ tts_voice: voice })}
        speed={assistant?.speed}
        onSpeedChange={(speed) => onConfigurationChange({ speed })}
        showAdvanced={true}
        showOnlineOnly={true}
      />
    </div>
  );
};
```

### 🏛️ ChurchFlow (@churchflow)

```tsx
// In VoiceSettingsModal.tsx
import { ComprehensiveTTSSelector, useComprehensiveTTS } from '@kasaai/shared-frontend';

function VoiceSettingsModal({ conferenceId, conferenceName }) {
  const [config, setConfig] = useState({
    tts_provider: 'f5tts',
    voice_id: 'archbishop_1',
    speed: 1.0,
    language: 'en'
  });

  const { providers } = useComprehensiveTTS('https://churchflow-api.ailabsafrica.com');

  return (
    <div>
      <ComprehensiveTTSSelector
        providers={providers}
        selectedProviderId={config.tts_provider}
        onSelectProvider={(provider) => setConfig({ ...config, tts_provider: provider })}
        selectedVoice={config.voice_id}
        onSelectVoice={(voice) => setConfig({ ...config, voice_id: voice })}
        speed={config.speed}
        onSpeedChange={(speed) => setConfig({ ...config, speed })}
        selectedLanguage={config.language}
        onSelectLanguage={(language) => setConfig({ ...config, language })}
        showAdvanced={true}
      />
    </div>
  );
}
```

### 📚 InkWave (@inkwave)

```tsx
// In AudiobookSettings.tsx
import { ComprehensiveTTSSelector, useComprehensiveTTS } from '@kasaai/shared-frontend';

function AudiobookSettings() {
  const [voiceSettings, setVoiceSettings] = useState({
    provider: 'kokoro',
    voice: 'af_heart', // Female American voice
    language: 'en',
    speed: 1.0
  });

  const { providers } = useComprehensiveTTS('https://inkwave-api.ailabsafrica.com');

  return (
    <ComprehensiveTTSSelector
      providers={providers}
      selectedProviderId={voiceSettings.provider}
      onSelectProvider={(provider) => setVoiceSettings({ ...voiceSettings, provider })}
      selectedVoice={voiceSettings.voice}
      onSelectVoice={(voice) => setVoiceSettings({ ...voiceSettings, voice })}
      speed={voiceSettings.speed}
      onSpeedChange={(speed) => setVoiceSettings({ ...voiceSettings, speed })}
      showOnlineOnly={true}
    />
  );
}
```

### 📖 StudyFlow (@studyflow)

```tsx
// In StudyVoicePreferences.tsx
import { ComprehensiveTTSSelector, useComprehensiveTTS } from '@kasaai/shared-frontend';

function StudyVoicePreferences() {
  const { providers } = useComprehensiveTTS('https://studyflow-api.ailabsafrica.com');

  return (
    <ComprehensiveTTSSelector
      providers={providers}
      selectedProviderId={userPreferences.tts_provider}
      onSelectProvider={updateTTSProvider}
      selectedLanguage={userPreferences.study_language}
      onSelectLanguage={updateStudyLanguage}
      showAdvanced={true}
    />
  );
}
```

---

## Available TTS Providers

The component automatically displays all providers from `@shared/tts/config.py`:

### 🚀 **RunPod GPU Providers**

1. **F5-TTS** 🎵
   - Voice cloning ✅
   - 4 languages (EN, ZH, JA, KO)
   - Streaming support

2. **StyleTTS2** 🎨
   - Voice cloning ✅
   - Emotion control ✅
   - English only
   - High quality

3. **Moshi** 🤖
   - Real-time conversation ✅
   - Full-duplex dialogue
   - WebSocket support

4. **TTS-WebUI** 🎛️
   - **20+ models** in one!
   - StyleTTS2, RVC, Bark, Tortoise, F5-TTS, XTTS, OpenVoice, Kokoro, Parler-TTS, etc.
   - Multi-model, multi-language
   - OpenAI-compatible API

5. **Fish Speech** 🐠
   - Zero-shot voice cloning
   - Minimal reference audio
   - Fast inference

### 🖥️ **Local Docker Providers**

6. **Coqui XTTS v2** 🎭
   - **17 languages**
   - Voice cloning ✅
   - SSML support

7. **MeloTTS** 🎼
   - Fast multilingual
   - Multi-speaker
   - 6 languages + dialects

8. **OpenVoice** 🎪
   - Advanced voice cloning
   - Emotion control
   - EN + ZH

9. **Kokoro TTS** 🌸
   - **11 voice packs**
   - American & British English
   - Natural prosody
   - Fast & high-quality

### 🔬 **Experimental/Additional**

10. **Zonos** 🌊
11. **Crawl4AI** 🕷️
12. **IndexTTS** 📇
13. **VoxCPM** 🎙️
14. **GPT-SoVITS** 🎬

---

## Component Props

### Required Props

```tsx
interface ComprehensiveTTSSelectorProps {
  providers: TTSProviderInfo[];
  selectedProviderId: string | null;
  onSelectProvider: (providerId: string) => void;
}
```

### Optional Props

```tsx
{
  // Model selection (for multi-model providers)
  selectedModel?: string | null;
  onSelectModel?: (model: string) => void;

  // Voice/Speaker selection
  selectedVoice?: string | null;
  onSelectVoice?: (voice: string) => void;

  // Language selection
  selectedLanguage?: string;
  onSelectLanguage?: (language: string) => void;

  // Voice controls
  speed?: number; // 0.5 - 2.0, default 1.0
  onSpeedChange?: (speed: number) => void;
  pitch?: number; // -20 to +20, default 0
  onPitchChange?: (pitch: number) => void;

  // Preview
  onPreview?: (text: string) => void;
  previewLoading?: boolean;

  // State
  isLoading?: boolean;
  disabled?: boolean;
  showOnlineOnly?: boolean; // Filter to show only online providers
  showAdvanced?: boolean; // Show speed/pitch controls
  className?: string;
}
```

---

## Hook API

### `useComprehensiveTTS(apiBaseUrl, options?)`

```tsx
const {
  providers,  // TTSProviderInfo[]
  loading,    // boolean
  error,      // string | null
  refetch     // () => void
} = useComprehensiveTTS(
  'https://api.ailabsafrica.com',
  {
    onlineOnly: false,  // Filter to online providers only
    autoFetch: true     // Automatically fetch on mount
  }
);
```

---

## Backend Integration

### API Endpoint

The hook fetches from: `GET /tts/providers`

Expected response format:

```json
{
  "providers": {
    "f5tts": {
      "id": "f5tts",
      "name": "F5-TTS",
      "description": "Flow-matching based TTS with voice cloning",
      "status": "online",
      "endpoint": { "base_url": "https://f5tts.ailabsafrica.com" },
      "capabilities": {
        "voice_cloning": true,
        "multi_language": true,
        "supported_languages": ["en", "zh", "ja", "ko"]
      },
      "languages": { "en": "English", "zh": "Chinese" },
      "metadata": { "deployment": "runpod" }
    }
  }
}
```

### Create Backend Endpoint

Add to your FastAPI backend:

```python
from apps.shared.tts.config import PROVIDER_CONFIGS
from fastapi import APIRouter

router = APIRouter()

@router.get("/tts/providers")
async def get_tts_providers():
    """Get all available TTS providers with capabilities."""
    providers = {}

    for provider_id, config in PROVIDER_CONFIGS.items():
        providers[provider_id] = {
            "id": config.id,
            "name": config.name,
            "description": config.description,
            "status": "online",  # Check actual status
            "endpoint": {
                "base_url": config.endpoint.base_url
            },
            "capabilities": {
                "voice_cloning": config.capabilities.voice_cloning,
                "multi_language": config.capabilities.multi_language,
                "speed_control": config.capabilities.speed_control,
                "pitch_control": config.capabilities.pitch_control,
                "multi_speaker": config.capabilities.multi_speaker,
                "multi_model": config.capabilities.multi_model,
                "emotion_control": config.capabilities.emotion_control,
                "streaming": config.capabilities.streaming,
                "supported_languages": config.capabilities.supported_languages,
                "available_models": config.capabilities.available_models,
            },
            "languages": config.languages,
            "speakers": config.speakers,
            "metadata": config.metadata
        }

    return {"providers": providers}
```

---

## Styling & Customization

### Tailwind Classes

The component uses Tailwind CSS. Ensure your app has Tailwind configured.

### Custom Styling

```tsx
<ComprehensiveTTSSelector
  className="my-custom-class"
  // ... other props
/>
```

### Dark Mode Support

Add dark mode classes in your theme:

```css
/* In your dark mode theme */
.dark .comprehensive-tts-selector {
  /* Dark mode styles */
}
```

---

## Examples

### Example 1: Voice Agent Integration

```tsx
// File: @b2c-portal/src/components/voice-agent/TTSConfiguration.tsx
import React, { useState } from 'react';
import { ComprehensiveTTSSelector, useComprehensiveTTS } from '@kasaai/shared-frontend';
import { API_BASE_URL } from '@/config/api-config';

export function TTSConfiguration({ assistant, onChange }) {
  const { providers, loading } = useComprehensiveTTS(API_BASE_URL);

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Text-to-Speech Settings</h3>

      <ComprehensiveTTSSelector
        providers={providers}
        selectedProviderId={assistant.tts_provider}
        onSelectProvider={(provider) => onChange({ tts_provider: provider })}
        selectedModel={assistant.tts_model}
        onSelectModel={(model) => onChange({ tts_model: model })}
        selectedVoice={assistant.tts_voice}
        onSelectVoice={(voice) => onChange({ tts_voice: voice })}
        selectedLanguage={assistant.language}
        onSelectLanguage={(language) => onChange({ language })}
        speed={assistant.speed}
        onSpeedChange={(speed) => onChange({ speed })}
        pitch={assistant.pitch}
        onPitchChange={(pitch) => onChange({ pitch })}
        showAdvanced={true}
        showOnlineOnly={true}
        isLoading={loading}
      />
    </div>
  );
}
```

### Example 2: User Preferences

```tsx
// File: @shared/frontend/components/UserVoicePreferences.tsx
import React from 'react';
import { ComprehensiveTTSSelector, useComprehensiveTTS } from '@kasaai/shared-frontend';

export function UserVoicePreferences({ user, onUpdate, apiBaseUrl }) {
  const { providers } = useComprehensiveTTS(apiBaseUrl);

  return (
    <div>
      <h2>Voice Preferences</h2>
      <p>Choose your preferred TTS provider and voice</p>

      <ComprehensiveTTSSelector
        providers={providers}
        selectedProviderId={user.preferences.tts_provider}
        onSelectProvider={(provider) =>
          onUpdate({ ...user, preferences: { ...user.preferences, tts_provider: provider }})
        }
        selectedVoice={user.preferences.tts_voice}
        onSelectVoice={(voice) =>
          onUpdate({ ...user, preferences: { ...user.preferences, tts_voice: voice }})
        }
        showOnlineOnly={true}
      />
    </div>
  );
}
```

---

## Testing

### Unit Tests

```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ComprehensiveTTSSelector } from '@kasaai/shared-frontend';

describe('ComprehensiveTTSSelector', () => {
  const mockProviders = [
    {
      id: 'f5tts',
      name: 'F5-TTS',
      description: 'Test provider',
      status: 'online',
      deployment: 'runpod',
      endpoint: 'https://test.com',
      capabilities: { voice_cloning: true },
      icon: '🎵'
    }
  ];

  it('renders providers', () => {
    render(
      <ComprehensiveTTSSelector
        providers={mockProviders}
        selectedProviderId={null}
        onSelectProvider={jest.fn()}
      />
    );

    expect(screen.getByText('F5-TTS')).toBeInTheDocument();
  });
});
```

---

## Troubleshooting

### Providers not loading?

1. Check API endpoint is accessible: `GET /tts/providers`
2. Verify CORS settings allow your frontend domain
3. Check browser console for errors

### No voices showing for a provider?

Some providers (like F5-TTS) use voice cloning instead of pre-defined voices. Check `capabilities.voice_cloning`.

### Speed/Pitch controls not showing?

Set `showAdvanced={true}` and ensure provider supports `speed_control` or `pitch_control` capabilities.

---

## Migration from Old Components

### Before (Old TTSProviderSelector)

```tsx
import { TTSProviderSelector } from '@kasaai/shared-frontend';

<TTSProviderSelector
  providers={limitedProviders} // Only shows configured providers
  selectedProviderId={provider}
  onSelectProvider={setProvider}
/>
```

### After (New ComprehensiveTTSSelector)

```tsx
import { ComprehensiveTTSSelector, useComprehensiveTTS } from '@kasaai/shared-frontend';

const { providers } = useComprehensiveTTS(API_BASE_URL);

<ComprehensiveTTSSelector
  providers={providers} // Automatically fetches ALL providers
  selectedProviderId={provider}
  onSelectProvider={setProvider}
  showAdvanced={true}
  showOnlineOnly={true}
/>
```

---

## Contributing

To add a new TTS provider:

1. Add provider to `@shared/tts/config.py`
2. Deploy provider service
3. Provider will automatically appear in the selector!

No frontend code changes needed! 🎉

---

## Support

For issues or questions:
- Check `@shared/tts/config.py` for provider configurations
- Review `@shared/tts/README.md` for TTS system documentation
- See `@shared/frontend/components/voice-settings/` for component source

---

## License

Part of the KasaAI platform - Internal use only
