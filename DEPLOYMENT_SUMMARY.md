# KasaAI Apps Deployment Summary

## 📦 Applications Deployed

This document summarizes the deployment configuration for all 4 new KasaAI applications.

### 1. InkWave (Interactive AI Bookshop)
- **Domain**: inkwave.ailabsafrica.com
- **Backend Port**: 30029
- **Service**: kasaai-inkwave.service
- **Frontend Path**: /var/www/inkwave/frontend/dist
- **Nginx Config**: /etc/nginx/sites-available/inkwave.ailabsafrica.com.conf

### 2. ChurchFlow (Church Management)
- **Domain**: churchflow.ailabsafrica.com
- **Backend Port**: 30030
- **Service**: kasaai-churchflow.service
- **Frontend Path**: /var/www/churchflow/frontend/dist
- **Nginx Config**: /etc/nginx/sites-available/churchflow.ailabsafrica.com.conf

### 3. StudyFlow (Personal Tutor)
- **Domain**: studyflow.ailabsafrica.com
- **Backend Port**: 30031
- **Service**: kasaai-studyflow.service
- **Frontend Path**: /var/www/studyflow/frontend/dist
- **Nginx Config**: /etc/nginx/sites-available/studyflow.ailabsafrica.com.conf

### 4. EventFlow (Event Manager)
- **Domain**: eventflow.ailabsafrica.com
- **Backend Port**: 30032
- **Service**: kasaai-eventflow.service
- **Frontend Path**: /var/www/eventflow/frontend/dist
- **Nginx Config**: /etc/nginx/sites-available/eventflow.ailabsafrica.com.conf

---

## 🚀 Complete Deployment Steps

### Step 1: Build Frontends

```bash
# Build all frontends
cd /opt/kasaai/apps/inkwave/frontend && npm install && npm run build
cd /opt/kasaai/apps/churchflow/frontend && npm install && npm run build
cd /opt/kasaai/apps/studyflow/frontend && npm install && npm run build
cd /opt/kasaai/apps/eventflow/frontend && npm install && npm run build
```

### Step 2: Create Frontend Deployment Directories

```bash
# Create directories
sudo mkdir -p /var/www/{inkwave,churchflow,studyflow,eventflow}/frontend/dist
sudo chown -R dev:www-data /var/www/{inkwave,churchflow,studyflow,eventflow}

# Copy dist files
cp -r /opt/kasaai/apps/inkwave/frontend/dist/* /var/www/inkwave/frontend/dist/
cp -r /opt/kasaai/apps/churchflow/frontend/dist/* /var/www/churchflow/frontend/dist/
cp -r /opt/kasaai/apps/studyflow/frontend/dist/* /var/www/studyflow/frontend/dist/
cp -r /opt/kasaai/apps/eventflow/frontend/dist/* /var/www/eventflow/frontend/dist/
```

### Step 3: Setup DNS Records

Configure DNS A records to point to this server's IP:

```
inkwave.ailabsafrica.com    -> [SERVER_IP]
churchflow.ailabsafrica.com -> [SERVER_IP]
studyflow.ailabsafrica.com  -> [SERVER_IP]
eventflow.ailabsafrica.com  -> [SERVER_IP]
```

### Step 4: Generate SSL Certificates

**IMPORTANT**: Only run after DNS records are configured!

```bash
# InkWave
sudo certbot certonly --nginx -d inkwave.ailabsafrica.com -d www.inkwave.ailabsafrica.com

# ChurchFlow
sudo certbot certonly --nginx -d churchflow.ailabsafrica.com -d www.churchflow.ailabsafrica.com

# StudyFlow
sudo certbot certonly --nginx -d studyflow.ailabsafrica.com -d www.studyflow.ailabsafrica.com

# EventFlow
sudo certbot certonly --nginx -d eventflow.ailabsafrica.com -d www.eventflow.ailabsafrica.com
```

### Step 5: Enable Nginx Sites

