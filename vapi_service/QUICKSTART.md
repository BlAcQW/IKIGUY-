# Vapi TTS Service - Quick Start Guide

Deploy a production-ready Vapi TTS webhook in 5 minutes!

## Prerequisites

✅ Server with TTS-WebUI deployed (`https://tts-webui.ailabsafrica.com`)
✅ Python 3.10+ with virtual environment at `/opt/kasaai/apps/venv`
✅ Vapi account with API key
✅ (Optional) Domain name with DNS access

## 1-Minute Deploy

### Step 1: Configure Environment

```bash
# Add Vapi API key to main .env
echo "VAPI_API_KEY=your-vapi-api-key-here" >> /opt/kasaai/.env
```

### Step 2: Deploy Service

```bash
cd /home/dev/apps/vapi_service
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

That's it! The service is now running on port 30035.

### Step 3: Test It

```bash
# Test locally
python test_webhook.py

# Test with API key
python test_webhook.py --api-key your-vapi-api-key
```

## Configure Vapi Dashboard

In your Vapi assistant configuration:

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

For local testing, use:
```
"url": "http://YOUR_SERVER_IP:30035/api/vapi/tts-webhook"
```

## Quick Commands

```bash
# Check status
sudo systemctl status kasaai-vapi-tts

# View logs
sudo journalctl -u kasaai-vapi-tts -f

# Restart service
sudo systemctl restart kasaai-vapi-tts

# Test health
curl http://localhost:30035/health | jq

# Test webhook
curl http://localhost:30035/api/vapi/health | jq
```

## Test with Real Voice Call

1. **Create Vapi Assistant** with custom TTS URL
2. **Make test call** to your Vapi phone number
3. **Listen** for the custom TTS voice!

## Production Deployment (with SSL)

### 1. Configure DNS

Add A record:
```
vapi-tts.ailabsafrica.com → YOUR_SERVER_IP
```

### 2. Deploy with SSL

The deploy script will prompt you to:
- Deploy nginx configuration
- Obtain SSL certificate

Or manually:

```bash
# Deploy nginx
sudo cp deployment/nginx/vapi-tts.ailabsafrica.com.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/vapi-tts.ailabsafrica.com.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL
sudo certbot --nginx -d vapi-tts.ailabsafrica.com
```

### 3. Test Production

```bash
# Test production webhook
python test_webhook.py --url https://vapi-tts.ailabsafrica.com --api-key your-key

# Quick health check
curl https://vapi-tts.ailabsafrica.com/health | jq
```

## Troubleshooting

### Service Not Starting

```bash
# Check logs
sudo journalctl -u kasaai-vapi-tts -n 50

# Test manually
cd /home/dev/apps/vapi_service/backend
source /opt/kasaai/apps/venv/bin/activate
export PYTHONPATH=/home/dev:/home/dev/apps
python -m app.main
```

### TTS Not Working

```bash
# Check TTS-WebUI
curl https://tts-webui.ailabsafrica.com/health

# Check service logs
sudo journalctl -u kasaai-vapi-tts -f | grep -i error
```

### API Key Issues

```bash
# Verify API key in .env
grep VAPI_API_KEY /opt/kasaai/.env

# Restart after changing
sudo systemctl restart kasaai-vapi-tts
```

## Monitoring

### View Statistics

```bash
curl http://localhost:30035/api/vapi/health | jq '.stats'
```

### Prometheus Metrics

```bash
curl http://localhost:30035/metrics
```

### Real-time Logs

```bash
sudo journalctl -u kasaai-vapi-tts -f | grep -v "GET /health"
```

## Cost Comparison

| Provider | 1,000 minutes | 10,000 calls/year |
|----------|--------------|-------------------|
| ElevenLabs | $30 | ~$3,600 |
| PlayHT | $25 | ~$3,000 |
| **KasaAI TTS** | **$0** | **$0** |

**Annual Savings**: $3,000 - $3,600

## Next Steps

1. ✅ Test with Vapi voice call
2. ✅ Monitor success rate and performance
3. ✅ Adjust rate limits if needed
4. ✅ Try different TTS providers (StyleTTS2, Kokoro, Bark)
5. ✅ Set up monitoring/alerting

## Support

- 📚 Full docs: See `README.md`
- 🔧 Shared services: `/home/dev/apps/shared/services/vapi_tts_webhook.py`
- 📝 Logs: `sudo journalctl -u kasaai-vapi-tts -f`
- 🐛 Issues: Check logs and service status first

## Summary

```
✓ 5-minute deployment
✓ Production-ready with systemd
✓ Rate limiting & auth built-in
✓ 20+ TTS models available
✓ Automatic fallback support
✓ $3,000+/year cost savings
```

Happy voice calling! 🎉📞
