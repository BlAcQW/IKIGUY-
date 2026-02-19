# EstateFlow Deployment Guide

## Overview
EstateFlow is a modern real estate property management SaaS platform with AI-powered features, multi-currency support, and integrated communication campaigns.

## Server Configuration

### Port Allocation
- **Backend Port**: 30037
- **Service Name**: kasaai-estateflow-backend.service

### Domain Configuration
- **API Domain**: estateflow-api.ailabsafrica.com
- **Frontend Domain**: estateflow.ailabsafrica.com

### Database
- **MongoDB Database**: estateflow
- **Collections**: Will be created automatically on first use

## Deployment Steps

### 1. Install Nginx Configurations

```bash
# Copy nginx configuration files
sudo cp /tmp/estateflow-api.ailabsafrica.com.conf /etc/nginx/sites-available/
sudo cp /tmp/estateflow.ailabsafrica.com.conf /etc/nginx/sites-available/

# Create symbolic links to enable sites
sudo ln -s /etc/nginx/sites-available/estateflow-api.ailabsafrica.com.conf /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/estateflow.ailabsafrica.com.conf /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t
```

### 2. Obtain SSL Certificates

```bash
# Request SSL certificates from Let's Encrypt
sudo certbot --nginx -d estateflow-api.ailabsafrica.com
sudo certbot --nginx -d estateflow.ailabsafrica.com

# Certbot will automatically update the nginx configurations
```

### 3. Install Python Dependencies

```bash
# Activate virtual environment
source /opt/kasaai/apps/venv/bin/activate

# Install backend dependencies
cd /opt/kasaai/apps/estateflow/backend
pip install -r requirements.txt
```

### 4. Install Systemd Service

```bash
# Copy service file
sudo cp /tmp/kasaai-estateflow-backend.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable kasaai-estateflow-backend

# Start the service
sudo systemctl start kasaai-estateflow-backend
```

### 5. Verify Installation

```bash
# Check service status
sudo systemctl status kasaai-estateflow-backend

# View logs
sudo journalctl -u kasaai-estateflow-backend -f

# Test API endpoint
curl https://estateflow-api.ailabsafrica.com/health

# Should return: {"status":"healthy","service":"estateflow","version":"1.0.0"}
```

### 6. Reload Nginx

```bash
# Reload nginx to apply all changes
sudo systemctl reload nginx
```

### 7. Build and Deploy Frontend

```bash
# Navigate to frontend directory
cd /opt/kasaai/apps/estateflow/frontend

# Install dependencies
npm install

# Build for production
npm run build

# The built files will be in /opt/kasaai/apps/estateflow/frontend/dist
# Nginx is already configured to serve from this directory
```

## Configuration Files Location

### Temporary Files (for deployment)
- `/tmp/estateflow-api.ailabsafrica.com.conf` - API nginx config
- `/tmp/estateflow.ailabsafrica.com.conf` - Frontend nginx config
- `/tmp/kasaai-estateflow-backend.service` - Systemd service file

### Installed Files
- `/etc/nginx/sites-available/estateflow-api.ailabsafrica.com.conf`
- `/etc/nginx/sites-available/estateflow.ailabsafrica.com.conf`
- `/etc/nginx/sites-enabled/estateflow-api.ailabsafrica.com.conf` (symlink)
- `/etc/nginx/sites-enabled/estateflow.ailabsafrica.com.conf` (symlink)
- `/etc/systemd/system/kasaai-estateflow-backend.service`

### SSL Certificates (after certbot)
- `/etc/letsencrypt/live/estateflow-api.ailabsafrica.com/fullchain.pem`
- `/etc/letsencrypt/live/estateflow-api.ailabsafrica.com/privkey.pem`
- `/etc/letsencrypt/live/estateflow.ailabsafrica.com/fullchain.pem`
- `/etc/letsencrypt/live/estateflow.ailabsafrica.com/privkey.pem`

## Service Management Commands

```bash
# Start service
sudo systemctl start kasaai-estateflow-backend

# Stop service
sudo systemctl stop kasaai-estateflow-backend

# Restart service
sudo systemctl restart kasaai-estateflow-backend

# Check status
sudo systemctl status kasaai-estateflow-backend

# View logs (real-time)
sudo journalctl -u kasaai-estateflow-backend -f

# View recent logs
sudo journalctl -u kasaai-estateflow-backend -n 100

# View logs for specific time period
sudo journalctl -u kasaai-estateflow-backend --since "1 hour ago"
```

## Nginx Management

```bash
# Test configuration
sudo nginx -t

# Reload (graceful restart)
sudo systemctl reload nginx

# Restart (hard restart)
sudo systemctl restart nginx

# View error logs
sudo tail -f /var/log/nginx/estateflow-api.error.log
sudo tail -f /var/log/nginx/estateflow-frontend.error.log

# View access logs
sudo tail -f /var/log/nginx/estateflow-api.access.log
sudo tail -f /var/log/nginx/estateflow-frontend.access.log
```

## Environment Variables

EstateFlow uses the shared environment file at `/opt/kasaai/.env`. Required variables:

```env
# MongoDB
MONGODB_URL=mongodb://admin:aawwER4444%@127.0.0.1:27017/

# Supabase Authentication
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_KEY=your_supabase_key
SUPABASE_JWT_SECRET=your_jwt_secret

# AI Services
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379
```

