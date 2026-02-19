# VAPI Squad Multi-Assistant Routing: Feasibility Analysis for Premier Health

**Date:** 2025-10-20
**Context:** Premier Health VAPI Assistant - Region-Based City Routing
**Problem:** Deepgram Nova-3's 100 keyterm limit prevents using all 295+ Ghanaian cities
**Proposed Solution:** Use VAPI Squads to route to region-specific assistants with 80-100 cities each

---

## Executive Summary

### ✅ FEASIBLE: Multi-Assistant Region-Based Routing

**VAPI Squads CAN solve the 100 keyterm limit problem** through region-based routing, BUT there are **better alternatives** that should be considered first:

| Solution | Feasibility | Complexity | Cost | Recommended |
|----------|-------------|------------|------|-------------|
| **AssemblyAI (1,000 word boost)** | ✅ High | Low | 40x cheaper | ⭐ **BEST** |
| **VAPI Squad Region Routing** | ✅ High | Medium | Same | ✓ **VIABLE** |
| **Priority 80 Cities (Current)** | ✅ High | Low | Current | ✓ Temporary |
| **Custom Deepgram Model** | ✅ Low | High | $10k + Enterprise | Future |

**Recommendation Order:**
1. **Primary:** Switch to AssemblyAI (1,000 word boost limit, 40x cheaper)
2. **Alternative:** Implement VAPI Squad region routing (if AssemblyAI fails testing)
3. **Fallback:** Keep current 80 priority cities (temporary solution)

---

## What Are VAPI Squads?

### Core Concept
Squads enable calls to **transfer assistants mid-conversation** while **maintaining full conversation context**. Think of it as intelligent call routing between specialized AI agents.

### Key Features
- **Context Preservation:** Full conversation history transfers between assistants
- **Dynamic Routing:** Real-time decisions based on user input, data, or external systems
- **Seamless Transfers:** User doesn't experience interruption (silent transfers available)
- **Multi-Domain Support:** Each assistant can be specialized for different tasks/regions

### How It Works
```
User Call → Main Assistant (General)
              ↓
         Identifies Region
              ↓
         Transfers to Regional Assistant
              ↓
         Regional Assistant (80-100 cities for that region)
              ↓
         Provides Healthcare Facilities
```

---

## Region-Based Routing Architecture

### Proposed Structure

#### Main Router Assistant
- **Role:** Identify user's region
- **Keyterms:** NONE (or only 10 regional names: Greater Accra, Ashanti, Northern, etc.)
- **Task:** Ask "Which region are you in?" and route accordingly

#### Regional Specialist Assistants (4-6 assistants)

1. **Greater Accra Assistant**
   - **Cities:** ~80 cities (Accra, Madina, Tema, Adenta, Legon, etc.)
   - **Coverage:** All Greater Accra facilities
   - **Keyterms:** 80 Accra-area cities

2. **Ashanti Region Assistant**
   - **Cities:** ~70 cities (Kumasi, Obuasi, Mampong, Tafo, etc.)
   - **Coverage:** All Ashanti facilities
   - **Keyterms:** 70 Ashanti-area cities

3. **Northern Regions Assistant**
   - **Cities:** ~60 cities (Tamale, Bolgatanga, Wa, Bawku, etc.)
   - **Coverage:** Northern, Upper East, Upper West facilities
   - **Keyterms:** 60 Northern cities

4. **Western/Central Assistant**
   - **Cities:** ~50 cities (Takoradi, Sekondi, Cape Coast, etc.)
   - **Coverage:** Western, Central regions
   - **Keyterms:** 50 Western/Central cities

5. **Eastern/Volta Assistant**
   - **Cities:** ~40 cities (Koforidua, Ho, Hohoe, etc.)
   - **Coverage:** Eastern, Volta regions
   - **Keyterms:** 40 Eastern/Volta cities

6. **Bono/Ahafo Assistant**
   - **Cities:** ~30 cities (Sunyani, Techiman, Berekum, etc.)
   - **Coverage:** Bono, Bono East, Ahafo regions
   - **Keyterms:** 30 Bono/Ahafo cities

**Total Coverage:** All 295+ cities across 6 specialized assistants

---

## Technical Implementation

