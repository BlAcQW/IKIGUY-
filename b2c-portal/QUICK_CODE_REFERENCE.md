# Quick Code Reference - Twi & English Assistants

## Frontend File Locations

### Main Voice Agent Pages
```
/opt/kasaai/apps/b2c-portal/src/pages/
├── VoiceAgent.tsx (Main UI - English/configurable)
├── TwiConversation.tsx (Twi-specific real-time)
└── VoiceLabTwi.tsx (Twi development/testing)
```

### Voice Agent Components
```
/opt/kasaai/apps/b2c-portal/src/components/voice-agent/
├── AssistantConfiguration.tsx (Language/provider settings)
├── AssistantList.tsx (Assistant selection)
├── VoiceConversationWS.tsx (WebSocket transport)
├── VoiceConversationRTC.tsx (WebRTC transport)
├── CreateAssistantModal.tsx (New assistant dialog)
└── CloneVoiceAgentModal.tsx (Clone assistant)
```

### Configuration Files
```
/opt/kasaai/apps/b2c-portal/src/config/
├── voice-models.ts (ASR/TTS/LLM model configs)
└── voice-agent-providers.ts (Provider definitions)

/opt/kasaai/apps/b2c-portal/src/utils/
└── languageMapping.ts (80+ language mappings)
```

---

## Backend File Locations

### Twi Voice Implementation
```
/opt/kasaai/apps/core_backend/backend/
├── services/twi_voice_service.py (Service logic)
└── routes/twi_voice.py (API endpoints)
```

### Assistant Implementation
```
/opt/kasaai/apps/core_backend/backend/
├── routes/voice_engine/assistant_routes.py (CRUD operations)
├── services/assistant_service.py (Service logic)
└── models/__init__.py (Data models)
```

---

## Key Code Snippets

### 1. Language Configuration (Frontend)

**From voice-models.ts**:
```typescript
export const DIALECT_OPTIONS: DialectOption[] = [
  { value: 'asante', label: 'Asante Twi' },
  { value: 'akuapem', label: 'Akuapem Twi' },
  { value: 'fante', label: 'Fante' },
];

export const DEFAULT_ASR_MODEL = 'akan-whisper';
export const DEFAULT_TTS_MODEL = 'akan-mms';
export const DEFAULT_DIALECT = 'asante';
```

### 2. Language Mapping (Frontend)

**From languageMapping.ts**:
```typescript
export const LANGUAGE_MAPPING: Record<string, LanguageInfo> = {
  'twi': { code: 'twi', name: 'Twi', nativeName: 'Twi' },
  'asante_twi': { code: 'asante_twi', name: 'Asante Twi', nativeName: 'Asante Twi' },
  'en': { code: 'en', name: 'English', nativeName: 'English' },
  // ... 80+ languages
};

export const COUNTRY_LANGUAGES: Record<string, string[]> = {
  'Ghana': ['en', 'twi', 'asante_twi', 'akuapem_twi', 'ewe', 'ga', ...],
  'US': ['en', ...],
  // ... 80+ countries
};
```

### 3. TwiConversation Language Binding

**From TwiConversation.tsx**:
```typescript
// Language and dialect configuration
const [selectedDialect, setSelectedDialect] = useState(DEFAULT_DIALECT);
const [ttsProvider, setTtsProvider] = useState('akan');

// WebSocket session start with language
const connectWebSocket = useCallback(() => {
  const ws = new WebSocket(`${WS_BASE_URL}/api/voice-lab/ws/chat`);
  
  ws.onopen = () => {
    const sessionRequest = {
      type: 'start_session',
      domain: 'general',
      language: 'tw',              // Twi language
      dialect: selectedDialect,    // User-selected dialect
      tts_provider: ttsProvider    // User-selected TTS
    };
    ws.send(JSON.stringify(sessionRequest));
  };
}, [ttsProvider]);

// TTS provider switching mid-session
const changeTtsProvider = (newProvider: string) => {
  setTtsProvider(newProvider);
  
  if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && sessionId) {
    wsRef.current.send(JSON.stringify({
      type: 'change_tts_provider',
      tts_provider: newProvider,
      session_id: sessionId
    }));
  }
};
```

### 4. VoiceAgent Configuration

