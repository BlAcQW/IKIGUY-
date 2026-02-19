# Maintenance & Operations

**Internal Documentation - AI Labs Africa Employees Only**

## Daily Operations

### Service Health Monitoring

Check all services daily:
```bash
# Check all KasaAI services
sudo systemctl list-units "kasaai-*.service" --state=running

# Quick status of critical services
sudo systemctl status kasaai-core-backend
sudo systemctl status kasaai-studyflow-backend
sudo systemctl status nginx
sudo systemctl status mongod
```

### Log Monitoring

```bash
# Check for errors in the last hour
sudo journalctl -u kasaai-core-backend --since "1 hour ago" | grep -i error

# Monitor live logs
sudo journalctl -u kasaai-core-backend -f
```

## Weekly Tasks

### Disk Space Check

```bash
# Check overall disk usage
df -h

# Find large directories
du -h --max-depth=1 /opt/kasaai/ | sort -hr | head -10

# Clean up old logs if needed
sudo journalctl --vacuum-time=30d
```

### Database Backup

```bash
# Backup all MongoDB databases
mongodump --uri="mongodb://admin:aawwER4444%@127.0.0.1:27017/" --out="/backup/mongodb/$(date +%Y%m%d)"

# Compress backup
tar -czf /backup/mongodb/backup-$(date +%Y%m%d).tar.gz /backup/mongodb/$(date +%Y%m%d)
```

### SSL Certificate Check

```bash
# Check certificate expiration
sudo certbot certificates

# Should show ~90 days remaining
# Auto-renewal happens at 30 days
```

## Monthly Tasks

### System Updates

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Restart services if kernel updated
sudo systemctl restart kasaai-*
```

### Security Audit

1. Review user access logs
2. Check for failed authentication attempts
3. Review environment variable security
4. Verify SSL certificates
5. Check firewall rules

### Performance Review

1. Check database query performance
2. Review API response times
3. Analyze error rates
4. Check resource utilization (CPU, memory, disk)

## Common Issues & Solutions

### Issue: Service Won't Start

**Symptoms**: `systemctl start` fails, service shows as "failed"

**Diagnosis**:
```bash
sudo systemctl status kasaai-yourapp-backend
sudo journalctl -u kasaai-yourapp-backend -n 100
```

**Common Causes**:
1. **Port already in use**
   ```bash
   sudo netstat -tulpn | grep 30036
   # Kill process if needed
   sudo kill <pid>
   ```

2. **Missing environment variables**
   ```bash
   # Check .env file exists and is readable
   cat /opt/kasaai/.env | grep REQUIRED_VAR
   ```

3. **Python dependencies missing**
   ```bash
   source /opt/kasaai/apps/venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Permission issues**
   ```bash
   sudo chown -R dev:dev /opt/kasaai/apps/yourapp
   ```

### Issue: 502 Bad Gateway

**Symptoms**: Nginx returns 502 error

**Diagnosis**:
```bash
sudo tail -f /var/log/nginx/error.log
```

**Common Causes**:
1. **Backend service not running**
   ```bash
   sudo systemctl status kasaai-yourapp-backend
   sudo systemctl start kasaai-yourapp-backend
   ```

2. **Wrong port in nginx config**
   ```bash
   sudo nano /etc/nginx/sites-available/yourapp-api.ailabsafrica.com.conf
   # Check proxy_pass port matches service port
   ```

3. **Firewall blocking internal connection**
   ```bash
   sudo ufw status
   # Should allow internal connections
   ```

### Issue: Database Connection Failed

**Symptoms**: "Connection refused" or "Authentication failed"

**Diagnosis**:
```bash
mongosh "mongodb://admin:aawwER4444%@127.0.0.1:27017/"
```

**Common Causes**:
1. **MongoDB not running**
   ```bash
   sudo systemctl status mongod
   sudo systemctl start mongod
   ```

2. **Wrong credentials**
   ```bash
   # Check .env file
   cat /opt/kasaai/.env | grep MONGO
   ```

3. **Connection limit reached**
   ```bash
   # Check MongoDB logs
   sudo tail -f /var/log/mongodb/mongod.log
   ```

### Issue: High CPU Usage

**Diagnosis**:
```bash
htop
# Or
top -u dev
```

**Common Causes**:
1. **Runaway process** - Kill and restart service
2. **Memory leak** - Restart service, investigate logs
3. **High traffic** - Check if legitimate, consider scaling

### Issue: Disk Space Full

**Quick Fix**:
```bash
# Find large files
sudo du -h --max-depth=1 / | sort -hr | head -10

# Clean old logs
sudo journalctl --vacuum-time=7d

# Clean Docker (if used)
docker system prune -af

# Clean npm cache
npm cache clean --force

# Clean pip cache
pip cache purge
```

