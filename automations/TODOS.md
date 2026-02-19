# =' VAPI Integration TODO Items

## <¯ Critical Issues Requiring Immediate Attention

### =Ê **Supabase Call Logging Integration**
**Status**: L **BROKEN** - No call data being logged to database
**Priority**: **HIGH** - Analytics and call tracking not functioning

**Root Cause**: Supabase integration failing despite:
-  Library installed (`supabase==2.18.1`)
-  Table exists (`call_logs` with proper schema)
-  Environment variables configured
- L Service role connection failing

**Tasks Required**:
1. **Debug Supabase Integration Module**
   - Check `/opt/kasaai/apps/shared/integration/supabase.py` import detection
   - Verify `SUPABASE_AVAILABLE` flag is properly set
   - Test direct connection outside health check

2. **Verify Service Role Permissions**
   - Ensure `DEMO_SUPABASE_SUPABASE_KEY` has write access to `call_logs` table
   - Check RLS (Row Level Security) policies
   - Validate service role has proper INSERT permissions

3. **Test Database Connection**
   - Manual test with service role key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ3Ym50cHpkbHJ0eGVsaXprcHJsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjY3MTA3NCwiZXhwIjoyMDcyMjQ3MDc0fQ.wTCQhurA1P_LNYwocHkq9BRrfkl9yOJxrkrYLamEhPk`
   - Verify URL: `https://fwbntpzdlrtxelizkprl.supabase.co`
   - Test INSERT operation directly

**Impact**:
- L No call analytics data
- L No usage tracking
- L No customer interaction history
-  Webhook processing still works (emails sent)

---

### <« **HubSpot Ticket Creation Integration**
**Status**: L **BLOCKED** - Missing required API scopes
**Priority**: **MEDIUM** - Escalation workflow incomplete

**Root Cause**: HubSpot Personal Access Token lacks required permissions:
- **Missing Scopes**: `tickets.sensitive.v2`, `tickets.highly_sensitive.v2`, `crm.objects.contacts.write`
- **Current Token**: `pat-na2-be182d71-d2e7-4c11-a405-d335560644db`
- **Portal ID**: `243880132`

**Tasks Required**:
1. **Update HubSpot API Token Permissions**
   - Go to HubSpot App Settings ’ Private Apps
   - Add required scopes:
     - `tickets.sensitive.v2`
     - `tickets.highly_sensitive.v2`
     - `crm.objects.contacts.write`
     - `crm.objects.contacts.read`

2. **Regenerate Access Token**
   - Create new token with full CRM permissions
   - Update `/opt/kasaai/apps/automations/examples/integration_api_keys.md`
   - Test ticket creation: `POST https://api.hubapi.com/crm/v3/objects/tickets`

3. **Test Escalation Workflow**
   - Verify VAPI assistant escalation triggers
   - Test `escalate_to_support` function calls
   - Confirm tickets appear in HubSpot portal: https://app-na2.hubspot.com/contacts/243880132/objects/0-5/views/all/list

**Current Workaround**:
-  Email notifications to `ailabsafrica@gmail.com` working
-  Escalation logic functional in assistant
- L No HubSpot ticket creation

---

##  **Completed Integrations**

### <¤ **VAPI Webhook System**
-  Webhook endpoint: `https://api.ailabsafrica.com/call-management/vapi/webhook`
-  Assistant configured: `baa69b3a-8944-4557-9ef9-3a5aa6956eb3`
-  AI-powered call summarization
-  Email notifications working
-  Real-time call processing

### <å **Healthcare Provider Tools**
-  Premier Health endpoints operational
-  Provider search functionality
-  Emergency services lookup
-  Database connectivity (PostgreSQL)

### =ç **Email System**
-  Local iRedMail server with DKIM authentication
-  Email accounts: `noreply@ailabsafrica.com`, `info@ailabsafrica.com`
-  SMTP configuration working
-  Call summary notifications automated

### =Å **Calendar Integration**
-  42+ integrations available via integrations manager
-  Calendly templates configured
-  Appointment booking logic in assistant

---

## = **Verification Commands**

### Test Supabase Connection:
```bash
curl -X POST "https://api.ailabsafrica.com/call-management/log-call" \
  -H "Content-Type: application/json" \
  -d '{"call_id": "test-123", "transcript": "test", "assistant_id": "baa69b3a-8944-4557-9ef9-3a5aa6956eb3"}'
```

### Test HubSpot Ticket Creation:
```bash
curl -X POST "https://api.hubapi.com/crm/v3/objects/tickets" \
  -H "Authorization: Bearer NEW_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"properties": {"subject": "Test Ticket", "hs_pipeline": "0", "hs_pipeline_stage": "1"}}'
```

### Check Call Logs:
```sql
SELECT call_id, assistant_id, status, created_at
FROM call_logs
ORDER BY created_at DESC
LIMIT 10;
```

---

**Last Updated**: September 22, 2025
**Integration Status**: =á Partially Functional (2 critical issues)
**Next Review**: After Supabase and HubSpot fixes