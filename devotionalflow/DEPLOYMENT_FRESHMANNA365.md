# FreshManna365.com Domain Deployment

> Deployment Date: December 20, 2025
> Status: ✅ Production Ready

---

## 📋 Overview

This document details the deployment of the DevotionalFlow application (FreshManna) to the **freshmanna365.com** domain with full HTTPS support.

## 🌐 Domains & URLs

### Production URLs
- **Frontend (Primary)**: https://freshmanna365.com
- **Frontend (WWW)**: https://www.freshmanna365.com
- **Backend API (Primary)**: https://api.freshmanna365.com

### Secondary URLs (Still Active)
- **Frontend (Secondary)**: https://freshmanna.ailabsafrica.com
- **Backend API (Secondary)**: https://freshmanna-api.ailabsafrica.com

### Local Configuration
- **Backend Port**: 30042 (localhost only, proxied via nginx)
- **Backend Service**: kasaai-devotionalflow-backend.service
- **Frontend Files**: /opt/kasaai/apps/devotionalflow/frontend/dist

---

## 🔐 SSL Certificates

All SSL certificates are managed by **Let's Encrypt** with automatic renewal.

### Certificate Details

**1. freshmanna365.com**
- Domains: freshmanna365.com, www.freshmanna365.com
- Expires: March 20, 2026
- Certificate Path: `/etc/letsencrypt/live/freshmanna365.com/fullchain.pem`
- Private Key: `/etc/letsencrypt/live/freshmanna365.com/privkey.pem`

**2. api.freshmanna365.com**
- Domains: api.freshmanna365.com
- Expires: March 20, 2026
- Certificate Path: `/etc/letsencrypt/live/api.freshmanna365.com/fullchain.pem`
- Private Key: `/etc/letsencrypt/live/api.freshmanna365.com/privkey.pem`

### Renewal
Certbot has set up automatic renewal via systemd timer. Certificates will auto-renew 30 days before expiration.

---

## 📝 Nginx Configuration

### Configuration Files

**Frontend Configuration**
- Path: `/etc/nginx/sites-available/freshmanna365.com.conf`
- Symlink: `/etc/nginx/sites-enabled/freshmanna365.com.conf`
- Features:
  - HTTP to HTTPS redirect
  - React SPA routing (try_files)
  - Static asset caching (365 days)
  - Gzip compression
  - Security headers (CSP, HSTS, X-Frame-Options)
  - API proxy to backend (port 30042)
  - CORS headers for Pexels images
  - CSP allows both api.freshmanna365.com and freshmanna-api.ailabsafrica.com (backward compatible)

**Backend API Configuration**
- Path: `/etc/nginx/sites-available/api.freshmanna365.com.conf`
- Symlink: `/etc/nginx/sites-enabled/api.freshmanna365.com.conf`
- Features:
  - HTTP to HTTPS redirect
  - Upstream backend pool (127.0.0.1:30042)
  - CORS headers for frontend domains
  - WebSocket support
  - Large file uploads (100MB max)
  - Static storage serving (/storage/)
  - Health check endpoint (/health)

### CORS Configuration

The backend API allows cross-origin requests from:
- https://freshmanna365.com
- https://www.freshmanna365.com
- https://freshmanna.ailabsafrica.com
- http://localhost:* (development)

---

## 🚀 Deployment Process

### Step-by-Step Deployment

1. **Created Nginx Configuration Files**
   ```bash
   # Frontend config
   /etc/nginx/sites-available/freshmanna365.com.conf

   # Backend API config
   /etc/nginx/sites-available/api.freshmanna365.com.conf
   ```

2. **Enabled Sites**
   ```bash
   sudo ln -sf /etc/nginx/sites-available/freshmanna365.com.conf /etc/nginx/sites-enabled/
   sudo ln -sf /etc/nginx/sites-available/api.freshmanna365.com.conf /etc/nginx/sites-enabled/
   ```

3. **Tested Nginx Configuration**
   ```bash
   sudo nginx -t
   ```

4. **Obtained SSL Certificates**
   ```bash
   # Frontend certificates (freshmanna365.com + www)
   sudo certbot certonly --webroot -w /var/www/letsencrypt \
     -d freshmanna365.com -d www.freshmanna365.com \
     --non-interactive --agree-tos --email admin@ailabsafrica.com

   # Backend API certificate
   sudo certbot certonly --webroot -w /var/www/letsencrypt \
     -d api.freshmanna365.com \
     --non-interactive --agree-tos --email admin@ailabsafrica.com
   ```

5. **Reloaded Nginx**
   ```bash
   sudo systemctl reload nginx
   ```

---

## 🧪 Testing & Verification

### Manual Testing

**1. Frontend Access**
```bash
curl -I https://freshmanna365.com
# Should return: 200 OK
```

**2. API Health Check**
```bash
curl https://api.freshmanna365.com/health
# Should return: healthy
```

**3. SSL Certificate Verification**
```bash
# Check frontend certificate
openssl s_client -connect freshmanna365.com:443 -servername freshmanna365.com

# Check API certificate
openssl s_client -connect api.freshmanna365.com:443 -servername api.freshmanna365.com
```

**4. CORS Verification**
```bash
curl -H "Origin: https://freshmanna365.com" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS https://api.freshmanna365.com/api/v1/devotionals/
```

