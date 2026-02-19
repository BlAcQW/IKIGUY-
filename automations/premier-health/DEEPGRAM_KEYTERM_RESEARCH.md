# Deepgram Nova-3 Keyterm Research: Issues with Many Location Names

**Date:** 2025-10-20
**Context:** Premier Health VAPI Assistant (ID: baa69b3a-8944-4557-9ef9-3a5aa6956eb3)
**Issue:** Transcription fails when using 295 city keyterms; works with fewer keyterms

---

## Executive Summary

Deepgram Nova-3's keyterm feature has **hard limits and performance degradation** when using many keyterms:
- ✗ **Hard limit:** 100 keyterms maximum
- ✗ **Token limit:** ~500 tokens (approximately 100 single-word keyterms)
- ✗ **Overfitting problem:** More keyterms = higher error rate due to forced matching
- ✗ **Current configuration:** 295 cities **EXCEEDS** the 100 keyterm limit

**Result:** The assistant likely cannot transcribe properly with 295 keyterms.

---

## The Problem: Keyterm Overfitting

### What Happens with Too Many Keyterms?

1. **Forced Matching:** The model "force-fits" keyterms even when they're not actually spoken
   - Example: "Fahad" → transcribed as "Fathom" (a keyterm)
   - Example: "Sales" → transcribed as "Pepsales" (a keyterm)

2. **Increased Misclassification:** More keyterms → model overfits → higher error rate

3. **Performance Degradation:** Large numbers of keyterms slow down real-time transcription

4. **Hard Limit Exceeded:** Nova-3 supports maximum 100 keyterms; we have 295 cities

---

## Research Findings

### Official Deepgram Nova-3 Limits

| Feature | Limit | Our Usage | Status |
|---------|-------|-----------|--------|
| Maximum keyterms | 100 | 295 cities | ❌ EXCEEDED |
| Token limit | ~500 tokens | ~295 tokens | ✓ Within limit |
| Model support | Nova-3 only | Nova-3 | ✓ Correct |
| Language support | Monolingual only | en-GB | ✓ Correct |

### Best Practices from Deepgram

✓ **DO:**
- Use keyterms for **uncommon** words the model struggles with
- Send each keyterm **once only**
- Use keyterms for proper nouns, product names, industry jargon
- Keep keyterms under 100 items
- Use single words when possible (multi-word phrases consume more tokens)

✗ **DON'T:**
- Send common words the model already recognizes
- Exceed 100 keyterms
- Send duplicate keyterms
- Use keyterms for words the model handles well

### Community Reports

From GitHub discussions and user feedback:
- Users report Nova-3 keyterm prompting causes "force-fitting" issues
- Deepgram acknowledges this is a known issue with Nova-3's model-driven approach
- Recommended workaround: Switch to Nova-2 with keyword boosting instead

---

## Solutions & Recommendations

### Option 1: Reduce to Top Priority Cities (RECOMMENDED - SHORT TERM)

**Approach:** Identify the 80-100 most commonly requested or hardest-to-transcribe cities

**Criteria for selection:**
1. Cities with non-standard pronunciations or spellings
2. Most frequently requested locations (analyze call logs)
3. Cities that sound similar to common English words
4. Major regional centers

**Implementation:**
```python
# Analyze which cities are most problematic or most requested
# Keep only ~80-100 keyterms
priority_cities = [
    # Major cities (always keep)
    "ACCRA", "KUMASI", "TAMALE", "TAKORADI", "KOFORIDUA",
    # Regional capitals
    "SUNYANI", "BOLGATANGA", "HO", "WA", "SEKONDI",
    # Frequently requested suburbs/districts
    "MADINA", "ASHONGMAN", "DANSOMAN", "LEGON", "KANESHIE",
    # Hard-to-transcribe cities (unusual spellings)
    "HOHOE", "BIBIANI", "NKAWKAW", "NSAWAM", "ASOKWA",
    # Add more based on usage analysis...
]
```

**Pros:**
- ✓ Immediate fix
- ✓ Within Deepgram's recommended limits
- ✓ Reduces overfitting risk
- ✓ No cost increase

**Cons:**
- ✗ Some cities won't have boosted recognition
- ✗ Requires maintenance as usage patterns change

