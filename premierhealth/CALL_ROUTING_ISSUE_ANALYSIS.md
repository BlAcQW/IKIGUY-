# PremierHealth Call Routing Issue - Root Cause Analysis

**Date:** 2025-11-06
**Squad ID:** d9c801a1-34df-4496-bb90-7ac9e3f9e44e
**Issue:** Calls not connecting to regional representatives

---

## Executive Summary

**ROOT CAUSE IDENTIFIED:** The main routing assistant (Premier Health Router) is missing the `transfer_call` tool configuration. While the system instructions tell the assistant to use the `transfer_call` tool, the tool itself is not actually configured in the assistant's tools array.

**Impact:** Calls cannot be transferred from the router to regional specialists, leaving customers stuck with the router who cannot provide healthcare information.

**Severity:** CRITICAL - Complete failure of the routing system

---

## Current Squad Configuration

### Squad Structure
- **Squad Name:** Premier Health Navigator Squad
- **Total Members:** 7 assistants
  - 1 Router assistant (main entry point)
  - 6 Regional specialists

### Squad Members

1. **Main Router** (ID: 87182b39-a050-4ef4-9319-773666fabd6d)
   - Name: "Premier Health Router"
   - Role: Routes calls to appropriate regional specialists
   - **Phone Number:** NOT CONFIGURED
   
2. **Greater Accra Specialist** (ID: 85e1cf7e-1711-4d01-9cad-c043b37707bd)
   - Name: "Premier Health Greater Accra"
   - Coverage: Accra, Tema, Madina, Legon, surrounding areas
   - **Phone Number:** NOT CONFIGURED
   
3. **Ashanti Specialist** (ID: 529d7292-c050-4f5c-941d-5207a4e3e3be)
   - Name: "Premier Health Ashanti"
   - Coverage: Kumasi, Obuasi, Mampong, Ashanti region
   - **Phone Number:** NOT CONFIGURED
   
4. **Northern Regions Specialist** (ID: 650340b7-76ee-46e9-ae34-268ebc217dba)
   - Name: "Premier Health Northern Regions"
   - Coverage: Tamale, Bolgatanga, Wa, Bawku, northern areas
   - **Phone Number:** NOT CONFIGURED
   
5. **Western and Central Specialist** (ID: caec99dc-3e51-43c2-a9cc-4b9b6bbef1dc)
   - Name: "Premier Health Western and Central"
   - Coverage: Takoradi, Sekondi, Cape Coast, Tarkwa, surrounding areas
   - **Phone Number:** NOT CONFIGURED
   
6. **Eastern and Volta Specialist** (ID: 0917ac57-8cac-44a1-9047-aead837af492)
   - Name: "Premier Health Eastern and Volta"
   - Coverage: Koforidua, Ho, Hohoe, Nkawkaw, surrounding areas
   - **Phone Number:** NOT CONFIGURED
   
7. **Bono Regions Specialist** (ID: e39da43d-1190-419a-9739-d2c11bc8fe78)
   - Name: "Premier Health Bono Regions"
   - Coverage: Sunyani, Techiman, Berekum, surrounding areas
   - **Phone Number:** NOT CONFIGURED

---

## Problem Analysis

### Issue #1: Missing Transfer Call Tool (PRIMARY ISSUE)

**Current State:**
The main router assistant's configuration shows:
```json
"model": {
  "model": "gpt-4o-mini",
  "tools": [],  // ← EMPTY - No tools configured!
  "toolIds": [],
  ...
}
```

**System Instructions Say:**
The router's system prompt explicitly instructs:
- "ALWAYS use transfer_call tool after identifying region"
- "As SOON as you identify the region, transfer immediately using transfer_call tool"
- Multiple examples showing transfer_call usage

**The Problem:**
The assistant is being told to use a tool that doesn't exist in its configuration. This is like giving someone a recipe that requires a blender, but not providing them with a blender.

