# Fix: Santasi Location Recognition

**Date:** October 17, 2025
**Issue:** "gynecologists in Santasi" returns no results despite MATA DEI HOSPITAL existing in database
**Root Cause:** Location name mismatch - "Santasi" (common name) vs "Santasipatase" (official region name)

---

## Problem

### User Query:
```
User: "Find gynecologists in Santasi"
```

### What Happened:
1. Deepgram transcribed: "Santasi" (no keyword boost - generic transcription)
2. CityNormalizer: No mapping, kept as "SANTASI"
3. RAG Query: "gynecologists in SANTASI"
4. Database has: Region = "SANTASIPATASE"
5. Vector search: "SANTASI" ≠ "SANTASIPATASE" (insufficient similarity)
6. Result: ❌ **"No gynecologists found in SANTASI"**

### What SHOULD Have Happened:
```
MATA DEI HOSPITAL exists in SANTASIPATASE region:
- Specialties: GP/PHY/SRY/GYN/OBS/PED
- Location: SANTASI ROUNDABOUT BEHIND GOIL FILLING STATION
- Phone: 0248559791
```

---

## Root Cause Analysis

### Database Status: ✅ Data Exists
```sql
SELECT * FROM langchain_pg_embedding
WHERE document ILIKE '%MATA DEI%'
```

Result:
```
## MATA DEI HOSPITAL
**Specialties**: Gynecology (GYN), Obstetrics (OBS), Pediatrics (PED)
**Location**: SANTASI ROUNDABOUT BEHIND GOIL FILLING STATION
**Region**: SANTASIPATASE  ← Official region name
```

### Deepgram Keywords: ⚠️ Missing Common Name
- Has: "Santasipatase" (keyword #136)
- Missing: "Santasi" (common local name)

### CityNormalizer: ❌ No Mapping
- No mapping: "Santasi" → "SANTASIPATASE"
- This is needed to handle both names

---

## Solution

### Fix 1: Add "Santasi" to Deepgram Keywords

**Why:** Boost recognition of the common name people actually say

**How:** Add "Santasi" to keywords list

### Fix 2: Add CityNormalizer Mapping

**Why:** Normalize "Santasi" → "SANTASIPATASE" for RAG queries

**How:** Add to STT variations:
```json
{
  "Santasi": "SANTASIPATASE",
  "San Tasi": "SANTASIPATASE",
  "Santasy": "SANTASIPATASE",
  "Santas": "SANTASIPATASE"
}
```

---

## Implementation Status

**Needs:**
1. ⏳ Add "Santasi" to Deepgram keywords
2. ⏳ Add CityNormalizer mapping for Santasi variations
3. ⏳ Test with real call

**Alternative Quick Fix:**
- Update RAG prompts to search for both "Santasi" AND "Santasipatase" when either is mentioned
- This would be a prompt-level fix without needing to update keywords

---

## Testing After Fix

### Test Query:
```
User: "Find gynecologists in Santasi"
```

### Expected Flow:
```
1. Deepgram: "Santasi" (keyword boosted) ✅
2. CityNormalizer: "Santasi" → "SANTASIPATASE" ✅
3. RAG Query: "gynecologists in SANTASIPATASE" ✅
4. Vector Search: Matches documents with region "SANTASIPATASE" ✅
5. Result: MATA DEI HOSPITAL returned ✅
```

### Expected Response:
```
Ama: "Based on our records, MATA DEI HOSPITAL in Santasi offers
gynecology services. They're located at Santasi Roundabout behind
GOIL Filling Station. Their phone number is 0248559791. Would you
like me to send you their details?"
```

---

## Similar Issues to Check

This same pattern may affect other locations with common vs official names:

- "Takoradi" vs "Sekondi-Takoradi"
- "Tema" vs "Tema Municipal"
- Other compound location names

Should audit all location names for similar mismatches.

---

## Summary

✅ **Data exists** - MATA DEI HOSPITAL is in database with GYN services
❌ **Recognition issue** - "Santasi" not in keywords
❌ **Normalization issue** - No mapping for "Santasi" → "SANTASIPATASE"
⏳ **Fix needed** - Add keyword + CityNormalizer mapping

**Impact:** Medium - affects all queries for "Santasi" location
