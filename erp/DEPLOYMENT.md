# ERP System Deployment Guide

**Server**: Dev Server (85.214.12.174)
**Last Updated**: 2025-02-11

---

## Pre-Deployment Checklist

### 1. Authentication Setup

- [ ] Create users in Supabase:
  - [ ] admin@ailabsafrica.com
  - [ ] user@ailabsafrica.com
- [ ] Create corresponding email accounts in iRedMail
- [ ] Get Supabase user UUIDs
- [ ] Update UNIVERSAL_ADMIN_USER_IDS in backend .env

### 2. Verify Prerequisites

```bash
# Check MongoDB is running
sudo systemctl status mongod

# Check Supabase is accessible
curl https://supabase.ailabsafrica.com/health

# Check nginx is installed
nginx -v

# Check Python version
python3 --version  # Should be 3.9+

# Check Node.js version
node --version  # Should be 18+
```

---

## Step 1: Backend Deployment

### 1.1 Install Dependencies

```bash
cd /opt/kasaai/apps/erp/backend

# Use shared virtual environment
source /opt/kasaai/apps/venv/bin/activate

# Install requirements
/opt/kasaai/apps/venv/bin/pip install -r requirements.txt
```

### 1.2 Configure Environment

```bash
# Edit .env file
nano /opt/kasaai/apps/erp/backend/.env

# Update these values:
# - SUPABASE_SERVICE_ROLE_KEY (get from Supabase dashboard)
# - UNIVERSAL_ADMIN_USER_IDS (get from Supabase users table)
```

### 1.3 Test Backend Locally

```bash
# Start backend
cd /opt/kasaai/apps/erp/backend
/opt/kasaai/apps/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 30034

# Test in another terminal
curl http://localhost:30034/
curl http://localhost:30034/health
```

Expected response:
```json
{
  "app": "KasaAI ERP",
  "version": "1.0.0",
  "status": "active"
}
```

### 1.4 Set Up Systemd Service

```bash
# Copy service file
sudo cp /opt/kasaai/apps/erp/kasaai-erp-backend.service /etc/systemd/system/

# Set correct permissions
sudo chown root:root /etc/systemd/system/kasaai-erp-backend.service
sudo chmod 644 /etc/systemd/system/kasaai-erp-backend.service

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable kasaai-erp-backend

# Start service
sudo systemctl start kasaai-erp-backend

# Check status
sudo systemctl status kasaai-erp-backend

# View logs
sudo journalctl -u kasaai-erp-backend -f
```

---

## Step 2: Frontend Deployment

### 2.1 Install Dependencies

```bash
cd /opt/kasaai/apps/erp/frontend

# Install Node modules
npm install
```

### 2.2 Configure Environment

```bash
# Edit .env file
nano /opt/kasaai/apps/erp/frontend/.env

# Verify:
VITE_API_BASE_URL=https://dev-erp-api.ailabsafrica.com/api/v1
VITE_SUPABASE_URL=https://supabase.ailabsafrica.com
VITE_SUPABASE_ANON_KEY=<your-anon-key>
```

### 2.3 Build Frontend

```bash
cd /opt/kasaai/apps/erp/frontend

# Build for production
npm run build

# Verify dist folder created
ls -la dist/
```

### 2.4 Set Permissions

```bash
# Set ownership to www-data
sudo chown -R www-data:www-data /opt/kasaai/apps/erp/frontend/dist

# Set read permissions
sudo chmod -R 755 /opt/kasaai/apps/erp/frontend/dist
```

---

## Step 3: Nginx Configuration

### 3.1 Install Nginx Configs

```bash
# Copy config files
sudo cp /opt/kasaai/apps/erp/nginx-dev-api.conf /etc/nginx/sites-available/dev-erp-api.ailabsafrica.com.conf
sudo cp /opt/kasaai/apps/erp/nginx-dev-frontend.conf /etc/nginx/sites-available/dev-erp.ailabsafrica.com.conf

# Create symbolic links
sudo ln -s /etc/nginx/sites-available/dev-erp-api.ailabsafrica.com.conf /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/dev-erp.ailabsafrica.com.conf /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t
```