**Expected Configuration:**
The router should have a transfer_call tool configured with destinations pointing to each regional assistant, like:
```json
"tools": [
  {
    "type": "transferCall",
    "destinations": [
      {
        "type": "assistant",
        "assistantName": "Premier Health Greater Accra",
        "message": "Let me connect you to our Greater Accra specialist...",
        "description": "Transfer to Greater Accra specialist for Accra, Tema, Madina..."
      },
      // ... other regions
    ]
  }
]
```

### Issue #2: No Phone Numbers Assigned (SECONDARY ISSUE)

**Current State:**
- ALL 7 assistants have `phoneNumberId: null` or not configured
- This means none of these assistants can receive inbound calls directly

**Impact:**
Even if transfers worked, there's no way for calls to reach the regional specialists because they have no phone numbers assigned.

**What Should Happen:**
Each regional specialist should either:
1. Have their own dedicated phone number, OR
2. Share a single phone number with the router, relying on the transfer mechanism

### Issue #3: Squad Member Configuration Mismatch

**Current State:**
The squad's `members` array shows:
```json
{
  "assistantId": "87182b39-a050-4ef4-9319-773666fabd6d",
  "assistantDestinations": [
    {
      "type": "assistant",
      "assistantName": "Premier Health Greater Accra",
      "message": "Let me connect you to our Greater Accra specialist...",
      "description": "Transfer to Greater Accra specialist..."
    },
    // ... 5 other destinations
  ]
}
```

**The Problem:**
The squad configuration defines destinations at the squad member level, but these destinations are NOT being synchronized to the actual assistant's tools configuration. The squad knows where transfers should go, but the assistant itself doesn't have the transfer capability.

---

## Expected vs. Actual Behavior

### Expected Call Flow

1. Customer calls Premier Health number
2. Router assistant answers: "Hello! Welcome to Premier Health..."
3. Router asks for region: "Which region are you calling from?"
4. Customer responds: "I'm in Madina"
5. **Router transfers call** to Greater Accra specialist
6. Greater Accra specialist answers: "Hello! I'm Ama, your Premier Health specialist for Greater Accra..."
7. Specialist helps customer find healthcare providers using RAG tool

### Actual Call Flow (Current Broken State)

1. Customer calls Premier Health number (likely fails - no phone configured)
2. **IF somehow connected:** Router assistant answers
3. Router asks for region
4. Customer responds with region
5. **Router tries to transfer but FAILS** - no transfer tool available
6. Router is stuck, cannot provide healthcare info (instructions say NEVER provide info, only transfer)
7. Customer receives no help

---

## Root Cause Summary

The system is experiencing a **configuration disconnect** between three layers:

1. **Squad Layer:** Knows about transfer destinations (defined in squad members)
2. **Assistant Instructions Layer:** Tells assistant to use transfer_call tool
3. **Assistant Tools Layer:** **MISSING** the actual transfer_call tool implementation

**This is like:**
- Having a directory of phone numbers (squad destinations) ✓
- Having instructions to make calls (system prompt) ✓
- But having no phone to make the calls with (tools) ✗

---

## Required Fixes

### Priority 1: Add Transfer Call Tool to Router

**Action:** Update the main router assistant (87182b39-a050-4ef4-9319-773666fabd6d) to include the transfer_call tool with all 6 regional destinations.

**API Call Required:**
```bash
PATCH https://api.vapi.ai/assistant/87182b39-a050-4ef4-9319-773666fabd6d
```

