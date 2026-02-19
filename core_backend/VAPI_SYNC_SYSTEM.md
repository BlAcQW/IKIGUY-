# VAPI Synchronization System

## Overview

Complete synchronization system between VAPI assistants and platform automation configs. Ensures that all VAPI assistant settings (including Deepgram keywords, transcriber settings, messages, and advanced configurations) are captured and kept in sync with the platform.

## Implementation Date
October 18, 2025

---

## Key Features

### ✅ **Comprehensive VAPI Config Capture**
The system now captures **ALL** VAPI assistant settings:

- **Core Settings**: assistant_id, name, system_prompt, voice_settings
- **Transcriber**: Deepgram keywords, keyterms, model, language, endpointing, smart_format
- **LLM Model**: provider, model, temperature, max_tokens, penalties
- **Messages**: first_message, voicemail_message, end_call_message
- **Call Behavior**: silence_timeout, max_duration, background_denoising
- **Advanced**: analysis_plan, artifact_plan, server_messages, start_speaking_plan
- **Features**: dial_keypad_enabled, end_call_function_enabled, recording_enabled
- **Full Config**: Complete VAPI JSON response stored for reference

### ✅ **Sync Status Tracking**
Automations now have sync metadata:
- `vapi_sync_status`: "synced", "out_of_sync", "never_synced", "error"
- `vapi_last_synced_at`: Timestamp of last successful sync
- `vapi_config_hash`: MD5 hash for change detection
- `full_vapi_config`: Complete VAPI assistant JSON

### ✅ **Automatic Sync on Import**
When importing a VAPI assistant via `/import-vapi-assistant`, the system now:
1. Fetches complete VAPI config
2. Extracts ALL settings (not just basic fields)
3. Stores comprehensive VAPIAgent model
4. Sets sync status to "synced"
5. Stores config hash for future change detection

---

## API Endpoints

### 1. **Sync from VAPI** (Manual Sync)

```bash
POST /automation-configs/{config_id}/sync-from-vapi?force=true
```

**Purpose**: Fetch latest VAPI assistant config and update platform automation.

**Query Parameters**:
- `force` (optional, default: false) - Force sync even if config appears unchanged

**Response**:
```json
{
  "success": true,
  "changed": true,
  "config_id": "68e6a313c7e9a3a8cda05e0e",
  "assistant_id": "baa69b3a-8944-4557-9ef9-3a5aa6956eb3",
  "old_hash": "abc123...",
  "new_hash": "def456...",
  "changes_summary": [
    "Transcriber keywords: 0 → 181"
  ],
  "synced_at": "2025-10-18T11:01:33.499079"
}
```

**Use Cases**:
- After updating VAPI assistant in VAPI dashboard
- Periodically to ensure configs stay in sync
- When adding/modifying Deepgram keywords in VAPI

---

### 2. **Check Sync Status**

```bash
GET /automation-configs/{config_id}/sync-status
```

**Purpose**: Check if platform config is in sync with current VAPI config.

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

**Sync Statuses**:
- `synced`: Platform config matches VAPI config
- `out_of_sync`: Configs differ (manual sync needed)
- `never_synced`: Automation never synced with VAPI
- `error`: Error checking sync status

---

## Premier Health Navigator - Sync Results

### ✅ **Successful Sync Completed**

**Automation ID**: `68e6a313c7e9a3a8cda05e0e`
**VAPI Assistant ID**: `baa69b3a-8944-4557-9ef9-3a5aa6956eb3`
**Sync Date**: October 18, 2025 @ 11:01:33 UTC

### **Captured Settings**:

#### 📞 **Transcriber (Deepgram)**
- **Provider**: deepgram
- **Model**: nova-3
- **Language**: en-GB
- **Endpointing**: 300ms
- **Smart Format**: Enabled
- **Keywords**: 181 single-word location names
  - Sample: Abelenkpe, Accra, Adenta, Ashaiman, Bolgatanga, Dansoman, EastLegon, Ho, Kumasi, Madina, Nkawkaw, Osu, Sakumono, Sunyani, Takoradi, Tamale, Tema, etc.
- **Keyterms**: 64 multi-word phrases (54 locations + 10 medical specialties)
  - Location samples: "East Legon Adjringanor", "Airport Residential Area 37 Area", "Tema Community 2", "Korle Bu", "Mamponteng"
  - Medical specialties: cardiologist, dermatologist, emergency medicine, general practitioner, gynecologist, internal medicine, ophthalmologist, orthopedic surgeon, pediatrician

#### 🤖 **LLM Model**
- **Provider**: openai
- **Model**: gpt-4-turbo
- **Temperature**: 0.7

#### 💬 **Messages**
- **First Message**: "Hello! I'm Ama, your Healthcare Navigator with Premier Health Insurance..."

#### ⚙️ **Call Settings**
- **Max Duration**: 900 seconds (15 minutes)
- **Silence Timeout**: 30 seconds
- **Background Denoising**: Enabled

#### 📦 **Additional Data**
- **Full VAPI Config**: Complete JSON stored (17 top-level keys)
- **Config Hash**: `c3a61d63fb4a1f75ef8f4c8ab8a42c91`
- **Sync Status**: `synced` ✅

---

