# DevotionalFlow (FreshManna) Deployment Guide

## Overview

DevotionalFlow is configured to run on:
- **Frontend**: https://freshmanna.ailabsafrica.com
- **Backend API**: https://freshmanna-api.ailabsafrica.com
- **Port**: 30037

## Configuration Files Created

### 1. Nginx Configurations

#### Backend API Config
**Location**: `/etc/nginx/sites-available/freshmanna-api.ailabsafrica.com.conf`
- Reverse proxy to port 30037
- CORS enabled for freshmanna.ailabsafrica.com and localhost
- File upload limit: 100MB
- Static file serving from `/opt/kasaai/apps/devotionalflow/backend/storage/`
- Health check endpoint at `/health`

#### Frontend Config
**Location**: `/etc/nginx/sites-available/freshmanna.ailabsafrica.com.conf`
- Serves built files from `/opt/kasaai/apps/devotionalflow/frontend/dist`
- React Router SPA support
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Gzip compression
- Static asset caching (365 days)
- API proxy to backend at `/api/`

### 2. Systemd Service

**Location**: `/etc/systemd/system/kasaai-devotionalflow-backend.service`
- Service name: `kasaai-devotionalflow-backend`
- Runs as user: `dev`
- Auto-restart on failure
- Logs to systemd journal

### 3. Frontend Environment

**Location**: `/opt/kasaai/apps/devotionalflow/frontend/.env.production`
```env
VITE_API_BASE_URL=https://freshmanna-api.ailabsafrica.com
VITE_SUPABASE_URL=https://supabase.ailabsafrica.com
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Automated Deployment

A deployment script has been created that handles the entire setup:

```bash
sudo /tmp/deploy_freshmanna.sh
```

### What the script does:

1. **Builds frontend** - Runs `npm run build` in the frontend directory
2. **Creates temporary HTTP configs** - Sets up nginx without SSL
3. **Enables nginx sites** - Creates symlinks in sites-enabled
4. **Reloads nginx** - Tests and reloads nginx
5. **Obtains SSL certificates** - Requests Let's Encrypt certificates for both domains
6. **Installs final configs** - Replaces temporary configs with SSL-enabled versions
7. **Sets up systemd** - Enables and starts the backend service
8. **Verifies deployment** - Checks health endpoints and service status

## Manual Deployment (Alternative)

If you prefer to deploy manually:

### Step 1: Build Frontend

```bash
cd /opt/kasaai/apps/devotionalflow/frontend
npm run build
```

### Step 2: Set up Nginx (without SSL first)

```bash
# Create temporary configs for SSL certificate generation
sudo cp /tmp/freshmanna-api.ailabsafrica.com.conf /etc/nginx/sites-available/
sudo cp /tmp/freshmanna.ailabsafrica.com.conf /etc/nginx/sites-available/

# Enable sites
sudo ln -sf /etc/nginx/sites-available/freshmanna-api.ailabsafrica.com.conf /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/freshmanna.ailabsafrica.com.conf /etc/nginx/sites-enabled/

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### Step 3: Obtain SSL Certificates

```bash
sudo certbot certonly --nginx \
    -d freshmanna.ailabsafrica.com \
    -d freshmanna-api.ailabsafrica.com \
    --non-interactive \
    --agree-tos \
    --email admin@ailabsafrica.com
```

### Step 4: Update Nginx Configs with SSL

The configs in `/tmp/` already have SSL certificate paths configured. Just copy them again after certificates are obtained.

```bash
sudo cp /tmp/freshmanna-api.ailabsafrica.com.conf /etc/nginx/sites-available/
sudo cp /tmp/freshmanna.ailabsafrica.com.conf /etc/nginx/sites-available/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 5: Set up Backend Service

```bash
# Copy service file
sudo cp /tmp/kasaai-devotionalflow-backend.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable kasaai-devotionalflow-backend
sudo systemctl start kasaai-devotionalflow-backend

