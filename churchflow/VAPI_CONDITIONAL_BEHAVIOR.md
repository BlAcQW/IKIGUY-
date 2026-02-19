# VAPI Conditional Behavior - Web vs Phone Calls

## Overview
Papa assistant now has **intelligent conditional behavior** that automatically detects whether a call is from the web (browser) or a phone (PSTN) and behaves accordingly.

## The Problem
- **Web calls (WebRTC)** cannot be transferred to phone numbers
- Attempting to transfer web calls results in errors
- Phone calls CAN be transferred using VAPI's transferCall function

## The Solution
Use VAPI's **dynamic variables** feature to pass call source information and instruct the AI to behave differently.

## Implementation

### 1. Dynamic Variable in System Prompt
**Variable:** `{{callSource}}`

The system prompt now includes:
```
### **CALL SOURCE DETECTION**

**IMPORTANT**: Check the {{callSource}} variable:
- If {{callSource}} is "web" → You are in a BROWSER CALL (WebRTC)
- If {{callSource}} is "phone" or empty → You are in a PHONE CALL (PSTN)
```

### 2. Conditional Instructions

#### For Web Calls (`callSource = "web"`):
```
You CANNOT transfer browser calls. Instead:

1. Answer basic questions about service times, locations, church information
2. For complex requests (tithes, offerings, bookings, complaints):
   - Warmly acknowledge their request
   - Collect their first name and phone number
   - Say: "Thank you [name]. I've noted your request about [topic].
     Someone from our team will call you back at [phone number]
     within 24 hours to assist you properly."
3. NEVER say you will transfer them
4. NEVER attempt to use the transferCall function
```

#### For Phone Calls (`callSource = "phone"` or empty):
```
You CAN transfer phone calls. When users need help:

1. Gather basic information: First name and nature of request
2. Transfer immediately by calling the transferCall function when:
   - They want to pay tithe or give an offering
   - They want to book services
   - They want to make a complaint
```

### 3. Web Widget Configuration
**File:** `apps/churchflow/frontend/src/pages/TalkToPapa.tsx`

Added `assistant-overrides` attribute:
```html
<vapi-widget
  assistant-id="c2854d74-dafe-445c-8c34-1326c2310cb7"
  assistant-overrides='{"variableValues": {"callSource": "web"}}'
  ...
></vapi-widget>
```

This passes `callSource: "web"` to the assistant, triggering web-specific behavior.

### 4. Phone Call Configuration
When making phone calls via VAPI API, either:
- Don't set `callSource` (defaults to phone behavior)
- Or explicitly pass: `assistantOverrides: { variableValues: { callSource: "phone" }}`

## How It Works

### Flow Diagram

```
┌─────────────────┐
│   User Call     │
└────────┬────────┘
         │
         ├──────────────┬──────────────┐
         │              │              │
    ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
    │   Web   │    │  Phone  │   │ No Var  │
    │ Widget  │    │  Call   │   │   Set   │
    └────┬────┘    └────┬────┘   └────┬────┘
         │              │              │
         │              │              │
    callSource     callSource     callSource
    = "web"        = "phone"      = undefined
         │              │              │
         │              │              │
    ┌────▼──────────────▼──────────────▼────┐
    │        Papa Assistant Receives         │
    │       {{callSource}} Variable          │
    └────┬──────────────┬──────────────┬─────┘
         │              │              │
    ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
    │  "web"  │    │ "phone" │   │  empty  │
    └────┬────┘    └────┬────┘   └────┬────┘
         │              │              │
    ┌────▼────────┐     └──────┬───────┘
    │ CALLBACK    │            │
    │ BEHAVIOR:   │       ┌────▼────────┐
    │ - Basic Q&A │       │ TRANSFER    │
    │ - Collect   │       │ BEHAVIOR:   │
    │   name &    │       │ - Gather    │
    │   phone     │       │   info      │
    │ - Promise   │       │ - Call      │
    │   callback  │       │   transferCall│
    │ - No        │       │ - Live      │
    │   transfer  │       │   handoff   │
    └─────────────┘       └─────────────┘
```

## Testing

### Test Web Call (Callback Behavior)
1. Visit: https://churchflow.ailabsafrica.com/talk-to-papa
2. Click "Start" and allow microphone
3. Say: "I want to pay my tithe"
4. **Expected:** Papa asks for your name and phone, promises callback
5. **NOT Expected:** Papa tries to transfer