---

### Option 2: Switch to Nova-2 with Keyword Boosting

**Approach:** Use Nova-2 model with `keywords` parameter instead of Nova-3's `keyterm`

**Configuration change:**
```json
{
  "transcriber": {
    "model": "nova-2",
    "provider": "deepgram",
    "language": "en-GB",
    "keywords": [
      "ACCRA:2",
      "KUMASI:2",
      "TAMALE:2",
      // ... with intensifiers
    ]
  }
}
```

**Pros:**
- ✓ Same 100 keyword limit but with intensifier control
- ✓ Less prone to overfitting (uses boosting, not prompting)
- ✓ Community reports better stability

**Cons:**
- ✗ Nova-2 is less accurate overall than Nova-3
- ✗ Still limited to 100 keywords
- ✗ Older model (Nova-3 is latest)

---

### Option 3: Implement Dynamic Keyterm Selection (RECOMMENDED - MEDIUM TERM)

**Approach:** Dynamically select relevant keyterms based on conversation context

**Implementation strategy:**
1. **Detect region first:** Ask user which region/city they're near
2. **Load regional keyterms:** Only load cities in that region (~20-40 cities)
3. **Update per call:** Each call gets contextual keyterms

**Example flow:**
```
User: "I need a doctor"
Assistant: "Which area are you in - Accra, Kumasi, Takoradi, or another region?"
User: "Accra"
→ System loads only Greater Accra cities as keyterms (MADINA, LEGON, DANSOMAN, etc.)
```

**Pros:**
- ✓ Always within 100 keyterm limit
- ✓ Most relevant cities boosted per conversation
- ✓ Better accuracy due to focused context
- ✓ Scalable to any number of total cities

**Cons:**
- ✗ Requires development work
- ✗ Adds conversation step
- ✗ Needs regional city grouping data

---

### Option 4: Custom Model Training (RECOMMENDED - LONG TERM)

**Approach:** Train a Deepgram custom model specifically for Ghanaian city names

**Details:**
- **Cost:** $10,000 USD (one-time)
- **Data needed:** 10-30 hours of audio with Ghanaian city names
- **Timeline:** Several weeks for training
- **Availability:** Enterprise plan only

**Process:**
1. Collect 10-30 hours of voice calls mentioning Ghanaian cities
2. Provide written list of all 295+ cities with correct spellings
3. Deepgram trains custom Nova-3 model
4. Model natively recognizes Ghanaian geography

**Pros:**
- ✓ Best long-term solution
- ✓ No keyterm limits needed
- ✓ Highest accuracy possible
- ✓ Model "knows" Ghanaian context natively
- ✓ One-time cost, unlimited usage

**Cons:**
- ✗ High upfront cost ($10k)
- ✗ Requires Enterprise plan
- ✗ Needs audio data collection
- ✗ Several weeks to implement

---

### Option 5: Hybrid RAG + Post-Processing Approach

**Approach:** Let model transcribe phonetically, then use RAG to correct city names

**Implementation:**
```python
# 1. Get transcription (no keyterms)
raw_transcript = deepgram_transcribe(audio)

# 2. Extract potential location mentions
potential_locations = extract_location_phrases(raw_transcript)

# 3. Use fuzzy matching against city database
for phrase in potential_locations:
    best_match = fuzzy_match(phrase, all_295_cities, threshold=0.8)
    if best_match:
        transcript = transcript.replace(phrase, best_match)

# 4. Update context for RAG query
corrected_transcript = apply_corrections(raw_transcript)
```

**Pros:**
- ✓ No keyterm limits
- ✓ Works with all 295 cities
- ✓ Can improve over time with better matching
- ✓ Lower cost than custom model

**Cons:**
- ✗ Requires development and testing
- ✗ May have latency impact
- ✗ Won't help with real-time transcription display
- ✗ Complex edge cases (multiple city mentions)

---

## Current Configuration Analysis

### What We Have Now

```json
{
  "transcriber": {
    "model": "nova-3",
    "keyterm": [295 cities],  // ❌ EXCEEDS 100 LIMIT
    "language": "en-GB",
    "provider": "deepgram"
  }
}
```

### Why It's Not Working