### 1. Squad Configuration

```json
{
  "name": "Premier Health Navigator Squad",
  "members": [
    {
      "assistant": {
        "name": "Region Router",
        "firstMessage": "Welcome to Premier Health! Which region are you calling from? Greater Accra, Ashanti, Northern, Western, Central, Eastern, Volta, or Bono?",
        "model": {
          "provider": "openai",
          "model": "gpt-4",
          "systemPrompt": "You are a routing assistant. Ask the user which region they are in and transfer them to the appropriate regional healthcare assistant."
        },
        "transcriber": {
          "provider": "deepgram",
          "model": "nova-3",
          "language": "en-GB",
          "keyterm": [
            "ACCRA",
            "ASHANTI",
            "KUMASI",
            "NORTHERN",
            "TAMALE",
            "WESTERN",
            "TAKORADI",
            "CENTRAL",
            "CAPE COAST",
            "EASTERN",
            "KOFORIDUA",
            "VOLTA",
            "HO",
            "BONO",
            "SUNYANI"
          ]
        },
        "transferDestinations": [
          {
            "type": "assistant",
            "assistantName": "Greater Accra Healthcare",
            "message": "Transferring you to our Greater Accra specialist..."
          },
          {
            "type": "assistant",
            "assistantName": "Ashanti Healthcare",
            "message": "Transferring you to our Ashanti region specialist..."
          },
          {
            "type": "assistant",
            "assistantName": "Northern Healthcare",
            "message": "Transferring you to our Northern regions specialist..."
          },
          {
            "type": "assistant",
            "assistantName": "Western Central Healthcare",
            "message": "Transferring you to our Western/Central specialist..."
          },
          {
            "type": "assistant",
            "assistantName": "Eastern Volta Healthcare",
            "message": "Transferring you to our Eastern/Volta specialist..."
          },
          {
            "type": "assistant",
            "assistantName": "Bono Healthcare",
            "message": "Transferring you to our Bono region specialist..."
          }
        ]
      }
    },
    {
      "assistant": {
        "name": "Greater Accra Healthcare",
        "transcriber": {
          "provider": "deepgram",
          "model": "nova-3",
          "language": "en-GB",
          "keyterm": [
            "ACCRA", "MADINA", "LEGON", "TEMA", "ADENTA",
            "DANSOMAN", "ASHONGMAN", "KANESHIE", "ASHAIMAN",
            "TESHIE", "LABADI", "SPINTEX", "ACHIMOTA",
            // ... 80 Greater Accra cities
          ]
        },
        "model": {
          "knowledgeBase": {
            "topK": 5,
            "provider": "custom",
            "fileIds": ["greater_accra_facilities"]
          }
        }
      }
    },
    // ... Additional 5 regional assistants
  ]
}
```

### 2. Transfer Logic

#### Option A: Manual User Selection
```
Router: "Which region are you in?"
User: "Accra"
Router: [Transfers to Greater Accra Assistant]
```

#### Option B: Intelligent Detection
```
Router: "Which city do you need healthcare in?"
User: "I'm in Madina"
Router: [Detects "Madina" → Ashanti region → Transfers]
```

#### Option C: Automatic Context Detection
```
Router: "How can I help you today?"
User: "I need a hospital in Kumasi"
Router: [NLP detects "Kumasi" → Transfers to Ashanti Assistant]
```

### 3. Context Preservation

When transferring between assistants:
```json
{
  "transferContext": {
    "region": "Greater Accra",
    "city": "Madina",
    "userQuery": "need a general practitioner",
    "conversationHistory": [
      "User: I need a doctor",
      "Assistant: Which region are you in?",
      "User: I'm in Accra, specifically Madina"
    ]
  }
}
```

The receiving assistant has full context and continues seamlessly.

---

## Pros and Cons Analysis

### ✅ Advantages of Squad Routing

1. **Solves 100 Keyterm Limit**
   - Each regional assistant has 80-100 cities (within Deepgram limit)
   - Total coverage: All 295+ cities

2. **Better Specialization**
   - Each assistant knows only their region's facilities
   - Faster, more accurate RAG queries
   - Reduced confusion between similar city names in different regions