## URLs After Deployment

### Production URLs
- **API Documentation**: https://estateflow-api.ailabsafrica.com/docs
- **API ReDoc**: https://estateflow-api.ailabsafrica.com/redoc
- **API Health Check**: https://estateflow-api.ailabsafrica.com/health
- **Frontend Application**: https://estateflow.ailabsafrica.com

### API Endpoints
- **Base URL**: https://estateflow-api.ailabsafrica.com/api/v1
- **Properties**: /api/v1/properties
- **Listings**: /api/v1/listings
- **Campaigns**: /api/v1/campaigns
- **Bookings**: /api/v1/bookings
- **Invoices**: /api/v1/invoices
- **Payments**: /api/v1/payments

## Monitoring

### Health Checks
```bash
# API health check
curl https://estateflow-api.ailabsafrica.com/health

# Expected response:
# {"status":"healthy","service":"estateflow","version":"1.0.0"}
```

### Log Monitoring
```bash
# Monitor all logs
sudo journalctl -u kasaai-estateflow-backend -f

# Monitor only errors
sudo journalctl -u kasaai-estateflow-backend -p err -f

# Monitor nginx errors
sudo tail -f /var/log/nginx/estateflow-api.error.log
```

### Service Status
```bash
# Check if service is running
sudo systemctl is-active kasaai-estateflow-backend

# Check if service is enabled
sudo systemctl is-enabled kasaai-estateflow-backend

# List all kasaai services
sudo systemctl list-units "kasaai-*.service" --all
```

## Troubleshooting

### Service Won't Start
```bash
# Check service logs
sudo journalctl -u kasaai-estateflow-backend -n 50

# Check if port 30037 is already in use
sudo lsof -i :30037

# Verify Python path and dependencies
/opt/kasaai/apps/venv/bin/python -c "import fastapi; print(fastapi.__version__)"
```

### 502 Bad Gateway
```bash
# Check if backend service is running
sudo systemctl status kasaai-estateflow-backend

# Check nginx error logs
sudo tail -f /var/log/nginx/estateflow-api.error.log

# Verify upstream server
curl http://127.0.0.1:30037/health
```

### SSL Certificate Issues
```bash
# Check certificate validity
sudo certbot certificates

# Renew certificates manually
sudo certbot renew

# Test renewal process
sudo certbot renew --dry-run
```

### Database Connection Issues
```bash
# Test MongoDB connection
mongosh "mongodb://admin:aawwER4444%@127.0.0.1:27017/"

# Check if estateflow database exists
mongosh "mongodb://admin:aawwER4444%@127.0.0.1:27017/" --eval "db.adminCommand('listDatabases')"
```

## Rollback Procedure

If deployment fails, rollback steps:

```bash
# Stop the service
sudo systemctl stop kasaai-estateflow-backend
sudo systemctl disable kasaai-estateflow-backend

# Remove nginx configurations
sudo rm /etc/nginx/sites-enabled/estateflow-api.ailabsafrica.com.conf
sudo rm /etc/nginx/sites-enabled/estateflow.ailabsafrica.com.conf
sudo rm /etc/nginx/sites-available/estateflow-api.ailabsafrica.com.conf
sudo rm /etc/nginx/sites-available/estateflow.ailabsafrica.com.conf

# Reload nginx
sudo nginx -t && sudo systemctl reload nginx

# Remove systemd service
sudo rm /etc/systemd/system/kasaai-estateflow-backend.service
sudo systemctl daemon-reload
```

## Updates and Maintenance

### Update Backend Code
```bash
# Pull latest code
cd /opt/kasaai/apps/estateflow/backend
git pull

# Install/update dependencies
source /opt/kasaai/apps/venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart kasaai-estateflow-backend
```

### Update Frontend
```bash
# Pull latest code
cd /opt/kasaai/apps/estateflow/frontend
git pull

# Install dependencies
npm install

# Build for production
npm run build

# No restart needed - nginx serves static files
```

## Security Considerations

1. **SSL/TLS**: All traffic encrypted via Let's Encrypt certificates
2. **CORS**: Configured to allow only specific domains
3. **Authentication**: Supabase JWT-based authentication
4. **Authorization**: Organization-scoped data access
5. **Input Validation**: Pydantic models validate all inputs
6. **Rate Limiting**: Consider implementing rate limiting for production

## Post-Deployment Checklist

- [ ] Backend service is running and healthy
- [ ] Frontend is accessible and loads correctly
- [ ] SSL certificates are valid and auto-renew is configured
- [ ] API documentation is accessible at /docs
- [ ] Health check endpoint returns 200 OK
- [ ] MongoDB database is created and accessible
- [ ] Nginx logs are being written correctly
- [ ] Service logs are being written to journald
- [ ] CORS is configured correctly for frontend domain
- [ ] Environment variables are set correctly
- [ ] Service starts automatically on server reboot

## Support

For issues or questions:
- Check logs: `sudo journalctl -u kasaai-estateflow-backend -f`
- Review README: `/opt/kasaai/apps/estateflow/backend/README.md`
- Check infrastructure docs: `/opt/kasaai/CLAUDE.md`

---

**Deployment Date**: December 7, 2025
**Version**: 1.0.0
**Status**: Configuration files created, ready for deployment
