# CRITICAL UPDATE: VAPI AssemblyAI Limitation

**Date:** 2025-10-20
**Status:** ⚠️ RECOMMENDATION CHANGED

---

## Critical Discovery

**VAPI DOES NOT SUPPORT AssemblyAI's word boost feature!**

While researching and attempting to configure the test assistant with AssemblyAI, I discovered that:

❌ **AssemblyAI word boost is NOT available through VAPI's API**
❌ **Custom vocabulary features are ONLY available for Deepgram** (keywords/keyterms)
❌ **The AssemblyAI provider in VAPI has limited configuration options**

---

## What This Means

### AssemblyAI Through VAPI
VAPI's AssemblyAI integration only supports:
- ✅ Universal-Streaming model (~300ms latency)
- ✅ formatTurns option (transcript formatting)
- ✅ Language selection
- ❌ **NO word boost**
- ❌ **NO custom vocabulary**
- ❌ **NO keyterms or keywords**

### Deepgram Through VAPI
VAPI's Deepgram integration supports:
- ✅ Keywords (for proper nouns, brand names)
- ✅ Keyterms (for domain-specific terminology)
- ✅ Multiple models (Nova-2, Nova-3, etc.)
- ✅ **Full custom vocabulary support**
- ⚠️ **Limited to 100 keyterms (hard limit)**

---

## Impact on Previous Recommendation

### Previous Recommendation ❌
"Switch to AssemblyAI for 1,000 word boost limit and 40x cost savings"

###Current Status Update:
- AssemblyAI word boost **NOT available in VAPI**
- Cannot use AssemblyAI for custom location name boosting
- Previous recommendation **NO LONGER VALID**

---

## Revised Options

### Option 1: Stay with Deepgram + 80 Priority Cities ✅ (CURRENT)
**Status:** Already implemented

**Configuration:**
- Provider: Deepgram Nova-3
- Keyterms: 80 priority cities
- Status: Working within limits

**Pros:**
- ✅ Already working
- ✅ Within Deepgram's 100 keyterm limit
- ✅ Custom vocabulary support
- ✅ Proven solution

**Cons:**
- ❌ Only covers 80/295 cities (27%)
- ❌ More expensive than AssemblyAI base rate
- ❌ 215 cities not boosted

**Cost:** $0.01/min

---

### Option 2: Dynamic Regional Keyterm Selection ⭐ (RECOMMENDED)
**Status:** Requires development (1-2 weeks)

**Approach:**
1. Ask user which region they're in
2. Load only that region's cities as keyterms (~20-40 per region)
3. Always stay within 100 keyterm limit
4. Cover all 295 cities contextually

**Example Flow:**
```
User: "I need a doctor"
Ama: "Which region are you in - Greater Accra, Ashanti, Northern, or another?"
User: "Accra"
→ Load only Greater Accra cities (MADINA, LEGON, TEMA, etc.)
```

**Pros:**
- ✅ All 295 cities covered (contextually)
- ✅ Always within 100 keyterm limit
- ✅ Better accuracy (focused vocabulary)
- ✅ Scalable solution

**Cons:**
- ⚠️ Requires development work
- ⚠️ Adds one extra conversation step
- ⚠️ Need to group cities by region

**Cost:** $0.01/min (same as current) + dev time

---

### Option 3: Custom Deepgram Model Training 💰 (LONG-TERM)
**Status:** Enterprise solution

**Approach:**
- Train custom Deepgram model on Ghanaian geography
- Model natively recognizes all cities
- No keyterm limits needed

**Requirements:**
- Cost: $10,000 USD (one-time)
- Audio data: 10-30 hours with Ghanaian city mentions
- Timeline: 4-8 weeks
- Plan: Deepgram Enterprise

**Pros:**
- ✅ All 295+ cities recognized natively
- ✅ No keyterm management needed
- ✅ Best accuracy possible
- ✅ Scalable to unlimited locations

**Cons:**
- ❌ High upfront cost ($10k)
- ❌ Requires audio data collection
- ❌ Long timeline (4-8 weeks)
- ❌ Enterprise plan required

**Cost:** $10k one-time + $0.01/min

---

### Option 4: Hybrid Post-Processing Approach 🔧 (TECHNICAL)
**Status:** Requires development (2-3 weeks)

**Approach:**
1. Use AssemblyAI without word boost (cheaper base rate)
2. Post-process transcripts to correct city names
3. Use fuzzy matching against all 295 cities
4. Feed corrected transcript to RAG system

**Implementation:**
```python
# 1. Get raw AssemblyAI transcript (no word boost)
raw_transcript = assemblyai_transcribe(audio)

# 2. Extract potential location mentions
locations = extract_location_phrases(raw_transcript)

# 3. Fuzzy match against all 295 cities
for location in locations:
    best_match = fuzzy_match(location, ALL_CITIES, threshold=0.85)
    if best_match:
        transcript = transcript.replace(location, best_match)

# 4. Use corrected transcript for RAG query
results = query_rag(corrected_transcript)
```

**Pros:**
- ✅ All 295 cities covered
- ✅ 40x cheaper transcription ($0.00025/min)
- ✅ No 100 keyterm limit
- ✅ Improves over time

**Cons:**
- ⚠️ Complex development
- ⚠️ Adds latency (post-processing time)
- ⚠️ Won't fix real-time transcript display
- ⚠️ Edge cases (multiple cities, similar names)