3. **Scalability**
   - Easy to add new regions or cities
   - Can expand to 1,000+ cities without hitting limits
   - Regional assistants can be updated independently

4. **Context Preservation**
   - User doesn't repeat information
   - Seamless experience with silent transfers
   - Full conversation history maintained

5. **Cost Neutral**
   - Same Deepgram pricing (still $0.01/min)
   - Same OpenAI costs
   - No additional VAPI charges for Squads

6. **Better RAG Performance**
   - Regional knowledge bases are smaller and more focused
   - Faster query times
   - More relevant results

### ❌ Disadvantages of Squad Routing

1. **Added Complexity**
   - 6 assistants to manage instead of 1
   - More configuration and testing required
   - Higher maintenance burden

2. **User Experience Friction**
   - Adds one extra step ("Which region?")
   - Some users may not know which region they're in
   - Transfer delay (~1-2 seconds)

3. **Edge Cases**
   - Users traveling between regions
   - Multi-region queries ("facilities in both Accra and Kumasi")
   - Ambiguous city names (cities that exist in multiple regions)

4. **Development Time**
   - ~2-3 weeks to implement and test
   - Need to segment knowledge base by region
   - Requires extensive testing across all regions

5. **Error Handling**
   - What if user provides invalid region?
   - What if transfer fails?
   - Need fallback mechanisms

6. **No Cost Savings**
   - Still using expensive Deepgram ($0.01/min)
   - Doesn't address the 40x cost difference vs AssemblyAI

---

## Comparison with AssemblyAI Alternative

| Factor | VAPI Squad Routing | AssemblyAI Word Boost |
|--------|-------------------|----------------------|
| **Keyterm Capacity** | 80-100 per assistant × 6 = 480-600 total | 1,000 total (single assistant) |
| **City Coverage** | ✅ All 295+ cities | ✅ All 295+ cities |
| **Implementation Complexity** | 🟡 Medium (6 assistants) | 🟢 Low (1 assistant) |
| **User Experience** | 🟡 Extra routing step | 🟢 Direct, no routing |
| **Cost per Minute** | 🔴 $0.01 (Deepgram) | 🟢 $0.00025 (40x cheaper) |
| **Latency** | 🟡 +1-2s for transfer | 🟢 No transfer delay |
| **Maintenance** | 🔴 6 assistants to update | 🟢 1 assistant |
| **Scalability** | 🟡 Good (can add more regional assistants) | 🟢 Excellent (room for 700+ more) |
| **Testing Burden** | 🔴 High (6 assistants × all regions) | 🟢 Low (1 assistant) |
| **Knowledge Base** | 🟡 6 separate regional KBs | 🟢 1 unified KB |

**Verdict:** AssemblyAI is simpler, cheaper, and provides a better user experience.

---

## When to Use Squad Routing vs AssemblyAI

### Use VAPI Squad Routing If:
- ✅ AssemblyAI testing shows poor accuracy (<90% vs Deepgram)
- ✅ You want regional specialization (different prompts per region)
- ✅ You need different LLM models per region
- ✅ Different regions have different workflows
- ✅ Cost is not the primary concern

### Use AssemblyAI If:
- ✅ Cost savings are important (40x cheaper)
- ✅ You want simplicity (1 assistant vs 6)
- ✅ You want faster implementation (1 week vs 3 weeks)
- ✅ Better user experience (no routing step)
- ✅ AssemblyAI testing shows acceptable accuracy (>90%)

---

## Implementation Roadmap

### Phase 1: Decision Point (Week 1)
1. **Test AssemblyAI** with 20+ sample calls
2. **Measure accuracy** vs Deepgram baseline
3. **Calculate actual cost savings**
4. **Make decision:**
   - If AssemblyAI passes (>90% accuracy): Proceed with AssemblyAI
   - If AssemblyAI fails (<90% accuracy): Proceed with Squad routing

### Phase 2A: AssemblyAI Path (Week 2)
1. Deploy AssemblyAI with all 295 cities
2. Monitor performance
3. Optimize word boost settings
4. **Done** ✓

### Phase 2B: Squad Routing Path (Weeks 2-4)
1. **Week 2: Design & Setup**
   - Segment 295 cities into 6 regional groups
   - Create 6 regional knowledge bases
   - Design router assistant logic
   - Write transfer prompts

