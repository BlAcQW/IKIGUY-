# Asterisk REST API Service

REST API wrapper for Asterisk Manager Interface (AMI) operations. Provides HTTP endpoints for SIP peer management, call routing, and Asterisk server administration.

## Features

- ✅ **SIP Peer Management**: Create, delete, and query SIP peers
- ✅ **Call Routing**: Configure webhook URLs for incoming calls
- ✅ **Asterisk Status**: Monitor server health and active calls
- ✅ **PJSIP Configuration**: Dynamic endpoint, auth, and AOR management
- ✅ **Simulation Mode**: Development mode without real Asterisk server
- ✅ **CORS Support**: Cross-origin requests from all Kasa AI apps

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────┐
│   Kasa AI Apps  │ HTTP    │  Asterisk API    │  AMI    │  Asterisk   │
│  (Core Backend, │────────▶│  (Port 30040)    │────────▶│  PBX Server │
│   Developer,    │         │  FastAPI + AMI   │         │  (Port 5038)│
│   etc.)         │         │  Client          │         │             │
└─────────────────┘         └──────────────────┘         └─────────────┘
```

## Installation

### 1. Install Dependencies

```bash
cd /opt/kasaai/apps/shared/asterisk-api
/opt/kasaai/apps/venv/bin/pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

Set the following variables:
```bash
ASTERISK_AMI_HOST=127.0.0.1
ASTERISK_AMI_PORT=5038
ASTERISK_AMI_USER=kasaai
ASTERISK_AMI_SECRET=<your-secure-password>
ASTERISK_API_PORT=30040
```

### 3. Configure Asterisk (if not already done)

See [ASTERISK_INTEGRATION_PLAN.md](../../core_backend/ASTERISK_INTEGRATION_PLAN.md) for detailed Asterisk setup instructions.

Quick setup:

```bash
# Edit Asterisk manager.conf
sudo nano /etc/asterisk/manager.conf

# Add this section:
[kasaai]
secret = <your-secure-password>
read = all
write = all

# Reload Asterisk
sudo asterisk -rx "manager reload"
```

## Running the Service

### Development Mode

```bash
cd /opt/kasaai/apps/shared/asterisk-api
/opt/kasaai/apps/venv/bin/python main.py
```

Service will run on `http://localhost:30040`

### Production Mode (Systemd)

1. Create systemd service:

```bash
sudo nano /etc/systemd/system/kasaai-asterisk-api.service
```

```ini
[Unit]
Description=Kasa AI Asterisk REST API
After=network.target asterisk.service

[Service]
Type=simple
User=dev
Group=dev
WorkingDirectory=/opt/kasaai/apps/shared/asterisk-api
Environment="PATH=/opt/kasaai/apps/venv/bin"
EnvironmentFile=/opt/kasaai/.env
ExecStart=/opt/kasaai/apps/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable kasaai-asterisk-api
sudo systemctl start kasaai-asterisk-api
sudo systemctl status kasaai-asterisk-api
```

### Nginx Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/asterisk-api.ailabsafrica.com.conf
```

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name asterisk-api.ailabsafrica.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name asterisk-api.ailabsafrica.com;

    ssl_certificate /etc/letsencrypt/live/asterisk-api.ailabsafrica.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/asterisk-api.ailabsafrica.com/privkey.pem;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:30040;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable and reload nginx:

```bash
sudo ln -s /etc/nginx/sites-available/asterisk-api.ailabsafrica.com.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Get SSL certificate:

```bash
sudo certbot --nginx -d asterisk-api.ailabsafrica.com
```

## API Endpoints

### Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "asterisk_connected": true,
  "ami_version": "Asterisk 20.0.0",
  "timestamp": "2025-11-12T12:00:00Z"
}
```

### Create SIP Peer

```bash
POST /sip/peer
Content-Type: application/json

{
  "number": "+12345678901",
  "sip_username": "kasaai_20251112120000",
  "sip_password": "secure_password_123",
  "webhook_url": "https://api.kasaai.ailabsafrica.com/voice/webhook/kasaai_20251112120000",
  "context": "kasaai-virtual"
}
```

**Response:**
```json
{
  "success": true,
  "message": "SIP peer created successfully for +12345678901",
  "number": "+12345678901",
  "sip_credentials": {
    "username": "kasaai_20251112120000",
    "password": "secure_password_123",
    "server": "asterisk.ailabsafrica.com",
    "port": 5060,
    "context": "kasaai-virtual"
  },
  "created_at": "2025-11-12T12:00:00Z"
}
```

### Delete SIP Peer

```bash
DELETE /sip/peer
Content-Type: application/json

{
  "number": "+12345678901",
  "sip_username": "kasaai_20251112120000"
}
```

**Response:**
```json
{
  "success": true,
  "message": "SIP peer deleted for +12345678901",
  "number": "+12345678901"
}
```

### Get SIP Peer

```bash
GET /sip/peer/kasaai_20251112120000
```

**Response:**
```json
{
  "username": "kasaai_20251112120000",
  "status": "active",
  "registered": true,
  "contact": "sip:kasaai_20251112120000@192.168.1.100:5060"
}
```

### List SIP Peers

```bash
GET /sip/peers
```

**Response:**
```json
{
  "peers": [
    "kasaai_20251112120000",
    "kasaai_20251112130000"
  ]
}
```

### Create Call Route

```bash
POST /call/route
Content-Type: application/json

