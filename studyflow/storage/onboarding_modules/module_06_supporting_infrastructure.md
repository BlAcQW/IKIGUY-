# Module 6: Supporting Infrastructure

**Topics Covered:** voice_lab, shared_services, databases

**Part of:** KasaAI Developer Intern Onboarding Course

---

## 6. Supporting Infrastructure

### 6.1 TTS Deployment (`@tts-deployment/`)

**🎯 Purpose**: Comprehensive multi-TTS system deployment for state-of-the-art text-to-speech and voice AI

**🖥️ Infrastructure**:
- **Local GPU**: NVIDIA RTX 4000 SFF Ada (20GB VRAM) - 8 Docker containers
- **RunPod GPU**: NVIDIA A40 (46GB VRAM) - F5-TTS, StyleTTS2

**⚡ Services**: 10 AI services (8 fully operational)

| Service | Status | Port | Endpoint | Features |
|---------|--------|------|----------|----------|
| Coqui TTS | ✅ Online | 8005 | https://coqui.ailabsafrica.com | XTTS v2 voice cloning, 20+ languages |
| MeloTTS | ✅ Online | 8001 | https://melotts.ailabsafrica.com | Fast multilingual synthesis |
| OpenVoice | ✅ Online | 8003 | https://openvoice.ailabsafrica.com | Voice cloning + tone transfer |
| Kokoro TTS | ✅ Online | 8010 | https://kokoro.ailabsafrica.com | Lightweight, mobile-optimized |
| F5-TTS | ✅ Online | 8002 | https://f5tts.ailabsafrica.com | Flow-matching TTS (RunPod) |
| StyleTTS2 | 🔄 Building | 8006 | https://styletts.ailabsafrica.com | Human-level expressive TTS (RunPod) |
| Ollama | ✅ Online | 11434 | https://ollama.ailabsafrica.com | 9 LLM models |
| Open WebUI | ✅ Online | 8007 | https://openwebui.ailabsafrica.com | Unified LLM/TTS interface |
| Moshi | 🟡 Degraded | 8011 | http://localhost:8011 | Conversational AI (GPU constrained) |
| Crawl4AI | ✅ Online | 8009 | https://crawl4ai.ailabsafrica.com | Web scraping |

**🌟 Key Capabilities**:
- 🎭 **Voice Cloning**: Zero-shot from 5-10 second audio
- 🌍 **African Languages**: 1000+ languages via Meta MMS (Akan/Twi, Ga, Ewe, Hausa, Yoruba, Swahili)
- 🤖 **9 LLM Models**: Including Ghanaian fine-tuned variants
- 🎤 **9 ASR Providers**: Including GiftMark Akan (92.9% accuracy)
- ⚡ **Real-time**: 1-3 second generation time, 24kHz audio

**🎨 Frontend Integration**: 3 labs in B2C Portal
- LLM Lab (`/llm-lab`)
- ASR Lab (`/asr-lab`)
- TTS Lab (`/tts-lab`)

**📊 Status**: ✅ Production Ready (8/10 services operational)

📖 **Read More**: `/opt/kasaai/apps/tts-deployment/README.md`

---

### 6.2 Community Platform (`@community/`)

**🎯 Purpose**: Community-driven African language data collection platform

**🌟 Vision**: Create the world's largest, highest-quality, community-driven repository of African language data to power next-generation voice AI systems.

**✨ Core Features**:
- **Language Family Organization**: Niger-Congo, Afroasiatic, Nilo-Saharan
- **Multi-tier Quality System**:
  - Tier 1: Gold Standard (3+ expert validators)
  - Tier 2: Community Reviewed (2 validators)
  - Tier 3: Raw Submissions
- **Multi-channel Submission**:
  - Discord bot (`!submit twi audio "story"`)
  - Mobile app (field recording)
  - Web portal (bulk upload)
- **Gamification**: Points, achievements, leaderboards
- **Community Governance**: Decentralized voting system

**🗣️ Language Families Supported**:
- **Kwa Family**: Twi, Fante, Ga, Ewe
- **Yoruboid**: Yoruba, Igala
- **Bantu**: Swahili, Zulu, Xhosa
- **Chadic**: Hausa, Kanuri
- **Cushitic**: Amharic, Oromo, Somali

**📊 Status**: Documentation complete, ready for implementation

📖 **Read More**: `/opt/kasaai/apps/community/COMMUNITY_DATA_PLATFORM.md`, `DEPLOYMENT.md`

---
