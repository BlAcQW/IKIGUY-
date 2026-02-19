# Vapi TTS Service - Production Implementation

A production-ready microservice that provides custom TTS for Vapi voice assistants using KasaAI's TTS-WebUI infrastructure with 20+ TTS models.

## Features

✅ **Custom TTS for Vapi**: Webhook integration for Vapi voice assistants
✅ **20+ TTS Models**: Access to StyleTTS2, Kokoro, Bark, CoquiTTS, and more
✅ **Real-time PCM Audio**: Converts audio to Vapi-compatible PCM format
✅ **Rate Limiting**: Per-user and per-organization rate limits
✅ **Fallback Support**: Automatic failover to secondary provider
✅ **Health Monitoring**: Built-in health checks and statistics
✅ **Production Ready**: systemd service, nginx config, logging

## Architecture

```
Vapi Phone Call
    ↓
Vapi POST /api/vapi/tts-webhook
    ↓
https://vapi-tts.ailabsafrica.com (Nginx + SSL)
    ↓
Vapi TTS Service (Port 30035)
    ↓
Shared Services:
    ├─> VapiTTSWebhookService
    ├─> TTSWebUIService (20+ models)
    └─> ServiceRateLimiter
    ↓
Returns raw PCM audio (16-bit, mono, 24kHz)
    ↓
Vapi streams to caller
```

## Quick Start

### 1. Clone and Configure

```bash
cd /home/dev/apps/vapi_service/backend

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 2. Add to `/opt/kasaai/.env`

```bash
# Vapi TTS Service Configuration
VAPI_API_KEY=your-vapi-api-key-here
VAPI_USER_RPM=30
VAPI_ORG_RPM=100
VAPI_TIMEOUT=30
```

### 3. Deploy Service

```bash
# Copy systemd service
sudo cp deployment/systemd/kasaai-vapi-tts.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable kasaai-vapi-tts
sudo systemctl start kasaai-vapi-tts

# Check status
sudo systemctl status kasaai-vapi-tts
```

### 4. Configure Nginx

```bash
# Copy nginx configuration
sudo cp deployment/nginx/vapi-tts.ailabsafrica.com.conf /etc/nginx/sites-available/

# Enable site
sudo ln -s /etc/nginx/sites-available/vapi-tts.ailabsafrica.com.conf /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 5. Setup SSL

```bash
# Get SSL certificate
sudo certbot --nginx -d vapi-tts.ailabsafrica.com
```

### 6. Configure DNS

Add A record:
```
vapi-tts.ailabsafrica.com → 148.251.0.46
```

## Vapi Configuration

In your Vapi dashboard, configure your assistant:

```json
{
  "voice": {
    "provider": "custom-tts",
    "url": "https://vapi-tts.ailabsafrica.com/api/vapi/tts-webhook",
    "secret": "your-vapi-api-key",
    "timeout": 30
  },
  "voiceSettings": {
    "sampleRate": 24000
  }
}
```

## API Endpoints

### Main Endpoints

- **POST** `/api/vapi/tts-webhook` - Vapi TTS webhook (main endpoint)
- **GET** `/api/vapi/health` - Vapi service health check
- **GET** `/api/vapi/config` - Service configuration
- **POST** `/api/vapi/stats/reset` - Reset statistics (requires auth)

### Monitoring Endpoints

- **GET** `/health` - Global health check
- **GET** `/metrics` - Prometheus metrics
- **GET** `/` - Service info

### Documentation

- **GET** `/docs` - Swagger UI
- **GET** `/redoc` - ReDoc documentation
- **GET** `/openapi.json` - OpenAPI schema

## Testing

### 1. Test Local Service

```bash
# Health check
curl http://localhost:30035/health

# Vapi health check
curl http://localhost:30035/api/vapi/health

# Service info
curl http://localhost:30035/
```

### 2. Test Production Endpoint

