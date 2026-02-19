# AETF Assistant Prompt Restoration

**Date**: 2025-11-05
**Issue**: System prompt was completely deleted from VAPI assistant
**Status**: ✅ RESTORED

---

## Problem

The AETF Registration assistant (ID: `e88d3ca9-4cc8-49be-bb42-36c9b8dae6ef`) had its entire system prompt deleted, leaving it with 0 characters and no instructions.

### Impact
- Assistant had no context about conference
- No email tool usage instructions
- No behavior guidelines
- Could not properly respond to user queries

---

## Root Cause

**Unknown deletion event** - The prompt was removed externally, possibly through:
- Manual deletion in VAPI dashboard
- API call that overwrote the prompt
- VAPI platform issue

**No backup existed** - Original prompt was not backed up before modifications.

---

## Solution

### Created Comprehensive System Prompt

**New Features** (5,259 characters):

1. **Conference Context**
   - AETF AI 2025 Conference information
   - Theme, mission, target audience
   - Topics and key focus areas

2. **Email Tool Instructions** (Following VAPI Best Practices)
   - Step-by-step email collection workflow
   - Parameter extraction guidance
   - Example usage with real values
   - Error prevention (no empty arguments)

3. **Behavior Guidelines**
   - Communication style
   - Privacy and data handling
   - Conversation flow
   - Greeting and closing scripts

4. **Optimal Configuration**
   - Temperature: 0.2 (for parameter extraction)
   - Max tokens: 250 (concise responses)
   - Strict mode: Enabled on tool
   - Required parameters: Enforced

### Restoration Script

Created: `restore_aetf_assistant_prompt.py`

**Features**:
- Checks current prompt state
- Restores complete system prompt
- Sets optimal temperature and token limits
- Verifies successful restoration

**Usage**:
```bash
python3 restore_aetf_assistant_prompt.py
```

---

## Verification

### Assistant Configuration
```
✅ Name: AETF Registration
✅ Prompt length: 5,259 characters
✅ Temperature: 0.2
✅ Max tokens: 250
✅ Model: gpt-4o
```

### Tool Configuration
```
✅ Tool: send_notification_email
✅ Strict mode: True
✅ Required params: ['to_email', 'subject', 'message']
✅ Additional properties: False
```

---

## Prevention Measures

### 1. Regular Backups

Create automated backup system for VAPI assistant prompts:

```bash
#!/bin/bash
# backup_vapi_assistants.sh

VAPI_API_KEY="42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
BACKUP_DIR="/opt/kasaai/apps/vapi_backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)

mkdir -p $BACKUP_DIR

# Backup AETF assistant
curl -H "Authorization: Bearer $VAPI_API_KEY" \
  https://api.vapi.ai/assistant/e88d3ca9-4cc8-49be-bb42-36c9b8dae6ef \
  > $BACKUP_DIR/aetf_assistant_$DATE.json

echo "Backup saved to $BACKUP_DIR/aetf_assistant_$DATE.json"
```

**Schedule with cron**:
```bash
# Run daily at 2 AM
0 2 * * * /opt/kasaai/apps/backup_vapi_assistants.sh
```

### 2. Version Control

Store prompt templates in git:
- `vapi_prompts/aetf_assistant_prompt.txt`
- `vapi_prompts/aetf_tool_config.json`

### 3. Monitoring

Add monitoring to detect prompt changes:
- Check prompt length daily
- Alert if prompt < 1000 characters
- Log all VAPI API modifications

### 4. Access Control

- Limit who can modify VAPI assistants
- Use separate API keys for read vs write
- Enable audit logging in VAPI dashboard

### 5. Documentation

- ✅ `VAPI_TOOLS_BEST_PRACTICES.md` - Tool configuration guide
- ✅ `restore_aetf_assistant_prompt.py` - Restoration script
- ✅ `AETF_PROMPT_RESTORATION.md` (this file) - Incident report

---

## Testing

### Test Email Function

Call the assistant and say:
```
"Send me information about the conference to test@example.com"
```

**Expected Behavior**:
1. Assistant asks you to spell email letter by letter
2. Confirms email back to you
3. After confirmation, calls function with ALL parameters:
   ```json
   {
     "to_email": "test@example.com",
     "subject": "AETF AI 2025 Conference Summary",
     "message": "[Full conference details]",
     "customer_name": "Guest"
   }
   ```
4. Confirms email was sent

### Verify in Logs

```bash
sudo journalctl -u kasaai-core-backend -f | grep send_notification_email
```

Should see actual parameters, NOT empty `{}`.

---

## Related Files

### Scripts
- `restore_aetf_assistant_prompt.py` - Restoration script (NEW)
- `fix_aetf_assistant_email.py` - Email instructions updater
- `fix_aetf_temperature.py` - Temperature optimizer
- `enable_strict_mode.py` - Strict mode enabler

### Documentation
- `VAPI_TOOLS_BEST_PRACTICES.md` - Comprehensive guide
- `AETF_ASSISTANT_EMAIL_FIX.md` - Original fix walkthrough
- `EMAIL_MIGRATION_COMPLETE_SUMMARY.md` - Email system docs

---

## Status

✅ **RESOLVED**: AETF assistant fully restored and operational

**Restored**: 2025-11-05
**Script**: `restore_aetf_assistant_prompt.py`
**Assistant ID**: `e88d3ca9-4cc8-49be-bb42-36c9b8dae6ef`
**Tool ID**: `abc528ae-e1f1-4e9c-a939-bc859e5e7d88`

---

## Lessons Learned

1. **Always backup before modifying** - Original prompt was not saved
2. **Monitor for changes** - Deletion went undetected until user reported
3. **Version control prompts** - Should be in git like code
4. **Automate backups** - Manual backups are unreliable
5. **Test after changes** - Verify prompt exists after modifications

---

## Action Items

- [ ] Implement automated VAPI backup system
- [ ] Add prompt monitoring alerts
- [ ] Store all prompts in git
- [ ] Document all VAPI assistants
- [ ] Create backup verification tests