---

## 🔧 Maintenance

### Certificate Renewal

Certificates auto-renew via systemd timer. To manually renew:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

### Nginx Configuration Updates

When updating nginx configs:

```bash
# Edit the config
sudo nano /etc/nginx/sites-available/freshmanna365.com.conf

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### View Logs

**Nginx Logs**
```bash
# Frontend access log
sudo tail -f /var/log/nginx/freshmanna365-frontend.access.log

# Frontend error log
sudo tail -f /var/log/nginx/freshmanna365-frontend.error.log

# API access log
sudo tail -f /var/log/nginx/freshmanna365-api.access.log

# API error log
sudo tail -f /var/log/nginx/freshmanna365-api.error.log
```

**Backend Service Logs**
```bash
sudo journalctl -u kasaai-devotionalflow-backend -f
```

---

## 🔒 Security Features

### Frontend Security Headers

- **HSTS**: Enforces HTTPS for 1 year
- **X-Content-Type-Options**: Prevents MIME sniffing
- **X-Frame-Options**: Prevents clickjacking
- **Content-Security-Policy**: Controls resource loading
- **Referrer-Policy**: Controls referrer information

### Backend Security

- **CORS**: Restricted to specific origins
- **HTTPS Only**: All HTTP requests redirect to HTTPS
- **File Upload Limits**: 100MB maximum
- **Timeout Protection**: 60s connect, 300s send/read

---

## 📊 Monitoring

### Health Checks

**Backend Health**
```bash
curl https://api.freshmanna365.com/health
```

**Frontend Availability**
```bash
curl -I https://freshmanna365.com
```

**Service Status**
```bash
sudo systemctl status kasaai-devotionalflow-backend
sudo systemctl status nginx
```

### SSL Expiry Monitoring

```bash
# List all certificates
sudo certbot certificates

# Check specific certificate
sudo certbot certificates | grep freshmanna365
```

---

## 🐛 Troubleshooting

### Common Issues

**1. 502 Bad Gateway**
- Check backend service: `sudo systemctl status kasaai-devotionalflow-backend`
- Check backend logs: `sudo journalctl -u kasaai-devotionalflow-backend -n 50`
- Verify port 30042 is listening: `sudo lsof -i :30042`

**2. SSL Certificate Errors**
- Verify certificate exists: `sudo ls -l /etc/letsencrypt/live/freshmanna365.com/`
- Test nginx config: `sudo nginx -t`
- Check certbot logs: `sudo cat /var/log/letsencrypt/letsencrypt.log`

**3. CORS Errors**
- Check API nginx config CORS headers
- Verify origin is in allowed list
- Check browser console for specific error

**4. Static Assets Not Loading**
- Verify frontend build: `ls -l /opt/kasaai/apps/devotionalflow/frontend/dist/`
- Check nginx static file permissions
- Clear browser cache

---

## 📁 File Locations

### Nginx Configuration
- `/etc/nginx/sites-available/freshmanna365.com.conf`
- `/etc/nginx/sites-available/api.freshmanna365.com.conf`
- `/etc/nginx/sites-enabled/freshmanna365.com.conf` (symlink)
- `/etc/nginx/sites-enabled/api.freshmanna365.com.conf` (symlink)

### SSL Certificates
- `/etc/letsencrypt/live/freshmanna365.com/`
- `/etc/letsencrypt/live/api.freshmanna365.com/`

### Application Files
- **Backend**: `/opt/kasaai/apps/devotionalflow/backend/`
- **Frontend**: `/opt/kasaai/apps/devotionalflow/frontend/`
- **Frontend Build**: `/opt/kasaai/apps/devotionalflow/frontend/dist/`
- **Service File**: `/etc/systemd/system/kasaai-devotionalflow-backend.service`

### Logs
- `/var/log/nginx/freshmanna365-frontend.access.log`
- `/var/log/nginx/freshmanna365-frontend.error.log`
- `/var/log/nginx/freshmanna365-api.access.log`
- `/var/log/nginx/freshmanna365-api.error.log`
- Systemd logs: `sudo journalctl -u kasaai-devotionalflow-backend`

---

## ✅ Deployment Checklist

- [x] Nginx frontend configuration created
- [x] Nginx backend API configuration created
- [x] Configurations symlinked to sites-enabled
- [x] Nginx configuration tested
- [x] SSL certificate obtained for freshmanna365.com
- [x] SSL certificate obtained for www.freshmanna365.com
- [x] SSL certificate obtained for api.freshmanna365.com
- [x] Nginx reloaded with SSL enabled
- [x] Frontend accessible via HTTPS
- [x] Backend API accessible via HTTPS
- [x] CORS properly configured
- [x] Documentation updated
- [x] README.md updated with new domains

---

## 📞 Support

For issues or questions:
- Check logs first (nginx and backend service)
- Review this deployment documentation
- Contact DevOps team: admin@ailabsafrica.com

---

**Deployment completed successfully on December 20, 2025** ✅

### Post-Deployment Fixes

**CSP Header Update (Dec 20, 2025)**
- Added `freshmanna-api.ailabsafrica.com` to Content-Security-Policy
- Ensures backward compatibility with existing API domain
- Allows seamless transition for existing users
