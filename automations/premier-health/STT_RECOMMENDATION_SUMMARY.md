# STT Provider Recommendation Summary

**Date:** 2025-10-20
**Decision:** Switch from Deepgram → AssemblyAI

---

## TL;DR

**Switch to AssemblyAI** to solve the keyterm limit issue:
- ✅ **1,000 word boost** (vs 100 keyterm limit in Deepgram)
- ✅ **40x cheaper** ($0.00025/min vs $0.01/min)
- ✅ **All 295 cities** fit comfortably with room to grow
- ✅ **~300ms latency** (excellent for real-time)

---

## The Problem

- Deepgram Nova-3: **100 keyterm maximum**
- Premier Health needs: **295 Ghanaian cities**
- Current status: Using only 80 priority cities (many cities missing)

---

## The Solution: AssemblyAI

### Why AssemblyAI?

| Feature | Deepgram | AssemblyAI | Winner |
|---------|----------|------------|--------|
| Custom vocab limit | 100 | 1,000 | ✅ AssemblyAI (10x) |
| Cost per minute | $0.01 | $0.00025 | ✅ AssemblyAI (40x cheaper) |
| Phrase length | 1 word | Up to 6 words | ✅ AssemblyAI |
| Real-time latency | Excellent | ~300ms | ✅ Tie |
| VAPI integration | Native | Native | ✅ Tie |
| Ghanaian cities | 80/295 | 295/295 | ✅ AssemblyAI |

### Cost Savings Example

**At 10,000 minutes/month:**
- Deepgram: $100/month = $1,200/year
- AssemblyAI: $2.50/month = $30/year
- **Savings: $1,170/year (97.5% reduction)**

**At 100,000 minutes/month:**
- Deepgram: $1,000/month = $12,000/year
- AssemblyAI: $25/month = $300/year
- **Savings: $11,700/year (97.5% reduction)**

---

## Implementation Plan

### Week 1: Testing
1. Configure AssemblyAI with all 295 cities
2. Run 20 parallel test calls (Deepgram vs AssemblyAI)
3. Compare accuracy, latency, cost

### Week 2: Validation
1. Measure Word Error Rate for city names
2. Test edge cases (noise, accents, multiple cities)
3. Calculate actual cost savings

### Week 3: Migration
1. Create AssemblyAI word boost configuration
2. Gradual rollout (10% → 50% → 100%)
3. Monitor performance and user feedback

---

## Configuration

```python
# AssemblyAI configuration for VAPI
{
  "transcriber": {
    "provider": "assembly-ai",
    "model": "universal-streaming",
    "word_boost": [
      # All 295 cities from PREMIER_CITIES_MIN.md
      "ACCRA", "KUMASI", "TAMALE", "TAKORADI",
      # ... (295 total)
    ],
    "boost_param": "high",
    "language": "en"
  }
}
```

---

## Expected Outcomes

✅ **All 295 cities** accurately transcribed (vs 80 currently)
✅ **97.5% cost reduction** (massive savings at scale)
✅ **Better user experience** (no missing cities)
✅ **Room to grow** (700+ more slots available for hospitals, services, etc.)

---

## Risk Assessment

**Low Risk:**
- Native VAPI integration
- Can run parallel tests
- Gradual rollout possible
- Instant rollback to Deepgram if issues

**Testing Required:**
- Ghanaian English accent compatibility
- Real-world call scenarios
- Edge case handling

---

## Documentation

Detailed analysis available in:
- **`VAPI_STT_ALTERNATIVES.md`** - Full provider comparison
- **`DEEPGRAM_KEYTERM_RESEARCH.md`** - Deepgram limitations
- **`PRIORITY_CITIES_80.md`** - Current 80-city configuration

---

## Next Steps

1. ✅ Review this recommendation
2. ⏳ Approve testing phase
3. ⏳ Run AssemblyAI tests
4. ⏳ Evaluate results
5. ⏳ Make final decision
6. ⏳ Migrate if tests pass

---

**Recommendation Confidence: HIGH**

AssemblyAI solves the keyterm limit issue while providing massive cost savings and excellent performance. The migration is low-risk with clear rollback options.

**Status: Ready for Testing**
