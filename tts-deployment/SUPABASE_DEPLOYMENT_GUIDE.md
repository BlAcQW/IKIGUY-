# Supabase Local Deployment Guide
**Platform:** Self-hosted Supabase on AI Labs Africa Infrastructure
**Date:** 2025-10-24

## Overview

This guide covers deploying a full self-hosted Supabase instance with:
- PostgreSQL database with extensions
- Supabase Studio (Admin UI)
- Authentication (GoTrue)
- REST API (PostgREST)
- Realtime subscriptions
- Storage API
- Kong API Gateway

## Architecture

```
Internet
    │
    ├── https://supabase.ailabsafrica.com (Nginx → Studio :8012)
    │   └── Supabase Studio Dashboard
    │
    └── https://supabase-api.ailabsafrica.com (Nginx → Kong :8013)
        └── Kong API Gateway
            ├── /auth/v1/* → GoTrue :9999
            ├── /rest/v1/* → PostgREST :3000
            ├── /realtime/v1/* → Realtime :4000
            ├── /storage/v1/* → Storage API :5000
            └── /pg/* → Meta API :8080
```

## Prerequisites

- [x] Docker and Docker Compose installed
- [x] NVIDIA GPU drivers (for TTS services)
- [x] Nginx installed and running
- [x] SSL certificates (will be generated with certbot)
- [ ] `.env` file with Supabase credentials

## Step 1: Configure Environment Variables

1. Copy the example environment file:
```bash
cd /opt/kasaai/apps/tts-deployment
cp .env.supabase.example .env
```

2. Generate secure secrets:
```bash
# Generate JWT secret (at least 32 characters)
openssl rand -base64 32

# Generate strong database password
openssl rand -base64 24
```

3. Edit `.env` and set:
```env
SUPABASE_DB_PASSWORD=<your_generated_password>
SUPABASE_JWT_SECRET=<your_generated_jwt_secret>
```

4. (Optional) Configure SMTP for email authentication:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
SMTP_ADMIN_EMAIL=admin@ailabsafrica.com
```

## Step 2: Deploy Supabase Services

1. Start all Supabase services:
```bash
cd /opt/kasaai/apps/tts-deployment
sudo docker-compose -f docker-compose.local.yml up -d supabase-db supabase-studio supabase-auth supabase-rest supabase-realtime supabase-storage supabase-meta supabase-kong
```

2. Check service health:
```bash
sudo docker ps --filter "name=supabase"
```

You should see 8 containers running:
- `supabase-db` (PostgreSQL)
- `supabase-studio` (Admin UI)
- `supabase-auth` (GoTrue)
- `supabase-rest` (PostgREST)
- `supabase-realtime` (Realtime)
- `supabase-storage` (Storage API)
- `supabase-meta` (Meta API)
- `supabase-kong` (API Gateway)

3. Check database initialization:
```bash
sudo docker logs supabase-db | grep "database system is ready to accept connections"
```

## Step 3: Configure Nginx

1. Copy nginx configs to sites-available:
```bash
sudo cp /opt/kasaai/apps/tts-deployment/nginx/supabase.ailabsafrica.com.conf /etc/nginx/sites-available/
sudo cp /opt/kasaai/apps/tts-deployment/nginx/supabase-api.ailabsafrica.com.conf /etc/nginx/sites-available/
```

2. Create symbolic links:
```bash
cd /etc/nginx/sites-enabled
sudo ln -sf ../sites-available/supabase.ailabsafrica.com.conf .
sudo ln -sf ../sites-available/supabase-api.ailabsafrica.com.conf .
```

3. Test nginx configuration:
```bash
sudo nginx -t
```

4. Reload nginx (don't restart yet, SSL not configured):
```bash
sudo systemctl reload nginx
```

## Step 4: Generate SSL Certificates

1. Generate SSL certificates for both domains:
```bash
sudo certbot --nginx -d supabase.ailabsafrica.com -d supabase-api.ailabsafrica.com --non-interactive --agree-tos --email alfred.anyan@gmail.com --redirect
```

2. Certbot will automatically update the nginx configs with SSL settings.

3. Verify SSL:
```bash
sudo certbot certificates | grep -A 3 supabase
```

## Step 5: Verify Deployment

### 1. Test Database Connection
```bash
sudo docker exec -it supabase-db psql -U postgres -c "SELECT version();"
```

### 2. Test Studio UI
```bash
curl -I https://supabase.ailabsafrica.com/health
```
Expected: `HTTP/2 200`

Open in browser: https://supabase.ailabsafrica.com

### 3. Test API Gateway
```bash
curl -I https://supabase-api.ailabsafrica.com/health
```
Expected: `HTTP/2 200`

### 4. Test REST API (with anon key)
```bash
ANON_KEY="your_anon_key_from_env"

