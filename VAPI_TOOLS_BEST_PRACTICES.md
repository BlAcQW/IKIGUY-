# VAPI Tools Best Practices - Complete Guide

**Last Updated**: 2025-11-05
**Status**: ✅ Production Tested & Verified

---

## 🎯 Critical Requirements for Function Parameter Extraction

### Problem: Empty Arguments `{}`

**Symptom**: VAPI assistant calls functions with empty arguments despite required parameters being defined.

**Root Causes**:
1. ❌ No temperature set (or too high temperature)
2. ❌ Strict mode disabled on tool
3. ❌ Vague parameter descriptions
4. ❌ Missing system prompt guidance

---

## ✅ Solution: The 4-Point Fix

### 1. Set Optimal Assistant Temperature

**CRITICAL**: Temperature affects how well the LLM extracts parameters from conversation.

```bash
# Update assistant via VAPI API
PATCH https://api.vapi.ai/assistant/{assistant_id}
```

```json
{
  "model": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.2,  // CRITICAL: 0-0.3 for parameter extraction
    "maxTokens": 250     // Keeps responses focused
  }
}
```

**Why**: Lower temperature (0-0.3) makes the model more deterministic and reliable at extracting specific information from conversation.

**Source**: VAPI Community recommendations, verified in production

---

### 2. Enable Strict Mode on Tools

**CRITICAL**: Strict mode enforces parameter validation.

```bash
# Update tool via VAPI API
PATCH https://api.vapi.ai/tool/{tool_id}
```

```json
{
  "function": {
    "name": "your_function_name",
    "description": "Clear description. Extract ALL parameters from conversation.",
    "strict": true,  // ✅ MUST BE TRUE
    "parameters": {
      "type": "object",
      "properties": {
        "param1": {
          "type": "string",
          "description": "Specific extraction instruction - e.g., 'User's email address spelled out letter by letter'"
        },
        "param2": {
          "type": "string",
          "description": "Clear purpose - e.g., 'Email subject line - use Conference Summary for conference requests'"
        }
      },
      "required": ["param1", "param2"],
      "additionalProperties": false  // ✅ REQUIRED for strict mode
    }
  }
}
```

**Key Points**:
- ✅ `"strict": true` - Enforces all required parameters
- ✅ `"additionalProperties": false` - Only allows defined properties
- ✅ Clear `"required"` array - Lists mandatory fields
- ✅ Explicit descriptions - Tell LLM exactly what to extract

---

### 3. Write Explicit Parameter Descriptions

**BAD** ❌:
```json
{
  "to_email": {
    "type": "string",
    "description": "Recipient email address"
  }
}
```

**GOOD** ✅:
```json
{
  "to_email": {
    "type": "string",
    "description": "Recipient's email address that the user spelled out letter by letter in the conversation (e.g., 'alfred.anyan@gmail.com'). Extract this from when the user confirmed their email."
  }
}
```

**Best Practices for Descriptions**:
- 📝 Include extraction hints (e.g., "spelled out by user")
- 📝 Provide example values (e.g., "alfred.anyan@gmail.com")
- 📝 Explain the context (e.g., "for conference requests, use...")
- 📝 Guide on format (e.g., "use YYYY-MM-DD format")

---

### 4. Add System Prompt Instructions

**CRITICAL**: System prompt must explain HOW to use the function.

```markdown
📧 **Function Usage: send_email**

**When to use**: When user requests information to be sent to their email.

**Required Steps**:
1. Ask user for their email address
2. Ask them to spell it letter by letter for accuracy
3. Confirm the email address back to them
4. After confirmation, prepare comprehensive message
5. Call function with ALL required parameters

**Function Parameters** (ALL REQUIRED):
- `to_email`: The user's confirmed email address (e.g., "alfred.anyan@gmail.com")
- `subject`: A clear subject line (e.g., "Conference Summary")
- `message`: The full content to send (include all requested details)
- `customer_name`: User's name if mentioned, otherwise "Guest"

**Example Usage**:
```
User: "Send me summary to alfred.anyan@gmail.com"

Assistant should:
1. Confirm: "Let me confirm - alfred dot anyan at gmail dot com, correct?"
2. After confirmation, call function with:
{
  "to_email": "alfred.anyan@gmail.com",
  "subject": "Conference Summary",
  "message": "[Full details here]",
  "customer_name": "Alfred"  // if name was mentioned
}
```

**CRITICAL**: Always include the actual email address, subject, and message content.
Never call with empty parameters {}.

**What to include in message**:
- [Specific content guidance based on your use case]
```

