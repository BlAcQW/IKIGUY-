# Pull VAPI Config Feature - Frontend Integration

## Overview
Added "Pull VAPI Config" menu item to the Automations page, allowing users to manually sync their automation configurations from VAPI with a single click.

**Implementation Date**: October 18, 2025

---

## Feature Details

### **Menu Item Location**
Available in the **Actions** dropdown menu (⋮) for deployed automations on the Automations page.

**Path**: `https://flow.ailabsafrica.com/automations`

### **Where It Appears**
- ✅ **Table View**: Actions column dropdown
- ✅ **Card View**: Card dropdown menu
- 📍 **Position**: After "View Analytics", before "Edit Configuration"

### **Visual Design**
- **Icon**: 🔄 RefreshCw (rotating arrows)
- **Color**: Orange (text-orange-600)
- **Label**: "Pull VAPI Config"

---

## Functionality

### **What It Does**
1. User clicks "Pull VAPI Config" from automation actions menu
2. Shows toast notification: "Syncing from VAPI - Pulling latest configuration..."
3. Calls API endpoint: `POST /automation-configs/{id}/sync-from-vapi?force=true`
4. Displays result:
   - ✅ **Success**: Shows changes detected (e.g., "Transcriber keywords: 0 → 181")
   - ⚠️ **No Changes**: "Configuration is already up-to-date"
   - ❌ **Error**: Shows error message
5. Refreshes automations list to reflect updated config

### **API Endpoint Used**
```
POST https://flow-api.ailabsafrica.com/automation-configs/{config_id}/sync-from-vapi?force=true
```

---

## Code Changes

### **File Modified**: `/opt/kasaai/apps/b2c-portal/src/pages/Automations.tsx`

#### 1. **Added Import**
```typescript
import {
  // ... existing imports
  RefreshCw  // Added for sync icon
} from 'lucide-react';
```

#### 2. **Added Handler Function**
```typescript
// Pull VAPI config (sync from VAPI)
const handlePullVapiConfig = async (automationId: string, automationName: string) => {
  try {
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://flow-api.ailabsafrica.com';
    const headers = await getAuthHeaders();

    toast({
      title: "Syncing from VAPI",
      description: `Pulling latest configuration for ${automationName}...`
    });

    const response = await fetch(
      `${API_BASE_URL}/automation-configs/${automationId}/sync-from-vapi?force=true`,
      {
        method: 'POST',
        headers
      }
    );

    if (!response.ok) {
      throw new Error('Failed to sync from VAPI');
    }

    const result = await response.json();

    if (result.success) {
      const changeMessage = result.changed
        ? result.changes_summary?.length > 0
          ? `Updated: ${result.changes_summary.join(', ')}`
          : 'Configuration updated successfully'
        : 'Configuration is already up-to-date';

      toast({
        title: "VAPI Sync Complete",
        description: changeMessage
      });
      fetchAutomations();
    } else {
      toast({
        title: "Sync failed",
        description: result.error || "Failed to sync from VAPI",
        variant: "destructive"
      });
    }
  } catch (error) {
    console.error('Error syncing from VAPI:', error);
    toast({
      title: "Sync failed",
      description: "Failed to pull VAPI configuration. Please try again.",
      variant: "destructive"
    });
  }
};
```

#### 3. **Added Menu Item** (in both Table & Card views)
```typescript
<DropdownMenuItem onClick={() => handlePullVapiConfig(automation.id, automation.automation_name)}>
  <RefreshCw className="h-4 w-4 mr-2 text-orange-600" />
  Pull VAPI Config
</DropdownMenuItem>
```

---

## User Experience Flow

### **Scenario 1: User Updates VAPI Assistant (e.g., adds Deepgram keywords)**

1. **User edits assistant in VAPI dashboard**
   - Adds 181 Deepgram keywords for Ghana locations
   - Updates transcriber settings
   - Modifies first message

2. **User opens platform** → Automations page
   - Sees Premier Health Navigator automation
   - Clicks Actions (⋮) dropdown

3. **User clicks "Pull VAPI Config"**
   - Toast shows: "Syncing from VAPI - Pulling latest configuration..."
   - Backend fetches latest VAPI config
   - Compares with platform config

4. **User sees result**
   - Toast shows: "VAPI Sync Complete - Updated: Transcriber keywords: 0 → 181"
   - Automation refreshes with latest config

5. **Config is now synced** ✅
   - All 181 keywords stored in MongoDB
   - Transcriber settings updated
   - Messages updated

---

## Use Cases

### **1. After VAPI Updates**
**When**: You update assistant settings directly in VAPI dashboard
**Action**: Click "Pull VAPI Config" to sync changes to platform

### **2. Config Drift Detection**
**When**: Platform config differs from VAPI
**Action**: Pull latest config to ensure sync

### **3. Recover Missing Settings**
**When**: Some settings weren't captured during initial import
**Action**: Use pull to fetch complete config

### **4. Multiple Team Members**
**When**: Team members edit VAPI assistant externally
**Action**: Pull config to stay synchronized

---

## Technical Details

### **API Response Format**

