# Moshi Voice Assistant Usage & Configuration Guide

**Date:** November 8, 2025
**Current Deployment:** kyutai.ailabsafrica.com
**Status:** ✅ Operational (Official Moshi.chat Web Interface)

---

## Current Setup

### What's Running

**URL:** https://kyutai.ailabsafrica.com

**Architecture:**
```
User Browser
    ↓
kyutai.ailabsafrica.com (HTTPS + SSL ✅)
    ↓
Nginx Proxy (148.251.0.46)
    ↓
RunPod GPU (194.68.245.121)
    ↓ Port 8012
Official Moshi.chat Web Application
    ↓
Moshi Models (7B LM + Mimi Codec)
```

**What It Is:**
- Official Kyutai **moshi.chat** web interface
- Complete self-contained application (frontend + backend + models)
- Real-time bidirectional voice conversation
- Full-duplex audio streaming (simultaneous talk & listen)

---

## How to Use Moshi as a Voice Assistant

### 1. Access the Web Interface

**URL:** https://kyutai.ailabsafrica.com

**Browser Requirements:**
- Modern browser with WebRTC support
- Microphone access permission
- Stable internet connection (for low-latency streaming)

### 2. Start a Conversation

1. **Open the URL** in your browser
2. **Grant microphone permission** when prompted
3. **Click the microphone button** to start talking
4. **Speak naturally** - Moshi responds in real-time
5. **Interrupt freely** - Full-duplex allows overlapping speech

### 3. Key Features

**Real-Time Conversation:**
- Ultra-low latency (~200ms)
- Bidirectional audio streaming
- Natural conversation flow
- Interrupt handling (you can talk while Moshi is speaking)

**Conversation Style:**
- Conversational AI personality
- Context-aware responses
- Emotional understanding
- Natural prosody and intonation

---

## System Prompt Configuration

### ⚠️ Current Limitation: NOT SUPPORTED

**Official Status (from Kyutai GitHub):**

> **"There is no support at the moment to do that, as mentioned in the FAQ!"**
> — Alexandre Défossez (Kyutai maintainer)

**Key Findings:**

1. **No Runtime Configuration**
   - System prompts cannot be set at runtime
   - No API parameters for personality customization
   - No configuration files for behavior modification

2. **Voice & Personality Hardcoded**
   - Voice characteristics are fixed in the model
   - Personality traits are baked into training
   - Cannot be changed without fine-tuning

3. **Prompt Engineering NOT Supported**
   - Unlike ChatGPT or Claude, Moshi doesn't accept system prompts
   - No way to inject instructions at inference time
   - Conversational behavior is model-driven, not prompt-driven

### Why This Limitation?

Moshi is a **speech-to-speech foundation model**, not a text-based LLM with TTS:

- **End-to-end audio** - Processes and generates speech directly
- **No intermediate text** - Doesn't use traditional prompt templates
- **Trained behavior** - Personality is learned during training, not configured
- **Real-time constraints** - Optimized for low latency, not flexibility

---

## Customization Options

### Option 1: Fine-Tuning (Advanced) 🔧

**Repository:** https://github.com/kyutai-labs/moshi-finetune

**What You Can Customize:**
- Conversation style and personality
- Domain-specific knowledge
- Response patterns
- Tone and formality

**Requirements:**
- GPU with 24-40GB VRAM (NVIDIA H100 recommended)
- Python 3.10+
- Training dataset (stereo audio + transcripts)
- ML/AI expertise

**Process Overview:**
```bash
# 1. Prepare dataset
# - Stereo WAV files (left: model, right: user)
# - JSON transcripts with timestamps
# - Organized in .jsonl manifest

# 2. Install moshi-finetune
git clone https://github.com/kyutai-labs/moshi-finetune.git
cd moshi-finetune
pip install -e .

# 3. Configure training
# Edit config.yaml with hyperparameters:
# - learning_rate: 2e-6
# - lora_rank: 128
# - batch_size: 4
# - max_steps: 10000

# 4. Run training
torchrun --nproc_per_node=1 train.py --config config.yaml

# 5. Deploy fine-tuned model
# Replace model weights in Moshi server
```