```bash
# Enable all sites
sudo ln -s /etc/nginx/sites-available/inkwave.ailabsafrica.com.conf /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/churchflow.ailabsafrica.com.conf /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/studyflow.ailabsafrica.com.conf /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/eventflow.ailabsafrica.com.conf /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Step 6: Install Backend Dependencies

```bash
# Use shared venv
cd /opt/kasaai
/opt/kasaai/apps/venv/bin/pip install -r apps/inkwave/backend/requirements.txt
/opt/kasaai/apps/venv/bin/pip install -r apps/churchflow/backend/requirements.txt
/opt/kasaai/apps/venv/bin/pip install -r apps/studyflow/backend/requirements.txt
/opt/kasaai/apps/venv/bin/pip install -r apps/eventflow/backend/requirements.txt
```

### Step 7: Start Backend Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start all services
sudo systemctl enable kasaai-inkwave.service
sudo systemctl start kasaai-inkwave.service

sudo systemctl enable kasaai-churchflow.service
sudo systemctl start kasaai-churchflow.service

sudo systemctl enable kasaai-studyflow.service
sudo systemctl start kasaai-studyflow.service

sudo systemctl enable kasaai-eventflow.service
sudo systemctl start kasaai-eventflow.service

# Check all services status
sudo systemctl status kasaai-inkwave.service
sudo systemctl status kasaai-churchflow.service
sudo systemctl status kasaai-studyflow.service
sudo systemctl status kasaai-eventflow.service
```

---

## 🔍 Health Checks

```bash
# Backend health checks
curl http://localhost:30029/health  # InkWave
curl http://localhost:30030/health  # ChurchFlow
curl http://localhost:30031/health  # StudyFlow
curl http://localhost:30032/health  # EventFlow

# Frontend health checks
curl https://inkwave.ailabsafrica.com
curl https://churchflow.ailabsafrica.com
curl https://studyflow.ailabsafrica.com
curl https://eventflow.ailabsafrica.com
```

---

## 📊 Monitoring

```bash
# View all backend logs in real-time
sudo journalctl -f -u kasaai-inkwave.service -u kasaai-churchflow.service -u kasaai-studyflow.service -u kasaai-eventflow.service

# View nginx logs
sudo tail -f /var/log/nginx/inkwave.ailabsafrica.access.log
sudo tail -f /var/log/nginx/churchflow.ailabsafrica.access.log
sudo tail -f /var/log/nginx/studyflow.ailabsafrica.access.log
sudo tail -f /var/log/nginx/eventflow.ailabsafrica.access.log
```

---

## 🔄 Updating Applications

### Backend Update

```bash
# Stop service
sudo systemctl stop kasaai-inkwave.service

# Pull latest changes
cd /opt/kasaai
git pull

# Restart service
sudo systemctl start kasaai-inkwave.service
```

### Frontend Update

```bash
# Rebuild
cd /opt/kasaai/apps/inkwave/frontend
npm run build

# Copy to deployment directory
cp -r dist/* /var/www/inkwave/frontend/dist/
```

---

## 🛠️ Troubleshooting

### Backend won't start
```bash
# Check logs
sudo journalctl -u kasaai-inkwave.service -n 100

# Check if port is already in use
sudo lsof -i :30029

# Check venv path
ls -la /opt/kasaai/apps/venv/bin/python
```

### Frontend shows 502 Bad Gateway
- Backend service is not running
- Check `sudo systemctl status kasaai-inkwave.service`

### SSL Certificate Issues
```bash
# Check certificate
sudo ls -la /etc/letsencrypt/live/inkwave.ailabsafrica.com/

# Test renewal
sudo certbot renew --dry-run
```

---

## 📝 Next Steps

1. **Test each application** in the browser
2. **Monitor backend logs** for any errors
3. **Set up automatic SSL renewal** (certbot auto-renews)
4. **Configure monitoring** (Prometheus, Grafana, etc.)
5. **Set up backups** for MongoDB data
6. **Document API endpoints** for each backend

---

## ✅ Checklist

- [ ] DNS records configured
- [ ] SSL certificates generated
- [ ] Nginx sites enabled
- [ ] Backend services running
- [ ] Frontends built and deployed
- [ ] Health checks passing
- [ ] Logs being monitored
- [ ] Environment variables set

---

**Created**: 2025-10-24
**Deployed By**: Claude Code
**Maintained By**: KasaAI Team
