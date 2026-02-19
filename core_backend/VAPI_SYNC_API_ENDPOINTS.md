# VAPI Sync System - API Endpoints Reference

## Base URL
**Production API**: `https://flow-api.ailabsafrica.com`

---

## Endpoint Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/automation-configs/{config_id}/sync-from-vapi` | Sync automation from VAPI |
| GET | `/automation-configs/{config_id}/sync-status` | Check sync status |
| POST | `/automation-configs/import-vapi-assistant` | Import new VAPI assistant |

---

## 1. Sync from VAPI (Manual Sync)

**Endpoint**: `POST /automation-configs/{config_id}/sync-from-vapi`

**URL**: `https://flow-api.ailabsafrica.com/automation-configs/{config_id}/sync-from-vapi`

**Query Parameters**:
- `force` (boolean, optional, default: false) - Force sync even if config appears unchanged

**Headers**:
- `Authorization: Bearer {YOUR_TOKEN}`
- `Content-Type: application/json`

**Example - Premier Health Navigator**:
```bash
curl -X POST "https://flow-api.ailabsafrica.com/automation-configs/68e6a313c7e9a3a8cda05e0e/sync-from-vapi?force=true" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully synced from VAPI",
  "changed": true,
  "config_id": "68e6a313c7e9a3a8cda05e0e",
  "assistant_id": "baa69b3a-8944-4557-9ef9-3a5aa6956eb3",
  "old_hash": null,
  "new_hash": "c3a61d63fb4a1f75ef8f4c8ab8a42c91",
  "changes_summary": [
    "Transcriber keywords: 0 → 181"
  ],
  "synced_at": "2025-10-18T11:01:33.499079"
}
```

---

## 2. Check Sync Status

**Endpoint**: `GET /automation-configs/{config_id}/sync-status`

**URL**: `https://flow-api.ailabsafrica.com/automation-configs/{config_id}/sync-status`

**Headers**:
- `Authorization: Bearer {YOUR_TOKEN}`

**Example - Premier Health Navigator**:
```bash
curl "https://flow-api.ailabsafrica.com/automation-configs/68e6a313c7e9a3a8cda05e0e/sync-status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response**:
```json
{
  "success": true,
  "config_id": "68e6a313c7e9a3a8cda05e0e",
  "assistant_id": "baa69b3a-8944-4557-9ef9-3a5aa6956eb3",
  "sync_status": "synced",
  "last_synced_at": "2025-10-18 11:01:33.495000",
  "platform_hash": "c3a61d63fb4a1f75ef8f4c8ab8a42c91",
  "vapi_hash": "c3a61d63fb4a1f75ef8f4c8ab8a42c91",
  "is_synced": true
}
```

**Sync Status Values**:
- `synced` - Platform config matches VAPI config ✅
- `out_of_sync` - Configs differ, sync needed ⚠️
- `never_synced` - Never synced before
- `error` - Error checking sync status ❌

---

## 3. Import VAPI Assistant

**Endpoint**: `POST /automation-configs/import-vapi-assistant`

**URL**: `https://flow-api.ailabsafrica.com/automation-configs/import-vapi-assistant`

**Headers**:
- `Authorization: Bearer {YOUR_TOKEN}`
- `Content-Type: application/json`

**Request Body**:
```json
{
  "assistant_id": "your-vapi-assistant-id",
  "automation_name": "Optional Custom Name"
}
```

**Example**:
```bash
curl -X POST "https://flow-api.ailabsafrica.com/automation-configs/import-vapi-assistant" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "baa69b3a-8944-4557-9ef9-3a5aa6956eb3",
    "automation_name": "Premier Health Navigator"
  }'
```

**Response**: Returns complete `AutomationConfigResponse` with:
- Full VAPI agent configuration
- All transcriber settings (Deepgram keywords, etc.)
- All messages and advanced settings
- Sync status set to "synced"
- Config hash computed

---

## Usage Workflows