**From VoiceAgent.tsx**:
```typescript
// Language/provider configuration
interface ConfigurationData {
  llm_provider: string;
  llm_model: string;
  tts_provider: string;
  tts_model: string;
  tts_voice: string;
  stt_provider: string;
  stt_model: string;
  language: string;        // Language selection
  country: string;         // Country context
  system_prompt: string;
  first_message: string;
}

// Configuration change handler
const handleConfigurationChange = async (config: Partial<Assistant>) => {
  if (selectedAssistant) {
    const updatedAssistant = { ...selectedAssistant, ...config };
    setSelectedAssistant(updatedAssistant);
    
    // Auto-save to backend
    try {
      await assistantApiClient.updateAssistant(
        selectedAssistant.id,
        config
      );
    } catch (error) {
      console.error('Error auto-saving configuration:', error);
    }
  }
};
```

### 5. Provider Configuration

**From voice-agent-providers.ts**:
```typescript
// LLM Providers
export const LLM_MODELS_BY_PROVIDER: Record<string, ProviderOption[]> = {
  ollama: [
    {
      value: 'kasaai_llama_twi',
      label: 'KasaAI Llama 3.2 Twi',
      status: 'training',
      badge: '🔵 🖥️',
      description: 'Fine-tuned for Twi & Ghanaian culture'
    },
    {
      value: 'kasaai_aya_ghana',
      label: 'KasaAI Aya-23 Ghana',
      status: 'training',
      badge: '🔵 🖥️',
      description: 'Twi, Akan, Ga, Ewe - 5 languages'
    },
    // ...
  ],
};

// TTS Voices by Provider
export const TTS_VOICES_BY_PROVIDER: Record<string, ProviderOption[]> = {
  meta_mms: [
    {
      value: 'akan-mms',
      label: 'Akan/Twi (MMS)',
      status: 'online',
      badge: '✅ 🖥️',
      description: 'Verified for Ghanaian Twi'
    },
    // ...
  ],
};

// ASR Models by Provider
export const ASR_MODELS_BY_PROVIDER: Record<string, ProviderOption[]> = {
  whisper: [
    {
      value: 'giftmark-akan-whisper',
      label: 'GiftMark Akan Whisper (92.9% accuracy)',
      status: 'online',
      badge: '✅ 🖥️',
      description: 'Fine-tuned for Twi/Akan'
    },
    // ...
  ],
};
```

### 6. Backend Assistant Model

**From models/__init__.py**:
```python
class Assistant(BaseModel):
    """Assistant model for database storage."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., description="Assistant name")
    
    # Model Configuration
    llm_provider: str = Field(default="", description="LLM provider")
    llm_model: str = Field(default="", description="LLM model")
    
    # Voice Configuration
    tts_provider: str = Field(default="", description="TTS provider")
    tts_voice: str = Field(default="", description="TTS voice")
    language: str = Field(default="en", description="Primary language")
    country: str = Field(default="US", description="Primary country")
    
    # Transcriber Configuration
    stt_provider: str = Field(default="", description="STT provider")
    stt_model: str = Field(default="", description="STT model")
    
    # Voice Parameters
    stability: float = Field(default=0.5, description="Voice stability (0-1)")
    clarity_similarity: float = Field(default=0.75, description="Clarity and similarity (0-1)")
    speed: float = Field(default=1.0, description="Voice speed (0.5-2)")
    
    # Conversation
    system_prompt: str = Field(default="", description="System prompt")
    first_message: str = Field(default="", description="First message text")
```

### 7. Twi Voice Service

**From twi_voice_service.py**:
```python
class ASRRequest(BaseModel):
    """Automatic speech recognition request model"""
    audio: str = Field(..., description="Base64-encoded audio")
    language: str = Field(default="tw", description="Language code")
    task: str = Field(default="transcribe", description="transcribe or translate")
    return_timestamps: bool = Field(default=True)
    vad_filter: bool = Field(default=True)

class TTSRequest(BaseModel):
    """Text-to-speech request model"""
    text: str = Field(..., description="Text to synthesize")
    speaker: str = Field(default="TWI-Speaker", description="Speaker ID")
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    output_format: str = Field(default="base64")

class TwiVoiceService:
    async def text_to_speech(self, request: TTSRequest) -> TTSResponse:
        """Convert text to Twi speech using MeloTTS via RunPod"""
        
    async def speech_to_text(self, request: ASRRequest) -> ASRResponse:
        """Convert Twi speech to text using Faster-Whisper via RunPod"""
```

### 8. Twi Voice Routes