## Service Management Commands

### Start/Stop/Restart

```bash
# Start
sudo systemctl start kasaai-yourapp-backend

# Stop
sudo systemctl stop kasaai-yourapp-backend

# Restart
sudo systemctl restart kasaai-yourapp-backend

# Reload (graceful restart)
sudo systemctl reload kasaai-yourapp-backend
```

### Enable/Disable Auto-start

```bash
# Enable (start on boot)
sudo systemctl enable kasaai-yourapp-backend

# Disable
sudo systemctl disable kasaai-yourapp-backend
```

### View Status and Logs

```bash
# Status
sudo systemctl status kasaai-yourapp-backend

# Logs (last 100 lines)
sudo journalctl -u kasaai-yourapp-backend -n 100

# Logs (follow/tail)
sudo journalctl -u kasaai-yourapp-backend -f

# Logs (since time)
sudo journalctl -u kasaai-yourapp-backend --since "1 hour ago"
```

## Database Operations

### MongoDB

#### Backup Single Database

```bash
mongodump --uri="mongodb://admin:aawwER4444%@127.0.0.1:27017/studyflow" --out="/backup/studyflow-$(date +%Y%m%d)"
```

#### Restore Database

```bash
mongorestore --uri="mongodb://admin:aawwER4444%@127.0.0.1:27017/" /backup/studyflow-20251107/
```

#### Database Statistics

```bash
mongosh "mongodb://admin:aawwER4444%@127.0.0.1:27017/"

use studyflow
db.stats()
```

#### Query Performance

```bash
# Enable profiling
db.setProfilingLevel(1, { slowms: 100 })

# View slow queries
db.system.profile.find().sort({ ts: -1 }).limit(5).pretty()
```

## Nginx Operations

### Reload Configuration

```bash
# Test configuration
sudo nginx -t

# Reload (graceful, no downtime)
sudo systemctl reload nginx

# Restart (brief downtime)
sudo systemctl restart nginx
```

### View Access Logs

```bash
# Real-time
sudo tail -f /var/log/nginx/access.log

# Specific domain
sudo tail -f /var/log/nginx/access.log | grep studyflow

# Last 100 requests
sudo tail -n 100 /var/log/nginx/access.log
```

### View Error Logs

```bash
# Real-time
sudo tail -f /var/log/nginx/error.log

# Last 100 errors
sudo tail -n 100 /var/log/nginx/error.log
```

## Performance Monitoring

### System Resources

```bash
# Interactive monitoring
htop

# CPU usage
top

# Memory usage
free -h

# Disk I/O
iostat -x 1

# Network
iftop
```

### Application Metrics

```bash
# Request count per service
sudo journalctl -u kasaai-studyflow-backend --since today | grep "POST\|GET" | wc -l

# Error count
sudo journalctl -u kasaai-studyflow-backend --since today | grep -i error | wc -l

# Average response time (requires custom logging)
sudo journalctl -u kasaai-studyflow-backend --since today | grep "response_time"
```

## Security Operations

### Review Failed Login Attempts

```bash
# SSH failed attempts
sudo grep "Failed password" /var/log/auth.log | tail -20

# Supabase auth failures (check application logs)
sudo journalctl -u kasaai-core-backend | grep "authentication failed"
```

### Update Firewall Rules

```bash
# Check current rules
sudo ufw status verbose

# Allow new port
sudo ufw allow 30036/tcp

# Deny specific IP
sudo ufw deny from 123.45.67.89
```

### Rotate Secrets

When rotating secrets (API keys, passwords):

1. Update in `/opt/kasaai/.env`
2. Update in Supabase/external services
3. Restart all affected services
4. Test functionality
5. Document in secure location

## Disaster Recovery

### Full System Restore

1. **Restore MongoDB**
   ```bash
   mongorestore --uri="mongodb://admin:aawwER4444%@127.0.0.1:27017/" /backup/latest/
   ```

2. **Restore Application Code**
   ```bash
   cd /opt/kasaai
   git fetch origin
   git checkout main
   git pull origin main
   ```

3. **Restore Environment Variables**
   ```bash
   # Copy from secure backup
   sudo cp /backup/.env /opt/kasaai/.env
   ```

4. **Restart All Services**
   ```bash
   sudo systemctl restart kasaai-*
   sudo systemctl restart nginx
   ```

### Emergency Contacts

- **Primary**: Alfred Anyan - alfred.anyan@gmail.com
- **Infrastructure Issues**: Contact server provider
- **Supabase Issues**: Check Supabase status page

---

**Last Updated**: November 7, 2025
