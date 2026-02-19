# KasaAI Drive - Deployment Guide

Complete guide for deploying the KasaAI Drive application to production.

## Prerequisites

- Ubuntu/Debian server with root access
- MongoDB installed and running
- Nginx installed
- Certbot for SSL certificates
- Python 3.8+ with venv
- Node.js 18+ and npm
- Hetzner Storage Box configured

## Quick Start

For a fully automated deployment:

```bash
cd /opt/kasaai/apps/drive
./deploy.sh
```

This script will:
1. Install backend dependencies
2. Configure systemd service
3. Set up Nginx with SSL
4. Build the frontend
5. Start all services

## Manual Deployment

### Step 1: Environment Configuration

Create `/opt/kasaai/.env` with the following variables:

```bash
# MongoDB
MONGODB_URL=mongodb://admin:password@127.0.0.1:27017/?authSource=admin
MONGODB_DB_NAME=kasaai_drive

# Supabase Authentication
SUPABASE_URL=https://supabase.ailabsafrica.com
SUPABASE_KEY=your_supabase_key

# Hetzner Storage
HETZNER_STORAGE_USERNAME=u497034-sub1
HETZNER_STORAGE_PASSWORD=your_password
HETZNER_STORAGE_HOST=u497034-sub1.your-storagebox.de
HETZNER_STORAGE_PROTOCOL=webdav

# Storage Limits
MAX_FILE_SIZE_MB=100
MAX_UPLOAD_SIZE_MB=500

# Security
SECRET_KEY=generate_random_secret_key_here
```

### Step 2: Backend Setup

```bash
cd /opt/kasaai/apps/drive/backend

# Install dependencies (uses shared venv)
/opt/kasaai/apps/venv/bin/pip install -r requirements.txt

# Test the application
/opt/kasaai/apps/venv/bin/python main.py
```

### Step 3: Configure Systemd Service

```bash
# Copy service file
sudo cp /opt/kasaai/apps/drive/kasaai-drive-backend.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable kasaai-drive-backend

# Start the service
sudo systemctl start kasaai-drive-backend

# Check status
sudo systemctl status kasaai-drive-backend
```

### Step 4: Configure Nginx

```bash
# Copy Nginx configurations
sudo cp /opt/kasaai/apps/drive/drive-api.ailabsafrica.com.conf /etc/nginx/sites-available/
sudo cp /opt/kasaai/apps/drive/drive.ailabsafrica.com.conf /etc/nginx/sites-available/

# Enable sites
sudo ln -s /etc/nginx/sites-available/drive-api.ailabsafrica.com.conf /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/drive.ailabsafrica.com.conf /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 5: Obtain SSL Certificates

```bash
# For API
sudo certbot --nginx -d drive-api.ailabsafrica.com

# For Frontend
sudo certbot --nginx -d drive.ailabsafrica.com
```

### Step 6: Frontend Setup

```bash
cd /opt/kasaai/apps/drive/frontend

# Copy environment file
cp .env.local.example .env.local

# Edit with production values
nano .env.local

# Install dependencies
npm install

# Build for production
npm run build

# Start production server
npm start
```

For production, it's recommended to use PM2 for the frontend:

```bash
# Install PM2
npm install -g pm2

# Start frontend with PM2
cd /opt/kasaai/apps/drive/frontend
pm2 start npm --name "kasaai-drive-frontend" -- start

# Save PM2 configuration
pm2 save

# Set PM2 to start on boot
pm2 startup
```

## Testing

### Run Unit Tests

```bash
cd /opt/kasaai/apps/drive/backend

# Run all tests
PYTHONPATH=/opt/kasaai:/opt/kasaai/apps \
/opt/kasaai/apps/venv/bin/pytest tests/ -v

# Run with coverage
PYTHONPATH=/opt/kasaai:/opt/kasaai/apps \
/opt/kasaai/apps/venv/bin/pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test API Endpoints

```bash
# Health check
curl https://drive-api.ailabsafrica.com/health

# Upload file (requires auth token)
curl -X POST https://drive-api.ailabsafrica.com/api/files/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf" \
  -F "parent_id=null" \
  -F "organization_id=org_123"

# List folder contents
curl https://drive-api.ailabsafrica.com/api/folders/root/contents \
  -H "Authorization: Bearer YOUR_TOKEN"

# Search files
curl "https://drive-api.ailabsafrica.com/api/search?q=report" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Monitoring

### View Backend Logs

```bash
# Follow live logs
sudo journalctl -u kasaai-drive-backend -f

# View recent logs
sudo journalctl -u kasaai-drive-backend -n 100

# Filter by error level
sudo journalctl -u kasaai-drive-backend -p err
```

### View Frontend Logs (PM2)

```bash
# View logs
pm2 logs kasaai-drive-frontend

# Monitor
pm2 monit
```

### Monitor MongoDB

```bash
# Check database size
mongosh --eval "
  use kasaai_drive;
  db.stats();
"

# Count documents
mongosh --eval "
  use kasaai_drive;
  db.drive_items.countDocuments();
"