**Training Parameters:**

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `duration_sec` | 10 | Max sequence length |
| `batch_size` | 4 | Examples per GPU |
| `max_steps` | 10000 | Training iterations |
| `optim.lr` | 2e-6 | Learning rate |
| `lora.rank` | 128 | Adapter size |

**Time & Cost Estimate:**
- **Training Time:** 12-48 hours (depending on dataset size)
- **GPU Cost:** ~$2/hour (H100 on RunPod)
- **Total Cost:** $24-96 for full fine-tune

**Example Use Cases:**
- Customer service assistant (formal, helpful tone)
- Medical consultation bot (empathetic, professional)
- Language tutor (encouraging, corrective)
- Technical support (patient, detailed explanations)

---

### Option 2: Build Custom Backend 🛠️

**Approach:** Create a custom API that wraps Moshi with additional logic

**Architecture:**
```
User Application
    ↓
Your Custom API (Python/FastAPI)
    ↓ ┌─────────────────────────┐
      │  Pre-processing Layer   │
      │  - Context injection    │
      │  - Intent detection     │
      │  - Domain routing       │
      └─────────────────────────┘
    ↓
Moshi Models (Speech-to-Speech)
    ↓
    ┌─────────────────────────┐
    │  Post-processing Layer  │
    │  - Response filtering   │
    │  - Content moderation   │
    │  - Analytics logging    │
    └─────────────────────────┘
    ↓
Response to User
```

**Implementation:**
```python
# Example: Custom Moshi wrapper with context injection
from fastapi import FastAPI, WebSocket
from moshi.models import load_moshi_lm, load_mimi

app = FastAPI()

class MoshiAssistant:
    def __init__(self, context: str):
        self.context = context
        self.model = load_moshi_lm()
        self.codec = load_mimi()

    async def process_audio(self, audio_input: bytes):
        # 1. Analyze intent (using separate ASR/NLU)
        intent = await self.detect_intent(audio_input)

        # 2. Select behavior based on intent
        if intent == "medical_question":
            # Route to specialized handler
            response = await self.medical_handler(audio_input)
        else:
            # Use default Moshi
            response = await self.moshi_inference(audio_input)

        # 3. Post-process response
        filtered = self.content_filter(response)

        return filtered

@app.websocket("/ws/assistant")
async def assistant_endpoint(websocket: WebSocket):
    assistant = MoshiAssistant(context="medical support")
    # ... handle conversation with custom logic
```

**Advantages:**
- No need to fine-tune models
- Flexible behavior modification
- Can add external knowledge (RAG)
- Content filtering and safety
- Multi-modal capabilities

**Disadvantages:**
- Adds latency (processing overhead)
- Limited control over Moshi's actual responses
- Requires additional infrastructure
- More complex architecture

---

### Option 3: Use Current Interface As-Is ✅

**Best For:** General-purpose conversational AI

**Advantages:**
- Zero configuration needed
- Production-ready
- Ultra-low latency
- No development required

**Limitations:**
- Fixed personality
- No domain specialization
- Cannot inject context
- Limited control over responses

**When to Use:**
- Quick demos and testing
- General conversation applications
- Exploring Moshi capabilities
- Non-critical use cases

---

## Alternative Approaches

### Hybrid System: Moshi + Text LLM

**Concept:** Use Moshi for speech I/O, text LLM for content generation

**Architecture:**
```
User speaks
    ↓
Moshi (Speech-to-Text)
    ↓
GPT-4/Claude (System Prompt + Context)
    ↓
Generated Text Response
    ↓
Moshi (Text-to-Speech)
    ↓
User hears response
```

**Advantages:**
- Full system prompt control (via text LLM)
- Domain expertise injection
- RAG integration
- Content moderation

**Disadvantages:**
- Higher latency (~1-2 seconds)
- More complex pipeline
- Additional API costs
- Not true "voice-to-voice"

**Implementation Example:**
```python
from moshi import Moshi
from openai import AsyncOpenAI

class HybridAssistant:
    def __init__(self, system_prompt: str):
        self.moshi = Moshi()
        self.llm = AsyncOpenAI()
        self.system_prompt = system_prompt

    async def converse(self, audio_input: bytes):
        # 1. Speech to text (Moshi)
        text = await self.moshi.transcribe(audio_input)

        # 2. LLM with system prompt
        response = await self.llm.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": text}
            ]
        )

        # 3. Text to speech (Moshi)
        audio = await self.moshi.synthesize(response.choices[0].message.content)

        return audio
```