1. **Limit exceeded:** 295 keyterms > 100 maximum
2. **API may be truncating:** Deepgram likely ignores keyterms beyond 100
3. **OR API may be rejecting:** Request might fail validation
4. **Overfitting if accepted:** Even if accepted, too many keyterms cause forced matching

---

## Immediate Action Plan

### Step 1: Test Current Behavior (Priority: HIGH)

Test if the VAPI assistant is actually using the keyterms:

```bash
# Make test call and observe transcription
# Try saying uncommon city names like:
# - "HOHOE" (should be: HO-ho-eh)
# - "NSAWAM" (should be: n-SAH-wam)
# - "BIBIANI" (should be: bee-bee-AH-nee)

# Check if they're transcribed correctly or phonetically
```

### Step 2: Implement Quick Fix (Priority: HIGH)

**Reduce to 80 priority cities immediately:**

```bash
# Create priority city list
# Update VAPI assistant configuration
# Test with same city names
```

### Step 3: Plan Medium-Term Solution (Priority: MEDIUM)

**Implement dynamic keyterm selection:**
- Design region detection logic
- Group cities by region
- Build dynamic keyterm loader

### Step 4: Evaluate Long-Term Investment (Priority: LOW)

**Assess custom model training:**
- Calculate ROI based on call volume
- Collect audio samples from existing calls
- Contact Deepgram for Enterprise quote

---

## Testing Recommendations

### Test Cases

1. **Common cities:** ACCRA, KUMASI, TAMALE
   - Expected: Should transcribe correctly even without keyterms

2. **Uncommon cities:** HOHOE, BIBIANI, NSAWAM
   - Expected: May be transcribed phonetically without keyterms

3. **Sound-alikes:** TEMA vs TEMU, KUMASI vs KUMASHI
   - Expected: Keyterms should help distinguish

4. **Regional variations:** Speaker accent differences
   - Expected: Keyterms may or may not help depending on pronunciation

### Metrics to Track

- **Keyword Recall Rate (KRR):** % of city names correctly transcribed
- **False Positive Rate:** % of times city names appear incorrectly
- **User correction rate:** How often users need to repeat city names
- **Call resolution time:** Impact of transcription errors on call duration

---

## References

### Deepgram Documentation
- [Keyterm Prompting](https://developers.deepgram.com/docs/keyterm)
- [Keywords (Nova-2)](https://developers.deepgram.com/docs/keywords)
- [Custom Model Training](https://offers.deepgram.com/product-sheet-custom-model-training)

### Community Discussions
- [Nova-3 Keyterm Overfitting Issue](https://github.com/orgs/deepgram/discussions/1233)
- [Keyterm Best Practices](https://github.com/orgs/deepgram/discussions/1118)
- [Token Limits](https://github.com/orgs/deepgram/discussions/1108)

### VAPI Integration
- [VAPI Deepgram Keywords](https://docs.vapi.ai/customization/custom-keywords)
- [VAPI Transcriber Options](https://docs.vapi.ai/providers/voice/deepgram)

---

## Decision Matrix

| Solution | Time to Implement | Cost | Accuracy | Scalability | Recommended For |
|----------|------------------|------|----------|-------------|-----------------|
| Reduce to 80 cities | 1 hour | $0 | Medium | Low | Immediate fix |
| Switch to Nova-2 | 2 hours | $0 | Medium | Low | Quick alternative |
| Dynamic keyterms | 1-2 weeks | Dev time | High | High | Medium-term |
| Custom model | 4-8 weeks | $10,000 | Highest | Highest | Long-term/scale |
| Post-processing | 2-3 weeks | Dev time | Medium-High | High | Budget-conscious |

---

## Conclusion

**The root cause is clear:** Deepgram Nova-3 has a **100 keyterm maximum**, and we're using 295 cities, which exceeds this limit by 3x.

**Recommended immediate action:**
1. ✅ **Short-term (today):** Reduce to 80-100 priority cities
2. ✅ **Medium-term (1-2 weeks):** Implement dynamic regional keyterm selection
3. ✅ **Long-term (if scale justifies):** Invest in custom model training at $10k

**This will restore transcription functionality while planning for better long-term solutions.**
