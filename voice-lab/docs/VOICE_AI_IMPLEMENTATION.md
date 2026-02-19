# Twi Voice AI Implementation Guide
## Real-time Transcription & Conversational AI

### Overview
This implementation provides a complete voice AI system for Twi/Akan languages with:
- Real-time speech-to-text (ASR) using Whisper
- Conversational AI with LLM integration
- Text-to-speech synthesis (TTS)
- WebSocket streaming for real-time interactions
- Multi-domain support (general, healthcare, education, finance)

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Voice Lab)                  │
├─────────────────────────────────────────────────────────┤
│                   WebSocket Connection                   │
│                        /ws/chat                          │
├─────────────────────────────────────────────────────────┤
│                    Backend Services                      │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Whisper    │  │     LLM      │  │     TTS      │  │
│  │   Service    │  │   Service    │  │   Service    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         ↓                  ↓                 ↓          │
│  ┌──────────────────────────────────────────────────┐  │
│  │          Conversation Manager                     │  │
│  │  - Session Management                             │  │
│  │  - Context Tracking                               │  │
│  │  - History Storage                                │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Whisper Real-time Service (`whisper_realtime_service.py`)
- **Purpose**: Provides real-time ASR for Twi/Akan languages
- **Features**:
  - Streaming transcription with VAD (Voice Activity Detection)
  - Support for multiple Whisper model sizes
  - Automatic silence detection and chunking
  - Multi-language support (Twi, Akan, English)
  
```python
# Usage example
whisper_service = get_whisper_service(model_size="base", language="tw")
result = await whisper_service.transcribe_audio(audio_data, sample_rate=16000)
```

#### 2. Twi LLM Service (`twi_llm_service.py`)
- **Purpose**: Conversational AI with Twi language support
- **Features**:
  - Multiple LLM provider support (OpenAI, Groq, Anthropic)
  - Domain-specific prompts (healthcare, education, finance)
  - Twi number and date translation
  - Language detection and code-switching
  
```python
# Usage example
llm_service = get_llm_service(provider=LLMProvider.OPENAI)
response = await llm_service.generate_response(
    message="Maakye! Me pɛ sɛ mesua Twi",
    domain="education"
)
```

#### 3. Conversation Manager (`conversation_manager.py`)
- **Purpose**: Orchestrates the complete voice AI pipeline
- **Features**:
  - Session management with context tracking
  - Voice and text message processing
  - Conversation history and export
  - Real-time streaming support
  
```python
# Usage example
manager = get_conversation_manager()
session_id = await manager.create_session(user_id="user123", domain="general")
result = await manager.process_voice_message(session_id, audio_data)
```

### API Endpoints

#### Chat Management
- `POST /api/voice-lab/chat/start` - Start new conversation
- `POST /api/voice-lab/chat/message` - Send text message
- `POST /api/voice-lab/chat/voice` - Send voice message
- `GET /api/voice-lab/chat/{session_id}/history` - Get conversation history
- `POST /api/voice-lab/chat/{session_id}/clear` - Clear context
- `GET /api/voice-lab/chat/{session_id}/export` - Export conversation
- `GET /api/voice-lab/chat/{session_id}/stats` - Get statistics
- `POST /api/voice-lab/chat/{session_id}/end` - End session

#### WebSocket Endpoints
- `/api/voice-lab/ws/chat` - Real-time voice conversation
- `/api/voice-lab/ws/stream` - Streaming ASR/TTS

### WebSocket Protocol

#### Client → Server Messages
```json
// Audio chunk for transcription
{
  "type": "audio_chunk",
  "audio": "base64_encoded_audio",
  "is_final": false
}

// Text message
{
  "type": "text_message",
  "text": "User message in Twi or English"
}

// Change domain
{
  "type": "change_domain",
  "domain": "healthcare"
}
```

#### Server → Client Messages
```json
// Transcription result
{
  "type": "transcription",
  "text": "Transcribed text",
  "confidence": 0.95
}

// AI response
{
  "type": "response",
  "text": "AI response in Twi",
  "turn_number": 1
}

// Session created
{
  "type": "session_created",
  "session_id": "uuid"
}
```

### Configuration

#### Environment Variables
```bash
# LLM API Keys (optional - uses mock if not set)
export OPENAI_API_KEY="your-openai-key"
export GROQ_API_KEY="your-groq-key"
export ANTHROPIC_API_KEY="your-anthropic-key"

# Model Configuration
export WHISPER_MODEL_SIZE="base"  # tiny, base, small, medium, large
export DEFAULT_LANGUAGE="tw"
export DEFAULT_DIALECT="asante"
```