**Cost:** $0.00025/min + dev time

---

### Option 5: Use Gladia (When Available) 🕐 (FUTURE)
**Status:** Waiting for VAPI integration

**Current Status:**
- Gladia supports custom vocabulary natively
- NOT yet available in VAPI
- Users requesting this feature

**When Available:**
- Check if custom vocabulary limit > 100
- Compare cost vs Deepgram
- Test with Ghanaian city names

**Cost:** $0.0126/min (when available)

---

## Decision Matrix (Revised)

| Solution | Time | Cost | Covers All Cities | Complexity | Recommended |
|----------|------|------|-------------------|------------|-------------|
| **80 Priority Cities** | 0 (done) | $0.01/min | ❌ 27% | Low | ✅ Current |
| **Dynamic Regional** | 1-2 weeks | $0.01/min | ✅ 100% | Medium | ⭐ **Best** |
| **Custom Model** | 4-8 weeks | $10k + $0.01/min | ✅ 100% | Low | 💰 If scale |
| **Post-Processing** | 2-3 weeks | $0.00025/min | ✅ 100% | High | 🔧 Technical |
| **AssemblyAI Direct** | N/A | N/A | ❌ 0% | N/A | ❌ Not in VAPI |

---

## Updated Recommendation

### Short-Term (Immediate): Keep 80 Priority Cities ✅
- Already working
- Covers most common use cases
- Low risk, proven solution

### Medium-Term (1-2 weeks): Implement Dynamic Regional Selection ⭐
**This is now the BEST solution:**

1. **Week 1:** Design & Implementation
   - Create regional city groupings
   - Implement region detection logic
   - Build dynamic keyterm loader
   - Test with various regions

2. **Week 2:** Testing & Deployment
   - Test all regions
   - Verify keyterm counts (<100 per region)
   - Gradual rollout
   - Monitor performance

**Benefits:**
- ✅ All 295 cities covered
- ✅ Works with VAPI's Deepgram integration
- ✅ Always within 100 keyterm limit
- ✅ Better accuracy (focused vocabulary)
- ✅ Room to add more cities per region

### Long-Term (If Call Volume Justifies): Custom Model
- Evaluate after 3-6 months
- If >100k minutes/month, ROI is positive
- Best solution for scale

---

## Why AssemblyAI Doesn't Work

### Technical Explanation

1. **VAPI's Integration is Limited:**
   - VAPI only exposes basic AssemblyAI features
   - Word boost is not part of VAPI's API
   - Would need direct AssemblyAI API integration (bypassing VAPI)

2. **Direct Integration Challenges:**
   - Would need custom transcriber implementation
   - Requires webhook management
   - Adds complexity to infrastructure
   - May not work with VAPI's voice pipeline

3. **Not Worth the Complexity:**
   - Dynamic regional selection is simpler
   - Achieves same goal (all 295 cities)
   - Works within VAPI's ecosystem
   - Lower development risk

---

## Action Items

### Immediate ✅
- [x] Keep current 80 priority city configuration
- [x] Document this critical limitation
- [x] Update recommendations

### This Week
- [ ] Design regional city groupings
- [ ] Map all 295 cities to regions
- [ ] Create region detection logic

### Next 1-2 Weeks
- [ ] Implement dynamic keyterm selection
- [ ] Test with all regions
- [ ] Deploy to production

### Future (3-6 months)
- [ ] Monitor call volume and costs
- [ ] Evaluate custom model ROI
- [ ] Consider if $10k investment makes sense

---

## Regional Grouping (Preview)

### Greater Accra Region (~50 cities)
ACCRA, MADINA, LEGON, TEMA, ASHAIMAN, DANSOMAN, ASHONGMAN, etc.

### Ashanti Region (~40 cities)
KUMASI, AHODWO, ASOKWA, BANTAMA, OBUASI, KONONGO, etc.

### Northern Regions (~30 cities)
TAMALE, BOLGATANGA, WA, BAWKU, YENDI, etc.

### Central/Western (~40 cities)
CAPE COAST, TAKORADI, SEKONDI, TARKWA, WINNEBA, etc.

### Eastern/Volta (~35 cities)
KOFORIDUA, HO, HOHOE, NSAWAM, AKOSOMBO, etc.

### Bono/Ahafo (~30 cities)
SUNYANI, TECHIMAN, BEREKUM, GOASO, etc.

### Other Regions (~70 cities)
Remaining cities and suburbs

**Total: 295 cities across ~7 regions**
**Max keyterms per region: ~50 (well within 100 limit)**

---

## Lessons Learned

1. **Always verify API capabilities** before making recommendations
2. **VAPI's integrations are simplified** - not all provider features available
3. **Direct API access** ≠ **VAPI-integrated access**
4. **Cost isn't everything** - feature availability matters more
5. **Dynamic context-based solutions** often better than brute-force approaches

---

## Conclusion

**AssemblyAI's word boost is NOT available through VAPI.**

**New Recommendation:** Implement dynamic regional keyterm selection
- Covers all 295 cities contextually
- Works within Deepgram's 100 limit
- Better accuracy through focused vocabulary
- 1-2 week development timeline

**Status:** Ready to proceed with regional grouping implementation

---

**Updated:** 2025-10-20
**Critical Discovery:** AssemblyAI word boost not supported in VAPI
**New Path:** Dynamic regional keyterm selection
