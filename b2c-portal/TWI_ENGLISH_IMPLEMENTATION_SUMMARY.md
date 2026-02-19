# Twi and English Voice Assistants - Implementation Summary

## Quick Reference

### Where the Implementation Lives

**Frontend (React/TypeScript)**:
```
b2c-portal/src/
├── pages/
│   ├── VoiceAgent.tsx (Main English assistant UI)
│   ├── TwiConversation.tsx (Twi-specific conversation page)
│   └── VoiceLabTwi.tsx (Twi testing/development page)
├── components/voice-agent/
│   ├── AssistantConfiguration.tsx (Language/provider selection)
│   ├── AssistantList.tsx
│   ├── VoiceConversationWS.tsx (WebSocket transport)
│   └── VoiceConversationRTC.tsx (WebRTC transport)
├── config/
│   ├── voice-models.ts (Twi/English model configs)
│   └── voice-agent-providers.ts (Provider definitions)
└── utils/
    └── languageMapping.ts (80+ languages with Twi/English)
```

**Backend (Python/FastAPI)**:
```
core_backend/backend/
├── routes/
│   ├── twi_voice.py (Twi ASR/TTS endpoints)
│   └── voice_engine/assistant_routes.py (CRUD operations)
├── services/
│   ├── twi_voice_service.py (Twi voice operations)
│   └── assistant_service.py (Assistant management)
└── models/__init__.py (Assistant & related models)
```

---

## How They Work Independently

### Twi Assistant (Individual/Separate)

**User Journey**:
```
User navigates to /twiconversation
    ↓
TwiConversation.tsx page loads
    ↓
Establishes WebSocket to backend
    ↓
Sends session request with language='tw', dialect='asante'
    ↓
User can:
    • Record/transcribe Twi speech (Akan Whisper - 92.9% accuracy)
    • Switch TTS provider (Akan MMS or Google TTS)
    • Send text messages in Twi
    • Receive AI responses with audio playback
    ↓
All communication in Twi language
```

**Key Components**:
- **Model**: GiftMark Akan Whisper (92.9% accuracy)
- **TTS**: Akan MMS (native Twi) or Google TTS
- **Dialects**: Asante, Akuapem, Fante
- **WebSocket Messages**: Language/dialect specified at session start

**Backend Flow**:
```python
# Twi Voice Service (twi_voice_service.py)
TwiVoiceService:
  └─ ASR: Sends audio → RunPod → Faster-Whisper → Twi text
  └─ TTS: Takes Twi text → RunPod → MeloTTS → Audio response
```

### English Assistant (Individual/Separate)

**User Journey**:
```
User navigates to /voiceagent
    ↓
VoiceAgent.tsx page loads
    ↓
AssistantList shows all assistants
    ↓
User selects or creates an assistant with:
    • language = 'en'
    • llm_provider = 'gemini', 'openai', etc.
    • tts_provider = 'elevenlabs', 'openai', etc.
    • stt_provider = 'whisper', etc.
    ↓
User can:
    • Configure the assistant
    • Start conversation (WebSocket or WebRTC)
    • Change transport mode mid-session
    ↓
All communication in English language
```

**Key Components**:
- **Model**: OpenAI Whisper (multiple sizes)
- **TTS**: ElevenLabs, OpenAI TTS, or others
- **LLM**: Gemini, OpenAI, Anthropic, or local Ollama
- **Transport**: WebSocket (streaming) or WebRTC (direct audio)

**Backend Flow**:
```python
# Assistant Service (assistant_service.py)
AssistantService:
  └─ CRUD operations for assistants
  └─ Stores language/provider configuration
  └─ Routes to appropriate service based on providers
```

---

## Language/Dialect Selection Mechanism

### Frontend Implementation

**1. Configuration Interface** (AssistantConfiguration.tsx):
```typescript
interface ConfigurationData {
  language: string;        // 'tw' or 'en'
  country: string;         // 'Ghana' or 'US', etc.
  llm_provider: string;    // Provider selection
  llm_model: string;       // Model selection
  tts_provider: string;    // TTS provider
  tts_voice: string;       // Voice ID
  stt_provider: string;    // ASR provider
  stt_model: string;       // Model selection
}
```

**2. Language Mapping** (languageMapping.ts):
```typescript
LANGUAGE_MAPPING = {
  'tw': { code: 'tw', name: 'Twi', ... },
  'asante_twi': { code: 'asante_twi', name: 'Asante Twi', ... },
  'en': { code: 'en', name: 'English', ... },
  ... // 80+ languages
}

COUNTRY_LANGUAGES = {
  'Ghana': ['en', 'twi', 'asante_twi', 'ewe', 'ga', ...],
  'US': ['en', ...],
  ... // 80+ countries
}
```