### Test Phone Call (Transfer Behavior)
1. Use VAPI dashboard or API to initiate phone call
2. Don't set `callSource` or set it to "phone"
3. Say: "I want to pay my tithe"
4. **Expected:** Papa transfers the call to +233548480355
5. **NOT Expected:** Papa asks for callback info

## Technical Details

### VAPI Dynamic Variables
- **Syntax:** `{{variableName}}` in system prompt
- **Set via:** `assistantOverrides.variableValues` in API/widget
- **Scope:** Available only in system prompt and dashboard messages
- **Reference:** [VAPI Variables Documentation](https://docs.vapi.ai/assistants/dynamic-variables)

### Assistant Configuration
- **Assistant ID:** c2854d74-dafe-445c-8c34-1326c2310cb7
- **Variable:** `{{callSource}}`
- **Values:** "web" | "phone" | undefined
- **Transfer Number:** +233548480355

## User Experience

### Web Call Experience
```
User: "I need to book a wedding"
Papa: "I'd be happy to help you with that! May I have your first name?"
User: "John"
Papa: "Thank you, John. And what's the best phone number to reach you?"
User: "0548480355"
Papa: "Perfect, John. I've noted that you'd like to book a wedding.
      Someone from our events team will call you at 0548480355
      within 24 hours to assist you properly. Is there anything
      else I can help answer right now?"
```

### Phone Call Experience
```
User: "I need to book a wedding"
Papa: "I'd be happy to help you with that! May I have your first name?"
User: "John"
Papa: "Thank you, John. I will connect you now so someone can
      assist you properly. Please hold on a moment."
[Call transfers to +233548480355]
```

## Benefits

1. **No Failed Transfers:** Web calls never attempt impossible transfers
2. **Better UX:** Clear expectations set for web users
3. **Consistent Behavior:** Phone calls work as before
4. **Single Assistant:** One assistant handles both scenarios
5. **Easy Updates:** Change behavior by updating system prompt
6. **Scalable:** Can add more call sources (e.g., "mobile-app", "sms")

## Future Enhancements

### Possible Additions:
1. **Save callback requests to database:**
   - Store name, phone, request type, timestamp
   - Create admin dashboard to view callback queue
   - Send notifications to team

2. **Different behavior for different web pages:**
   - Landing page: callSource = "web-public"
   - Member portal: callSource = "web-member"
   - Adjust assistant tone/permissions accordingly

3. **SMS integration:**
   - callSource = "sms"
   - Text-based responses only
   - Collect info for callback

4. **Analytics:**
   - Track web vs phone call volume
   - Callback request conversion rates
   - Response time metrics

## Files Modified

```
apps/churchflow/
├── frontend/src/pages/TalkToPapa.tsx (MODIFIED)
│   └── Added assistant-overrides='{"variableValues": {"callSource": "web"}}'
│
└── VAPI_CONDITIONAL_BEHAVIOR.md (NEW)

VAPI Assistant Configuration:
└── Assistant ID: c2854d74-dafe-445c-8c34-1326c2310cb7
    ├── System prompt updated with {{callSource}} variable
    ├── Conditional instructions for web vs phone
    └── Transfer tool available for phone calls only
```

## Troubleshooting

### Web calls still trying to transfer
- **Check:** Widget has `assistant-overrides` attribute
- **Verify:** JSON is properly formatted: `'{"variableValues": {"callSource": "web"}}'`
- **Test:** Check VAPI call logs to see if variable is received

### Phone calls not transferring
- **Check:** `callSource` is NOT set to "web" for phone calls
- **Verify:** transferCall tool is configured on assistant
- **Test:** Check if transferCall appears in call transcript

### Variable not working
- **Check:** Variable uses correct syntax: `{{callSource}}` (double braces)
- **Verify:** Variable is referenced in system prompt messages
- **Test:** Check assistant configuration via VAPI API

## References

- [VAPI Dynamic Variables](https://docs.vapi.ai/assistants/dynamic-variables)
- [VAPI Web Widget](https://docs.vapi.ai/chat/web-widget)
- [VAPI Assistant Overrides](https://vapi.ai/community/m/1248134802859757618)
- [VAPI Web SDK](https://docs.vapi.ai/sdk/web)

## Support

For issues or questions:
1. Check VAPI call logs in dashboard
2. Verify assistant configuration
3. Test with different callSource values
4. Review VAPI documentation links above