2. **Week 3: Build & Configure**
   - Create 6 regional assistants in VAPI
   - Configure Deepgram keyterms for each (80-100 cities)
   - Set up transfer destinations
   - Create Squad configuration

3. **Week 4: Testing & Deployment**
   - Test each regional assistant individually
   - Test routing logic (all 6 regions)
   - Test edge cases (invalid regions, multi-region queries)
   - Gradual rollout (10% → 50% → 100%)

---

## Regional City Distribution

Based on the 295+ cities in the Premier Health database:

### Greater Accra Region (~80 cities)
ACCRA, MADINA, TEMA, ADENTA, LEGON, DANSOMAN, ASHONGMAN, KANESHIE, ASHAIMAN, TESHIE, LABADI, SPINTEX, ACHIMOTA, ADABRAKA, OSU, LABONE, DZORWULU, EAST LEGON, HAATSO, DOME, KASOA, WEIJA, GBAWE, KWABENYA, NUNGUA, SAKUMONO, LASHIBI, AWOSHIE, BUBUASHIE, LAPAZ, KOKOMLEMLE, CIRCLE, DARKUMAN, DANSOMAN, MAMPROBI, KORLE BU, CANTONMENT, AIRPORT, TESANO, KANDA, ASYLUM, RIDGE, and more...

### Ashanti Region (~70 cities)
KUMASI, AHODWO, ASOKWA, BANTAMA, ADUM, TAFO, SUAME, SANTASI, OBUASI, KONONGO, MAMPONG, BEKWAI, AGOGO, EJISU, BOMSO, BREMANG, PATASI, ASAWASE, AFRANCHO, ABREPO, KENTINKRONO, and more...

### Northern Regions (~60 cities)
TAMALE, BOLGATANGA, WA, BAWKU, NAVRONGO, YENDI, SAVELUGU, WALEWALE, SALAGA, DAMONGO, SAWLA, LAWRA, BOLE, GUSHIEGU, and more...

### Western/Central Regions (~50 cities)
TAKORADI, SEKONDI, CAPE COAST, TARKWA, WINNEBA, ELMINA, TAKORADI, PRESTEA, BOGOSO, BIBIANI, ESSIKADO, FIJAI, MANKESSIM, SALTPOND, AGONA SWEDRU, and more...

### Eastern/Volta Regions (~40 cities)
KOFORIDUA, HO, HOHOE, NKAWKAW, NSAWAM, ABURI, AKOSOMBO, SOMANYA, KIBI, BEGORO, ASIAKWA, SUHUM, ASAMANKESE, and more...

### Bono/Ahafo/Other (~30 cities)
SUNYANI, TECHIMAN, BEREKUM, GOASO, KINTAMPO, DORMAA, WENCHI, SAMPA, HWIDIEM, DROBO, NKORANZA, and more...

---

## Cost Analysis: Squad Routing vs AssemblyAI

### Scenario: 10,000 minutes/month

| Solution | STT Cost | LLM Cost | Total Cost | Notes |
|----------|----------|----------|------------|-------|
| **Current (80 cities, Deepgram)** | $100 | $50 | **$150/mo** | Only 80 cities |
| **Squad Routing (6 assistants, Deepgram)** | $100 | $55 | **$155/mo** | All 295 cities, +$5 for routing |
| **AssemblyAI (1 assistant)** | $2.50 | $50 | **$52.50/mo** | All 295 cities, 66% savings |

### Scenario: 100,000 minutes/month

| Solution | STT Cost | LLM Cost | Total Cost | Notes |
|----------|----------|----------|------------|-------|
| **Current (80 cities, Deepgram)** | $1,000 | $500 | **$1,500/mo** | Only 80 cities |
| **Squad Routing (6 assistants, Deepgram)** | $1,000 | $550 | **$1,550/mo** | All 295 cities, +$50 for routing |
| **AssemblyAI (1 assistant)** | $25 | $500 | **$525/mo** | All 295 cities, 66% savings |

**Key Insight:** Squad routing doesn't save money vs current solution; it only adds city coverage. AssemblyAI provides BOTH coverage AND massive cost savings.

---

## Risk Assessment