### 3.2 Configure DNS (If Needed)

Ensure DNS points to dev server:
```
dev-erp.ailabsafrica.com -> 85.214.12.174
dev-erp-api.ailabsafrica.com -> 85.214.12.174
```

---

## Step 4: SSL Certificates

### 4.1 Obtain Certificates

```bash
# Install certbot (if not already installed)
sudo apt install certbot python3-certbot-nginx

# Obtain certificates for both domains
sudo certbot --nginx -d dev-erp.ailabsafrica.com -d dev-erp-api.ailabsafrica.com

# Follow prompts:
# - Enter email: admin@ailabsafrica.com
# - Agree to terms: Yes
# - Share email: No
# - Redirect HTTP to HTTPS: Yes
```

### 4.2 Verify SSL

```bash
# Test certificate
sudo certbot certificates

# Test auto-renewal
sudo certbot renew --dry-run
```

### 4.3 Reload Nginx

```bash
sudo systemctl reload nginx
```

---

## Step 5: Create Default Organization

### 5.1 Via API

```bash
# Get JWT token first
TOKEN=$(curl -X POST https://supabase.ailabsafrica.com/auth/v1/token?grant_type=password \
  -H "apikey: <SUPABASE_ANON_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ailabsafrica.com",
    "password": "Admin@2024!"
  }' | jq -r '.access_token')

# Create default organization
curl -X POST https://dev-erp-api.ailabsafrica.com/api/v1/organizations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "AI Labs Africa",
    "description": "Default organization for AI Labs Africa"
  }'
```

### 5.2 Via Frontend

1. Navigate to https://dev-erp.ailabsafrica.com
2. Login with admin@ailabsafrica.com
3. Go to Admin > Organizations
4. Click "New Organization"
5. Enter details and create

---

## Step 6: Testing

### 6.1 Backend Tests

```bash
# Test health endpoint
curl https://dev-erp-api.ailabsafrica.com/health

# Test authentication
curl https://dev-erp-api.ailabsafrica.com/api/v1/organizations \
  -H "Authorization: Bearer <token>"
```

### 6.2 Frontend Tests

1. **Login Page**
   - Navigate to https://dev-erp.ailabsafrica.com
   - Should see login form
   - Test with admin@ailabsafrica.com

2. **Dashboard**
   - Should redirect to dashboard after login
   - Should see stats and quick actions

3. **Admin Page**
   - Navigate to Admin
   - Should see Organizations tab
   - Should see Users tab
   - Test creating organization

4. **CRM Page**
   - Navigate to CRM
   - Should see customer list (empty initially)
   - Test "New Customer" button

5. **Organization Switching**
   - Create multiple organizations
   - Use dropdown in top nav to switch
   - Verify data filters by organization

### 6.3 Authentication Tests

```bash
# Test admin login
curl -X POST https://supabase.ailabsafrica.com/auth/v1/token?grant_type=password \
  -H "apikey: <SUPABASE_ANON_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@ailabsafrica.com",
    "password": "Admin@2024!"
  }'

# Test user login
curl -X POST https://supabase.ailabsafrica.com/auth/v1/token?grant_type=password \
  -H "apikey: <SUPABASE_ANON_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@ailabsafrica.com",
    "password": "User@2024!"
  }'
```

---

## Step 7: Monitoring

### 7.1 Service Status

```bash
# Check backend service
sudo systemctl status kasaai-erp-backend

# Check nginx
sudo systemctl status nginx

# Check MongoDB
sudo systemctl status mongod
```

### 7.2 View Logs

```bash
# Backend logs
sudo journalctl -u kasaai-erp-backend -f

# Nginx access logs
sudo tail -f /var/log/nginx/dev-erp-api_access.log
sudo tail -f /var/log/nginx/dev-erp_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/dev-erp-api_error.log
sudo tail -f /var/log/nginx/dev-erp_error.log
```

### 7.3 Monitor Resources

```bash
# Check port 30034 is listening
sudo lsof -i :30034

# Check disk space
df -h

# Check memory
free -h

# Check processes
ps aux | grep uvicorn
```

