# InkWave Authentication - Quick Troubleshooting Checklist

## 🚨 Users Being Logged Out Immediately?

Run these checks in order:

### 1. Check Backend Service Status
```bash
sudo systemctl status inkwave-backend.service --no-pager | head -20
```
- ✅ Should show: `Active: active (running)`
- ❌ If failed: Check logs → `sudo journalctl -u inkwave-backend.service -n 50`

### 2. Check for Permission Errors
```bash
sudo journalctl -u inkwave-backend.service -n 100 | grep -i "permission"
```
- ❌ If found: Run permission fix
  ```bash
  sudo chown -R dev:www-data /opt/kasaai/apps/inkwave/backend/
  sudo chown -R dev:www-data /opt/kasaai/apps/shared/
  sudo chmod -R 755 /opt/kasaai/apps/inkwave/backend/
  sudo chmod -R 755 /opt/kasaai/apps/shared/
  find /opt/kasaai/apps/inkwave/backend -type d -name "__pycache__" -exec sudo rm -rf {} + 2>/dev/null
  sudo systemctl restart inkwave-backend.service
  ```

### 3. Check Supabase API Status
```bash
sudo systemctl status supabase-api.service --no-pager | head -20
```
- ✅ Should show: `Active: active (running)`
- ❌ If failed: Check database connection

### 4. Test Token Verification Endpoint (MOST CRITICAL!)
```bash
# Create test user
curl -s -X POST http://localhost:54321/auth/v1/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test'$(date +%s)'@example.com","password":"TestPass123!"}' > /tmp/signup_response.json

# Extract token
TOKEN=$(cat /tmp/signup_response.json | jq -r .access_token)

# Test verification
curl -s http://localhost:54321/auth/v1/user -H "Authorization: Bearer $TOKEN"
```

**Expected**: User data returned
```json
{
  "id": "...",
  "email": "...",
  "created_at": "..."
}
```

**If 404/401**: Auth endpoints missing → Restart supabase-api
```bash
sudo systemctl restart supabase-api.service
sleep 3
```

### 5. Check Nginx Supabase Proxy
```bash
grep "proxy_pass" /etc/nginx/sites-available/supabase.ailabsafrica.com.conf
```
- ✅ Should show: `proxy_pass http://localhost:54321`
- ❌ If shows 8090: Fix and reload
  ```bash
  sudo sed -i 's/localhost:8090/localhost:54321/g' /etc/nginx/sites-available/supabase.ailabsafrica.com.conf
  sudo nginx -t && sudo systemctl reload nginx
  ```

### 6. Check Database Connection
```bash
PGPASSWORD='aawwER444444' psql -h localhost -U postgres -d postgres -c "\dt auth.*"
```
- ✅ Should show: `auth | users | table`
- ❌ If fails: Create auth schema
  ```bash
  sudo -u postgres psql <<'EOF'
  CREATE SCHEMA IF NOT EXISTS auth;
  CREATE TABLE IF NOT EXISTS auth.users (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      email VARCHAR(255) UNIQUE NOT NULL,
      encrypted_password VARCHAR(255) NOT NULL,
      email_confirmed_at TIMESTAMP,
      created_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP DEFAULT NOW(),
      raw_user_meta_data JSONB DEFAULT '{}'::jsonb,
      raw_app_meta_data JSONB DEFAULT '{}'::jsonb
  );
  EOF
  ```

### 7. Test Complete Login Flow
```bash
# Signup
SIGNUP_RESPONSE=$(curl -s -X POST https://dev-inkwave-api.ailabsafrica.com/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test$(date +%s)@example.com\",\"password\":\"TestPass123!\"}")

echo "Signup Response:"
echo $SIGNUP_RESPONSE | jq .

# Check for success
echo $SIGNUP_RESPONSE | jq -e '.success == true' && echo "✅ Signup works!" || echo "❌ Signup failed!"
```

---

## 🔄 Service Restart Sequence

If all else fails, restart services in this order:

```bash
# 1. Supabase API first
sudo systemctl restart supabase-api.service
sleep 3
sudo systemctl status supabase-api.service --no-pager | head -15

# 2. InkWave Backend second
sudo systemctl restart inkwave-backend.service
sleep 5
sudo systemctl status inkwave-backend.service --no-pager | head -15

# 3. Test auth
curl -s http://localhost:54321/health && echo " ✅ Supabase OK"
curl -s http://localhost:8001/health && echo " ✅ InkWave OK"
```

---

## 📊 Health Check Dashboard

Run this to see complete status:

```bash
echo "=== SERVICE STATUS ==="
sudo systemctl status inkwave-backend.service --no-pager | head -3
sudo systemctl status supabase-api.service --no-pager | head -3

echo -e "\n=== HEALTH CHECKS ==="
echo -n "Supabase API: "
curl -s http://localhost:54321/health | jq -r .status 2>/dev/null || echo "❌ FAILED"
echo -n "InkWave Backend: "
curl -s http://localhost:8001/health | jq -r .status 2>/dev/null || echo "❌ FAILED"

echo -e "\n=== DATABASE ==="
sudo -u postgres psql -c "\dt auth.*" 2>/dev/null | grep users && echo "✅ auth.users exists" || echo "❌ auth.users missing"

echo -e "\n=== NGINX CONFIG ==="
grep -A 2 "proxy_pass" /etc/nginx/sites-available/supabase.ailabsafrica.com.conf | grep 54321 && echo "✅ Nginx proxying to correct port" || echo "❌ Wrong port in nginx"

echo -e "\n=== RECENT ERRORS ==="
sudo journalctl -u inkwave-backend.service -n 10 --no-pager | grep -i "error" || echo "✅ No recent errors"
```

---

## 🎯 Quick Fixes

### Fix 1: Permission Issues
```bash
sudo chown -R dev:www-data /opt/kasaai/apps/inkwave/backend/ /opt/kasaai/apps/shared/
sudo chmod -R 755 /opt/kasaai/apps/inkwave/backend/ /opt/kasaai/apps/shared/
find /opt/kasaai/apps -type d -name "__pycache__" -exec sudo rm -rf {} + 2>/dev/null
sudo systemctl restart inkwave-backend.service
```

### Fix 2: Nginx Port Wrong
```bash
sudo sed -i 's/localhost:8090/localhost:54321/g' /etc/nginx/sites-available/supabase.ailabsafrica.com.conf
sudo nginx -t && sudo systemctl reload nginx
```

### Fix 3: Auth Tables Missing
```bash
sudo -u postgres psql <<'EOF'
CREATE SCHEMA IF NOT EXISTS auth;
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    encrypted_password VARCHAR(255) NOT NULL,
    email_confirmed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    raw_user_meta_data JSONB DEFAULT '{}'::jsonb,
    raw_app_meta_data JSONB DEFAULT '{}'::jsonb
);
EOF
```

### Fix 4: Supabase API Not Running Auth
```bash
# Check if using correct file
grep "simple_api_with_auth.py" /opt/supabase/start_api.sh || {
    sudo sed -i 's/simple_api\.py/simple_api_with_auth.py/g' /opt/supabase/start_api.sh
    sudo systemctl restart supabase-api.service
}
```

---

## 📞 Emergency Contact Info

If issues persist after all checks:

1. Review full documentation: `/opt/kasaai/apps/inkwave/SUPABASE_AUTH_ISSUES_RESOLVED.md`
2. Check service logs: `sudo journalctl -u inkwave-backend.service -f`
3. Test auth flow manually: See section 7 above

**DO NOT** reboot the server unless absolutely necessary - restart only the specific failing service.