### Workflow 1: Update VAPI Assistant, Then Sync Platform

1. **Make changes in VAPI dashboard** (e.g., add Deepgram keywords)
2. **Check if platform is out of sync**:
   ```bash
   curl "https://flow-api.ailabsafrica.com/automation-configs/{config_id}/sync-status" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
3. **If out of sync, sync from VAPI**:
   ```bash
   curl -X POST "https://flow-api.ailabsafrica.com/automation-configs/{config_id}/sync-from-vapi?force=true" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

### Workflow 2: Import New VAPI Assistant

1. **Create assistant in VAPI dashboard**
2. **Import to platform**:
   ```bash
   curl -X POST "https://flow-api.ailabsafrica.com/automation-configs/import-vapi-assistant" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"assistant_id": "your-vapi-id"}'
   ```
3. **Platform automatically syncs complete config** ✅

### Workflow 3: Periodic Sync Check

**Recommended**: Run weekly/monthly to detect config drift

```bash
# Check all automations for sync status
# (Future enhancement: batch sync endpoint)

curl "https://flow-api.ailabsafrica.com/automation-configs/{config_id}/sync-status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Frontend Integration

The B2C portal (`https://flow.ailabsafrica.com/automations`) can display:

1. **Sync Status Badge** on each automation card:
   - 🟢 Synced
   - 🟡 Out of Sync (with "Sync Now" button)
   - ⚪ Never Synced
   - 🔴 Sync Error

2. **Sync Button** in automation settings:
   - Triggers `/sync-from-vapi` endpoint
   - Shows sync progress and results
   - Displays change summary

3. **Last Synced Timestamp**:
   - Display `vapi_last_synced_at` on automation details
   - Show relative time (e.g., "Synced 2 hours ago")

---

## Authentication

All endpoints require valid JWT token in `Authorization` header:

```
Authorization: Bearer {SUPABASE_JWT_TOKEN}
```

Tokens are issued by Supabase authentication and include:
- User ID
- Organization context
- Permissions

---

## Error Handling

### Common Errors:

**404 Not Found**:
- Automation config not found
- User doesn't have access to automation

**401 Unauthorized**:
- Missing or invalid JWT token
- Token expired

**500 Internal Server Error**:
- VAPI API key not configured
- VAPI API unavailable
- Assistant not found in VAPI
- Database connection error

**Example Error Response**:
```json
{
  "detail": "Automation config not found"
}
```

---

## Testing

### Quick Test - Premier Health Navigator:

```bash
# 1. Check sync status
curl "https://flow-api.ailabsafrica.com/automation-configs/68e6a313c7e9a3a8cda05e0e/sync-status" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. Force sync
curl -X POST "https://flow-api.ailabsafrica.com/automation-configs/68e6a313c7e9a3a8cda05e0e/sync-from-vapi?force=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Rate Limiting

Currently no rate limiting implemented. Future considerations:
- Max 10 syncs per minute per automation
- Max 100 syncs per hour per organization

---

## Monitoring

Sync operations are logged with:
- User ID who initiated sync
- Timestamp
- Success/failure status
- Changes detected

Check logs:
```bash
sudo journalctl -u kasaai-core-backend -f | grep "VAPI sync"
```

---

## Related Documentation

- **Full System Documentation**: `/opt/kasaai/apps/core_backend/VAPI_SYNC_SYSTEM.md`
- **Nginx Configuration**: `/etc/nginx/sites-enabled/flow-api.ailabsafrica.com.conf`
- **Service File**: `/etc/systemd/system/kasaai-core-backend.service`
- **Backend Port**: 30027

---

## Support

For issues or questions:
- Check backend logs: `sudo journalctl -u kasaai-core-backend -n 100`
- Verify VAPI API key is configured
- Ensure automation exists and user has access
- Test VAPI API connectivity: `curl https://api.vapi.ai/assistant/{id} -H "Authorization: Bearer {VAPI_KEY}"`