**Payload:**
```json
{
  "model": {
    "tools": [
      {
        "type": "transferCall",
        "destinations": [
          {
            "type": "assistant",
            "assistantName": "Premier Health Greater Accra",
            "assistantId": "85e1cf7e-1711-4d01-9cad-c043b37707bd",
            "message": "Let me connect you to our Greater Accra specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Greater Accra specialist for Accra, Tema, Madina, Legon, and surrounding areas"
          },
          {
            "type": "assistant",
            "assistantName": "Premier Health Ashanti",
            "assistantId": "529d7292-c050-4f5c-941d-5207a4e3e3be",
            "message": "Let me connect you to our Ashanti specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Ashanti specialist for Kumasi, Obuasi, Mampong, and surrounding areas"
          },
          {
            "type": "assistant",
            "assistantName": "Premier Health Northern Regions",
            "assistantId": "650340b7-76ee-46e9-ae34-268ebc217dba",
            "message": "Let me connect you to our Northern regions specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Northern specialist for Tamale, Bolgatanga, Wa, Bawku, and surrounding areas"
          },
          {
            "type": "assistant",
            "assistantName": "Premier Health Western and Central",
            "assistantId": "caec99dc-3e51-43c2-a9cc-4b9b6bbef1dc",
            "message": "Let me connect you to our Western and Central specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Western/Central specialist for Takoradi, Sekondi, Cape Coast, and surrounding areas"
          },
          {
            "type": "assistant",
            "assistantName": "Premier Health Eastern and Volta",
            "assistantId": "0917ac57-8cac-44a1-9047-aead837af492",
            "message": "Let me connect you to our Eastern and Volta specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Eastern/Volta specialist for Koforidua, Ho, Hohoe, and surrounding areas"
          },
          {
            "type": "assistant",
            "assistantName": "Premier Health Bono Regions",
            "assistantId": "e39da43d-1190-419a-9739-d2c11bc8fe78",
            "message": "Let me connect you to our Bono specialist who knows all the healthcare facilities in your area.",
            "description": "Transfer to Bono specialist for Sunyani, Techiman, Berekum, and surrounding areas"
          }
        ]
      }
    ]
  }
}
```

### Priority 2: Assign Phone Number to Entry Point

**Action:** Assign a phone number to either:
- **Option A (Recommended):** The main router assistant so it can receive calls and transfer
- **Option B:** Each regional specialist gets their own number (more complex, higher cost)

**For Option A:**
```bash
PATCH https://api.vapi.ai/assistant/87182b39-a050-4ef4-9319-773666fabd6d
```

**Payload:**
```json
{
  "phoneNumberId": "310e0da9-3ef0-4bd2-847a-631e8572921e"  // Ghana number from .env
}
```

### Priority 3: Test the Transfer Flow

**Action:** After implementing fixes, test:
1. Call the Premier Health number
2. State a region (e.g., "I'm in Accra")
3. Verify successful transfer to Greater Accra specialist
4. Verify specialist can query healthcare providers

---

## Additional Observations

### Positive Findings

1. **Regional specialists are well-configured:**
   - Each has proper RAG tool (query_premier_health_knowledge_base)
   - Each has comprehensive system prompts
   - Each has region-specific keywords for transcription
   - Each has proper webhook configuration

2. **Squad structure is logical:**
   - Clear separation of concerns (router vs. specialists)
   - Good regional coverage across Ghana
   - Appropriate transfer destinations defined

3. **Web interface works:**
   - index.html properly configured with Vapi widgets
   - Voice and chat options available
   - Uses squad ID for voice calls

### Potential Issues

1. **Website squad invocation:**
   - index.html calls squad with: `window.vapiWebInstance.start(null, null, squadId)`
   - This should work IF the router has phone number assigned
   - May need testing after fixes applied

2. **Webhook endpoints vary:**
   - Router: https://api.ailabsafrica.com/call-management/vapi/webhook
   - Regional specialists: https://flow-api.ailabsafrica.com/call-management/vapi/webhook
   - Ensure both endpoints are operational

---

## Recommendations

1. **Immediate:** Implement Priority 1 fix (add transfer_call tool)
2. **Immediate:** Implement Priority 2 fix (assign phone number)
3. **Test:** Verify end-to-end call flow works
4. **Monitor:** Watch for successful transfers in call logs
5. **Document:** Update PremierHealth README with current configuration
6. **Consider:** Adding fallback logic if transfer fails

---

## Next Steps

1. Apply the transfer_call tool configuration to the router assistant
2. Assign the Ghana phone number to the router
3. Test a live call through the system
4. Verify transfers work to all 6 regions
5. Update documentation with working configuration

---

**Analysis Completed:** 2025-11-06
**Analyzed By:** Claude (AI Labs Africa)
**Confidence Level:** HIGH - Clear configuration mismatch identified
