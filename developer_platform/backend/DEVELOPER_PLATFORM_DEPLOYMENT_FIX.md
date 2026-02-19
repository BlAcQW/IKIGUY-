# Developer Platform Deployment Fix

## Problem

The Developer Platform deployment was failing with Python 3.12 due to:

1. Database connection issues (MongoDB connection refused)
2. Python 3.12 compatibility issues
3. Environment configuration problems

## Error Details

```
pymongo.errors.ServerSelectionTimeoutError: localhost:27017: [Errno 111] Connection refused
```

This error occurs because:

1. The Developer Platform is trying to connect to MongoDB on localhost:27017
2. The environment variables are not properly configured
3. MongoDB might not be running or accessible

## Solution

### 1. Updated Database Configuration

- Deployment scripts now read `MONGODB_URL` and `MONGODB_DB` from the consolidated environment file
- Default port updated to `27017`
- Validates MongoDB connectivity during deployment

### 2. Updated Requirements Files

**Standard requirements.txt:**

- Added setuptools>=68.0.0 for Python 3.12 compatibility
- Added wheel>=0.41.0
- All existing dependencies maintained

**Python 3.12 specific requirements (requirements-py312.txt):**

- All Python 3.12 compatible versions
- Includes distutils compatibility fixes
- Uses newer versions of all packages

### 3. Updated Deployment Scripts

**deploy_dev_api.sh:**

- Now detects Python version automatically
- Uses appropriate requirements file based on Python version
- Handles both Python 3.11 and 3.12

**deploy_dev_python312.sh:**

- Python 3.12 specific deployment script
- Includes distutils compatibility fixes
- Tests database connection before starting service

**fix_dev_deployment.sh:**

- Comprehensive fix script
- Handles Python 3.12 compatibility
- Tests database connection
- Creates environment file if missing

### 4. Environment Configuration

**Service Configuration:**

- Developer Platform service uses `/opt/kasaai/.env` as environment file
- This should be the consolidated environment file
- Contains all database and service configurations

## Usage

### For Python 3.12 Systems:

```bash
# Use the Python 3.12 specific deployment script
sudo ./deploy_dev_python312.sh

# Or use the comprehensive fix script
sudo ./fix_dev_deployment.sh
```

### For Mixed Python Versions:

```bash
# Use the updated deployment script (auto-detects version)
sudo ./deploy_dev_api.sh
```

## Key Changes Made

1. **database.py:**

   - Uses `POSTGRES_DB_DEV` environment variable
   - Updated default port to 5432 (server port)
   - Properly reads from consolidated environment file

2. **requirements.txt:**

   - setuptools>=68.0.0
   - wheel>=0.41.0

3. **requirements-py312.txt:**

   - All Python 3.12 compatible versions
   - Includes distutils compatibility fixes

4. **deploy_dev_api.sh:**

   - Auto-detects Python version
   - Uses appropriate requirements file

5. **deploy_dev_python312.sh:**

   - New Python 3.12 specific deployment script
   - Includes database connection testing

6. **fix_dev_deployment.sh:**
   - Comprehensive fix script
   - Handles all deployment issues

## Database Connection Testing

The deployment scripts now include database connection testing:

```bash
# Test PostgreSQL connection
python3 -c "
import os
import psycopg2

# Load environment variables from /opt/kasaai/.env
env_file = '/opt/kasaai/.env'
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                try:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
                except ValueError:
                    continue

# Get database URL
db_url = os.getenv('DEVPLAT_DB_URL', 'postgresql://postgres:aawwER444444@localhost:5432/kasaai_dev_api')
print(f'Attempting to connect to: {db_url}')

try:
    conn = psycopg2.connect(db_url)
    print('✅ PostgreSQL connection successful!')
    conn.close()
except Exception as e:
    print(f'❌ PostgreSQL connection failed: {e}')
"
```

## Verification

After deployment, verify the installation:

```bash
# Check service status
sudo systemctl status kasaai-dev-backend.service

# Check logs
sudo journalctl -u kasaai-dev-backend.service --since "1 minute ago"

# Test the application
curl http://localhost:8002/health
```

## Troubleshooting

### Database Connection Issues:

1. Ensure PostgreSQL is running on localhost:5432 (server) or localhost:5433 (development)
2. Verify database `kasaai_dev_api` exists
3. Check user `postgres` has access
4. Verify environment variables in `/opt/kasaai/.env`

### Python 3.12 Issues:

1. Use the Python 3.12 specific deployment script
2. Ensure setuptools>=68.0.0 is installed
3. Install distutils-compat if needed

### Environment Issues:

1. Ensure `/opt/kasaai/.env` exists and is properly configured
2. Copy from `env.example` if missing
3. Update database connection strings as needed

## Notes

- Developer Platform uses port 8002 by default
- Service runs as www-data user
- Environment file is loaded from `/opt/kasaai/.env`
- Database connection is tested before service start
- All deployment scripts handle Python 3.12 compatibility
