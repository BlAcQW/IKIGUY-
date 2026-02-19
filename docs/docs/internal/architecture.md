# System Architecture

**Internal Documentation - AI Labs Africa Employees Only**

## Infrastructure Overview

KasaAI operates across multiple servers with a microservices architecture.

### Production Environment (148.251.0.46)

#### Core Services

| Service | Port | Domain | Description |
|---------|------|--------|-------------|
| Core Backend | 30027 | api.ailabsafrica.com | Main API server |
| Developer Platform | 30028 | developer-portal-api.ailabsafrica.com | Developer console API |
| ChurchFlow | 30030 | churchflow-api.ailabsafrica.com | Church management system |
| StudyFlow | 30031 | studyflow-api.ailabsafrica.com | Education platform |
| EventFlow | 30032 | eventflow-api.ailabsafrica.com | Event management |
| InkWave | 30033 | inkwave-api.ailabsafrica.com | Content creation platform |
| ERP | 30034 | erp-api.ailabsafrica.com | Enterprise resource planning |
| Documentation | 30035 | docs.ailabsafrica.com | This documentation site |
| Vapi TTS Service | 30036 | vapi-tts.ailabsafrica.com | Custom TTS webhook for Vapi |
| Asterisk API | 30040 | asterisk-api.ailabsafrica.com | Asterisk REST API for phone provisioning |

#### TTS Services (RunPod Proxy)

All TTS services run on RunPod GPU (NVIDIA A40, 44GB VRAM) and are proxied through local nginx:

| Service | Local Domain | RunPod Proxy | Description |
|---------|--------------|--------------|-------------|
| StyleTTS2 API | styletts.ailabsafrica.com | jzfmzviw26huka-8006.proxy.runpod.net | High-quality voice cloning |
| StyleTTS2 UI | styletts-ui.ailabsafrica.com | jzfmzviw26huka-8007.proxy.runpod.net | Gradio interface |
| Kokoro API | kokoro.ailabsafrica.com | jzfmzviw26huka-8004.proxy.runpod.net | Fast, reliable TTS |
| Kokoro UI | kokoro-ui.ailabsafrica.com | jzfmzviw26huka-8005.proxy.runpod.net | Gradio interface |
| F5-TTS API | f5tts.ailabsafrica.com | jzfmzviw26huka-8010.proxy.runpod.net | Advanced neural TTS |
| F5-TTS UI | f5tts-ui.ailabsafrica.com | jzfmzviw26huka-8011.proxy.runpod.net | Gradio interface |
| MeloTTS API | melotts.ailabsafrica.com | jzfmzviw26huka-8014.proxy.runpod.net | Multi-lingual TTS |
| MeloTTS UI | melotts-ui.ailabsafrica.com | jzfmzviw26huka-8015.proxy.runpod.net | Gradio interface |
| OpenVoice API | openvoice.ailabsafrica.com | jzfmzviw26huka-8016.proxy.runpod.net | Voice cloning |
| OpenVoice UI | openvoice-ui.ailabsafrica.com | jzfmzviw26huka-8017.proxy.runpod.net | Gradio interface |
| Chatterbox API | chatterbox.ailabsafrica.com | jzfmzviw26huka-8018.proxy.runpod.net | Conversational TTS |
| Coqui API | coqui.ailabsafrica.com | jzfmzviw26huka-8020.proxy.runpod.net | XTTS v2 |
| Coqui UI | coqui-ui.ailabsafrica.com | jzfmzviw26huka-8021.proxy.runpod.net | Gradio interface |
| Kyutai/Moshi | moshi.ailabsafrica.com | jzfmzviw26huka-8012.proxy.runpod.net | Advanced voice assistant |
| TTS-WebUI | tts-webui.ailabsafrica.com | jzfmzviw26huka-8013.proxy.runpod.net | Unified TTS platform (20+ models) |

**RunPod Pod Details:**
- **Pod ID**: jzfmzviw26huka-644113c7
- **GPU**: NVIDIA A40 (44GB VRAM)
- **SSH**: `ssh -p 22153 root@194.68.245.121 -i ~/.ssh/id_ed25519`
- **Location**: `/workspace/tts-deployment/`
- **Tunnels**: Managed by `/opt/kasaai/apps/tts-deployment/scripts/runpod_tunnels.sh`

#### Telephony Infrastructure

**Asterisk PBX** - Phone number provisioning and SIP routing

| Component | Location | Description |
|-----------|----------|-------------|
| **Asterisk Container** | Docker (kasaai-asterisk-proxy) | Main PBX server |
| **Asterisk API** | Port 30040 (asterisk-api.ailabsafrica.com) | REST API for phone management |
| **AMI Port** | 5038 (localhost only) | Asterisk Manager Interface |
| **SIP Port** | 5060 (UDP/TCP) | SIP peer connections |
| **Config Directory** | `/opt/kasaai/asterisk/config/` | Asterisk configuration files |
| **Dialplan** | `extensions.conf` | kasaai-virtual context |
| **PJSIP Config** | `pjsip_kasaai.conf` | Dynamic SIP peer configuration |