```bash
# Health check
curl https://vapi-tts.ailabsafrica.com/health

# Test webhook
curl -X POST https://vapi-tts.ailabsafrica.com/api/vapi/tts-webhook \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-vapi-api-key" \
  -d '{
    "message": {
      "type": "voice-request",
      "text": "Hello! This is a test of the KasaAI custom TTS system.",
      "sampleRate": 24000
    },
    "timestamp": 1234567890,
    "assistant": {
      "organizationId": "test_org"
    },
    "customer": {
      "number": "+1234567890"
    }
  }' \
  --output test_audio.pcm

# Play the audio
ffplay -f s16le -ar 24000 -ac 1 test_audio.pcm
```

### 3. Test with Python

```python
import httpx
import base64

# Test webhook
url = "https://vapi-tts.ailabsafrica.com/api/vapi/tts-webhook"
headers = {
    "Authorization": "Bearer your-vapi-api-key",
    "Content-Type": "application/json"
}
data = {
    "message": {
        "type": "voice-request",
        "text": "Testing KasaAI TTS webhook",
        "sampleRate": 24000
    },
    "timestamp": 1234567890
}

with httpx.Client() as client:
    response = client.post(url, headers=headers, json=data)

    if response.status_code == 200:
        # Save PCM audio
        with open("test.pcm", "wb") as f:
            f.write(response.content)
        print("✓ Audio saved to test.pcm")
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
```

## Monitoring

### Check Service Status

```bash
# Service status
sudo systemctl status kasaai-vapi-tts

# View logs (live)
sudo journalctl -u kasaai-vapi-tts -f

# View recent logs
sudo journalctl -u kasaai-vapi-tts -n 100

# Check nginx logs
sudo tail -f /var/log/nginx/vapi-tts-access.log
sudo tail -f /var/log/nginx/vapi-tts-error.log
```

### Health Check

```bash
# Check health
curl https://vapi-tts.ailabsafrica.com/health | jq

# Check Vapi service health
curl https://vapi-tts.ailabsafrica.com/api/vapi/health | jq

# Get configuration
curl https://vapi-tts.ailabsafrica.com/api/vapi/config | jq

# Get metrics
curl https://vapi-tts.ailabsafrica.com/metrics
```

### Statistics

```python
import httpx

# Get statistics
response = httpx.get("https://vapi-tts.ailabsafrica.com/api/vapi/health")
stats = response.json()

print(f"Total requests: {stats['uptime_stats']['total_requests']}")
print(f"Success rate: {stats['uptime_stats']['success_rate']:.1%}")
print(f"Fallback usage: {stats['uptime_stats']['fallback_used']}")
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `30035` | Service port |
| `VAPI_API_KEY` | - | Vapi API key for authentication |
| `VAPI_USER_RPM` | `30` | Requests per minute per user |
| `VAPI_USER_RPH` | `500` | Requests per hour per user |
| `VAPI_ORG_RPM` | `100` | Requests per minute per org |
| `VAPI_ORG_RPH` | `2000` | Requests per hour per org |
| `VAPI_TIMEOUT` | `30` | Request timeout (seconds) |
| `TTSWEBUI_WEBUI_ENDPOINT` | `https://tts-webui.ailabsafrica.com` | TTS-WebUI URL |
| `TTSWEBUI_API_ENDPOINT` | `https://tts-webui.ailabsafrica.com/api` | TTS-WebUI API URL |

### TTS Providers

Default configuration:
- **Primary**: StyleTTS2 (expressive, natural voices)
- **Fallback**: Kokoro (fast, reliable)

Available providers (20+):
- StyleTTS2, Kokoro, Chatterbox, Bark, Tortoise
- MahaTTS, MMS, VALL-E X, RVC, CoquiTTS
- OpenVoice, F5-TTS, Moshi, Fish Speech
- Edge TTS, Google TTS, Azure TTS, and more

### Rate Limits

