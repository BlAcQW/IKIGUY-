# Open WebUI Deployment

**Deployed:** 2025-10-20
**Status:** ✅ Online
**URL:** https://openwebui.ailabsafrica.com

---

## Overview

Open WebUI is an all-in-one LLM/TTS web interface that provides a ChatGPT-like experience for interacting with various AI models and TTS services.

## Configuration

### Service Details
- **Container Name:** `openwebui`
- **Image:** `ghcr.io/open-webui/open-webui:main`
- **Internal Port:** 8080
- **External Port:** 8007
- **Domain:** openwebui.ailabsafrica.com
- **SSL Certificate:** Let's Encrypt (Auto-renewal enabled)

### Environment Variables
```bash
WEBUI_NAME=KasaAI TTS Lab
WEBUI_URL=https://openwebui.ailabsafrica.com
ENABLE_SIGNUP=true
DEFAULT_USER_ROLE=user
ENABLE_COMMUNITY_SHARING=false
OPENAI_API_BASE_URL=https://api.ailabsafrica.com/v1
OPENAI_API_KEY=optional
```

### Docker Compose
Open WebUI is defined in `/opt/kasaai/apps/tts-deployment/docker-compose.local.yml`:

```yaml
openwebui:
  image: ghcr.io/open-webui/open-webui:main
  container_name: openwebui
  ports:
    - "8007:8080"
  environment:
    - WEBUI_NAME=KasaAI TTS Lab
    - WEBUI_URL=https://openwebui.ailabsafrica.com
    - ENABLE_SIGNUP=true
    - DEFAULT_USER_ROLE=user
    - ENABLE_COMMUNITY_SHARING=false
    - OPENAI_API_BASE_URL=https://api.ailabsafrica.com/v1
    - OPENAI_API_KEY=optional
  volumes:
    - openwebui_data:/app/backend/data
  restart: unless-stopped
  networks:
    - tts_network
```

## Management

### Start/Stop/Restart
```bash
cd /opt/kasaai/apps/tts-deployment

# Start Open WebUI
sudo docker-compose -f docker-compose.local.yml up -d openwebui

# Stop Open WebUI
sudo docker-compose -f docker-compose.local.yml stop openwebui

# Restart Open WebUI
sudo docker-compose -f docker-compose.local.yml restart openwebui

# View logs
sudo docker logs openwebui -f

# Check status
sudo docker ps | grep openwebui
```

### Check Health
```bash
# Local health check
curl http://localhost:8007/health

# Public HTTPS check
curl https://openwebui.ailabsafrica.com/health
```

## Nginx Configuration

Configuration file: `/opt/kasaai/apps/tts-deployment/nginx/openwebui.ailabsafrica.com.conf`

Key features:
- HTTP to HTTPS redirect
- SSL/TLS certificates via Let's Encrypt
- WebSocket support for real-time chat
- Extended timeouts for LLM responses (300s)
- Proxy buffering disabled for streaming responses
- Client max body size: 100M

### Reload Nginx
```bash
# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## SSL Certificate

- **Domain:** openwebui.ailabsafrica.com
- **Provider:** Let's Encrypt
- **Certificate Path:** `/etc/letsencrypt/live/openwebui.ailabsafrica.com/fullchain.pem`
- **Private Key Path:** `/etc/letsencrypt/live/openwebui.ailabsafrica.com/privkey.pem`
- **Auto-Renewal:** Enabled via certbot

### Manual Certificate Renewal
```bash
sudo certbot renew --cert-name openwebui.ailabsafrica.com
```

## Features

- **User Management:** Sign-up enabled, default role is "user"
- **LLM Integration:** Connected to KasaAI API at `https://api.ailabsafrica.com/v1`
- **TTS Integration:** Can be configured to use local TTS services
- **Real-time Chat:** WebSocket support for streaming responses
- **Document Upload:** Supports up to 100MB file uploads
- **Model Selection:** Access to multiple AI models
- **Community Sharing:** Disabled for privacy

## Troubleshooting

### Container won't start
```bash
# Check logs
sudo docker logs openwebui

# Restart the container
sudo docker-compose -f docker-compose.local.yml restart openwebui
```

### SSL Certificate Issues
```bash
# Check certificate validity
sudo certbot certificates

# Renew certificate
sudo certbot renew --cert-name openwebui.ailabsafrica.com
```

### Nginx Issues
```bash
# Check nginx configuration
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/openwebui.error.log
sudo tail -f /var/log/nginx/openwebui.access.log
```

### Port Conflicts
```bash
# Check what's using port 8007
sudo lsof -i :8007
sudo netstat -tlnp | grep 8007
```

## Access

- **URL:** https://openwebui.ailabsafrica.com
- **First Access:** Create an admin account on first visit
- **Sign-up:** Enabled for new users

## Data Persistence

All Open WebUI data is stored in the Docker volume `openwebui_data`:
```bash
# View volume details
sudo docker volume inspect tts-deployment_openwebui_data

# Backup data
sudo docker run --rm -v tts-deployment_openwebui_data:/data -v $(pwd):/backup ubuntu tar czf /backup/openwebui-backup-$(date +%Y%m%d).tar.gz /data

# Restore data
sudo docker run --rm -v tts-deployment_openwebui_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/openwebui-backup-YYYYMMDD.tar.gz -C /
```

## Integration with TTS Services

Open WebUI can be configured to use the local TTS services:

- **Coqui TTS:** https://coqui.ailabsafrica.com
- **MeloTTS:** https://melotts.ailabsafrica.com
- **OpenVoice:** https://openvoice.ailabsafrica.com
- **Kokoro TTS:** https://kokoro.ailabsafrica.com

Configure these in Open WebUI's settings under "Audio" or "TTS Configuration".

## Version Information

- **Open WebUI Version:** v0.6.34
- **Docker Image:** ghcr.io/open-webui/open-webui:main (latest)
- **Python Version:** 3.11
- **Node Version:** 20

## Next Steps

1. Access https://openwebui.ailabsafrica.com
2. Create an admin account
3. Configure OpenAI API settings
4. Add TTS service endpoints
5. Test chat functionality
6. Configure user permissions

## Support

- **GitHub:** https://github.com/open-webui/open-webui
- **Documentation:** https://docs.openwebui.com
- **Issues:** Report deployment issues in the KasaAI repository