**Features:**
- ✅ Virtual phone number provisioning (Kasa AI provider)
- ✅ SIP peer automatic registration
- ✅ Webhook-based call routing to voice assistants
- ✅ AstDB webhook URL storage
- ✅ Multi-provider support (Twilio, Vonage import)
- ✅ E.164 international number format
- ✅ Real-time call statistics

**Architecture:**
```
Phone Call → Asterisk PBX (Docker)
                ↓
        Lookup Webhook (AstDB)
                ↓
        HTTP POST to Voice Assistant
                ↓
        AI Conversation Processing
                ↓
        Call Recording & Statistics
```

**Shared Library:**
- Location: `@shared/asterisk_api/`
- Components: REST API (`main.py`), AMI Client (`ami_client.py`), Python Client (`client.py`)
- Documentation: `INTEGRATION_REFERENCE.md`, `README.md`
- Access: All apps can import via `from apps.shared.asterisk_api.client import AsteriskAPIClient`

### Development Environment (85.214.12.174)

Same port allocation as production, but with `dev-` prefix on domains:
- `dev-api.ailabsafrica.com`
- `dev-studyflow-api.ailabsafrica.com`
- etc.

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: MongoDB (primary), PostgreSQL (RAG/vector storage)
- **Cache**: Redis
- **Authentication**: Supabase
- **API Gateway**: Nginx

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Library**: Tailwind CSS, shadcn/ui
- **State Management**: React Context, Zustand

### Infrastructure
- **Web Server**: Nginx
- **Process Manager**: systemd
- **SSL**: Let's Encrypt (via certbot)
- **Container Runtime**: Docker
- **GPU Services**: RunPod

## Shared Libraries

### `@apps/shared/`

Centralized shared library used by all applications:

- **auth/** - Supabase authentication
- **services/** - Common service implementations
- **models/** - Shared data models
- **utils/** - Utility functions
- **config/** - Shared configuration
- **middleware/** - FastAPI middleware
- **ai/** - AI service integrations (TTS, ASR, LLM)

### `@apps/voice-lab/`

Voice processing library providing:
- TTS integration (23+ providers)
- ASR integration (multiple providers)
- Audio processing utilities
- Voice cloning capabilities

## Multi-Tenant Architecture

All applications support multi-tenancy:

1. **Organization Isolation**: Each organization's data is segregated
2. **Custom Branding**: White-label capabilities per organization
3. **Role-Based Access Control**: Fine-grained permissions
4. **Audit Logging**: Complete activity tracking

### Universal Admins

Special admin users with access to all organizations:
- `admin@ailabsafrica.com`
- `alfred.anyan@gmail.com`
- `user@ailabsafrica.com`

## Database Schema

### MongoDB Collections

Primary database for all applications:
```
kasaai_core:
  - organizations
  - organization_users
  - assistants
  - workflows
  - executions
  - usage_records

studyflow:
  - courses
  - lessons
  - students
  - assessments

churchflow:
  - churches
  - members
  - events
  - donations

inkwave:
  - posts
  - drafts
  - publications
  - analytics

erp:
  - employees
  - projects
  - finance
  - inventory
```

### PostgreSQL (Supabase + RAG)

Used for:
- **Authentication**: Supabase auth schema
- **Vector Storage**: pgvector for RAG systems
- **Analytics**: Time-series data

## External Integrations

### AI Services
- **LLM**: OpenAI, Anthropic, Gemini, DeepSeek, etc.
- **TTS**: OpenAI, ElevenLabs, Cartesia, PlayHT, etc.
- **ASR**: OpenAI Whisper, AssemblyAI, Deepgram

### Communication
- **Telephony**: Vapi, Bland AI, Telnyx
- **Email**: iRedMail (mail.ailabsafrica.com)
- **SMS**: Twilio, Africa's Talking

### Workflow Automation
- **n8n**: Workflow orchestration
- **Webhooks**: Custom webhook handlers

## Security

### Authentication Flow
1. User logs in via Supabase
2. JWT token issued
3. Token verified on each API request
4. Organization membership checked
5. Role-based permissions enforced

### Data Encryption
- **In Transit**: TLS 1.3 (Let's Encrypt)
- **At Rest**: MongoDB encryption
- **Secrets**: Environment variables, never committed

### Network Security
- **Firewall**: UFW configured
- **SSH**: Key-based authentication only
- **CORS**: Strict origin policies
- **Rate Limiting**: Per-user and per-organization

## Monitoring & Logging

### Application Logs
```bash
# View service logs
sudo journalctl -u kasaai-studyflow-backend -f
sudo journalctl -u kasaai-core-backend -f
```

### Nginx Logs
```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

### System Monitoring
- **CPU/Memory**: htop, monitoring dashboards
- **Disk Usage**: df, du
- **Database**: MongoDB Atlas monitoring

---

**Last Updated**: November 7, 2025
