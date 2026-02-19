# InkWave Deployment Guide

## Quick Start

### 1. Setup Backend

```bash
# Navigate to project root
cd /opt/kasaai

# Install Python dependencies (using shared venv)
/opt/kasaai/apps/venv/bin/pip install -r apps/inkwave/backend/requirements.txt

# Test backend locally
cd /opt/kasaai
/opt/kasaai/apps/venv/bin/python -m uvicorn apps.inkwave.backend.app.main:app --reload --port 30029
```

### 2. Setup Frontend

```bash
# Navigate to frontend directory
cd /opt/kasaai/apps/inkwave/frontend

# Install dependencies
npm install

# Test locally
npm run dev

# Build for production
npm run build
```

### 3. Deploy Backend Service

```bash
# Enable and start the systemd service
sudo systemctl daemon-reload
sudo systemctl enable kasaai-inkwave.service
sudo systemctl start kasaai-inkwave.service

# Check status
sudo systemctl status kasaai-inkwave.service

# View logs
sudo journalctl -u kasaai-inkwave.service -f
```

### 4. Setup SSL Certificates

**Prerequisites**: DNS A record for `inkwave.ailabsafrica.com` must point to this server.

```bash
# Generate SSL certificate with certbot
sudo certbot certonly --nginx -d inkwave.ailabsafrica.com -d www.inkwave.ailabsafrica.com --non-interactive --agree-tos --email admin@ailabsafrica.com

# Verify certificate was created
sudo ls -la /etc/letsencrypt/live/inkwave.ailabsafrica.com/
```

### 5. Deploy Nginx Configuration

```bash
# Enable nginx site
sudo ln -s /etc/nginx/sites-available/inkwave.ailabsafrica.com.conf /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 6. Create Frontend Deployment Directory

```bash
# Create directory for frontend dist
sudo mkdir -p /var/www/inkwave/frontend
sudo chown -R dev:www-data /var/www/inkwave

# Copy built frontend
cp -r /opt/kasaai/apps/inkwave/frontend/dist/* /var/www/inkwave/frontend/dist/
```

## Port Configuration

- **Backend Port**: 30029
- **Frontend Dev Port**: 5173

## Environment Variables

Add to `/opt/kasaai/.env`:

```bash
# InkWave Configuration
INKWAVE_PORT=30029
INKWAVE_API_URL=https://api.ailabsafrica.com
```

## Health Checks

- Backend: `curl http://localhost:30029/health`
- Frontend: `https://inkwave.ailabsafrica.com`

## Troubleshooting

### Backend not starting
```bash
sudo journalctl -u kasaai-inkwave.service -n 50
```

### Frontend build errors
```bash
cd /opt/kasaai/apps/inkwave/frontend
npm run build
```

### SSL certificate renewal
```bash
sudo certbot renew --dry-run
```

## Monitoring

```bash
# Backend status
sudo systemctl status kasaai-inkwave.service

# Backend logs (real-time)
sudo journalctl -u kasaai-inkwave.service -f

# Nginx access logs
sudo tail -f /var/log/nginx/inkwave.ailabsafrica.access.log

# Nginx error logs
sudo tail -f /var/log/nginx/inkwave.ailabsafrica.error.log
```