---

## 🧪 Testing Your Tool

### Test Checklist

#### 1. Verify Tool Configuration
```bash
curl -H "Authorization: Bearer YOUR_VAPI_KEY" \
  https://api.vapi.ai/tool/{tool_id} | jq '.function.strict'

# Should return: true
```

#### 2. Verify Assistant Temperature
```bash
curl -H "Authorization: Bearer YOUR_VAPI_KEY" \
  https://api.vapi.ai/assistant/{assistant_id} | jq '.model.temperature'

# Should return: 0.2 (or 0-0.3 range)
```

#### 3. Test Function Call
Make a test call and check logs:

```bash
# Check backend logs for function arguments
sudo journalctl -u your-backend-service --since "1 minute ago" | grep "arguments"

# Should see actual parameters, NOT empty {}
✅ Good: {"to_email": "user@example.com", "subject": "..."}
❌ Bad:  {"arguments": {}}
```

#### 4. Verify Email Delivery
- Check recipient's inbox
- Verify content matches expectations
- Confirm all requested information included

---

## 📊 Tool Schema Template

### Complete Function Tool Schema

```json
{
  "type": "function",
  "function": {
    "name": "your_function_name",
    "description": "Clear description of what this function does. Mention that it extracts parameters from conversation.",
    "strict": true,
    "parameters": {
      "type": "object",
      "properties": {
        "param1": {
          "type": "string",
          "description": "Detailed description with extraction hints and examples"
        },
        "param2": {
          "type": "string",
          "description": "Clear purpose and format guidance"
        },
        "optional_param": {
          "type": "string",
          "description": "Description with default behavior",
          "default": "default_value"
        }
      },
      "required": ["param1", "param2"],
      "additionalProperties": false
    }
  },
  "server": {
    "url": "https://your-api.com/webhook"
  }
}
```

---

## 🔧 Common Issues & Solutions

### Issue 1: Still Getting Empty Arguments

**Check**:
1. ✅ Tool has `"strict": true`?
2. ✅ Tool has `"additionalProperties": false`?
3. ✅ Assistant temperature is 0-0.3?
4. ✅ System prompt has detailed function instructions?
5. ✅ Parameter descriptions are explicit with examples?

**Debug**:
```bash
# Get full tool configuration
curl -H "Authorization: Bearer $VAPI_KEY" \
  https://api.vapi.ai/tool/{tool_id} | jq '.'

# Get full assistant configuration
curl -H "Authorization: Bearer $VAPI_KEY" \
  https://api.vapi.ai/assistant/{assistant_id} | jq '.model'
```

### Issue 2: Parameters Missing But Not All Empty

**Cause**: Some parameters extract well, others don't.

**Solution**:
- Review descriptions for missing parameters
- Add more specific extraction hints
- Include examples in descriptions
- Mention the parameter again in system prompt

### Issue 3: Wrong Parameter Values

**Cause**: LLM misunderstands what to extract.

**Solution**:
- Make descriptions more explicit
- Add format examples (e.g., "YYYY-MM-DD")
- Use system prompt to show exact examples
- Lower temperature further (try 0.1)

### Issue 4: Inconsistent Parameter Extraction

**Cause**: High temperature causing variability.

**Solution**:
- **Lower temperature to 0.1-0.2**
- Add more examples in descriptions
- Make system prompt instructions more detailed

---

## 📝 Update Checklist for Existing Tools

When updating existing VAPI tools, follow this checklist:

### Tool Configuration
- [ ] Enable `strict: true`
- [ ] Add `additionalProperties: false`
- [ ] Review all parameter descriptions
- [ ] Add extraction hints to descriptions
- [ ] Include example values in descriptions
- [ ] Verify `required` array is complete

### Assistant Configuration
- [ ] Set temperature to 0.2 (or 0-0.3)
- [ ] Add maxTokens (recommend 250)
- [ ] Update system prompt with function usage section
- [ ] Include step-by-step workflow
- [ ] Add example function calls with real values
- [ ] Emphasize "never use empty arguments"