**Success with Changes**:
```json
{
  "success": true,
  "changed": true,
  "config_id": "68e6a313c7e9a3a8cda05e0e",
  "assistant_id": "baa69b3a-8944-4557-9ef9-3a5aa6956eb3",
  "changes_summary": [
    "Transcriber keywords: 0 → 181"
  ],
  "synced_at": "2025-10-18T11:01:33.499079"
}
```

**Success with No Changes**:
```json
{
  "success": true,
  "changed": false,
  "message": "Config already up-to-date"
}
```

**Error**:
```json
{
  "success": false,
  "error": "VAPI API key not configured"
}
```

### **Toast Notifications**

| Status | Title | Description |
|--------|-------|-------------|
| Loading | "Syncing from VAPI" | "Pulling latest configuration for {name}..." |
| Success (Changed) | "VAPI Sync Complete" | "Updated: {changes_summary}" |
| Success (No Change) | "VAPI Sync Complete" | "Configuration is already up-to-date" |
| Error | "Sync failed" | Error message from API |

---

## Testing

### **Manual Test - Premier Health Navigator**

1. **Open**: https://flow.ailabsafrica.com/automations
2. **Find**: Premier Health Navigator automation
3. **Click**: Actions (⋮) → "Pull VAPI Config"
4. **Verify**:
   - Toast shows "Syncing from VAPI..."
   - API call to `/sync-from-vapi` succeeds
   - Toast shows "VAPI Sync Complete" with changes
   - Automation list refreshes

### **Expected Result**:
```
✅ VAPI Sync Complete
Updated: Transcriber keywords: 0 → 181
```

---

## Benefits

### **For Users**
- ✅ **One-Click Sync**: No manual data entry
- ✅ **Visual Feedback**: Clear toast notifications
- ✅ **Change Detection**: See what was updated
- ✅ **Error Handling**: Clear error messages

### **For Administrators**
- ✅ **Config Integrity**: Ensures platform matches VAPI
- ✅ **Audit Trail**: Sync timestamps tracked
- ✅ **Troubleshooting**: Easy to re-sync if issues occur

---

## Keywords vs Keyterms

### **Current Status** (as of Oct 18, 2025):

**Premier Health Navigator**:
- ✅ **Keywords**: 181 single-word Ghana location names
- ✅ **Keyterms**: 64 multi-word phrases (54 locations + 10 medical specialties)

**What's the Difference?**

| Field | Purpose | Example |
|-------|---------|---------|
| **keywords** | Single-word location names | "Accra", "Kumasi", "EastLegon", "Tamale" |
| **keyterms** | Multi-word phrases | "East Legon Adjringanor", "Airport Residential Area 37 Area", "Tema Community 2" |

**Keyterm Examples**:
- **Location phrases**: "East Legon Adjringanor", "Dansoman Mamprobi Korle Bu", "Airport Residential Area 37 Area"
- **Medical specialties**: "cardiologist", "emergency medicine", "general practitioner", "orthopedic surgeon"

**Technical Note**: VAPI uses the field name `keyterm` (singular) in their API, but our platform normalizes it to `keyterms` (plural) for consistency. The sync service handles both formats automatically.

---

## Future Enhancements

### **Potential Improvements**:

1. **Sync Status Indicator**
   - Show sync badge on automation card (🟢 Synced, 🟡 Out of Sync)
   - Display last sync timestamp

2. **Batch Sync**
   - "Sync All" button to sync multiple automations
   - Scheduled auto-sync (daily/weekly)

3. **Sync History**
   - View sync history with timestamps
   - See what changed in each sync

4. **Conflict Resolution**
   - Detect conflicts between platform and VAPI
   - Allow users to choose which to keep

5. **Bi-Directional Sync**
   - Push platform changes back to VAPI
   - Two-way sync capability

---

## Related Documentation

- **Backend API**: `/opt/kasaai/apps/core_backend/VAPI_SYNC_API_ENDPOINTS.md`
- **System Documentation**: `/opt/kasaai/apps/core_backend/VAPI_SYNC_SYSTEM.md`
- **Frontend Source**: `/opt/kasaai/apps/b2c-portal/src/pages/Automations.tsx`

---

## Support

### **If Sync Fails**:

1. **Check Backend Logs**:
   ```bash
   sudo journalctl -u kasaai-core-backend -n 50 | grep "VAPI sync"
   ```

2. **Verify VAPI API Key**: Ensure `VAPI_API_KEY` is configured in backend

3. **Test API Directly**:
   ```bash
   curl -X POST "https://flow-api.ailabsafrica.com/automation-configs/{id}/sync-from-vapi" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

4. **Check Automation ID**: Ensure automation exists and has `assistant_id`

---

## Deployment

### **Build & Deploy**:
```bash
cd /opt/kasaai/apps/b2c-portal
npm run build
```

### **Service**:
- Frontend hosted at: `https://flow.ailabsafrica.com`
- Nginx config: `/opt/kasaai/nginx/flow.ailabsafrica.com.conf`

---

**Feature Status**: ✅ **Production Ready**
**Last Updated**: October 18, 2025