---

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
sudo journalctl -u kasaai-erp-backend -n 50

# Common issues:
# 1. MongoDB not running
sudo systemctl start mongod

# 2. Port already in use
sudo lsof -i :30034
sudo kill -9 <PID>

# 3. Python dependencies missing
source /opt/kasaai/apps/venv/bin/activate
pip install -r /opt/kasaai/apps/erp/backend/requirements.txt

# 4. Permission issues
sudo chown -R www-data:www-data /opt/kasaai/apps/erp/backend
```

### Frontend Not Loading

```bash
# Check nginx config
sudo nginx -t

# Check if dist folder exists
ls -la /opt/kasaai/apps/erp/frontend/dist

# Rebuild frontend
cd /opt/kasaai/apps/erp/frontend
npm run build

# Check permissions
sudo chown -R www-data:www-data /opt/kasaai/apps/erp/frontend/dist
```

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Check nginx config after certbot
sudo nginx -t
sudo systemctl reload nginx
```

### Authentication Errors

```bash
# Check Supabase URL is accessible
curl https://supabase.ailabsafrica.com/health

# Verify .env configuration
cat /opt/kasaai/apps/erp/backend/.env | grep SUPABASE

# Check user exists in Supabase
# (via Supabase dashboard or SQL)

# Test with curl
curl -X POST https://supabase.ailabsafrica.com/auth/v1/token?grant_type=password \
  -H "apikey: <SUPABASE_ANON_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@ailabsafrica.com", "password": "Admin@2024!"}'
```

### CORS Errors

```bash
# Check nginx CORS headers
curl -I https://dev-erp-api.ailabsafrica.com

# Should see:
# Access-Control-Allow-Origin: https://dev-erp.ailabsafrica.com
# Access-Control-Allow-Credentials: true

# Update nginx config if needed
sudo nano /etc/nginx/sites-available/dev-erp-api.ailabsafrica.com.conf
sudo nginx -t
sudo systemctl reload nginx
```

---

## Rollback Procedure

If deployment fails:

```bash
# 1. Stop backend service
sudo systemctl stop kasaai-erp-backend

# 2. Remove nginx configs
sudo rm /etc/nginx/sites-enabled/dev-erp-api.ailabsafrica.com.conf
sudo rm /etc/nginx/sites-enabled/dev-erp.ailabsafrica.com.conf
sudo systemctl reload nginx

# 3. Restore from backup (if available)
# 4. Check logs for errors
sudo journalctl -u kasaai-erp-backend -n 100
```

---

## Post-Deployment

### 1. Update Documentation

- [ ] Update TASKS.md with deployment status
- [ ] Update CLAUDE.md with ERP configuration
- [ ] Document any issues encountered

### 2. Security Hardening

- [ ] Change default passwords in production
- [ ] Enable Supabase email confirmation
- [ ] Set up monitoring alerts
- [ ] Configure backup schedule
- [ ] Review CORS settings
- [ ] Enable rate limiting

### 3. Performance Optimization

- [ ] Enable nginx caching
- [ ] Configure CDN for static assets
- [ ] Add database indexes
- [ ] Monitor response times

---

## Quick Reference

### Service Commands

```bash
# Backend
sudo systemctl start kasaai-erp-backend
sudo systemctl stop kasaai-erp-backend
sudo systemctl restart kasaai-erp-backend
sudo systemctl status kasaai-erp-backend

# Nginx
sudo systemctl reload nginx
sudo systemctl restart nginx
```

### URLs

- **Frontend**: https://dev-erp.ailabsafrica.com
- **API**: https://dev-erp-api.ailabsafrica.com
- **API Docs**: https://dev-erp-api.ailabsafrica.com/docs
- **Health**: https://dev-erp-api.ailabsafrica.com/health

### Credentials

- **Admin**: admin@ailabsafrica.com / Admin@2024!
- **User**: user@ailabsafrica.com / User@2024!

---

**Deployment Complete! 🎉**

Next steps:
1. Test all functionality
2. Create sample data
3. Train users
4. Monitor for issues
