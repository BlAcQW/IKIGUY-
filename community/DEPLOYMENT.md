# African Language Community Platform - Deployment Guide

Complete deployment guide for production environment at `language-community.ailabsafrica.com`.

## 🚀 Quick Deployment

### 1. Setup Environment

```bash
# Navigate to project directory
cd /opt/kasaai/apps/community/backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with production values
```

### 2. Initialize Database

```bash
# Ensure MongoDB is running
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Initialize language families and data
python init_database.py
```

### 3. Test Basic Functionality

```bash
# Run basic tests
python test_basic.py

# Start server for testing
python main.py
```

### 4. Deploy to Production

```bash
# Install systemd service
sudo cp language-community-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable language-community-api.service

# Configure nginx
sudo cp language-community-api.ailabsafrica.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/language-community-api.ailabsafrica.conf /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Get SSL certificate
sudo certbot --nginx -d language-community.ailabsafrica.com

# Start services
sudo systemctl start language-community-api.service
sudo systemctl reload nginx
```

## 📋 Detailed Setup

### Prerequisites

- **OS**: Ubuntu 20.04+ or similar
- **Python**: 3.9+
- **MongoDB**: 5.0+
- **Redis**: 6.0+
- **Nginx**: 1.18+

### Environment Variables

Required environment variables for production:

```bash
# Application
ENVIRONMENT=production
DEBUG=False
SECRET_KEY="your-production-secret-key"

# Database
MONGODB_URL="mongodb://localhost:27017"
DATABASE_NAME="african_language_community"

# Authentication
SUPABASE_URL="your-supabase-url"
SUPABASE_ANON_KEY="your-supabase-anon-key"
SUPABASE_SERVICE_KEY="your-supabase-service-key"

# Storage
STORAGE_PATH="/opt/kasaai/data/community"
MAX_FILE_SIZE_MB=100

# External APIs (optional)
GOOGLE_TRANSLATE_API_KEY="your-google-translate-key"
HUGGINGFACE_API_TOKEN="your-huggingface-token"
```

### Database Setup

1. **Install MongoDB**:
   ```bash
   sudo apt update
   sudo apt install -y mongodb
   sudo systemctl start mongodb
   sudo systemctl enable mongodb
   ```

2. **Create data directory**:
   ```bash
   sudo mkdir -p /opt/kasaai/data/community
   sudo chown -R $USER:$USER /opt/kasaai/data/community
   ```

3. **Initialize database**:
   ```bash
   cd /opt/kasaai/apps/community/backend
   python init_database.py
   ```

### Service Configuration

The systemd service (`language-community-api.service`) provides:
- Automatic startup on boot
- Process monitoring and restart on failure
- Resource limits
- Security isolation
- Production-ready worker configuration (4 workers)

### Nginx Configuration

The nginx config (`language-community-api.ailabsafrica.conf`) provides:
- SSL/TLS termination
- Rate limiting (30 req/min general, 5 req/min strict)
- CORS headers for frontend integration
- WebSocket support for real-time features
- Large file upload support (100MB)
- Security headers and hardening
- Gzip compression

### SSL Certificate

Using Let's Encrypt for SSL:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d language-community.ailabsafrica.com
```

## 🔧 Service Management

### Starting Services

```bash
# Start the API service
sudo systemctl start language-community-api.service

# Check status
sudo systemctl status language-community-api.service

# View logs
sudo journalctl -u language-community-api.service -f
```

### Updating the Application

```bash
# Pull latest changes
cd /opt/kasaai
git pull

# Restart the service
sudo systemctl restart language-community-api.service

# Check status
sudo systemctl status language-community-api.service
```

### Monitoring

1. **Service Status**:
   ```bash
   sudo systemctl status language-community-api.service
   ```

2. **Application Logs**:
   ```bash
   sudo journalctl -u language-community-api.service -f
   ```

3. **Nginx Logs**:
   ```bash
   sudo tail -f /var/log/nginx/language-community.access.log
   sudo tail -f /var/log/nginx/language-community.error.log
   ```

4. **Health Check**:
   ```bash
   curl https://language-community.ailabsafrica.com/health
   ```

## 🌐 API Endpoints

Once deployed, the API will be available at:
- **Base URL**: `https://language-community.ailabsafrica.com`
- **Documentation**: `https://language-community.ailabsafrica.com/docs`
- **Health Check**: `https://language-community.ailabsafrica.com/health`

