# African Language Community Platform - Production Deployment

This directory contains all the necessary files and scripts for deploying the African Language Community Platform to production.

## 🚀 Quick Start

### Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Root or sudo access
- Domain names configured (language-community.ailabsafrica.com, language-community-api.ailabsafrica.com)
- Basic dependencies: nginx, python3, nodejs, mongodb

### Deployment

1. **Run the deployment script:**
   ```bash
   sudo ./deploy.sh
   ```

2. **Configure environment variables:**
   ```bash
   sudo systemctl edit language-community-api
   ```
   Add your production environment variables.

3. **Start services:**
   ```bash
   sudo systemctl start language-community-api
   sudo systemctl reload nginx
   ```

## 📁 File Structure

```
deployment/
├── deploy.sh                          # Main deployment script
├── backup.sh                          # Automated backup script
├── language-community-api.service     # Systemd service file
├── language-community.ailabsafrica.conf            # Frontend nginx config
├── language-community-api.ailabsafrica.conf        # API nginx config
├── monitoring/
│   ├── prometheus.yml                 # Prometheus configuration
│   ├── language_community_rules.yml   # Alerting rules
│   └── grafana-dashboard.json         # Grafana dashboard
└── README.md                          # This file
```

## 🔧 Configuration Files

### Systemd Service

**File:** `language-community-api.service`

The systemd service runs the FastAPI backend with the following features:
- Automatic restart on failure
- Resource limits (2GB RAM, 200% CPU)
- Security hardening
- Proper logging

**Installation:**
```bash
sudo cp language-community-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable language-community-api
```

### Nginx Configuration

**Frontend Config:** `language-community.ailabsafrica.conf`
- Serves React frontend from `/opt/kasaai/apps/community/frontend-main/dist`
- Proxies API calls to backend
- SSL termination with security headers
- Gzip compression and asset caching
- PWA support with service worker handling

**API Config:** `language-community-api.ailabsafrica.conf`
- Dedicated API server configuration
- Rate limiting and security headers
- CORS configuration
- Large file upload support
- WebSocket proxy for real-time features

**Installation:**
```bash
sudo cp *.ailabsafrica.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/language-community.ailabsafrica.conf /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/language-community-api.ailabsafrica.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## 🔒 SSL Certificates

The deployment script automatically obtains SSL certificates using Let's Encrypt:

```bash
# Manual certificate generation
sudo certbot certonly --webroot \
  -w /var/www/certbot \
  -d language-community.ailabsafrica.com \
  -d language-community-api.ailabsafrica.com
```

Auto-renewal is configured via crontab.

## 📊 Monitoring

### Prometheus

**File:** `monitoring/prometheus.yml`

Monitors:
- API metrics (requests, latency, errors)
- System metrics (CPU, memory, disk)
- MongoDB metrics
- Nginx metrics

### Grafana Dashboard

**File:** `monitoring/grafana-dashboard.json`

Includes:
- API health overview
- Community engagement metrics
- System resource usage
- Language distribution
- Dataset processing status

### Alerts

**File:** `monitoring/language_community_rules.yml`

Alerts for:
- API downtime
- High error rates
- Resource exhaustion
- MongoDB issues
- SSL certificate expiry

## 💾 Backup Strategy

### Automated Backups

**Script:** `backup.sh`

Features:
- MongoDB database dumps
- File upload backups
- Configuration backups
- S3 upload support
- Automated cleanup
- Integrity verification

**Schedule:** Add to crontab for daily backups:
```bash
0 2 * * * /opt/kasaai/apps/community/deployment/backup.sh
```

### Manual Backup

```bash
# Run backup manually
sudo ./backup.sh

# Verify backups only
sudo ./backup.sh --verify-only

# Cleanup old backups
sudo ./backup.sh --cleanup-only
```

## 🔍 Health Checks

### API Health

```bash
curl https://language-community-api.ailabsafrica.com/health
```

### System Status

```bash
sudo systemctl status language-community-api
sudo systemctl status nginx
sudo systemctl status mongod
```

### Log Files

```bash
# API logs
sudo journalctl -u language-community-api -f

# Nginx logs
sudo tail -f /var/log/nginx/language-community*.log

# Application logs
sudo tail -f /opt/kasaai/data/community/logs/*.log
```

## 🚨 Troubleshooting

### Common Issues

1. **API not starting:**
   ```bash
   sudo systemctl status language-community-api
   sudo journalctl -u language-community-api --no-pager -l
   ```

2. **Database connection issues:**
   ```bash
   sudo systemctl status mongod
   mongosh --eval "db.adminCommand('ping')"
   ```

3. **SSL certificate issues:**
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

4. **High resource usage:**
   ```bash
   top -p $(pgrep -f language-community-api)
   df -h /opt/kasaai/data/community
   ```

### Log Analysis

```bash
# Check for errors in API logs
sudo journalctl -u language-community-api | grep ERROR

# Monitor real-time API activity
sudo journalctl -u language-community-api -f | grep -E "(POST|PUT|DELETE)"

# Check nginx error logs
sudo grep ERROR /var/log/nginx/language-community*.log
```

## 🔧 Maintenance

### Updates

1. **Backend updates:**
   ```bash
   cd /opt/kasaai/apps/community/backend
   git pull
   source venv/bin/activate
   pip install -r requirements.txt
   sudo systemctl restart language-community-api
   ```

2. **Frontend updates:**
   ```bash
   cd /opt/kasaai/apps/community/frontend-main
   git pull
   npm ci
   npm run build
   sudo systemctl reload nginx
   ```

### Database Maintenance

```bash
# MongoDB index optimization
mongosh language_community --eval "db.runCommand({reIndex: 'submissions'})"

# Database size check
mongosh language_community --eval "db.stats(1024*1024)"
```

### Performance Tuning

1. **Nginx worker processes:**
   ```nginx
   worker_processes auto;
   worker_connections 1024;
   ```

2. **API worker count:**
   Adjust `--workers` parameter in systemd service based on CPU cores.

3. **MongoDB optimization:**
   ```javascript
   // Enable profiling for slow queries
   db.setProfilingLevel(1, { slowms: 100 })
   ```

## 📈 Scaling

### Horizontal Scaling

1. **Load balancer setup:**
   - Use nginx upstream for multiple API instances
   - Session affinity for WebSocket connections

2. **Database scaling:**
   - MongoDB replica sets
   - Read replicas for analytics

### Vertical Scaling

1. **Resource limits:**
   - Adjust systemd service memory/CPU limits
   - MongoDB memory allocation
   - Nginx worker processes

## 🔐 Security

### Security Headers

Both nginx configurations include comprehensive security headers:
- HSTS
- Content Security Policy
- X-Frame-Options
- X-Content-Type-Options

### Rate Limiting

API endpoints have rate limiting configured:
- General API: 100 requests/minute
- File uploads: 10 requests/minute

### File Upload Security

- Size limits: 500MB for datasets, 100MB for general uploads
- File type validation
- Virus scanning (recommended to add)

## 📞 Support

For deployment issues:
1. Check logs first
2. Verify service status
3. Run health checks
4. Review monitoring dashboards
5. Check backup integrity

For additional help, refer to the main project documentation or contact the development team.

---

**Last Updated:** $(date +%Y-%m-%d)
**Version:** 1.0.0