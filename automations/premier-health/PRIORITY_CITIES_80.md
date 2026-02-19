# Priority Cities for Keyterm Boosting (Max 80-100)

**Purpose:** Optimized list of Ghanaian cities for Deepgram Nova-3 keyterm boosting
**Limit:** 80-100 keyterms (within Deepgram's recommended limits)
**Selection Criteria:**
1. Major cities and regional capitals
2. Cities with complex/unusual spellings or pronunciations
3. Cities that sound similar to common English words
4. High-population areas with likely frequent requests
5. Cities with multiple healthcare facilities (based on Premier Health data)

---

## Category 1: Major Cities (Always Include) - 10 cities

ACCRA
KUMASI
TAMALE
TAKORADI
SEKONDI
KOFORIDUA
SUNYANI
CAPE COAST
HO
BOLGATANGA

---

## Category 2: Greater Accra Region - 25 cities

MADINA
LEGON
DANSOMAN
ASHONGMAN
KANESHIE
ADENTA
TEMA
ASHAIMAN
TESHIE
LABADI
SPINTEX
ACHIMOTA
ADABRAKA
OSU
LABONE
DZORWULU
EAST LEGON
HAATSO
DOME
KASOA
WEIJA
GBAWE
KWABENYA
MALLAM
SOWUTUOM

---

## Category 3: Greater Kumasi Region - 15 cities

AHODWO
ASOKWA
BANTAMA
ADUM
TAFO
SUAME
SANTASI
EJISU
OBUASI
KONONGO
MAMPONG
BEKWAI
AGOGO
JUABEN
ASAWASE

---

## Category 4: Northern Region - 8 cities

WA
BAWKU
BOLGA
NAVRONGO
YENDI
SAVELUGU
WALEWALE
SALAGA

---

## Category 5: Regional Capitals & Key Cities - 12 cities

TECHIMAN
HOHOE
KINTAMPO
NKAWKAW
NSAWAM
WINNEBA
TARKWA
BIBIANI
BEREKUM
GOASO
KETA
ANLOGA

---

## Category 6: Difficult Pronunciations/Spellings - 10 cities

ASAMANKESE
ATEBUBU
ASIAKWA
ODUMASE
SUHUM
KIBI
BEGORO
KPANDAE
SALAGA
WALEWALE

---

## Total: 80 Cities

This optimized list balances:
- ✓ Geographic coverage across all regions
- ✓ Major population centers
- ✓ Cities with complex names that need transcription help
- ✓ Within Deepgram's 100 keyterm limit
- ✓ Reduced overfitting risk

---

## Usage Notes

1. **For VAPI configuration:** Use these 80 cities in the `keyterm` array
2. **Format:** All caps, as shown (matches transcription preferences)
3. **Monitoring:** Track which cities users request but aren't in this list
4. **Updates:** Review quarterly and adjust based on usage analytics
5. **Future:** When implementing dynamic regional selection, expand to full 295 cities

---

## Implementation

To update the VAPI assistant:

```python
PRIORITY_CITIES = [
    # Category 1: Major cities
    "ACCRA", "KUMASI", "TAMALE", "TAKORADI", "SEKONDI",
    "KOFORIDUA", "SUNYANI", "CAPE COAST", "HO", "BOLGATANGA",

    # Category 2: Greater Accra (25 cities)
    "MADINA", "LEGON", "DANSOMAN", "ASHONGMAN", "KANESHIE",
    "ADENTA", "TEMA", "ASHAIMAN", "TESHIE", "LABADI",
    "SPINTEX", "ACHIMOTA", "ADABRAKA", "OSU", "LABONE",
    "DZORWULU", "EAST LEGON", "HAATSO", "DOME", "KASOA",
    "WEIJA", "GBAWE", "KWABENYA", "MALLAM", "SOWUTUOM",

    # Category 3: Greater Kumasi (15 cities)
    "AHODWO", "ASOKWA", "BANTAMA", "ADUM", "TAFO",
    "SUAME", "SANTASI", "EJISU", "OBUASI", "KONONGO",
    "MAMPONG", "BEKWAI", "AGOGO", "JUABEN", "ASAWASE",

    # Category 4: Northern Region (8 cities)
    "WA", "BAWKU", "BOLGA", "NAVRONGO", "YENDI",
    "SAVELUGU", "WALEWALE", "SALAGA",

    # Category 5: Regional centers (12 cities)
    "TECHIMAN", "HOHOE", "KINTAMPO", "NKAWKAW", "NSAWAM",
    "WINNEBA", "TARKWA", "BIBIANI", "BEREKUM", "GOASO",
    "KETA", "ANLOGA",

    # Category 6: Difficult names (10 cities)
    "ASAMANKESE", "ATEBUBU", "ASIAKWA", "ODUMASE", "SUHUM",
    "KIBI", "BEGORO", "KPANDAE", "SALAGA", "WALEWALE"
]

# Total: 80 cities
```

---

## Multi-word Cities to Add (if space allows, up to 100 total)

If you have room for 20 more keyterms to reach 100:

EAST LEGON
CAPE COAST
NEW TAFO
HALF ASSINI
KASOA OFAAKOR
PRAMPRAM
ADA FOAH
AGONA SWEDRU
TWIFO PRASO
MFANTSIMAN
SEKONDI-TAKORADI
SUNYANI WEST
KUMASI SOUTH
ACCRA CENTRAL
TEMA EAST
ASHAIMAN WEST
OBUASI EAST
EJISU JUABEN
TECHIMAN NORTH
HOHOE SOUTH

---

## Validation Checklist

Before deploying:
- [ ] Verify total count ≤ 100 keyterms
- [ ] Test transcription with sample city names
- [ ] Compare accuracy vs. 295 keyterm configuration
- [ ] Monitor false positive rate (forced matches)
- [ ] Track user correction frequency
- [ ] Document performance metrics

---

## Next Steps

1. **Immediate:** Update VAPI assistant with this 80-city list
2. **Week 1-2:** Monitor transcription accuracy and user corrections
3. **Week 3-4:** Analyze which missing cities are frequently requested
4. **Month 2:** Plan dynamic regional keyterm selection system
5. **Quarter 2:** Evaluate ROI for custom model training