**3. Voice Model Configuration** (voice-models.ts):
```typescript
DEFAULT_ASR_MODEL = 'akan-whisper';    // For Twi
DEFAULT_TTS_MODEL = 'akan-mms';        // For Twi
DEFAULT_LLM_MODEL = 'gemini-2.5-flash';

DIALECT_OPTIONS = [
  { value: 'asante', label: 'Asante Twi' },
  { value: 'akuapem', label: 'Akuapem Twi' },
  { value: 'fante', label: 'Fante' }
];
```

### Backend Implementation

**1. Assistant Model**:
```python
class Assistant(BaseModel):
    id: str
    name: str
    language: str          # 'tw', 'en', etc.
    country: str          # 'Ghana', 'US', etc.
    llm_provider: str     # Provider selection
    llm_model: str        # Model selection
    tts_provider: str     # TTS provider
    tts_voice: str        # Voice ID
    stt_provider: str     # ASR provider
    stt_model: str        # Model selection
    system_prompt: str    # Language-independent prompt
```

**2. Language Selection Flow**:
```python
@router.get("/assistants/")
async def get_assistants(user_id: str = None):
    # Returns all assistants with their language configurations
    assistants = assistant_service.get_assistants_by_user(user_id)
    return assistants  # Each has language/provider settings

@router.put("/assistants/{assistant_id}")
async def update_assistant(assistant_id: str, updates: AssistantConfigUpdate):
    # User can change language/country/providers
    # Backend validates and persists
    return assistant_service.update_assistant(assistant_id, update_data)
```

---

## Real-Time Language Switching

### In TwiConversation (Active Session)

**Before Session Start**:
```typescript
// User selects dialect from dropdown
setSelectedDialect('akuapem');  // Switch from 'asante'

// When connecting, session includes dialect
const sessionRequest = {
  type: 'start_session',
  language: 'tw',
  dialect: selectedDialect,    // Now 'akuapem'
  tts_provider: ttsProvider
};
```

**During Session**:
```typescript
// User switches TTS provider mid-conversation
changeTtsProvider('gtts');  // Switch to Google TTS

// Message sent to backend
{
  type: 'change_tts_provider',
  tts_provider: 'gtts',
  session_id: sessionId
}
```

### In VoiceAgent (Configuration)

**Configuration Update**:
```typescript
const handleConfigurationChange = async (config: Partial<Assistant>) => {
  if (selectedAssistant) {
    const updatedAssistant = { ...selectedAssistant, ...config };
    setSelectedAssistant(updatedAssistant);
    
    // Auto-save to backend
    await assistantApiClient.updateAssistant(
      selectedAssistant.id,
      config
    );
  }
};
```

**Provider Auto-Selection** (Potential Enhancement):
```typescript
// Could add logic to auto-select providers based on language
if (selectedLanguage === 'tw') {
  setSelectedASRModel('akan-whisper');
  setSelectedTTSProvider('akan-mms');
} else if (selectedLanguage === 'en') {
  setSelectedASRModel('whisper-large-v3');
  setSelectedTTSProvider('elevenlabs');
}
```

---

## Provider Configuration by Language

### Twi Language Support

**Recommended Providers**:
```typescript
const twiProviders = {
  asr: [
    { value: 'giftmark-akan-whisper', label: 'GiftMark Akan Whisper (92.9%)', status: 'online' },
    { value: 'whisper-large-v3', label: 'Whisper Large v3', status: 'online' },
    { value: 'meta-mms-1b-aka', label: 'Meta MMS 1B Akan', status: 'online' }
  ],
  tts: [
    { value: 'akan-mms', label: 'Akan/Twi (MMS)', status: 'online' },
    { value: 'xtts-twi-v1', label: 'XTTS Twi v1 (Voice Cloning)', status: 'online' }
  ],
  llm: [
    { value: 'kasaai_llama_twi', label: 'KasaAI Llama 3.2 Twi', status: 'training' },
    { value: 'kasaai_aya_ghana', label: 'KasaAI Aya-23 Ghana (5 languages)', status: 'training' },
    { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash', status: 'online' }
  ]
};
```

### English Language Support

**Recommended Providers**:
```typescript
const enProviders = {
  asr: [
    { value: 'whisper-large-v3', label: 'Whisper Large v3', status: 'online' },
    { value: 'whisper-1', label: 'OpenAI Whisper API', status: 'online' },
    { value: 'deepgram-nova', label: 'Deepgram Nova', status: 'online' }
  ],
  tts: [
    { value: 'adam', label: 'ElevenLabs Adam', status: 'online' },
    { value: 'alloy', label: 'OpenAI TTS Alloy', status: 'online' },
    { value: 'google-wavenet', label: 'Google Cloud TTS', status: 'online' }
  ],
  llm: [
    { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash', status: 'online' },
    { value: 'gpt-4o', label: 'OpenAI GPT-4o', status: 'online' },
    { value: 'claude-3-5-sonnet', label: 'Claude 3.5 Sonnet', status: 'online' }
  ]
};
```