# Check status
sudo systemctl status kasaai-devotionalflow-backend
```

## DNS Configuration

**IMPORTANT**: Before deployment, ensure DNS records are configured:

```
A Record:  freshmanna.ailabsafrica.com          → 148.251.0.46
A Record:  freshmanna-api.ailabsafrica.com      → 148.251.0.46
```

Verify DNS propagation:
```bash
nslookup freshmanna.ailabsafrica.com
nslookup freshmanna-api.ailabsafrica.com
```

## Service Management

### View Logs
```bash
sudo journalctl -u kasaai-devotionalflow-backend -f
```

### Restart Service
```bash
sudo systemctl restart kasaai-devotionalflow-backend
```

### Stop Service
```bash
sudo systemctl stop kasaai-devotionalflow-backend
```

### Check Status
```bash
sudo systemctl status kasaai-devotionalflow-backend
```

### Reload Nginx
```bash
sudo systemctl reload nginx
```

## Verification

After deployment, verify:

### 1. Backend Health
```bash
curl http://localhost:30037/health
# Should return: healthy

curl https://freshmanna-api.ailabsafrica.com/health
# Should return: healthy
```

### 2. Frontend
```bash
curl -I https://freshmanna.ailabsafrica.com
# Should return: 200 OK
```

### 3. Service Status
```bash
sudo systemctl status kasaai-devotionalflow-backend
# Should show: active (running)
```

### 4. Nginx Status
```bash
sudo systemctl status nginx
# Should show: active (running)
```

### 5. SSL Certificates
```bash
sudo certbot certificates | grep freshmanna
# Should show certificates for both domains
```

## Troubleshooting

### Backend not starting
```bash
# Check logs
sudo journalctl -u kasaai-devotionalflow-backend -n 50

# Check if port is in use
sudo lsof -i :30037

# Verify .env file exists
ls -la /opt/kasaai/apps/devotionalflow/backend/.env
```

### Nginx errors
```bash
# Test configuration
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/freshmanna-api.error.log
sudo tail -f /var/log/nginx/freshmanna-frontend.error.log
```

### SSL certificate issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificates
sudo certbot renew --dry-run
```

### Frontend not loading
```bash
# Verify build exists
ls -la /opt/kasaai/apps/devotionalflow/frontend/dist/

# Check nginx access logs
sudo tail -f /var/log/nginx/freshmanna-frontend.access.log
```

## Port Allocation

DevotionalFlow uses port **30037** as documented in the infrastructure setup:

```
Port 30027 - Core Backend
Port 30028 - Developer Platform
Port 30030 - ChurchFlow
Port 30031 - StudyFlow
Port 30032 - EventFlow
Port 30033 - InkWave
Port 30035 - Documentation
Port 30036 - Vapi TTS
Port 30037 - DevotionalFlow (FreshManna)  ← This application
Port 30039 - EstateFlow
```

## Database

DevotionalFlow uses MongoDB:
- **Database**: `devotionalflow`
- **Connection**: mongodb://admin:aawwER4444%@127.0.0.1:27017/
- **Credentials**: In `/opt/kasaai/apps/devotionalflow/backend/.env`

## Next Steps

After successful deployment:

1. ✅ Verify DNS points to server (148.251.0.46)
2. ✅ Test API endpoints with Postman/curl
3. ✅ Verify frontend loads and can connect to API
4. ✅ Test authentication flow with Supabase
5. ✅ Monitor logs for errors
6. ✅ Set up monitoring/alerts
7. ✅ Configure backup for MongoDB database

## Related Documentation

- **README**: `/opt/kasaai/apps/devotionalflow/README.md`
- **PRD**: `/opt/kasaai/apps/devotionalflow/PRD.md`
- **Implementation Status**: `/opt/kasaai/apps/devotionalflow/IMPLEMENTATION_STATUS.md`
- **Infrastructure Guide**: `/opt/kasaai/CLAUDE.md`

## Support

For issues or questions:
- **Email**: admin@ailabsafrica.com
- **Infrastructure Docs**: `/opt/kasaai/CLAUDE.md`

---

**Last Updated**: 2025-12-11
**Status**: Ready for deployment