---

## Comparison Matrix

| Approach | Customization | Latency | Cost | Complexity | System Prompts |
|----------|--------------|---------|------|------------|----------------|
| **Current Interface** | None | ~200ms | Free | None | ❌ No |
| **Fine-Tuning** | Full | ~200ms | $24-96 | High | ✅ Via Training |
| **Custom Backend** | Moderate | ~500ms | Low | Medium | ⚠️ Limited |
| **Hybrid (Moshi+LLM)** | Full | ~2000ms | Medium | High | ✅ Yes |

---

## Recommendations

### For Quick Start & Testing
**Use:** Current interface (kyutai.ailabsafrica.com)
- No setup required
- Production-ready
- Good for demos

### For Domain-Specific Assistant
**Use:** Fine-tuning
- Customer support
- Medical consultation
- Technical troubleshooting
- Educational tutoring

**Rationale:** Worth the investment for specialized applications

### For Flexible Experimentation
**Use:** Hybrid system (Moshi + LLM)
- Research projects
- Prototype development
- Multi-domain applications

**Rationale:** Full control without fine-tuning commitment

### For Production RAG Applications
**Use:** Custom backend wrapper
- Knowledge base integration
- Content filtering
- Analytics and monitoring
- Multi-tenant support

**Rationale:** Balance of control and performance

---

## Technical Deep Dive: Why No System Prompts?

### Speech-to-Speech vs Text-Based Models

**Traditional TTS Pipeline:**
```
Text Input
    ↓
Text LLM (with system prompt) ← Can inject prompts here
    ↓
Generated Text Response
    ↓
TTS Engine (neutral voice)
    ↓
Audio Output
```

**Moshi's End-to-End Pipeline:**
```
Audio Input
    ↓
Mimi Codec (audio encoding)
    ↓
Moshi LM (7B speech-language model) ← No text representation!
    ↓
Mimi Codec (audio decoding)
    ↓
Audio Output
```

**Key Difference:**
- Moshi processes **audio tokens**, not text tokens
- No intermediate text representation for prompt injection
- Behavior is encoded in model weights, not runtime prompts
- Optimized for real-time streaming, not flexibility

### Why This Design?

**Advantages:**
1. **Lower Latency:** No ASR → LLM → TTS pipeline
2. **Natural Prosody:** Voice characteristics preserved end-to-end
3. **Full-Duplex:** Can listen while speaking
4. **Interruption Handling:** Natural conversation flow

**Trade-offs:**
1. **No System Prompts:** Behavior fixed at training time
2. **Limited Flexibility:** Cannot inject instructions
3. **Requires Fine-Tuning:** Customization needs retraining

---

## Future Possibilities

### Kyutai Roadmap Speculation

Based on GitHub issues and community requests:

1. **System Prompt Support** - Likely in future releases
2. **Multi-Language Fine-Tuning** - Expand beyond English
3. **RAG Integration** - Official support for external knowledge
4. **Streaming Context** - Inject context during conversation
5. **Voice Cloning** - Custom voice characteristics

**Status:** Not officially announced, community feature requests

---

## Practical Examples

### Example 1: Using Moshi for Customer Support (Current Limitations)

**Desired Behavior:**
```
System Prompt: "You are a helpful customer support agent for TechCo.
Always be polite, ask clarifying questions, and offer solutions from
our knowledge base."
```

**Reality:**
- ❌ Cannot set system prompt
- ❌ Cannot inject company knowledge
- ❌ Cannot enforce specific tone

**Workaround:**
- Fine-tune on customer support conversations
- Include company knowledge in training data
- Train on desired tone and style

### Example 2: Medical Consultation Bot

**Desired Behavior:**
```
System Prompt: "You are a medical assistant. Always ask about symptoms,
duration, and severity. Never diagnose. Recommend seeing a doctor for
serious symptoms."
```

**Reality:**
- ❌ Cannot enforce medical protocols via prompts
- ❌ Cannot inject safety guidelines
- ❌ Risk of inappropriate medical advice

