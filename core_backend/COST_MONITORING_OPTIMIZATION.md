# Cost Monitoring Optimization - Asterisk vs VAPI

## Current Situation

### Call Flow
```
External Caller → Asterisk Proxy → VAPI → AI Assistant
```

### Current Tracking (DUPLICATION ISSUE)
1. **Asterisk CDR** (`asterisk_calls` collection):
   - Tracks: Phone cost (0.15 GHC/min) ✅
   - Tracks: Call duration ✅
   - Source: Direct from Asterisk CDR files

2. **VAPI Webhooks** (`campaign_calls` collection):
   - Tracks: AI service cost (GPT-4, voice synthesis, etc.) ✅
   - Tracks: Call duration ✅ (DUPLICATE!)
   - Source: VAPI webhook events

### Problem
- **Double-counting minutes**: Both sources track duration for the same calls
- **Unnecessary VAPI tracking**: For Asterisk numbers, we only need VAPI AI costs, not phone costs

## Best Solution

### For Asterisk Numbers (MTN, Ant Cellular)
- ✅ **Use Asterisk CDR** for:
  - Phone minutes (billable duration)
  - Phone cost (0.15 GHC/min)
- ✅ **Use VAPI webhook** for:
  - AI service costs only (GPT-4, ElevenLabs, etc.)
  - **DO NOT** use VAPI duration for phone cost calculation

### For VAPI-Only Numbers (not through Asterisk)
- ✅ **Use VAPI webhook** for:
  - Phone minutes
  - Phone cost
  - AI service costs

## Implementation Strategy

### Option 1: Smart Merging (Recommended)
Modify `get_cost_summary()` to:
1. Check if phone has Asterisk CDR data
2. If yes: Use Asterisk for phone costs, VAPI for AI costs only
3. If no: Use VAPI for everything

### Option 2: Filter VAPI Data
Skip VAPI duration tracking for phones that have Asterisk CDR data.

### Option 3: Single Source of Truth
- Mark Asterisk numbers in phone metadata
- Skip VAPI phone cost tracking for marked numbers

## Recommended: Option 1 (Smart Merging)

**Logic:**
```python
if asterisk_cost_ghc > 0:
    # This phone uses Asterisk - use Asterisk for phone costs
    phone_cost_ghc = asterisk_cost_ghc
    phone_minutes = asterisk_minutes
    # VAPI cost is only for AI services
    vapi_cost_usd = vapi_cost_usd  # AI service cost only
else:
    # VAPI-only number - use VAPI for everything
    phone_cost_ghc = vapi_minutes * cost_per_minute
    phone_minutes = vapi_minutes
    vapi_cost_usd = vapi_cost_usd  # Includes both phone and AI
```

## Benefits
1. ✅ No duplication of minutes
2. ✅ Accurate phone costs from Asterisk (0.15 GHC/min)
3. ✅ Accurate AI costs from VAPI
4. ✅ Works for both Asterisk and VAPI-only numbers
5. ✅ Single unified view in cost summary

