# NKAWKAW Data Fix - Complete Summary

**Date:** October 17, 2025
**Issues Reported:**
1. Only 1 facility found when searching "hospitals in nkawkaw"
2. Speech recognition hearing "producing kokow" instead of "nkawkaw"

---

## Problems Identified

### Problem 1: Data Split Issue
NKAWKAW facilities were incorrectly split into multiple files due to location extraction issues:
- `NKAWKAW.md` - Had only 4 facilities initially
- `NKAWKAW,.md` - Had 1 facility (created due to comma in location name)
- Some facilities missing entirely

### Problem 2: Missing Facilities
**Expected from Excel:** 8 facilities total under NKAWKAW region
**Actually processed:** Only 5 facilities

**Missing facilities:**
1. ❌ **KWAHU GOVERNMENT HOSPITAL**
   - Address: "NEAR GCB" (too vague, no city name)
   - Was assigned to: "UNKNOWN" location
   - Original region: NKAWKAW

2. ❌ **CLIMAX PHARMACY & LAB. LTD**
   - Address: "KUMASI STATION, NKAWKAW"
   - Was assigned to: KUMASI (regex matched "KUMASI" first)
   - Should be: NKAWKAW (it's at Kumasi Station in Nkawkaw)

3. ✅ **MPRAESO GENERAL HOSPITAL**
   - Address: "MPREASO- KWAHU"
   - Correctly assigned to: MPREASO
   - Note: This is actually in Mpraeso, not Nkawkaw (correctly separated)

### Problem 3: Speech Recognition
"nkawkaw" being transcribed as:
- "producing kokow"
- "pro doing kokow"
- "produceing kokow"

No STT variations existed for these mishearings.

---

## Solutions Implemented

### Fix 1: Merged Split Files ✅
- Merged `NKAWKAW,.md` into `NKAWKAW.md`
- Cleaned up location names (removed trailing commas)

### Fix 2: Added Missing Facilities ✅

**KWAHU GOVERNMENT HOSPITAL** - Added to NKAWKAW.md
```
## KWAHU GOVERNMENT HOSPITAL
**Specialties**: General Practice (GP), DEM
**Specialty Codes**: GP/ DEM
**Phone**: 0842-22126/22280
**Location**: NEAR GCB, NKAWKAW
**Region**: NKAWKAW
```

**CLIMAX PHARMACY & LAB. LTD** - Moved from KUMASI to NKAWKAW
```
## CLIMAX PHARMACY & LAB. LTD
**Specialties**: Pharmacy
**Specialty Codes**: PHARMACY
**Phone**: 241998230
**Location**: KUMASI STATION, NKAWKAW
**Region**: NKAWKAW
```

### Fix 3: Added STT Variations ✅
Updated `ghana_cities_stt_mapping.py`:
```python
'NKAWKAW': [
    'n kaw kaw',
    'enkawkaw',
    'en caw caw',
    'n cow cow',
    'n ka ka',
    'producing kokow',    # NEW
    'pro doing kokow',    # NEW
    'produceing kokow'    # NEW
]
```

### Fix 4: Re-ingested RAG Database ✅
- Updated collection: `helpdesk_premier_health_production`
- Documents indexed: 423
- Chunks created: 466
- Last updated: 2025-10-17T21:19:53

---

## Final NKAWKAW Facilities List

✅ **All 7 facilities now in database:**

1. **AGYAKWA HOSPITAL LTD**
   - Specialties: GP/PHY
   - Phone: 0842 - 22079
   - Location: NKAWKAW

2. **HOLY FAMILY HOSPITAL**
   - Specialties: GP/ PHY/ SUR/ PAE/ PHY/ ANAE/ ORTHO/ PATH
   - Phone: 03431-22081/034321-22269
   - Location: NKAWKAW

3. **STELLEX PHARMACY**
   - Specialties: Pharmacy
   - Phone: 0243311444
   - Location: NKAWKAW

4. **RICOMONS PHARMACY**
   - Specialties: Pharmacy
   - Phone: 0208954111
   - Location: NKAWKAW ROMAN JUNCTION

5. **AHENFO MEDICAL CENTRE**
   - Specialties: GP/SP
   - Phone: 0244804748
   - Location: NKAWKAW, AKWASIHO (NEAR THE PRESBY CHURCH)

6. **KWAHU GOVERNMENT HOSPITAL** ← ADDED
   - Specialties: GP/ DEM
   - Phone: 0842-22126/22280
   - Location: NEAR GCB, NKAWKAW

7. **CLIMAX PHARMACY & LAB. LTD** ← MOVED FROM KUMASI
   - Specialties: Pharmacy
   - Phone: 241998230
   - Location: KUMASI STATION, NKAWKAW

---

## Testing Instructions

### Test Query 1: "hospitals in nkawkaw"
**Expected Results:**
- AGYAKWA HOSPITAL LTD
- HOLY FAMILY HOSPITAL
- KWAHU GOVERNMENT HOSPITAL
- AHENFO MEDICAL CENTRE

**Total:** 4 hospitals

### Test Query 2: "pharmacies in nkawkaw"
**Expected Results:**
- STELLEX PHARMACY
- RICOMONS PHARMACY
- CLIMAX PHARMACY & LAB. LTD

**Total:** 3 pharmacies

### Test Query 3: "facilities in nkawkaw"
**Expected Results:** All 7 facilities

### Test Query 4: Using STT Variations
Try saying:
- "producing kokow" → Should recognize as NKAWKAW ✅
- "pro doing kokow" → Should recognize as NKAWKAW ✅
- "enkawkaw" → Should recognize as NKAWKAW ✅

---

## What Was Fixed

| Issue | Status | Solution |
|-------|--------|----------|
| Data split (NKAWKAW vs NKAWKAW,) | ✅ Fixed | Merged files |
| Missing KWAHU GOVERNMENT HOSPITAL | ✅ Fixed | Added to NKAWKAW |
| CLIMAX PHARMACY in wrong city | ✅ Fixed | Moved from KUMASI to NKAWKAW |
| STT mishearing "producing kokow" | ✅ Fixed | Added STT variations |
| RAG database outdated | ✅ Fixed | Re-ingested all documents |

---

## Note About MPRAESO GENERAL HOSPITAL

**MPRAESO GENERAL HOSPITAL** is **NOT** included in NKAWKAW facilities.

**Reason:** This facility is in **Mpraeso-Kwahu**, which is a separate town from Nkawkaw, despite both being in the Kwahu region.

**Location:** `MPREASO-.md` (correctly separated)

---

## Files Modified

1. `/opt/kasaai/apps/automations/premier-health/processed_data/markdown_documents/NKAWKAW.md`
   - Added KWAHU GOVERNMENT HOSPITAL
   - Added CLIMAX PHARMACY & LAB. LTD
   - Merged AHENFO MEDICAL CENTRE from NKAWKAW,.md

2. `/opt/kasaai/apps/automations/premier-health/processed_data/markdown_documents/KUMASI.md`
   - Removed CLIMAX PHARMACY & LAB. LTD

3. `/opt/kasaai/apps/automations/premier-health/ghana_cities_stt_mapping.py`
   - Added 3 new NKAWKAW STT variations

4. RAG Database: `helpdesk_premier_health_production`
   - Re-indexed with updated documents

---

## Next Steps

1. ✅ **Test Voice Queries**
   - Try: "find hospitals in nkawkaw"
   - Try: "show me pharmacies in producing kokow" (should work!)

2. ✅ **Verify Results**
   - Should return all 7 facilities for general queries
   - Should filter correctly by specialty

3. ✅ **Monitor Logs**
   - Check Custom Tools UI for query success
   - Verify correct facilities are being returned

---

## Tool Call Logs Access

**Custom Tools UI:** https://flow.ailabsafrica.com/custom-tools/68efb5b12b896f72b91236c8

To verify the fix is working:
1. Make a test call asking about "hospitals in nkawkaw"
2. Check the logs for the `query_premier_health_knowledge_base` tool
3. Verify the response includes all 7 facilities

---

## Success Criteria

- [x] All 7 NKAWKAW facilities in database
- [x] KWAHU GOVERNMENT HOSPITAL added
- [x] CLIMAX PHARMACY moved from KUMASI
- [x] STT variations added for "producing kokow"
- [x] RAG database re-ingested
- [x] Files merged and cleaned up

**Status:** ✅ COMPLETE

---

**Questions or Issues?**
- Check `/opt/kasaai/apps/automations/premier-health/processed_data/markdown_documents/NKAWKAW.md`
- Review STT mappings in `ghana_cities_stt_mapping.py`
- Test queries via VAPI assistant

**Date Completed:** October 17, 2025
**Documents Re-indexed:** 423
**NKAWKAW Facilities:** 7 (was 5, now complete)