---

## Session Management

### Twi Session Example

**WebSocket Flow**:
```
Client: {
  "type": "start_session",
  "language": "tw",
  "dialect": "asante",
  "domain": "general",
  "tts_provider": "akan"
}
    ↓
Server: {
  "type": "session_started",
  "session_id": "twi-session-12345"
}
    ↓
Client: {
  "type": "voice_message",
  "audio_base64": "UklGRi4AAAA...",
  "session_id": "twi-session-12345"
}
    ↓
Server: {
  "type": "final_transcription",
  "text": "Me pɛ wo din",
  "confidence": 0.94,
  "language": "tw"
}
    ↓
Server: {
  "type": "response",
  "text": "Me din de Kofi",
  "audio": "//NExAAUXAAHJADm4...",
  "session_id": "twi-session-12345"
}
```

### English Session Example

**WebRTC Flow**:
```
Client connects with WebRTC
    ↓
Assistant configuration: language='en', llm_provider='gemini'
    ↓
Direct audio exchange (peer-to-peer)
    ↓
Server processes: English ASR → Gemini LLM → English TTS
    ↓
Real-time audio streaming back to client
```

---

## Key Differences Between Implementations

| Aspect | Twi Assistant | English Assistant |
|--------|---------------|-------------------|
| **UI Page** | TwiConversation.tsx | VoiceAgent.tsx |
| **Default Language** | 'tw' (hardcoded) | User-configurable |
| **ASR Model** | GiftMark Akan Whisper | Whisper variants |
| **TTS Provider** | Akan MMS or Google TTS | ElevenLabs, OpenAI, etc. |
| **Dialect Support** | Yes (Asante, Akuapem, Fante) | No |
| **Configuration** | Limited to pre-defined | Full customization |
| **Transport** | WebSocket only | WebSocket or WebRTC |
| **Use Case** | Twi-specific conversations | Multi-language support |

---

## Areas for Enhancement/Integration

### 1. Unified Language Selector
```typescript
// Add to VoiceAgent.tsx
<LanguageSelector 
  value={selectedLanguage}
  onChange={(lang) => {
    // Switch between Twi and English UIs
    // Or update assistant language
  }}
/>
```

### 2. Language-Aware Prompts
```python
LANGUAGE_PROMPTS = {
  'tw': "Akwaaba! Me yɛ AI assistant...",
  'en': "Hello! I'm an AI assistant..."
}
```

### 3. Automatic Provider Selection
```typescript
function getRecommendedProviders(language: string) {
  if (language === 'tw') {
    return {
      asr: 'giftmark-akan-whisper',
      tts: 'akan-mms',
      llm: 'kasaai_llama_twi'
    };
  }
  // etc.
}
```

### 4. Cross-Language Support
```typescript
// Allow bilingual conversations
{
  languages: ['tw', 'en'],  // Support both
  dialect: 'asante',         // For Twi
  auto_translate: false      // Keep original
}
```

---

## Testing the Implementations

### Twi Assistant
```bash
# Test TTS
curl -X POST https://api.ailabsafrica.com/twi-voice/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Me pɛ wo din", "speaker": "TWI-Speaker"}'

# Test ASR
curl -X POST https://api.ailabsafrica.com/twi-voice/asr/upload \
  -F "file=@twi_audio.wav" \
  -F "language=tw"

# Test Conversation
curl -X POST https://api.ailabsafrica.com/twi-voice/conversation \
  -F "file=@user_audio.wav" \
  -F "response_text=Meda wo ase!"
```

### English Assistant
```typescript
// Frontend: Navigate to /voiceagent
// Create new assistant with:
// - language: 'en'
// - llm_model: 'gemini-2.5-flash'
// - tts_provider: 'elevenlabs'
// - Start conversation via WebSocket or WebRTC
```

---

## Documentation References

- **Full Implementation Details**: VOICE_ASSISTANT_IMPLEMENTATION.md
- **Language Mapping**: `/opt/kasaai/apps/b2c-portal/src/utils/languageMapping.ts`
- **Voice Models**: `/opt/kasaai/apps/b2c-portal/src/config/voice-models.ts`
- **Provider Configuration**: `/opt/kasaai/apps/b2c-portal/src/config/voice-agent-providers.ts`