### Squad Routing Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Transfer failures | Medium | High | Fallback to router, error handling |
| User confusion on region | Medium | Medium | Clear prompts, help text, fuzzy matching |
| Ambiguous city names | Low | Medium | Disambiguation prompts |
| Maintenance complexity | High | Medium | Good documentation, automated testing |
| Regional KB sync issues | Medium | High | Single source of truth, automated updates |

### AssemblyAI Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Poor accuracy vs Deepgram | Medium | High | Extensive testing before migration |
| Latency issues | Low | Medium | Monitor performance, revert if needed |
| Word boost not working in VAPI | Low | High | Pre-validate with VAPI support |
| Ghanaian accent issues | Medium | Medium | Test with real users, adjust boost |

---

## Final Recommendation

### 🎯 Recommended Approach: Hybrid Strategy

**Step 1: Primary Solution - AssemblyAI (Week 1-2)**
1. Test AssemblyAI with all 295 cities
2. If accuracy ≥90%: Deploy AssemblyAI ✓
3. If accuracy <90%: Proceed to Step 2

**Step 2: Fallback - Squad Routing (Weeks 3-5)**
1. Implement 6-region squad routing
2. Use Deepgram with regional keyterm sets
3. Deploy with gradual rollout

**Step 3: Long-term - Custom Model (Quarter 2-3)**
1. Collect audio data from calls
2. Evaluate ROI for $10k custom Deepgram model
3. If justified: Train custom model for ultimate accuracy

### Decision Tree
```
Start
  ↓
Test AssemblyAI
  ↓
Accuracy ≥90%? ──YES──→ Deploy AssemblyAI ✓ (BEST)
  ↓ NO
Build Squad Routing
  ↓
Deploy 6-Region Squads ✓ (VIABLE)
  ↓
Monitor Performance
  ↓
High Call Volume? ──YES──→ Consider Custom Model ($10k)
  ↓ NO
Continue with Squads ✓
```

---

## Conclusion

**VAPI Squad multi-assistant routing is FEASIBLE and VIABLE** for solving the 100 keyterm limit problem. It provides:
- ✅ Full coverage of all 295+ cities
- ✅ Context-preserving transfers
- ✅ Regional specialization benefits
- ✅ Scalability for future growth

**HOWEVER, AssemblyAI is the BETTER first choice** because:
- ✅ 40x cheaper ($0.00025 vs $0.01 per minute)
- ✅ Simpler (1 assistant vs 6)
- ✅ Better UX (no routing step)
- ✅ Faster to implement (1 week vs 3 weeks)
- ✅ 1,000 word boost limit (room for 700+ more cities)

**Recommended Action Plan:**
1. **Immediate (Week 1):** Test AssemblyAI thoroughly
2. **If AssemblyAI passes:** Deploy and save 40x on costs ✓
3. **If AssemblyAI fails:** Implement Squad routing as proven fallback
4. **Long-term:** Consider custom model if call volume justifies $10k investment

**Both solutions are technically sound. The decision comes down to testing AssemblyAI first.**

---

## References

### VAPI Documentation
- [VAPI Squads Introduction](https://docs.vapi.ai/squads)
- [Squad Configuration Examples](https://docs.vapi.ai/squads-example)
- [Dynamic Call Transfers](https://docs.vapi.ai/calls/call-dynamic-transfers)
- [Silent Transfers](https://docs.vapi.ai/squads/silent-transfers)

### Related Documents
- [DEEPGRAM_KEYTERM_RESEARCH.md](/opt/kasaai/apps/automations/premier-health/DEEPGRAM_KEYTERM_RESEARCH.md)
- [VAPI_STT_ALTERNATIVES.md](/opt/kasaai/apps/automations/premier-health/VAPI_STT_ALTERNATIVES.md)
- [PRIORITY_CITIES_80.md](/opt/kasaai/apps/automations/premier-health/PRIORITY_CITIES_80.md)
- [CITIES_AND_TOWNS.md](/opt/kasaai/apps/automations/premier-health/CITIES_AND_TOWNS.md)

---

**Status:** ✅ **ANALYSIS COMPLETE - READY FOR DECISION**
**Next Step:** Test AssemblyAI in Week 1, then choose path based on results