Default limits:
- **Per User**: 30 req/min, 500 req/hour
- **Per Organization**: 100 req/min, 2000 req/hour

Adjust in `.env`:
```bash
VAPI_USER_RPM=50
VAPI_ORG_RPM=200
```

## Troubleshooting

### Service Not Starting

```bash
# Check logs
sudo journalctl -u kasaai-vapi-tts -n 50

# Check if port is available
sudo lsof -i :30035

# Test manually
cd /home/dev/apps/vapi_service/backend
source /opt/kasaai/apps/venv/bin/activate
export PYTHONPATH=/home/dev:/home/dev/apps
python -m app.main
```

### TTS Not Working

```bash
# Check TTS-WebUI service
curl https://tts-webui.ailabsafrica.com/health

# Test TTS-WebUI directly
curl https://tts-webui.ailabsafrica.com/api/health

# Check logs for errors
sudo journalctl -u kasaai-vapi-tts -f | grep -i error
```

### Rate Limiting Issues

```bash
# Disable rate limiting temporarily
# Edit .env and restart service

# Check current usage
curl https://vapi-tts.ailabsafrica.com/api/vapi/health | jq '.uptime_stats'
```

### Audio Quality Issues

1. **Check sample rate**: Vapi requires 8000, 16000, 22050, or 24000 Hz
2. **Try different provider**: Switch from StyleTTS2 to Kokoro
3. **Check logs**: Look for conversion errors
4. **Test locally**: Save PCM and play with ffplay

## Scaling

### Increase Workers

Edit systemd service:
```bash
sudo nano /etc/systemd/system/kasaai-vapi-tts.service

# Change workers
ExecStart=/opt/kasaai/apps/venv/bin/uvicorn \
    app.main:app \
    --workers 4  # Increase from 2

sudo systemctl daemon-reload
sudo systemctl restart kasaai-vapi-tts
```

### Increase Rate Limits

Edit `.env`:
```bash
VAPI_USER_RPM=100
VAPI_ORG_RPM=500
```

Restart service:
```bash
sudo systemctl restart kasaai-vapi-tts
```

## Security

### API Key Rotation

```bash
# Update .env
nano /opt/kasaai/.env
# Change VAPI_API_KEY

# Restart service
sudo systemctl restart kasaai-vapi-tts

# Update Vapi dashboard with new key
```

### Restrict Access

Edit nginx config to allow only Vapi IPs:
```nginx
location /api/vapi/tts-webhook {
    # Allow Vapi IPs only
    allow 1.2.3.4;  # Vapi IP addresses
    deny all;

    proxy_pass http://127.0.0.1:30035;
}
```

## Cost Savings

Using custom TTS vs. ElevenLabs/PlayHT:

| Service | Cost per 1,000 minutes | Annual (10k calls) |
|---------|------------------------|-------------------|
| ElevenLabs | $30/1000 min | $3,600 |
| PlayHT | $25/1000 min | $3,000 |
| **KasaAI TTS** | **$0** | **$0** |

**Savings**: ~$3,000 - $3,600 per year for 10,000 calls

## Support

### Documentation
- Service code: `/home/dev/apps/vapi_service/`
- Shared services: `/home/dev/apps/shared/services/vapi_tts_webhook.py`
- Integration guide: `/home/dev/apps/shared/INTEGRATION_GUIDE_FOR_APPS.md`

### Logs
- Service logs: `sudo journalctl -u kasaai-vapi-tts -f`
- Nginx access: `/var/log/nginx/vapi-tts-access.log`
- Nginx errors: `/var/log/nginx/vapi-tts-error.log`

### Commands
```bash
# Restart service
sudo systemctl restart kasaai-vapi-tts

# View status
sudo systemctl status kasaai-vapi-tts

# Stop service
sudo systemctl stop kasaai-vapi-tts

# Disable service
sudo systemctl disable kasaai-vapi-tts
```

## License

Copyright © 2025 AI Labs Africa