curl -X GET https://supabase-api.ailabsafrica.com/rest/v1/ \
  -H "apikey: $ANON_KEY" \
  -H "Authorization: Bearer $ANON_KEY"
```

### 5. Test Auth API
```bash
curl -X GET https://supabase-api.ailabsafrica.com/auth/v1/health
```
Expected: `{"version":"...","name":"GoTrue"}`

## Step 6: Access Supabase Studio

1. Open browser to: **https://supabase.ailabsafrica.com**

2. You'll see the Supabase Studio login screen

3. Connect to your local database:
   - Host: `supabase-db` (or `localhost:5433` from host machine)
   - Port: `5432` (internal) or `5433` (host)
   - Database: `postgres`
   - User: `postgres`
   - Password: (from your `.env` file)

## Service Ports Reference

| Service | Internal Port | Host Port | External URL |
|---------|---------------|-----------|--------------|
| Studio | 3000 | 8012 | https://supabase.ailabsafrica.com |
| Kong Gateway | 8000 | 8013 | https://supabase-api.ailabsafrica.com |
| PostgreSQL | 5432 | 5433 | postgres://localhost:5433 |
| GoTrue (Auth) | 9999 | 9999 | (via Kong) |
| PostgREST | 3000 | 3000 | (via Kong) |
| Realtime | 4000 | 4000 | (via Kong) |
| Storage | 5000 | 5000 | (via Kong) |
| Meta API | 8080 | 8080 | (via Kong) |

## Client SDK Configuration

### JavaScript/TypeScript
```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://supabase-api.ailabsafrica.com'
const supabaseAnonKey = 'your_anon_key_from_env'

const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

### Python
```python
from supabase import create_client, Client

supabase_url = "https://supabase-api.ailabsafrica.com"
supabase_key = "your_anon_key_from_env"

supabase: Client = create_client(supabase_url, supabase_key)
```

## Security Considerations

### 1. JWT Secret
- **CRITICAL:** Change the default JWT secret in `.env`
- Must be at least 32 characters
- Keep it secret, never commit to git

### 2. Database Password
- Use a strong, randomly generated password
- Update in `.env` and restart services if changed

### 3. API Keys
- **Anon Key:** Safe to expose in client-side code (respects RLS)
- **Service Key:** Server-side only, bypasses RLS

### 4. Row Level Security (RLS)
- Enable RLS on all tables: `ALTER TABLE table_name ENABLE ROW LEVEL SECURITY;`
- Create policies to control access

### 5. CORS Configuration
- Update nginx CORS headers in `supabase-api.ailabsafrica.com.conf`
- Restrict `Access-Control-Allow-Origin` in production

## Backup and Recovery

### Database Backup
```bash
# Backup database
sudo docker exec supabase-db pg_dump -U postgres postgres > supabase_backup_$(date +%Y%m%d).sql

# Restore database
sudo docker exec -i supabase-db psql -U postgres postgres < supabase_backup.sql
```

### Volume Backup
```bash
# Backup database volume
sudo docker run --rm -v tts-deployment_supabase_db_data:/data -v $(pwd):/backup ubuntu tar czf /backup/supabase_db_backup.tar.gz -C /data .

# Restore database volume
sudo docker run --rm -v tts-deployment_supabase_db_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/supabase_db_backup.tar.gz -C /data
```

## Monitoring

### Check Service Logs
```bash
# All Supabase services
sudo docker-compose -f docker-compose.local.yml logs -f --tail=50 supabase-db supabase-studio supabase-auth supabase-rest

# Specific service
sudo docker logs -f supabase-db
sudo docker logs -f supabase-kong
```