### Domain-Specific Features

#### Healthcare Domain
- Medical terminology in Twi
- Symptom description assistance
- Emergency detection
- Healthcare professional referral reminders

#### Education Domain
- Language learning support
- Math problem solving in Twi
- Cultural storytelling (Anansesɛm)
- Age-appropriate responses

#### Finance Domain
- Mobile money assistance
- Banking terminology in Twi
- Financial literacy education
- Currency conversion (GH₵)

### Testing

#### Test Chat Start
```bash
curl -X POST http://localhost:30027/api/voice-lab/chat/start \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "general",
    "language": "tw",
    "dialect": "asante"
  }'
```

#### Test Message
```bash
curl -X POST http://localhost:30027/api/voice-lab/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "message": "Hello, I want to learn Twi"
  }'
```

#### WebSocket Test (JavaScript)
```javascript
const ws = new WebSocket('wss://api.ailabsafrica.com/voice-lab/ws/chat');

ws.onopen = () => {
  console.log('Connected to Voice AI');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'session_created') {
    console.log('Session:', data.session_id);
  } else if (data.type === 'transcription') {
    console.log('You said:', data.text);
  } else if (data.type === 'response') {
    console.log('AI says:', data.text);
  }
};

// Send text message
ws.send(JSON.stringify({
  type: 'text_message',
  text: 'Maakye! Me pɛ sɛ mekasa Twi'
}));
```

### Performance Optimization

#### Caching
- Session data cached in memory
- LLM responses can be cached for common queries
- Audio processing results cached by hash

#### Streaming
- Real-time transcription with partial results
- Streaming LLM responses for lower latency
- WebSocket for bidirectional communication

#### Model Optimization
- Whisper model quantization (INT8)
- Faster-whisper for improved performance
- Model selection based on device capabilities

### Security Considerations

1. **Authentication**: Optional authentication via `X-Service-Token` header
2. **Session Timeout**: Automatic cleanup of inactive sessions (30 minutes)
3. **Input Validation**: All inputs validated with Pydantic models
4. **Rate Limiting**: Inherited from core backend
5. **Content Filtering**: Safety checks in LLM responses

### Deployment

#### Requirements
```txt
# Core dependencies
fastapi>=0.100.0
uvicorn>=0.23.0
websockets>=11.0
pydantic>=2.0.0

# ASR dependencies
openai-whisper>=20230918
faster-whisper>=0.9.0
torch>=2.0.0
torchaudio>=2.0.0
webrtcvad>=2.0.10

# LLM dependencies (optional)
openai>=1.0.0
anthropic>=0.5.0
google-generativeai>=0.3.0
aiohttp>=3.8.0

# Audio processing
numpy>=1.24.0
scipy>=1.10.0
librosa>=0.10.0
soundfile>=0.12.0
```

#### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "30027"]
```

### Monitoring & Logging

#### Metrics to Track
- Session count and duration
- Average response time
- Transcription accuracy (WER)
- LLM token usage
- Error rates by endpoint

#### Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"Session {session_id} created for domain {domain}")
logger.error(f"Transcription failed: {error}")
```

### Future Enhancements

1. **RAG Integration**: Add knowledge base for domain-specific information
2. **Voice Cloning**: Personalized TTS voices
3. **Offline Mode**: Edge deployment with smaller models
4. **Multi-turn Reasoning**: Complex conversation flows
5. **Emotion Detection**: Sentiment analysis in Twi
6. **Group Conversations**: Multi-user chat support
7. **Video Support**: Visual context for better understanding

### Troubleshooting

#### Common Issues

1. **No Whisper Model Loaded**
   - Install whisper: `pip install openai-whisper`
   - Download model: Models auto-download on first use

2. **LLM API Errors**
   - Check API keys in environment variables
   - Falls back to mock responses if no API key

3. **WebSocket Connection Failed**
   - Check CORS settings in nginx
   - Verify WebSocket upgrade headers

4. **High Latency**
   - Use smaller Whisper model (tiny/base)
   - Enable response streaming
   - Consider edge deployment

### Support

For issues or questions:
- GitHub Issues: [Report bugs](https://github.com/your-org/kasaai/issues)
- Documentation: Check `/opt/kasaai/apps/voice-lab/docs/`
- Logs: `journalctl -u kasaai-core-backend -f`

---

*Last Updated: September 2025*
*Version: 1.0.0*