# Get storage usage by organization
mongosh --eval "
  use kasaai_drive;
  db.drive_items.aggregate([
    { \$match: { is_deleted: false } },
    { \$group: {
      _id: '\$organization_id',
      total_size: { \$sum: '\$size' },
      file_count: { \$sum: 1 }
    }}
  ]);
"
```

### Monitor Hetzner Storage

```bash
# Check WebDAV connection
curl -u u497034-sub1:password https://u497034-sub1.your-storagebox.de/

# List files
curl -u u497034-sub1:password -X PROPFIND https://u497034-sub1.your-storagebox.de/kasaai/drive/

# Check storage quota (via SFTP)
sftp -P 23 u497034-sub1@u497034-sub1.your-storagebox.de
> quota
```

## Troubleshooting

### Backend Won't Start

```bash
# Check service status
sudo systemctl status kasaai-drive-backend

# Check logs for errors
sudo journalctl -u kasaai-drive-backend -n 50

# Test manually
cd /opt/kasaai/apps/drive/backend
PYTHONPATH=/opt/kasaai:/opt/kasaai/apps /opt/kasaai/apps/venv/bin/python main.py
```

### Database Connection Issues

```bash
# Test MongoDB connection
mongosh "mongodb://admin:password@127.0.0.1:27017/?authSource=admin"

# Check MongoDB status
sudo systemctl status mongodb

# View MongoDB logs
sudo journalctl -u mongodb -f
```

### File Upload Failures

Common issues:
1. **File too large**: Check `MAX_UPLOAD_SIZE_MB` in .env
2. **Hetzner connection**: Test WebDAV connection
3. **Disk space**: Check server disk space
4. **Permissions**: Ensure correct file permissions

```bash
# Test Hetzner storage
curl -u username:password https://storage-host/

# Check disk space
df -h

# Check file permissions
ls -la /opt/kasaai/apps/drive/
```

### SSL Certificate Issues

```bash
# Renew certificates
sudo certbot renew

# Force renewal
sudo certbot renew --force-renewal

# Check certificate expiry
sudo certbot certificates
```

## Backup and Recovery

### Database Backup

```bash
# Backup MongoDB
mongodump --uri="mongodb://admin:password@localhost:27017/kasaai_drive?authSource=admin" \
  --out=/backup/drive/$(date +%Y%m%d)

# Restore MongoDB
mongorestore --uri="mongodb://admin:password@localhost:27017/kasaai_drive?authSource=admin" \
  /backup/drive/20251110/kasaai_drive/
```

### Hetzner Storage Backup

Files are already backed up on Hetzner Storage Box. For additional safety:

```bash
# Download all files (use with caution for large datasets)
rsync -avz -e "ssh -p 23" \
  u497034-sub1@u497034-sub1.your-storagebox.de:/kasaai/drive/ \
  /backup/hetzner/drive/
```

## Performance Optimization

### Database Indexes

Indexes are created automatically on startup. To verify:

```bash
mongosh --eval "
  use kasaai_drive;
  db.drive_items.getIndexes();
"
```

### Nginx Caching

Add to Nginx config for static assets:

```nginx
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 365d;
    add_header Cache-Control "public, immutable";
}
```

### MongoDB Performance

```bash
# Enable profiling
mongosh --eval "
  use kasaai_drive;
  db.setProfilingLevel(1, { slowms: 100 });
"

# View slow queries
mongosh --eval "
  use kasaai_drive;
  db.system.profile.find().limit(10).sort({ ts: -1 }).pretty();
"
```

## Security Best Practices

1. **Environment Variables**: Never commit .env files
2. **File Validation**: All uploads are validated by MIME type
3. **Rate Limiting**: Consider adding rate limiting to upload endpoints
4. **CORS**: Restrict allowed origins in production
5. **Token Expiry**: Configure appropriate JWT token expiry
6. **Audit Logs**: All file operations are logged

## Scaling Considerations

For high-traffic scenarios:

1. **Load Balancer**: Add nginx load balancer for multiple backend instances
2. **Separate MongoDB**: Move to dedicated MongoDB server
3. **Redis Cache**: Add Redis for caching file metadata
4. **CDN**: Use CDN for file downloads
5. **Object Storage**: Consider adding S3-compatible backup

## Maintenance

### Regular Tasks

- **Daily**: Check service status and logs
- **Weekly**: Review storage usage and database size
- **Monthly**: SSL certificate renewal check, backup verification
- **Quarterly**: Security updates, dependency updates

### Update Procedure

```bash
# Pull latest code
cd /opt/kasaai/apps
git pull

# Update backend dependencies
cd /opt/kasaai/apps/drive/backend
/opt/kasaai/apps/venv/bin/pip install -r requirements.txt --upgrade

# Update frontend dependencies
cd /opt/kasaai/apps/drive/frontend
npm update

# Rebuild frontend
npm run build

# Restart services
sudo systemctl restart kasaai-drive-backend
pm2 restart kasaai-drive-frontend
```

## Support

For issues or questions:
- Email: support@ailabsafrica.com
- Documentation: https://docs.ailabsafrica.com
- GitHub Issues: https://github.com/ailabsafrica/kasaai/issues

## License

Copyright © 2025 AI Labs Africa. All rights reserved.