**Workaround:**
- Fine-tune on medical conversation corpus
- Include safety guidelines in training examples
- Add post-processing filter for dangerous content

### Example 3: Language Learning Tutor

**Desired Behavior:**
```
System Prompt: "You are a Spanish tutor. Correct pronunciation gently,
provide grammar tips, and encourage the learner."
```

**Reality:**
- ❌ Cannot specify teaching behavior
- ❌ Cannot enforce correction patterns
- ❌ Limited language support (primarily English)

**Workaround:**
- Fine-tune on language tutoring conversations
- Include correction examples in training
- Build custom wrapper for grammar analysis

---

## API Access & Integration

### Current Setup: Official Web Interface Only

**Available:**
- ✅ Web interface at kyutai.ailabsafrica.com
- ✅ WebRTC audio streaming
- ✅ Browser-based access

**NOT Available:**
- ❌ REST API endpoints
- ❌ WebSocket API for custom clients
- ❌ SDK for integration
- ❌ Programmatic access

### Our Custom API (Incomplete)

**Location:** `/opt/kasaai/apps/tts-deployment/docker/moshi/app.py`

**Status:** ⚠️ Models loaded, but conversation logic not implemented

**Endpoints (if completed):**
- `GET /health` - Model status
- `GET /gpu_stats` - GPU usage
- `WS /ws/conversation` - Real-time conversation (TODO)

**Current Blockers:**
- WebSocket conversation handler incomplete
- Audio streaming pipeline not implemented
- Mimi codec integration pending

### Building API Access

**Option A: Use Moshi Python Package**
```bash
pip install moshi

# Start Moshi server
moshi serve --port 8008

# Access via WebSocket
ws://localhost:8008/ws/conversation
```

**Option B: Deploy Our Custom API**
```bash
# SSH to RunPod
ssh -p 22130 root@194.68.245.121

# Complete app.py implementation
cd /workspace/tts-deployment/docker/moshi
vim app.py  # Implement WebSocket handler

# Restart service
python app.py
```

**Option C: Use Official moshi.chat Source**
```bash
# Clone official repo
git clone https://github.com/kyutai-labs/moshi.git

# Build and deploy
cd moshi
npm install
npm run build

# Expose as API
```

---

## Cost Analysis

### Current Setup (Free)

**What We Pay:**
- RunPod GPU: $0.39/hour (NVIDIA A40)
- Shared with F5-TTS and StyleTTS2
- Moshi uses ~15GB of 46GB VRAM

**Monthly Cost:** ~$280/month (24/7 operation)

### Fine-Tuning Cost

**One-Time Training:**
- GPU: $2/hour (H100)
- Duration: 12-48 hours
- Total: $24-96 per fine-tune

**Dataset Preparation:**
- Audio recording: $100-500 (voice actors)
- Annotation: $200-1000 (transcription)
- Total: $300-1500

**Grand Total:** $324-1596 per custom assistant

### Hybrid System Cost

**Per Request:**
- Moshi: Free (self-hosted)
- GPT-4: $0.03 per 1K tokens
- Average conversation: $0.10-0.50

**Monthly (1000 conversations):**
- Low usage: $100-500/month
- High usage: $1000-5000/month

---

## Security & Privacy Considerations

### Current Setup (Official Moshi.chat)

**Data Flow:**
```
User Browser → HTTPS → Our Server → RunPod → Moshi
```

**Privacy:**
- ✅ HTTPS encrypted
- ✅ No data stored by default
- ⚠️ Audio processed on remote GPU
- ❌ No conversation logging

**Concerns:**
- Audio data leaves user's machine
- Processed on cloud GPU (RunPod)
- No audit trail
- Limited compliance (HIPAA, GDPR)

### For Production Deployment

**Recommendations:**
1. **Data Encryption:** End-to-end encryption for audio streams
2. **Audit Logging:** Log all conversations for compliance
3. **Content Filtering:** Post-process responses for safety
4. **User Consent:** Clear privacy policy for voice data
5. **Data Retention:** Define and enforce retention policies