**From twi_voice.py**:
```python
router = APIRouter(prefix="/twi-voice", tags=["Twi Voice"])

@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """Convert Twi text to speech"""
    return await twi_voice_service.text_to_speech(request)

@router.post("/asr", response_model=ASRResponse)
async def speech_to_text(request: ASRRequest):
    """Convert Twi speech to text"""
    return await twi_voice_service.speech_to_text(request)

@router.post("/conversation")
async def conversation(
    file: UploadFile = File(...),
    response_text: Optional[str] = Form(None),
    speaker: str = Form(default="TWI-Speaker")
):
    """Full conversation cycle: ASR (user) → TTS (response)"""
    # 1. Transcribe user audio
    # 2. Process response text
    # 3. Generate TTS audio
    # 4. Return both text and audio
```

### 9. Assistant Routes

**From assistant_routes.py**:
```python
@router.get("/", response_model=List[Assistant])
async def get_assistants(user_id: str = None, active_only: bool = True):
    """Get all voice assistants (optionally filtered by user)"""
    
@router.post("/", response_model=Assistant)
async def create_assistant(config: AssistantConfigRequest):
    """Create a new voice assistant"""
    
@router.put("/{assistant_id}", response_model=Assistant)
async def update_assistant(assistant_id: str, updates: AssistantConfigUpdate):
    """Update assistant configuration (including language/providers)"""
    
@router.get("/{assistant_id}", response_model=Assistant)
async def get_assistant(assistant_id: str):
    """Get assistant by ID"""
    
@router.delete("/{assistant_id}")
async def delete_assistant(assistant_id: str):
    """Delete assistant"""
```

---

## Common Patterns

### Pattern 1: Language Selection
```typescript
const [language, setLanguage] = useState('en');

const handleLanguageChange = (newLanguage: string) => {
  setLanguage(newLanguage);
  
  // Update configuration
  if (newLanguage === 'tw') {
    // Auto-select Twi-optimized providers
    setASRModel('giftmark-akan-whisper');
    setTTSProvider('akan-mms');
  } else {
    // Use default English providers
    setASRModel('whisper-large-v3');
    setTTSProvider('elevenlabs');
  }
};
```

### Pattern 2: Dialect Selection (Twi)
```typescript
const [dialect, setDialect] = useState('asante');

const handleDialectChange = (newDialect: string) => {
  setDialect(newDialect);
  
  // Update session if active
  if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
    wsRef.current.send(JSON.stringify({
      type: 'change_dialect',
      dialect: newDialect
    }));
  }
};
```

### Pattern 3: Provider Switching
```python
def get_service_for_provider(provider_id: str):
    """Route to appropriate service based on provider"""
    if provider_id == 'twi_voice':
        return twi_voice_service
    elif provider_id == 'openai':
        return openai_service
    # ... etc
```

---

## Testing Commands

### Test Twi Voice API
```bash
# Health check
curl https://api.ailabsafrica.com/twi-voice/health

# Text-to-Speech
curl -X POST https://api.ailabsafrica.com/twi-voice/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Me pɛ wo din",
    "speaker": "TWI-Speaker",
    "speed": 1.0
  }'

# Speech-to-Text
curl -X POST https://api.ailabsafrica.com/twi-voice/asr/upload \
  -F "file=@audio.wav" \
  -F "language=tw" \
  -F "task=transcribe"
```

### Test Assistant API
```bash
# Get all assistants
curl https://api.ailabsafrica.com/assistants/

# Create new assistant
curl -X POST https://api.ailabsafrica.com/assistants/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Twi Assistant",
    "language": "tw",
    "llm_provider": "gemini",
    "tts_provider": "akan-mms",
    "stt_provider": "whisper"
  }'

# Update assistant
curl -X PUT https://api.ailabsafrica.com/assistants/{id} \
  -H "Content-Type: application/json" \
  -d '{"language": "en"}'
```

---

## Important Notes

1. **Twi and English are architecturally separate** but share the same Assistant model
2. **Language is configurable** - any assistant can be set to any language
3. **Providers are swappable** - can change LLM/TTS/ASR providers per assistant
4. **Dialect support is Twi-specific** - only Twi has dialect options (Asante, Akuapem, Fante)
5. **WebSocket vs WebRTC** - VoiceAgent supports both, TwiConversation uses WebSocket only

---

## Related Documentation

- Full implementation: `VOICE_ASSISTANT_IMPLEMENTATION.md`
- Summary: `TWI_ENGLISH_IMPLEMENTATION_SUMMARY.md`
- Language mapping: `languageMapping.ts`
- Voice models: `voice-models.ts`
- Providers: `voice-agent-providers.ts`
