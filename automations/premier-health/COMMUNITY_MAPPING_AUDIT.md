# Tema Community Document Mapping Audit

**Date**: October 30, 2025  
**Issue**: Community 5 vector search failure  
**Root Cause**: Data mapping error

---

## Issue Summary

**Problem**: Query "providers in community 5" returns wrong results (Community 38, 31) instead of Community 5.

**Root Cause**: LAGOON CLINIC is incorrectly placed in "TEMA COMMUNITY 5" document when it actually belongs to Community 2.

---

## Data Analysis

### Current Knowledge Base (INCORRECT)
- **Document**: "Healthcare Providers in TEMA COMMUNITY 5"
- **Provider**: LAGOON CLINIC
- **Location in Document**: "SITE 13, COMMUNITY ONE, TEMA"
- **Problem**: Document title says "Community 5" but provider location says "Community ONE"

### Source Data (CORRECT)
- **File**: `tema_community_2.csv`
- **Master List**: Row labeled "Tema Community 2"
- **Provider**: LAGOON CLINIC
- **Location**: "SITE 13, COMMUNITY ONE, TEMA. NEAR THE POST OFFICE"

### Actual Community 5 Provider
According to `tema_community_4__5__6__9__10__12.csv`:
- **Provider**: JEAVCO SPECIALIST MEDICAL LAB
- **Location**: "TEMA COMM 10 JUNCTION AND TEMA COMM 5 JUNCTION"
- **Specialties**: LABORATORY
- **Phone**: 0277-573316 / 0303-336440

---

## Impact on Vector Search

The semantic mismatch between:
- Document title: "TEMA COMMUNITY 5"
- Provider location: "COMMUNITY ONE"

Creates confusion in vector embeddings, causing the similarity search to return semantically similar but incorrect documents (Community 38, 31) instead of the correct Community 5 document.

Even with proper embeddings in the vector store (confirmed: 3 chunks exist for Community 5), the semantic inconsistency prevents accurate retrieval.

---

## Recommended Fix

### Option 1: Correct the Data (RECOMMENDED)
1. **Remove LAGOON CLINIC** from "TEMA COMMUNITY 5" document
2. **Add LAGOON CLINIC** to "TEMA COMMUNITY 2" document (or Community 1)
3. **Add JEAVCO SPECIALIST MEDICAL LAB** to "TEMA COMMUNITY 5" document
4. **Reindex** the affected documents

### Option 2: Hybrid Search
Implement keyword + vector hybrid search to catch exact matches on community numbers even when semantic meaning is unclear.

---

## Files to Update

### Source Data
- `/opt/kasaai/apps/automations/premier-health/data/by_region/tema_community_2.csv`
- `/opt/kasaai/apps/automations/premier-health/data/by_region/tema_community_4__5__6__9__10__12.csv`

### Knowledge Base Documents
- Document ID: 1913 - "Healthcare Providers in TEMA COMMUNITY 5" (needs correction)
- Find Community 2 document and verify LAGOON CLINIC placement

---

## Testing After Fix

```bash
# Test Community 5 query
curl -X POST "https://api.ailabsafrica.com/knowledge-base/premier_health_production/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "providers in community 5"}'

# Expected result: JEAVCO SPECIALIST MEDICAL LAB
# Current result: "No providers found" (returns Community 38, 31 instead)
```

---

## Status

- ✅ Issue Identified
- ✅ Root Cause Confirmed
- ⏳ Waiting for Data Correction
- ⏳ Re-indexing Required After Fix

---

## Notes

This is a **data quality issue**, not a technical bug. The RAG system, vector search, and normalization are all working correctly. The problem is that the source data was incorrectly mapped during knowledge base document generation.

**Action Required**: Client/data team needs to verify and correct the provider-to-community mappings in the source CSV files before regenerating the knowledge base documents.


## UPDATE: Enrichment Bug Identified

**Root Cause**: The enrichment process incorrectly assigns providers to communities based on row numbers instead of actual location data.

**Evidence**:
```csv
Provider #2 → TEMA COMMUNITY 4 (actual: 'TEMA COMM. 1')
Provider #3 → TEMA COMMUNITY 5 (actual: 'COMMUNITY ONE') ← LAGOON CLINIC
Provider #4 → TEMA COMMUNITY 6
```

**Impact**: Multiple Tema community documents have incorrect provider assignments, not just Community 5.

**Fix Required**: Re-run enrichment process with corrected mapping logic that uses actual location data instead of row numbers.