### Testing
- [ ] Make test call to assistant
- [ ] Check backend logs for actual parameters
- [ ] Verify all required parameters extracted
- [ ] Confirm parameter values are correct
- [ ] Test edge cases (long emails, special characters)
- [ ] Verify error handling works

---

## 🎯 Real-World Example: Email Function

### Complete Working Configuration

**Tool Definition** (`abc528ae-e1f1-4e9c-a939-bc859e5e7d88`):
```json
{
  "type": "function",
  "function": {
    "name": "send_notification_email",
    "description": "Send email notification. Extract ALL parameters from conversation.",
    "strict": true,
    "parameters": {
      "type": "object",
      "properties": {
        "to_email": {
          "type": "string",
          "description": "Recipient email address spelled out by user (e.g., 'alfred.anyan@gmail.com'). Extract from when user confirmed their email."
        },
        "subject": {
          "type": "string",
          "description": "Email subject - use 'AETF AI 2025 Conference Summary' for conference emails, or appropriate subject for other requests"
        },
        "message": {
          "type": "string",
          "description": "Full email content with all conference details, schedule, speakers, and contact information"
        },
        "customer_name": {
          "type": "string",
          "description": "User name if mentioned, otherwise 'Guest'",
          "default": "Guest"
        }
      },
      "required": ["to_email", "subject", "message"],
      "additionalProperties": false
    }
  },
  "server": {
    "url": "https://api.ailabsafrica.com/integrations/vapi-webhook"
  }
}
```

**Assistant Configuration** (`e88d3ca9-4cc8-49be-bb42-36c9b8dae6ef`):
```json
{
  "model": {
    "provider": "openai",
    "model": "gpt-4o",
    "temperature": 0.2,
    "maxTokens": 250
  }
}
```

**System Prompt** (excerpt):
```markdown
📧 **Email Tool Usage (IMPORTANT)**

Function: send_notification_email

**When to use**: When user requests information sent to their email.

**Required Steps**:
1. Ask user for their email address
2. Ask them to spell it letter by letter
3. Confirm email address back to them
4. After confirmation, prepare comprehensive message
5. Call function with ALL required parameters

[... full instructions from Solution #4 above ...]
```

**Result**: ✅ Successfully extracts all parameters from conversation

---

## 📚 Additional Resources

### VAPI Community Discussions
- [Empty Arguments Issue](https://vapi.ai/community/m/1369707288260116654)
- [Strict Parameters Discussion](https://vapi.ai/community/m/1380296269603274895)
- [Function Calling Best Practices](https://docs.vapi.ai/tools/custom-tools)

### Internal Documentation
- `AETF_ASSISTANT_EMAIL_FIX.md` - Complete fix walkthrough
- `EMAIL_MIGRATION_COMPLETE_SUMMARY.md` - Email system architecture
- `CUSTOM_TOOLS.md` - Custom tools management

### Scripts for Updates
- `fix_aetf_temperature.py` - Update assistant temperature
- `enable_strict_mode.py` - Enable strict mode on tools
- `fix_aetf_assistant_email.py` - Update system prompts

---

## 🎓 Key Takeaways

### The 4 Pillars of Reliable Parameter Extraction:

1. **📊 Temperature**: 0-0.3 for deterministic extraction
2. **🔒 Strict Mode**: Enforces parameter validation
3. **📝 Clear Descriptions**: Explicit extraction instructions with examples
4. **📋 System Prompt**: Detailed usage guide with real examples

### Remember:
- ❌ VAPI showing "Completed successfully" does NOT mean parameters were passed
- ✅ Always check backend logs for actual arguments
- ✅ Test with real user flows, not just API calls
- ✅ Lower temperature if extraction is inconsistent

---

## 🚀 Quick Start for New Tools

1. **Create tool with strict mode**:
```bash
curl -X POST https://api.vapi.ai/tool \
  -H "Authorization: Bearer $VAPI_KEY" \
  -H "Content-Type: application/json" \
  -d @tool_config.json
```

2. **Update assistant temperature**:
```bash
curl -X PATCH https://api.vapi.ai/assistant/{id} \
  -H "Authorization: Bearer $VAPI_KEY" \
  -d '{"model": {"temperature": 0.2}}'
```

3. **Add system prompt instructions**
4. **Test and verify in logs**

---

**Status**: ✅ Production Tested on AETF Assistant
**Verification**: Email function now successfully extracts all parameters
**Date**: 2025-11-05