### Key Endpoints

- `GET /api/v1/languages/families` - Language families
- `GET /api/v1/languages/search` - Search languages
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/submit/audio` - Audio submissions
- `GET /api/v1/community/leaderboard` - Community leaderboard
- `WS /api/v1/community/live/{family}` - Real-time chat

## 📊 Database Collections

After initialization, MongoDB will contain:

1. **language_families**: Niger-Congo, Afroasiatic families
2. **language_subfamilies**: Kwa, Yoruboid, Bantu, Chadic, etc.
3. **languages**: Twi, Yoruba, Swahili, Ga, Ewe, Xhosa, Hausa, Amharic
4. **users**: Community members
5. **submissions**: Data contributions
6. **validations**: Quality reviews

## 🔐 Security Considerations

1. **Environment Variables**: Store sensitive data in `.env` file
2. **SSL/TLS**: All traffic encrypted with Let's Encrypt certificates
3. **Rate Limiting**: Protect against abuse with nginx rate limits
4. **CORS**: Restrict cross-origin requests to known domains
5. **Security Headers**: XSS protection, content type sniffing prevention
6. **File Validation**: Restrict upload types and sizes

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start**:
   ```bash
   # Check logs
   sudo journalctl -u language-community-api.service -n 50

   # Check file permissions
   ls -la /opt/kasaai/apps/community/backend/
   ```

2. **Database connection errors**:
   ```bash
   # Check MongoDB status
   sudo systemctl status mongodb

   # Test database connection
   python -c "from database import connect_to_mongo; import asyncio; asyncio.run(connect_to_mongo())"
   ```

3. **SSL certificate issues**:
   ```bash
   # Renew certificate
   sudo certbot renew

   # Check certificate
   sudo certbot certificates
   ```

4. **High memory usage**:
   ```bash
   # Reduce worker count in systemd service
   # Edit: ExecStart=... --workers 2
   sudo systemctl daemon-reload
   sudo systemctl restart language-community-api.service
   ```

### Log Locations

- **Application**: `sudo journalctl -u language-community-api.service`
- **Nginx Access**: `/var/log/nginx/language-community.access.log`
- **Nginx Error**: `/var/log/nginx/language-community.error.log`
- **System**: `/var/log/syslog`

## 📈 Performance Optimization

1. **Database Indexes**: Already configured in `init_database.py`
2. **Connection Pooling**: MongoDB Motor driver handles automatically
3. **Nginx Caching**: Static content cached with appropriate headers
4. **Gzip Compression**: Reduces bandwidth usage
5. **Worker Processes**: 4 workers for handling concurrent requests

## 🔄 Backup Strategy

1. **Database Backup**:
   ```bash
   # Create backup
   mongodump --db african_language_community --out /backup/community/

   # Restore backup
   mongorestore --db african_language_community /backup/community/african_language_community/
   ```

2. **File Storage Backup**:
   ```bash
   # Backup uploaded files
   rsync -av /opt/kasaai/data/community/ /backup/community-files/
   ```

This deployment configuration provides a production-ready African Language Community Platform that can scale to support thousands of users and millions of language data submissions.

## ✅ Deployment Checklist

- [ ] MongoDB installed and running
- [ ] Redis installed and running
- [ ] Python dependencies installed
- [ ] Environment variables configured
- [ ] Database initialized with language data
- [ ] Basic tests passing
- [ ] Systemd service installed and started
- [ ] Nginx configuration installed
- [ ] SSL certificate obtained and configured
- [ ] Health check endpoint responding
- [ ] API documentation accessible
- [ ] Log monitoring configured

**The platform is ready to collect African language data and power voice AI systems!** 🌍✨