## Code Architecture

### Files Created/Modified

#### 1. **Models** (`backend/models/automation_config.py`)
- Added `SyncStatus` enum
- Enhanced `VAPIAgent` model with comprehensive fields:
  - `TranscriberSettings` - STT config with keywords/keyterms
  - `ModelSettings` - LLM configuration
  - All VAPI message fields
  - Advanced settings (analysis plans, artifacts, etc.)
- Added sync metadata to `AutomationConfig` model

#### 2. **Sync Service** (`backend/services/vapi_sync_service.py`)
New service with:
- `fetch_vapi_config()` - Fetch from VAPI API
- `sync_config_from_vapi()` - Sync platform config from VAPI
- `check_sync_status()` - Compare platform vs VAPI configs
- `_compute_config_hash()` - MD5 hash for change detection
- `_extract_vapi_agent()` - Extract comprehensive VAPIAgent
- `_extract_transcriber_settings()` - Extract Deepgram config
- `_extract_model_settings()` - Extract LLM config

#### 3. **API Routes** (`backend/routes/automation_configs.py`)
- Updated `import-vapi-assistant` endpoint to use comprehensive extraction
- Added `POST /{config_id}/sync-from-vapi` endpoint
- Added `GET /{config_id}/sync-status` endpoint

---

## Usage Examples

### Example 1: Manual Sync After VAPI Update

```python
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from core_backend.backend.services.vapi_sync_service import VAPISyncService

async def sync_automation():
    client = AsyncIOMotorClient('mongodb://...')
    db = client['kasaai_core']

    sync_service = VAPISyncService(db)
    sync_service.vapi_service.api_key = 'your-vapi-api-key'

    # Sync automation
    result = await sync_service.sync_config_from_vapi(
        config_id='68e6a313c7e9a3a8cda05e0e',
        force=True
    )

    print(f"Sync result: {result}")

asyncio.run(sync_automation())
```

### Example 2: Check Sync Status

```python
async def check_status():
    client = AsyncIOMotorClient('mongodb://...')
    db = client['kasaai_core']

    sync_service = VAPISyncService(db)
    sync_service.vapi_service.api_key = 'your-vapi-api-key'

    # Check status
    result = await sync_service.check_sync_status('68e6a313c7e9a3a8cda05e0e')

    if result['is_synced']:
        print("✅ Config is in sync!")
    else:
        print("⚠️ Config is out of sync - manual sync needed")

asyncio.run(check_status())
```

### Example 3: Import New Assistant

```bash
curl -X POST "https://flow-api.ailabsafrica.com/automation-configs/import-vapi-assistant" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "your-vapi-assistant-id",
    "automation_name": "My New Assistant"
  }'
```

**Result**: Complete VAPI config captured on import (including transcriber keywords, messages, etc.)

---

## Benefits

### ✅ **No More Lost Settings**
- Deepgram keywords no longer missed
- Transcriber settings preserved
- All VAPI messages captured
- Advanced configurations synced

### ✅ **Change Detection**
- Hash-based comparison detects config drift
- Sync status shows when update needed
- Changes summary shows what changed

### ✅ **Analytics Still Working**
- Existing analytics system unchanged
- Still fetches calls, costs, details from VAPI
- No disruption to existing features

### ✅ **Future-Proof**
- Full VAPI JSON stored for reference
- Easy to add new fields as VAPI evolves
- Backward compatible with existing automations

---

## Future Enhancements

### Potential Additions:
1. **Scheduled Sync**: Background cron job to auto-sync all automations daily
2. **Webhook Integration**: VAPI webhooks to trigger sync on assistant updates
3. **Bi-Directional Sync**: Push platform changes back to VAPI
4. **Sync History**: Track sync history and changes over time
5. **Batch Sync**: Sync multiple automations at once
6. **UI Integration**: Show sync status in frontend dashboard

---

## Troubleshooting

### Sync Failed - API Key Error
**Solution**: Ensure VAPI_API_KEY is configured in environment/service

### Sync Shows Out of Sync But Configs Match
**Solution**: Use `force=true` to force re-sync and update hash

### Missing Transcriber Keywords After Sync
**Issue**: Check if keywords are in VAPI assistant config
**Solution**: Verify keywords in VAPI dashboard, then re-sync

---

## Testing Checklist

- [x] VAPIAgent model captures all fields
- [x] Sync metadata added to AutomationConfig
- [x] Import endpoint uses comprehensive extraction
- [x] Sync service created and functional
- [x] Sync-from-vapi endpoint works
- [x] Sync-status endpoint works
- [x] Premier Health synced successfully
- [x] 181 Deepgram keywords captured
- [x] Transcriber settings preserved
- [x] Model settings captured
- [x] Messages captured
- [x] Full VAPI config stored
- [x] Config hash computed correctly
- [x] Sync status tracking works
- [x] Change detection functional
- [x] Analytics unchanged and working

---

## Conclusion

The VAPI sync system is now **production-ready** and has been successfully tested with the Premier Health Navigator automation. All VAPI assistant settings are now captured and can be kept in sync with the platform.

**Key Achievement**: The 181 Deepgram location keywords for Premier Health are now safely stored in the platform's MongoDB automation config and will be preserved through future syncs.