{
  "number": "+12345678901",
  "webhook_url": "https://api.kasaai.ailabsafrica.com/voice/webhook/kasaai_20251112120000"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Call route created for +12345678901",
  "webhook_url": "https://api.kasaai.ailabsafrica.com/voice/webhook/kasaai_20251112120000"
}
```

### Get Asterisk Status

```bash
GET /asterisk/status
```

**Response:**
```json
{
  "status": "running",
  "uptime": "10 days, 5 hours",
  "active_channels": 3,
  "active_calls": 1,
  "sip_peers": 15
}
```

### Reload PJSIP

```bash
POST /asterisk/reload
```

**Response:**
```json
{
  "success": true,
  "message": "PJSIP configuration reloaded successfully"
}
```

## Usage from Other Apps

### Python (Core Backend)

```python
import httpx

async def provision_phone_number(number: str, sip_username: str, sip_password: str):
    """Provision phone number via Asterisk API"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://asterisk-api.ailabsafrica.com/sip/peer",
            json={
                "number": number,
                "sip_username": sip_username,
                "sip_password": sip_password,
                "webhook_url": f"https://api.kasaai.ailabsafrica.com/voice/webhook/{sip_username}",
                "context": "kasaai-virtual"
            }
        )
        return response.json()
```

### JavaScript/TypeScript (Frontend)

```typescript
async function provisionPhoneNumber(number: string, sipUsername: string, sipPassword: string) {
  const response = await fetch('https://asterisk-api.ailabsafrica.com/sip/peer', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      number,
      sip_username: sipUsername,
      sip_password: sipPassword,
      webhook_url: `https://api.kasaai.ailabsafrica.com/voice/webhook/${sipUsername}`,
      context: 'kasaai-virtual'
    })
  });

  return await response.json();
}
```

## Simulation Mode

If Asterisk is not available or `ASTERISK_AMI_SECRET` is not set, the API runs in **simulation mode**:

- All operations succeed with simulated responses
- No actual AMI connection is made
- Perfect for development and testing
- Logs indicate `[SIMULATION]` for simulated operations

To disable simulation mode:
1. Install Asterisk on the server
2. Configure AMI credentials
3. Set `ASTERISK_AMI_SECRET` in `.env`

## Monitoring

### View Logs

```bash
# Service logs
sudo journalctl -u kasaai-asterisk-api -f

# Application logs
tail -f /var/log/asterisk-api.log
```

### Health Monitoring

```bash
# Check health endpoint
curl https://asterisk-api.ailabsafrica.com/health

# Check service status
sudo systemctl status kasaai-asterisk-api

# Check Asterisk status
sudo asterisk -rx "core show version"
sudo asterisk -rx "pjsip show endpoints"
```

## Troubleshooting

### API Returns 503 Service Unavailable

**Cause**: AMI client not available

**Solution**:
1. Check if Asterisk is running: `sudo systemctl status asterisk`
2. Verify AMI credentials in `.env`
3. Test AMI connection: `telnet localhost 5038`
4. Check AMI configuration: `cat /etc/asterisk/manager.conf`

### SIP Peer Creation Fails

**Cause**: UpdateConfig command not working

**Solution**:
1. Ensure `pjsip_kasaai.conf` exists and is included in `pjsip.conf`
2. Check file permissions: `ls -la /etc/asterisk/pjsip_kasaai.conf`
3. Verify AMI user has write permissions in `manager.conf`
4. Check Asterisk logs: `sudo asterisk -rx "core show logs"`

### Connection Timeout

**Cause**: Firewall blocking AMI port

**Solution**:
```bash
# Allow AMI port from localhost
sudo ufw allow from 127.0.0.1 to any port 5038
```

## Security Considerations

1. **AMI Access**:
   - Bind AMI to localhost only (127.0.0.1)
   - Use strong passwords (32+ characters)
   - Limit AMI user permissions in manager.conf

2. **API Access**:
   - Use HTTPS only (nginx with SSL)
   - Implement API key authentication (optional)
   - Rate limit requests

3. **SIP Credentials**:
   - Generate strong passwords (16+ characters)
   - Store securely (never log passwords)
   - Rotate credentials periodically

## Performance

- **Async Operations**: All AMI operations are async (non-blocking)
- **Connection Pooling**: Consider implementing for high load
- **Caching**: Consider caching SIP peer status for frequently queried peers
- **Rate Limiting**: Implement rate limiting for production use

## Development

### Run Tests

```bash
cd /opt/kasaai/apps/shared/asterisk-api
/opt/kasaai/apps/venv/bin/pytest tests/
```

### API Documentation

Interactive API docs available at:
- Swagger UI: `https://asterisk-api.ailabsafrica.com/docs`
- ReDoc: `https://asterisk-api.ailabsafrica.com/redoc`

## Support

For issues or questions:
- Check logs: `sudo journalctl -u kasaai-asterisk-api -f`
- Review [ASTERISK_INTEGRATION_PLAN.md](../../core_backend/ASTERISK_INTEGRATION_PLAN.md)
- Contact: dev@ailabsafrica.com

## Version

Current version: **1.0.0**

## License

Copyright © 2025 AI Labs Africa. All rights reserved.