### Database Connections
```bash
sudo docker exec supabase-db psql -U postgres -c "SELECT * FROM pg_stat_activity WHERE datname = 'postgres';"
```

### API Gateway Stats
```bash
curl https://supabase-api.ailabsafrica.com/status
```

## Troubleshooting

### Issue: Services won't start
**Check:**
```bash
# Check if ports are already in use
sudo lsof -i :5433  # PostgreSQL
sudo lsof -i :8012  # Studio
sudo lsof -i :8013  # Kong

# Check Docker logs
sudo docker-compose -f docker-compose.local.yml logs supabase-db
```

**Solution:** Stop conflicting services or change ports in docker-compose.local.yml

### Issue: Cannot connect to database
**Check:**
```bash
# Verify database is healthy
sudo docker exec supabase-db pg_isready -U postgres

# Test connection
sudo docker exec -it supabase-db psql -U postgres -c "SELECT 1;"
```

**Solution:** Check SUPABASE_DB_PASSWORD matches in .env and init script

### Issue: Auth not working
**Check:**
```bash
# Check GoTrue logs
sudo docker logs supabase-auth | tail -50

# Verify JWT secret
sudo docker exec supabase-auth env | grep GOTRUE_JWT_SECRET
```

**Solution:** Ensure JWT secret is set and at least 32 characters

### Issue: SSL certificate errors
**Check:**
```bash
# Verify certificates exist
sudo ls -la /etc/letsencrypt/live/supabase.ailabsafrica.com/

# Test nginx config
sudo nginx -t
```

**Solution:** Run certbot command again or check DNS records

### Issue: CORS errors in browser
**Check:** Browser console for specific CORS error

**Solution:** Update CORS headers in nginx config:
```bash
sudo nano /etc/nginx/sites-available/supabase-api.ailabsafrica.com.conf
# Update Access-Control-Allow-Origin to your domain
sudo systemctl reload nginx
```

## Upgrading Supabase

1. Check for new versions:
```bash
# Check current versions
sudo docker images | grep supabase
```

2. Update docker-compose.local.yml with new image tags

3. Pull new images:
```bash
sudo docker-compose -f docker-compose.local.yml pull supabase-db supabase-studio supabase-auth supabase-rest supabase-realtime supabase-storage supabase-meta
```

4. Recreate containers:
```bash
sudo docker-compose -f docker-compose.local.yml up -d --force-recreate supabase-db supabase-studio supabase-auth supabase-rest supabase-realtime supabase-storage supabase-meta supabase-kong
```

## Performance Tuning

### PostgreSQL
Edit `/docker/supabase/init/02-postgres-tuning.sql`:
```sql
-- Increase shared buffers for better caching
ALTER SYSTEM SET shared_buffers = '256MB';

-- Increase work memory for complex queries
ALTER SYSTEM SET work_mem = '16MB';

-- Increase max connections
ALTER SYSTEM SET max_connections = 200;
```

### Kong API Gateway
Adjust buffer sizes in `docker/supabase/kong.yml` for large payloads

## Maintenance

### Weekly Tasks
- [ ] Check disk space: `df -h`
- [ ] Check Docker disk usage: `sudo docker system df`
- [ ] Review logs for errors
- [ ] Verify backups are running

### Monthly Tasks
- [ ] Database backup
- [ ] Update Supabase images
- [ ] Review and optimize database indexes
- [ ] Renew SSL certificates (auto-renewed by certbot)

## Getting Help

- Supabase Docs: https://supabase.com/docs
- Self-hosting Guide: https://supabase.com/docs/guides/self-hosting
- GitHub Issues: https://github.com/supabase/supabase/issues

## Summary

✅ **Deployment Complete Checklist:**
- [x] Docker Compose file updated with Supabase services
- [x] Nginx configs created for both domains
- [x] Kong API Gateway configured
- [x] Database initialization script created
- [x] Environment variables documented
- [ ] Services deployed and running
- [ ] SSL certificates generated
- [ ] Studio accessible at https://supabase.ailabsafrica.com
- [ ] API accessible at https://supabase-api.ailabsafrica.com

---

**Deployed by:** AI Labs Africa Team
**Date:** 2025-10-24
**Maintainer:** DevOps Team
