# Voice Settings Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER APPLICATIONS                                 │
├─────────────────────────────┬───────────────────────────────────────────┤
│        InkWave              │           StudyFlow                        │
│                             │                                            │
│  ┌──────────────────────┐   │   ┌──────────────────────┐                │
│  │ VoiceSettingsPage    │   │   │ VoiceSettingsPage    │                │
│  │ - TTS Settings       │   │   │ - TTS Settings       │                │
│  │ - ASR Settings       │   │   │ - ASR Settings       │                │
│  │ - LLM Settings       │   │   │ - LLM Settings       │                │
│  │ - Voice Library      │   │   │ - Voice Library      │                │
│  └──────────┬───────────┘   │   └──────────┬───────────┘                │
│             │               │              │                            │
│  ┌──────────▼───────────┐   │   ┌──────────▼───────────┐                │
│  │ PlayerPage           │   │   │ MaterialDetails      │                │
│  │ (uses TTS settings)  │   │   │ (uses TTS settings)  │                │
│  └──────────────────────┘   │   └──────────────────────┘                │
│                             │                                            │
└─────────────────────────────┴───────────────────────────────────────────┘
                              │
                              │ Uses
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     SHARED FRONTEND LIBRARY                              │
│                    @kasaai/shared-frontend                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐ │
│  │ Hooks              │  │ Components         │  │ Services           │ │
│  │                    │  │                    │  │                    │ │
│  │ - useTTSProvider   │  │ - TTSProvider      │  │ - voice-api        │ │
│  │ - useASRProvider   │  │   Selector         │  │   -client          │ │
│  │ - useLLMModel      │  │ - ASRProvider      │  │                    │ │
│  │ - useClonedVoices  │  │   Selector         │  │                    │ │
│  │ - useVoiceSettings │  │ - LLMModel         │  │                    │ │
│  │   (NEW)            │  │   Selector         │  │                    │ │
│  │                    │  │ - VoiceLibrary     │  │                    │ │
│  │                    │  │   Selector         │  │                    │ │
│  │                    │  │ - VoiceSettings    │  │                    │ │
│  │                    │  │   Panel (NEW)      │  │                    │ │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘ │
│                                                                           │
└───────────────────────────────────┬───────────────────────────────────────┘
                                    │
                                    │ HTTP/WebSocket
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        BACKEND APIS                                      │
├─────────────────────────────┬───────────────────────────────────────────┤
│   InkWave Backend           │      StudyFlow Backend                    │
│   Port: 30033               │      Port: 30031                          │
│                             │                                            │
│  ┌──────────────────────┐   │   ┌──────────────────────┐                │
│  │ /api/voice-settings  │   │   │ /api/voice-settings  │                │
│  │                      │   │   │                      │                │
│  │ GET /my-settings     │   │   │ GET /my-settings     │                │
│  │ PUT /my-settings     │   │   │ PUT /my-settings     │                │
│  │ GET /org-defaults    │   │   │ GET /org-defaults    │                │
│  │ PUT /org-defaults    │   │   │ PUT /org-defaults    │                │
│  └──────────┬───────────┘   │   └──────────┬───────────┘                │
│             │               │              │                            │
└─────────────┼───────────────┴──────────────┼────────────────────────────┘
              │                              │
              │                              │
              └──────────────┬───────────────┘
                             │
                             │ Uses
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    SHARED BACKEND SERVICES                               │
│                     @shared/services/                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  VoiceSettingsService (NEW)                                        │ │
│  │  - get_settings(user_id, org_id)                                   │ │
│  │  - update_settings(user_id, org_id, settings)                      │ │
│  │  - get_organization_defaults(org_id)                               │ │
│  │  - set_organization_defaults(org_id, settings)                     │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  TTSProviderService                                                │ │
│  │  - get_providers()                                                 │ │
│  │  - synthesize(request)                                             │ │
│  │  - synthesize_with_voice_cloning(request)                          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  ASRProviderService                                                │ │
│  │  - get_providers()                                                 │ │
│  │  - transcribe(request)                                             │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  LLMProviderService                                                │ │
│  │  - get_providers()                                                 │ │
│  │  - chat(request)                                                   │ │
│  │  - chat_stream(request)                                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  VoiceLabService                                                   │ │
│  │  - get_voices()                                                    │ │
│  │  - clone_voice(request)                                            │ │
│  │  - batch_clone_voices(providers)                                   │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└───────────────────────────────────┬───────────────────────────────────────┘
                                    │
                                    │ Stores/Reads
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATABASE LAYER                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                         MongoDB                                          │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │  Collection: voice_settings                                        │ │
│  │  {                                                                 │ │
│  │    user_id: "user_123",                                            │ │
│  │    organization_id: "org_456",                                     │ │
│  │    tts: {                                                          │ │
│  │      default_provider: "coqui_xtts",                               │ │
│  │      default_voice: "nana_aba_24bit",                              │ │
│  │      speed: 1.0,                                                   │ │
│  │      pitch: 0.0                                                    │ │
│  │    },                                                              │ │
│  │    asr: {                                                          │ │
│  │      default_provider: "whisper_local",                            │ │
│  │      language: "en",                                               │ │
│  │      task: "transcribe"                                            │ │
│  │    },                                                              │ │
│  │    llm: {                                                          │ │
│  │      default_model: "llama3.2",                                    │ │
│  │      temperature: 0.7,                                             │ │
│  │      max_tokens: 2000                                              │ │
│  │    },                                                              │ │
│  │    voices: {                                                       │ │
│  │      favorite_voices: ["nana_aba"],                                │ │
│  │      custom_voices: []                                             │ │
│  │    }                                                               │ │
│  │  }                                                                 │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  Indexes:                                                                │
│  - { user_id: 1, organization_id: 1 } (unique)                          │
│  - { organization_id: 1 }                                               │
│  - { updated_at: -1 }                                                   │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Connects to
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CORE BACKEND & AI SERVICES                            │
│                    api.ailabsafrica.com                                  │
│                    Port: 30027                                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐ │
│  │ /api/tts/*         │  │ /api/asr/*         │  │ /api/llm/*         │ │
│  │                    │  │                    │  │                    │ │
│  │ - /providers       │  │ - /providers       │  │ - /providers       │ │
│  │ - /synthesize      │  │ - /transcribe      │  │ - /chat            │ │
│  │ - /clone           │  │ - /languages       │  │ - /chat/stream     │ │
│  │ - /voices          │  │ - /health          │  │ - /health          │ │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘ │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │ /api/voice-lab/*                                                 │   │
│  │ - /voices                                                        │   │
│  │ - /voices/cloned                                                 │   │
│  │ - /voices/batch-clone                                            │   │
│  │ - /library-voices                                                │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                           │
└───────────────────────────────────┬───────────────────────────────────────┘
                                    │
                                    │ Uses
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    TTS DEPLOYMENT INFRASTRUCTURE                         │
│                    @tts-deployment/                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│  │ Coqui XTTS     │  │ F5-TTS         │  │ StyleTTS2      │             │
│  │ (Deployed)     │  │ (Deployed)     │  │ (Deployed)     │             │
│  └────────────────┘  └────────────────┘  └────────────────┘             │
│                                                                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│  │ OpenVoice      │  │ Moshi          │  │ Whisper        │             │
│  │ (Deployed)     │  │ (Deployed)     │  │ (Deployed)     │             │
│  └────────────────┘  └────────────────┘  └────────────────┘             │
│                                                                           │
│  ┌────────────────┐  ┌────────────────┐                                 │
│  │ Ollama LLMs    │  │ OpenWebUI      │                                 │
│  │ (Deployed)     │  │ (Deployed)     │                                 │
│  └────────────────┘  └────────────────┘                                 │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### 1. User Updates Voice Settings

```
┌─────────┐     Update Settings      ┌────────────────┐
│  User   │ ───────────────────────> │ VoiceSettings  │
│         │                           │ Page           │
└─────────┘                           └───────┬────────┘
                                              │
                                              │ useVoiceSettings.update()
                                              ▼
                                      ┌────────────────┐
                                      │ voice-api      │
                                      │ -client        │
                                      └───────┬────────┘
                                              │
                                              │ PUT /api/voice-settings/my-settings
                                              ▼
                                      ┌────────────────┐
                                      │ InkWave/       │
                                      │ StudyFlow      │
                                      │ Backend API    │
                                      └───────┬────────┘
                                              │
                                              │ VoiceSettingsService.update_settings()
                                              ▼
                                      ┌────────────────┐
                                      │ MongoDB        │
                                      │ voice_settings │
                                      └────────────────┘
```

### 2. User Synthesizes Speech with Settings

```
┌─────────┐    Click Play Button     ┌────────────────┐
│  User   │ ───────────────────────> │ PlayerPage     │
│         │                           │ (InkWave)      │
└─────────┘                           └───────┬────────┘
                                              │
                                              │ useVoiceSettings.get()
                                              ▼
                                      ┌────────────────┐
                                      │ Get User       │
                                      │ Settings       │
                                      └───────┬────────┘
                                              │
                                              │ TTS Settings: provider, voice, speed
                                              ▼
                                      ┌────────────────┐
                                      │ useTTSProvider │
                                      │ .synthesize()  │
                                      └───────┬────────┘
                                              │
                                              │ POST /api/tts/synthesize
                                              ▼
                                      ┌────────────────┐
                                      │ Core Backend   │
                                      │ TTS Service    │
                                      └───────┬────────┘
                                              │
                                              │ Forward to Provider
                                              ▼
                                      ┌────────────────┐
                                      │ Coqui XTTS     │
                                      │ (or selected)  │
                                      └───────┬────────┘
                                              │
                                              │ Audio Data
                                              ▼
┌─────────┐    Play Audio            ┌────────────────┐
│  User   │ <───────────────────────  │ Audio Player   │
│         │                           │                │
└─────────┘                           └────────────────┘
```

### 3. Organization Admin Sets Defaults

```
┌─────────┐    Set Org Defaults      ┌────────────────┐
│  Admin  │ ───────────────────────> │ Admin Settings │
│         │                           │ Page           │
└─────────┘                           └───────┬────────┘
                                              │
                                              │ PUT /org-defaults
                                              ▼
                                      ┌────────────────┐
                                      │ Backend API    │
                                      └───────┬────────┘
                                              │
                                              │ set_organization_defaults()
                                              ▼
                                      ┌────────────────┐
                                      │ MongoDB        │
                                      │ voice_settings │
                                      │ (org defaults) │
                                      └───────┬────────┘
                                              │
                                              │ Inherited by new users
                                              ▼
┌─────────┐    First Login            ┌────────────────┐
│New User │ ───────────────────────> │ Gets Org       │
│         │                           │ Defaults       │
└─────────┘                           └────────────────┘
```

## Component Hierarchy

### VoiceSettingsPanel Component Tree

```
VoiceSettingsPanel
│
├── Header
│   ├── Title: "Voice Settings"
│   └── Save/Cancel Buttons
│
├── TTSSection
│   ├── TTSProviderSelector
│   │   ├── Provider Dropdown (Coqui, F5-TTS, etc.)
│   │   ├── Provider Status Badge
│   │   └── Health Check Button
│   │
│   ├── VoiceLibrarySelector
│   │   ├── Voice Grid/List
│   │   ├── Search/Filter
│   │   ├── Favorite Toggle
│   │   └── Play Preview Button
│   │
│   └── TTSAdvancedSettings (Optional)
│       ├── Speed Slider (0.5 - 2.0)
│       ├── Pitch Slider (-1.0 - 1.0)
│       └── Output Format Dropdown
│
├── ASRSection
│   ├── ASRProviderSelector
│   │   ├── Provider Dropdown (Whisper, etc.)
│   │   ├── Provider Status Badge
│   │   └── Health Check Button
│   │
│   ├── LanguageSelector
│   │   └── Language Dropdown
│   │
│   └── ASRAdvancedSettings (Optional)
│       ├── Task Selection (Transcribe/Translate)
│       ├── Response Format
│       └── Temperature Slider
│
├── LLMSection
│   ├── LLMModelSelector
│   │   ├── Model Dropdown (Llama, Gemma, etc.)
│   │   ├── Model Status Badge
│   │   └── Health Check Button
│   │
│   └── LLMAdvancedSettings (Optional)
│       ├── Temperature Slider (0.0 - 2.0)
│       ├── Max Tokens Input
│       ├── Top P Slider
│       └── Context Window Display
│
└── Footer
    ├── Reset to Defaults Button
    ├── Preview Changes Button
    └── Save/Cancel Buttons
```

## State Management Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    Application State                          │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  useVoiceSettings Hook                                  │ │
│  │                                                          │ │
│  │  State:                                                  │ │
│  │  - settings: VoiceSettings                              │ │
│  │  - isLoading: boolean                                   │ │
│  │  - error: string | null                                 │ │
│  │  - isDirty: boolean (has unsaved changes)               │ │
│  │                                                          │ │
│  │  Actions:                                                │ │
│  │  - loadSettings()                                        │ │
│  │  - updateSettings(partial)                               │ │
│  │  - saveSettings()                                        │ │
│  │  - resetToDefaults()                                     │ │
│  │  - resetToOrgDefaults()                                  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  useTTSProvider Hook                                    │ │
│  │                                                          │ │
│  │  State:                                                  │ │
│  │  - providers: Record<string, TTSProvider>               │ │
│  │  - selectedProvider: TTSProvider | null                 │ │
│  │  - isLoading: boolean                                   │ │
│  │                                                          │ │
│  │  Auto-syncs with:                                        │ │
│  │  - settings.tts.default_provider                        │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  useASRProvider Hook                                    │ │
│  │  (Similar structure)                                     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  useLLMModel Hook                                       │ │
│  │  (Similar structure)                                     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

## Security & Permission Model

```
┌──────────────────────────────────────────────────────────────┐
│                     Permission Hierarchy                      │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Platform Admin                                         │ │
│  │  - Can set global defaults                              │ │
│  │  - Can manage all providers                             │ │
│  │  - Can view all organization settings                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                │                              │
│                                ▼                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Organization Admin                                     │ │
│  │  - Can set organization defaults                        │ │
│  │  - Can view organization usage                          │ │
│  │  - Can manage organization voices                       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                │                              │
│                                ▼                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Regular User                                           │ │
│  │  - Can set personal settings                            │ │
│  │  - Can view available providers                         │ │
│  │  - Can use organization voices                          │ │
│  │  - Inherits organization defaults                       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
└──────────────────────────────────────────────────────────────┘

Settings Resolution Order:
1. User Personal Settings (highest priority)
2. Organization Defaults
3. Platform Defaults (fallback)
```

## Deployment Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Production Environment                     │
│                    148.251.0.46                               │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Nginx (SSL Termination)                                │ │
│  │  - inkwave.ailabsafrica.com → :30033                    │ │
│  │  - studyflow.ailabsafrica.com → :30031                  │ │
│  │  - api.ailabsafrica.com → :30027                        │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  InkWave     │  │  StudyFlow   │  │  Core API    │        │
│  │  :30033      │  │  :30031      │  │  :30027      │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  MongoDB :27017                                         │ │
│  │  - inkwave.voice_settings                               │ │
│  │  - studyflow.voice_settings                             │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Shared Virtual Environment                             │ │
│  │  /opt/kasaai/apps/venv                                  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

---

**Document Version:** 1.0
**Last Updated:** 2025-11-03
**Related Documents:** VOICE_SETTINGS_IMPLEMENTATION_PLAN.md