**Compliance Requirements:**
- **HIPAA (Healthcare):** Requires fine-tuned model with content filtering
- **GDPR (EU):** Requires data residency and deletion capabilities
- **COPPA (Children):** Requires age verification and parental consent

---

## Troubleshooting

### Issue: No Audio Output

**Check:**
1. Browser microphone permission granted
2. System audio not muted
3. WebRTC supported in browser
4. Network connectivity stable

### Issue: High Latency (>1 second)

**Causes:**
- Slow internet connection
- Server overloaded
- GPU memory full
- Network routing issues

**Solutions:**
- Use wired connection
- Check GPU usage
- Restart Moshi service
- Test with different browser

### Issue: Poor Response Quality

**Causes:**
- Microphone quality poor
- Background noise
- Model not appropriate for use case

**Solutions:**
- Use better microphone
- Quiet environment
- Fine-tune for domain
- Add pre-processing filters

---

## Next Steps

### Immediate Actions

1. **Test Current Interface**
   - Visit kyutai.ailabsafrica.com
   - Try various conversation scenarios
   - Document limitations and strengths

2. **Define Use Case Requirements**
   - What personality do you need?
   - What domain knowledge required?
   - What are latency requirements?
   - What are compliance needs?

3. **Choose Approach**
   - Fine-tuning (for specific domain)
   - Hybrid system (for flexibility)
   - Custom wrapper (for control)

### Development Roadmap (if customizing)

**Phase 1: Requirements (1 week)**
- Define assistant personality
- Gather example conversations
- Identify domain knowledge needed

**Phase 2: Data Preparation (2-4 weeks)**
- Record stereo audio conversations
- Transcribe and annotate
- Create training manifest

**Phase 3: Fine-Tuning (1 week)**
- Setup training environment
- Run fine-tuning
- Evaluate results

**Phase 4: Deployment (1 week)**
- Deploy fine-tuned model
- Build API wrapper
- Test and iterate

**Total Timeline:** 5-7 weeks

---

## Resources

### Official Documentation
- **GitHub:** https://github.com/kyutai-labs/moshi
- **Fine-Tuning:** https://github.com/kyutai-labs/moshi-finetune
- **Paper:** https://kyutai.org/Moshi.pdf
- **Blog:** https://kyutai.org/2024/09/18/moshi-release.html

### Community Resources
- **GitHub Issues:** https://github.com/kyutai-labs/moshi/issues
- **Discussions:** https://github.com/kyutai-labs/moshi/discussions

### Alternative Voice Assistants
- **OpenAI Whisper + GPT-4 + TTS:** Full control, higher latency
- **ElevenLabs Conversational AI:** Similar concept, closed-source
- **Google Duplex:** Not available for self-hosting

---

## Summary

### Current State
- ✅ Moshi running at kyutai.ailabsafrica.com
- ✅ Official web interface (moshi.chat)
- ✅ Real-time voice conversation
- ❌ No system prompt configuration
- ❌ No API access (web UI only)

### Customization Options
1. **Fine-Tuning:** Full control, high cost, requires expertise
2. **Hybrid System:** Flexible, higher latency, moderate cost
3. **Custom Wrapper:** Moderate control, moderate complexity
4. **As-Is:** No customization, zero setup

### Recommendation
**For immediate use:** Continue with current setup (web interface)
**For production:** Fine-tune for specific domain OR build hybrid system
**For experimentation:** Build custom wrapper with additional logic

---

## Conclusion

Moshi is a groundbreaking speech-to-speech model, but it's **not designed for runtime system prompt configuration** like text-based LLMs. To customize behavior, you must either:

1. **Fine-tune the model** (best for production)
2. **Build a hybrid system** (best for flexibility)
3. **Add wrapper logic** (best for moderate control)

The lack of system prompts is a **fundamental architectural choice**, not a missing feature. Moshi prioritizes real-time performance and natural speech over configurability.

For your use case, we recommend:
- **Immediate:** Use current interface for testing
- **Short-term:** Build hybrid system (Moshi + GPT-4) for system prompt control
- **Long-term:** Fine-tune Moshi for your specific domain

---

**Document Version:** 1.0
**Last Updated:** November 8, 2025
**Deployment:** kyutai.ailabsafrica.com
**Status:** Production
