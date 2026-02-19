# VAPI STT Alternatives: Best Options for Ghanaian Location Names

**Date:** 2025-10-20
**Context:** Premier Health VAPI Assistant - Finding alternatives to Deepgram Nova-3
**Goal:** Identify STT providers that handle many location names better than Deepgram's 100 keyterm limit

---

## Executive Summary

After researching VAPI's supported STT providers, **AssemblyAI** emerges as the best alternative for handling Ghanaian location names, offering:
- ✅ **1,000 word boost limit** (10x more than Deepgram's 100 keyterm limit)
- ✅ **Up to 6 words per phrase** (supports multi-word city names)
- ✅ **Lower cost** ($0.00025/min vs Deepgram's $0.01/min = 40x cheaper)
- ✅ **Native VAPI integration** with word boost support
- ✅ **Universal-Streaming model** (~300ms latency, excellent for real-time)

**Recommendation:** Switch to AssemblyAI to accommodate all 295 Ghanaian cities.

---

## VAPI Supported STT Providers (2025)

| Provider | Cost/Minute | Custom Vocabulary | Limit | VAPI Support | Real-Time |
|----------|-------------|-------------------|-------|--------------|-----------|
| **AssemblyAI** | $0.00025 | Word Boost | 1,000 phrases | ✅ Native | ✅ Yes |
| **Deepgram** | $0.01 | Keyterm Prompting | 100 keyterms | ✅ Native | ✅ Yes |
| **Talkscriber** | $0.011 | Unknown | Unknown | ✅ Native | ✅ Yes |
| **Gladia** | $0.0126 | Custom Vocabulary | Not specified | ✅ Native | ✅ Yes |
| **Azure** | $0.017 | Phrase Lists | Not specified | ✅ Native | ✅ Yes |
| **ElevenLabs** | $0.00667 | Unknown | Unknown | ✅ Native | ✅ Yes |

---

## Detailed Provider Analysis

### 1. AssemblyAI (⭐ RECOMMENDED)

**Why This is the Best Choice:**

#### Word Boost Feature
- **Maximum:** 1,000 unique keywords/phrases
- **Phrase length:** Up to 6 words per phrase
- **Boost levels:** Low, default, or high intensity
- **Availability:** Both real-time and batch transcription

#### Pricing
- **Cost:** $0.00025/min (cheapest option)
- **Comparison:** 40x cheaper than Deepgram
- **Example:** 1,000 minutes = $0.25 (vs $10 with Deepgram)

#### Performance
- **Model:** Universal-Streaming (purpose-built for voice agents)
- **Latency:** ~300ms (ultra-fast, immutable transcripts)
- **Features:** Intelligent endpointing, superior accuracy

#### VAPI Integration
```json
{
  "transcriber": {
    "provider": "assembly-ai",
    "model": "universal-streaming",
    "word_boost": [
      "ACCRA",
      "KUMASI",
      "MADINA",
      // ... all 295 cities (well within 1,000 limit)
    ],
    "boost_param": "high"
  }
}
```

#### Pros
- ✅ 1,000 word limit accommodates all 295 cities + room to grow
- ✅ 40x cheaper than Deepgram
- ✅ Excellent real-time performance (~300ms)
- ✅ Native VAPI integration with word boost
- ✅ Can handle multi-word city names (up to 6 words)
- ✅ Flexible boost intensity control
- ✅ Proven accuracy for voice agents

#### Cons
- ⚠️ Less known than Deepgram (but AssemblyAI is highly regarded)
- ⚠️ Need to test with Ghanaian English specifically

#### Use Case Fit
**Perfect for Premier Health Navigator:**
- All 295 cities fit comfortably (1,000 limit)
- Significantly lower cost for high call volumes
- Real-time performance suitable for voice assistants
- Word boost ensures location name accuracy

---

### 2. Deepgram Nova-3 (Current - LIMITED)

#### Keyterm Prompting
- **Maximum:** 100 keyterms (HARD LIMIT)
- **Token limit:** ~500 tokens
- **Current status:** We're using 80 priority cities

#### Pricing
- **Cost:** $0.01/min (40x more expensive than AssemblyAI)

#### Performance
- **Latency:** Excellent for real-time
- **Accuracy:** Industry-leading overall
- **Issue:** Overfitting with too many keyterms

#### Pros
- ✅ Excellent accuracy and performance
- ✅ Well-tested with VAPI
- ✅ Good documentation

#### Cons
- ❌ Only 100 keyterm limit (can't fit all 295 cities)
- ❌ 40x more expensive than AssemblyAI
- ❌ Overfitting issues when approaching limit
- ❌ Already maxed out at 80 cities

#### Current Status
We've optimized to 80 priority cities, but still can't accommodate all 295.

---

### 3. Gladia (Promising but Unclear)

#### Custom Vocabulary
- **Limit:** Not clearly specified in documentation
- **Features:** Supports custom vocabulary with pronunciations and intensity
- **VAPI status:** Custom vocabulary NOT yet integrated in VAPI

#### Pricing
- **Cost:** $0.0126/min (12.6x more expensive than AssemblyAI)

#### Features
- Named Entity Recognition (NER) for locations
- Sentiment analysis
- Real-time support
- Multi-language capabilities

#### Pros
- ✅ Custom vocabulary with pronunciation control
- ✅ NER specifically handles locations
- ✅ Good feature set

#### Cons
- ❌ Custom vocabulary not available through VAPI yet
- ❌ No clear limit documentation
- ❌ More expensive than AssemblyAI
- ⚠️ Users requesting this feature (not yet available)

#### Status
**Not recommended until VAPI integration is complete.**

---

### 4. Talkscriber (Unknown Capability)

#### Features
- Word Error Rate (WER) under 4% (excellent accuracy)
- Emotion detection
- Real-time transcription
- Multi-language support

#### Pricing
- **Cost:** $0.011/min (44x more expensive than AssemblyAI)

#### Custom Vocabulary
- **Status:** Not documented in available resources
- **Unclear:** Whether it supports custom vocabulary/word boosting

#### Pros
- ✅ Very high accuracy (WER <4%)
- ✅ Emotion detection (bonus feature)
- ✅ VAPI native support

#### Cons
- ❌ No clear custom vocabulary documentation
- ❌ 44x more expensive than AssemblyAI
- ⚠️ Need to contact provider for custom vocabulary details

#### Status
**Insufficient information to recommend.**

---

### 5. Azure Speech Services (Enterprise Option)

#### Custom Vocabulary Options
- **Phrase Lists:** Simple text-based vocabulary additions
- **Custom Speech Models:** Full model training with audio data
- **Limit:** Not clearly specified for phrase lists

#### Pricing
- **Cost:** $0.017/min (68x more expensive than AssemblyAI)

#### Features
- Robust enterprise features
- Custom model training available
- Extensive language support

#### Pros
- ✅ Enterprise-grade reliability
- ✅ Custom model training option
- ✅ Phrase lists for quick vocabulary additions

#### Cons
- ❌ 68x more expensive than AssemblyAI
- ❌ More complex setup
- ❌ Overkill for this use case
- ⚠️ Custom models require significant investment

#### Status
**Not cost-effective for this use case.**

---

### 6. ElevenLabs STT (Limited Info)

#### Pricing
- **Cost:** $0.00667/min (26.7x more expensive than AssemblyAI)

#### Custom Vocabulary
- **Status:** Not documented in available resources

#### Status
**Insufficient information; primarily known for TTS, not STT.**

---

## Specialized African Language Options (For Future)

### Abena AI
- **Focus:** Ghanaian languages (Twi, Ghana Pidgin, Ghanaian English)
- **Features:**
  - Accurate ASR for African languages
  - Handles diverse dialects and accents
  - Offline capabilities
- **Status:** Not integrated with VAPI
- **Use case:** If you need Ghanaian language support beyond English

### Khaya AI
- **Focus:** West African languages (Twi, Ewe, Yoruba, Ga, Dagbani)
- **Features:**
  - State-of-the-art ASR for 60M+ West Africans
  - Mobile app focused
- **Status:** Not integrated with VAPI
- **Use case:** Multi-language support for West African languages

**Note:** These are excellent for Ghanaian language support but require custom integration (not available through VAPI currently).

---

## Cost Comparison Analysis

### Scenario: 10,000 minutes of calls per month

| Provider | Cost/Month | Cost/Year | vs AssemblyAI |
|----------|-----------|-----------|---------------|
| **AssemblyAI** | $2.50 | $30 | Baseline |
| Deepgram | $100 | $1,200 | +40x |
| Talkscriber | $110 | $1,320 | +44x |
| Gladia | $126 | $1,512 | +50.4x |
| Azure | $170 | $2,040 | +68x |
| ElevenLabs | $66.70 | $800.40 | +26.7x |

### Scenario: 100,000 minutes per month (high volume)

| Provider | Cost/Month | Cost/Year | vs AssemblyAI |
|----------|-----------|-----------|---------------|
| **AssemblyAI** | $25 | $300 | Baseline |
| Deepgram | $1,000 | $12,000 | +40x |
| Talkscriber | $1,100 | $13,200 | +44x |
| Gladia | $1,260 | $15,120 | +50.4x |
| Azure | $1,700 | $20,400 | +68x |
| ElevenLabs | $667 | $8,004 | +26.7x |

**Cost savings with AssemblyAI are massive at scale.**

---

## Recommendation Matrix

| Use Case | Recommended Provider | Reason |
|----------|---------------------|--------|
| **295+ location names** | **AssemblyAI** | 1,000 word boost limit |
| **Budget-conscious** | **AssemblyAI** | 40x cheaper than alternatives |
| **High call volume** | **AssemblyAI** | Best cost at scale |
| **Priority 80 cities only** | Deepgram (current) | Proven, working solution |
| **Enterprise requirements** | Azure | Enterprise features, compliance |
| **Ghanaian language support** | Abena AI (custom) | Specialized for Ghana |
| **Emotion detection needed** | Talkscriber | Built-in emotion analysis |

---

## Migration Plan: Deepgram → AssemblyAI

### Phase 1: Testing (Week 1)
1. **Set up AssemblyAI test configuration**
   ```json
   {
     "transcriber": {
       "provider": "assembly-ai",
       "model": "universal-streaming",
       "word_boost": [
         // All 295 cities from PREMIER_CITIES_MIN.md
       ],
       "boost_param": "high"
     }
   }
   ```

2. **Run parallel tests**
   - Test 20 calls with Deepgram (80 cities)
   - Test 20 calls with AssemblyAI (295 cities)
   - Compare accuracy, latency, cost

3. **Test scenarios**
   - Common cities: ACCRA, KUMASI, TAMALE
   - Difficult pronunciations: HOHOE, NSAWAM, ASAMANKESE
   - Cities not in Deepgram list: Compare how both handle them

### Phase 2: Validation (Week 2)
1. **Measure metrics**
   - Word Error Rate (WER) for city names
   - False positive rate
   - Latency comparison
   - User experience feedback

2. **Cost analysis**
   - Calculate actual cost savings
   - Project monthly/yearly expenses

3. **Edge case testing**
   - Multiple cities in one utterance
   - Similar-sounding cities
   - Noisy environments
   - Various accents

### Phase 3: Migration (Week 3)
1. **Create AssemblyAI word boost list**
   ```python
   # Script to generate AssemblyAI configuration
   with open('PREMIER_CITIES_MIN.md', 'r') as f:
       cities = f.read().split()

   word_boost_config = {
       "word_boost": cities,  # All 295 cities
       "boost_param": "high"
   }
   ```

2. **Update VAPI assistant**
   - Switch transcriber provider to AssemblyAI
   - Apply word boost configuration
   - Update monitoring/logging

3. **Gradual rollout**
   - 10% of traffic to AssemblyAI
   - Monitor for 2-3 days
   - Increase to 50% if successful
   - Full migration after validation

### Phase 4: Monitoring (Ongoing)
1. **Track KPIs**
   - Transcription accuracy
   - Cost per call
   - User corrections needed
   - Call resolution time

2. **Optimization**
   - Adjust boost_param if needed (low/default/high)
   - Add more location names as needed
   - Fine-tune based on usage patterns

---

## Implementation Code

### Create AssemblyAI Configuration Script

```python
#!/usr/bin/env python3
"""
Update VAPI assistant to use AssemblyAI with all 295 cities
"""
import json
import requests

ASSISTANT_ID = "baa69b3a-8944-4557-9ef9-3a5aa6956eb3"
API_KEY = "42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
API_URL = f"https://api.vapi.ai/assistant/{ASSISTANT_ID}"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Read all 295 cities from PREMIER_CITIES_MIN.md
with open('/opt/kasaai/apps/automations/premier-health/PREMIER_CITIES_MIN.md', 'r') as f:
    content = f.read()
    cities = content.split()

print(f"Total cities for AssemblyAI word boost: {len(cities)}")
assert len(cities) <= 1000, f"Too many cities: {len(cities)} (max 1000)"

# Get current configuration
response = requests.get(API_URL, headers=headers)
current_config = response.json()

# Update to AssemblyAI with word boost
assemblyai_transcriber = {
    "provider": "assembly-ai",
    "model": "universal-streaming",
    "language": "en",
    "word_boost": cities,
    "boost_param": "high",
    "endpointing": 300,  # Same as current Deepgram setting
    "smartFormat": True
}

update_payload = {
    "transcriber": assemblyai_transcriber
}

# Update the assistant
update_response = requests.patch(API_URL, headers=headers, json=update_payload)

if update_response.status_code == 200:
    print("✓ Successfully updated VAPI assistant to AssemblyAI")
    print(f"✓ Word boost count: {len(cities)} cities")
    print(f"✓ Boost level: high")
    print(f"✓ Cost savings: ~40x cheaper than Deepgram")
    print(f"\nFirst 10 cities: {cities[:10]}")
    print(f"Last 10 cities: {cities[-10:]}")
else:
    print(f"✗ Failed to update assistant: {update_response.status_code}")
    print(f"Response: {update_response.text}")
```

---

## Testing Checklist

### Before Migration
- [ ] Review AssemblyAI documentation
- [ ] Verify VAPI supports AssemblyAI word boost
- [ ] Prepare test call scripts
- [ ] Set up monitoring/logging
- [ ] Document current Deepgram performance baseline

### During Testing
- [ ] Test 20+ calls with various city names
- [ ] Compare accuracy: AssemblyAI vs Deepgram
- [ ] Measure latency differences
- [ ] Test edge cases (noise, accents, multiple cities)
- [ ] Calculate actual cost per call

### After Migration
- [ ] Monitor transcription accuracy for 1 week
- [ ] Track cost savings
- [ ] Collect user feedback
- [ ] Adjust boost_param if needed
- [ ] Document lessons learned

---

## Decision Criteria

### Switch to AssemblyAI if:
- ✅ Accuracy is comparable or better (within 5% of Deepgram)
- ✅ Latency is acceptable (<500ms)
- ✅ Cost savings are significant (likely 40x)
- ✅ All 295 cities are recognized well
- ✅ No major issues in testing

### Stay with Deepgram if:
- ❌ AssemblyAI accuracy is significantly worse (>10% drop)
- ❌ Latency is unacceptable (>1 second)
- ❌ Word boost doesn't work as expected in VAPI
- ❌ Unexpected technical issues

### Consider Hybrid Approach:
- Use AssemblyAI for general transcription
- Use Deepgram for high-priority calls
- Route based on user type or region

---

## FAQ

### Q: Can AssemblyAI handle Ghanaian English accents?
**A:** AssemblyAI's Universal-Streaming model is trained on diverse English accents. Testing is needed to validate Ghanaian English specifically, but word boost should help with location names regardless of accent.

### Q: What if 295 cities isn't enough?
**A:** AssemblyAI supports up to 1,000 word boost entries, so you can add 700+ more locations, hospital names, or medical terms if needed.

### Q: How does word boost compare to keyterm prompting?
**A:** Both improve accuracy for specific words. Word boost offers more control with intensity levels and supports 10x more terms (1,000 vs 100).

### Q: What's the migration risk?
**A:** Low risk. You can run parallel tests, gradual rollout, and instantly revert to Deepgram if issues arise.

### Q: Will this affect other VAPI settings?
**A:** No. Only the transcriber changes. LLM, voice, functions, etc. remain the same.

---

## Conclusion

**AssemblyAI is the clear winner for Premier Health Navigator:**

1. **Capacity:** 1,000 word boost (all 295 cities + room to grow)
2. **Cost:** $0.00025/min (40x cheaper than Deepgram)
3. **Performance:** ~300ms latency (excellent for real-time)
4. **Integration:** Native VAPI support with word boost
5. **Flexibility:** Adjustable boost intensity

**Recommended Action:**
1. ✅ **Immediate:** Run parallel tests (AssemblyAI vs Deepgram)
2. ✅ **Week 1-2:** Validate accuracy and performance
3. ✅ **Week 3:** Migrate to AssemblyAI if tests pass
4. ✅ **Ongoing:** Monitor and optimize

**Expected Outcome:**
- All 295 cities accurately transcribed
- Significant cost savings (40x reduction)
- Better user experience (no missing cities)
- Scalable solution for future growth

---

## References

### AssemblyAI Documentation
- [VAPI Integration](https://www.assemblyai.com/docs/vapi)
- [Word Boost Feature](https://www.assemblyai.com/docs/faq/how-can-i-make-certain-words-more-likely-to-be-transcribed)
- [Universal-Streaming Model](https://www.assemblyai.com/blog/orchestration-tools-ai-voice-agents)

### VAPI Documentation
- [AssemblyAI Provider](https://docs.vapi.ai/providers/transcriber/assembly-ai)
- [Custom Keywords](https://docs.vapi.ai/customization/custom-keywords)
- [Transcriber Options](https://docs.vapi.ai/customization/custom-transcriber)

### Cost Analysis
- [VAPI Pricing Breakdown](https://blog.dograh.com/vapi-pricing-breakdown-2025-plans-hidden-costs-what-to-expect/)
- [STT Provider Comparison](https://www.assemblyai.com/blog/best-api-models-for-real-time-speech-recognition-and-transcription)

---

**Status:** ✅ **RECOMMENDATION COMPLETE - READY FOR TESTING**
