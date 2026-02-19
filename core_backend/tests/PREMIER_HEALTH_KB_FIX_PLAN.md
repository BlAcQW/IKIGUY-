# Action Plan: Fix and Test Premier Health KB Tool Recommendations

**Date:** October 28, 2025
**Tool:** `query_premier_health_knowledge_base`
**Current Status:** 96.9% pass rate (31/32 tests passed)
**Target:** 100% pass rate with improved performance

---

## Priority Classification

### 🔴 **HIGH PRIORITY** - Critical issues affecting functionality
1. Greater Accra Regional Query Timeout
2. Plan Type Filtering Not Working
3. Tema Communities Query Issues (COMM 5, COMM 6, etc.)

### 🟡 **MEDIUM PRIORITY** - Performance and coverage improvements
4. Optimize Complex Query Performance
5. Regional Coverage Testing
6. Specialty Search Enhancement

### 🟢 **LOW PRIORITY** - Nice-to-have improvements
7. Query Pattern Analysis
8. Enhanced Error Messages

---

## Detailed Fix Plan

---

## 🔴 HIGH PRIORITY #1: Greater Accra Regional Query Timeout

### Issue
Query for "hospitals in Greater Accra" timed out (0.0s response time).
- **Root Cause:** Greater Accra has 20+ cities, causing very large query expansion
- **Impact:** Users cannot search entire Greater Accra region

### Fix Steps

#### Step 1: Investigate Current Behavior
```python
# File: apps/automations/premier-health/city_normalizer.py
# Check how many cities are in Greater Accra region
```

**Action:**
- [ ] Find `city_normalizer.py` and check `get_cities_for_region("GREATER ACCRA")`
- [ ] Count number of cities (likely 20-30)
- [ ] Test current timeout threshold

#### Step 2: Implement Progressive Regional Search
```python
# File: apps/core_backend/backend/services/helpdesk_rag_service.py
# Instead of querying all cities at once, use a smarter approach:

async def query_knowledge_base(self, company_name: str, query: str, region: str = None):
    if region and len(regional_cities) > 15:
        # Use progressive search:
        # 1. First, search for "region" as keyword
        # 2. Then aggregate results from top 10 most populous cities
        # 3. Add disclaimer about coverage
        pass
```

**Actions:**
- [ ] Update `helpdesk_rag_service.py` to detect large regional queries
- [ ] Implement progressive search strategy:
  - Search by region keyword first
  - If insufficient results, search top 10 cities
  - Return combined results
- [ ] Add response disclaimer: "Showing results for major cities in {region}..."

#### Step 3: Pre-compute Regional Queries
**Actions:**
- [ ] Add Greater Accra to pre-computation list
- [ ] Run pre-computation for all regions
- [ ] Verify cached responses exist

#### Step 4: Test Fix
```bash
# Test regional queries
curl -X POST "https://api.ailabsafrica.com/knowledge-base/premier_health_production/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "hospitals in Greater Accra", "region": "Greater Accra"}'
```

**Expected Result:**
- Response time < 10s
- Confidence ≥ 0.95
- Sources from multiple cities
- No timeout

---

## 🔴 HIGH PRIORITY #2: Plan Type Filtering Not Working

### Issue
Query for "general practitioners" with `plan_type="REGULAR"` returned providers marked "PLATINUM PLUS ONLY".
- **Confidence:** 0.0 (indicates poor match)
- **Impact:** Users get incorrect plan information

### Fix Steps

#### Step 1: Investigate Current Filtering Logic
**File:** `apps/core_backend/backend/services/helpdesk_rag_service.py`

**Current Behavior:**
```python
# Query likely searches for "general practitioners" but doesn't filter embeddings by plan
result = await self.query_knowledge_base(query="general practitioners")
```

**Actions:**
- [ ] Read current plan type filtering implementation
- [ ] Check if plan type is passed to vector search
- [ ] Verify metadata filtering in LangChain

#### Step 2: Implement Strict Plan Filtering
```python
# File: apps/core_backend/backend/services/helpdesk_rag_service.py

async def query_knowledge_base(
    self,
    company_name: str,
    query: str,
    plan_type: Optional[str] = None,
    region: Optional[str] = None
):
    # Add plan type to search filter
    filter_dict = {}

    if plan_type:
        # Map plan type to acceptable values
        plan_mapping = {
            "PLATINUM PLUS": ["PLAT PLUS", "PLATINUM PLUS", "PLAT. PLUS", "ALL"],
            "PLATINUM": ["PLATINUM", "PLAT", "ALL"],
            "MERCURY": ["MERCURY", "MER", "ALL"],
            "REGULAR": ["REGULAR", "REG", "ALL"]
        }

        acceptable_plans = plan_mapping.get(plan_type, [plan_type])
        filter_dict["plan_accepted"] = {"$in": acceptable_plans}

    # Pass filter to vector search
    results = await vector_store.similarity_search_with_filter(
        query=query,
        filter=filter_dict,
        k=10
    )
```

**Actions:**
- [ ] Add plan type metadata to document embeddings (if missing)
- [ ] Implement filter dictionary for vector search
- [ ] Create plan type mapping (PLATINUM PLUS, PLATINUM, MERCURY, REGULAR)
- [ ] Update vector search to use metadata filtering

#### Step 3: Post-Process Results to Remove Invalid Matches
```python
# After getting results, filter out mismatched plans
filtered_results = []
for doc in results:
    doc_plan = extract_plan_from_content(doc.page_content)
    if is_plan_acceptable(doc_plan, requested_plan_type):
        filtered_results.append(doc)
```

**Actions:**
- [ ] Add post-processing filter
- [ ] Extract plan from document content using regex
- [ ] Validate plan matches request

#### Step 4: Test Plan Filtering
```bash
# Test each plan type
for plan in "PLATINUM PLUS" "PLATINUM" "MERCURY" "REGULAR"; do
  echo "Testing plan: $plan"
  curl -X POST "https://api.ailabsafrica.com/knowledge-base/premier_health_production/query" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"doctors in Madina\", \"plan_type\": \"$plan\"}"
done
```

**Expected Result:**
- Only providers accepting the specified plan are returned
- Confidence ≥ 0.85
- No providers with "X ONLY" where X ≠ requested plan

---

## 🔴 HIGH PRIORITY #3: Tema Communities Query Issues

### Issue
Query "providers in community 5" incorrectly normalized to "COMMUNITY 1 5".
- **Impact:** Tema communities (COMM 5, COMM 6, COMM 18, etc.) not found

### Fix Steps

#### Step 1: Investigate City Normalizer
**File:** `apps/automations/premier-health/city_normalizer.py`

**Actions:**
- [ ] Check how "community 5" is being parsed
- [ ] Find where the "1" is being inserted
- [ ] Check regex patterns for community names

#### Step 2: Add Tema Community Mappings
```python
# File: apps/automations/premier-health/city_normalizer.py

TEMA_COMMUNITIES = {
    "community 1": "COMM. 1",
    "community 2": "COMM. 2",
    "community 3": "COMM. 3",
    "community 4": "COMM. 4",
    "community 5": "COMM. 5",
    "community 6": "COMM. 6",
    # ... up to COMM. 25
    "comm 1": "COMM. 1",
    "comm 2": "COMM. 2",
    # Also handle "comm. 5", "tema community 5", etc.
}

def normalize_tema_community(text: str) -> Optional[str]:
    """Normalize Tema community references."""
    import re

    # Pattern: "community <number>" or "comm <number>" or "comm. <number>"
    pattern = r'\b(?:community|comm\.?)\s+(\d+)\b'
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        comm_num = match.group(1)
        return f"COMM. {comm_num}"

    return None
```

**Actions:**
- [ ] Add `TEMA_COMMUNITIES` dictionary to city normalizer
- [ ] Implement `normalize_tema_community()` function
- [ ] Update main normalization logic to call this function first
- [ ] Test with "community 5", "comm 5", "comm. 5", "tema community 5"

#### Step 3: Check Knowledge Base Documents
**Action:**
- [ ] Query database for how communities are stored:
```sql
SELECT DISTINCT title
FROM kb_documents
WHERE collection_name = 'premier_health_production'
  AND title ILIKE '%comm%'
ORDER BY title;
```

#### Step 4: Test Community Queries
```bash
# Test all common variations
for comm in "community 5" "comm 5" "comm. 5" "tema community 5" "community 18"; do
  echo "Testing: $comm"
  curl -s -X POST "https://api.ailabsafrica.com/knowledge-base/premier_health_production/query" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"providers in $comm\"}" | \
    python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  Normalized: {d[\"query\"]}'); print(f'  Found: {len(d.get(\"sources_used\", []))} sources')"
done
```

**Expected Result:**
- "community 5" → "COMM. 5" or "COMMUNITY 5"
- "comm 5" → "COMM. 5"
- Sources found for each community
- Confidence ≥ 0.85

---

## 🟡 MEDIUM PRIORITY #4: Optimize Complex Query Performance

### Issue
Some queries take 15-18s (e.g., very long queries, multiple locations).
- **Impact:** Slow user experience

### Fix Steps

#### Step 1: Implement Query Result Caching
Already implemented! Redis cache shows 98.7x speedup.

**Enhancement:**
- [ ] Increase cache TTL from 24h to 7 days for stable queries
- [ ] Add cache warming for top 100 queries
- [ ] Monitor cache hit rate

#### Step 2: Query Pre-computation
**File:** `apps/core_backend/backend/services/query_precompute_service.py`

**Actions:**
- [ ] Pre-compute top 50 queries daily
- [ ] Pre-compute all regional queries
- [ ] Pre-compute common specialty queries ("pediatricians", "cardiologists", etc.)

#### Step 3: Optimize Vector Search
```python
# Reduce k value for faster searches
results = await vector_store.similarity_search(query=query, k=5)  # Instead of k=10

# Add timeout to prevent long-running queries
results = await asyncio.wait_for(
    vector_store.similarity_search(query=query, k=5),
    timeout=8.0  # 8 second max
)
```

**Actions:**
- [ ] Tune `k` parameter (number of results)
- [ ] Add query timeout
- [ ] Test performance impact

---

## 🟡 MEDIUM PRIORITY #5: Regional Coverage Testing

### Fix Steps

**Actions:**
- [ ] Test all 16 regions of Ghana:
  1. Greater Accra
  2. Ashanti
  3. Western
  4. Central
  5. Eastern
  6. Volta
  7. Northern
  8. Upper East
  9. Upper West
  10. Bono
  11. Bono East
  12. Ahafo
  13. Savannah
  14. North East
  15. Oti
  16. Western North

- [ ] Create regional test script:
```python
# File: tests/test_regional_coverage.py
REGIONS = [
    "Greater Accra", "Ashanti", "Western", "Central",
    # ... all 16 regions
]

for region in REGIONS:
    test_regional_query(f"hospitals in {region}")
```

---

## 🟡 MEDIUM PRIORITY #6: Specialty Search Enhancement

### Issue
Some specialties not found (cardiologists, orthopedic surgeons).

### Fix Steps

#### Step 1: Audit Knowledge Base for Missing Specialties
```sql
SELECT DISTINCT
    UNNEST(string_to_array(content, ',')) as specialty
FROM kb_documents
WHERE collection_name = 'premier_health_production'
  AND content LIKE '%Specialties%'
ORDER BY specialty;
```

**Actions:**
- [ ] List all specialties in knowledge base
- [ ] Identify missing specialties
- [ ] Request data from Premier Health for missing specialties

#### Step 2: Add Specialty Synonyms
```python
# File: apps/core_backend/backend/services/helpdesk_rag_service.py

SPECIALTY_SYNONYMS = {
    "cardiologist": ["cardiology", "heart specialist", "cardiac care"],
    "orthopedic": ["orthopedics", "bone specialist", "ortho"],
    "pediatrician": ["pediatrics", "paediatrics", "child specialist", "paed"],
    # ... more mappings
}

def expand_specialty_query(query: str) -> str:
    """Expand query with specialty synonyms."""
    for specialty, synonyms in SPECIALTY_SYNONYMS.items():
        if specialty in query.lower():
            # Add synonyms to query
            query += f" OR {' OR '.join(synonyms)}"
    return query
```

**Actions:**
- [ ] Add specialty synonym dictionary
- [ ] Implement query expansion
- [ ] Test specialty searches

---

## 🟢 LOW PRIORITY #7: Query Pattern Analysis

### Actions
- [ ] Set up MongoDB aggregation pipeline to analyze queries
- [ ] Track:
  - Most common locations
  - Most common specialties
  - Most common plan types
  - Query patterns (time of day, day of week)
- [ ] Generate weekly report
- [ ] Use insights to optimize pre-computation

---

## 🟢 LOW PRIORITY #8: Enhanced Error Messages

### Actions
- [ ] Add "Did you mean?" suggestions for misspelled cities
```python
# If city not found, suggest closest match
if not found:
    suggestions = fuzzy_match_cities(city_name, max_distance=2)
    error_msg = f"City '{city_name}' not found. Did you mean: {', '.join(suggestions)}?"
```

- [ ] Include example queries in error messages
- [ ] Add links to support

---

## Implementation Timeline

### Week 1: High Priority Fixes
- **Day 1-2:** Fix Greater Accra timeout
- **Day 3-4:** Fix plan type filtering
- **Day 5:** Fix Tema communities normalization
- **Day 6-7:** Test and validate all HIGH priority fixes

### Week 2: Medium Priority Improvements
- **Day 8-9:** Optimize query performance
- **Day 10-11:** Regional coverage testing
- **Day 12-13:** Specialty search enhancement
- **Day 14:** Test and validate MEDIUM priority fixes

### Week 3: Low Priority & Polish
- **Day 15-16:** Query pattern analysis setup
- **Day 17-18:** Enhanced error messages
- **Day 19-20:** Final testing and documentation
- **Day 21:** Deploy to production

---

## Testing Strategy

### Unit Tests
```python
# File: tests/test_plan_filtering.py
def test_platinum_plus_filtering():
    result = query_kb("doctors in Madina", plan_type="PLATINUM PLUS")
    assert all("PLAT PLUS" in doc or "ALL" in doc for doc in result.sources)

def test_tema_community_normalization():
    assert normalize_city("community 5") == "COMM. 5"
    assert normalize_city("comm 5") == "COMM. 5"
    assert normalize_city("tema community 18") == "COMM. 18"
```

### Integration Tests
```python
# File: tests/test_regional_queries_integration.py
def test_all_regions():
    for region in ALL_REGIONS:
        result = query_kb(f"hospitals in {region}")
        assert result.success
        assert result.confidence_score >= 0.85
        assert len(result.sources_used) > 0
```

### Performance Tests
```python
# File: tests/test_performance.py
def test_query_performance():
    start = time.time()
    result = query_kb("doctors in Madina")
    duration = time.time() - start

    assert duration < 5.0  # Must complete in < 5s
    assert result.confidence_score >= 0.85
```

---

## Success Criteria

### Functional Requirements
- [ ] 100% test pass rate (32/32 tests)
- [ ] No timeouts for any regional query
- [ ] Plan type filtering works correctly (100% accuracy)
- [ ] Tema communities queries work correctly
- [ ] All 16 regions tested and working

### Performance Requirements
- [ ] Average response time < 4s (currently 5.2s)
- [ ] 95th percentile response time < 8s (currently 18s)
- [ ] Cache hit rate > 60% in production
- [ ] Confidence score ≥ 0.85 for 95% of queries

### Quality Requirements
- [ ] Confidence scores ≥ 0.85 for location queries
- [ ] Confidence scores ≥ 0.80 for specialty queries
- [ ] Escalation rate < 10% (currently tracking)
- [ ] Source attribution for all responses

---

## Rollback Plan

If issues arise after deployment:

1. **Immediate Rollback**
   - Revert code changes
   - Clear Redis cache
   - Monitor error logs

2. **Gradual Rollout**
   - Deploy to dev server first
   - Test for 48 hours
   - Deploy to 10% of production traffic
   - Monitor metrics
   - Full production deployment

---

## Monitoring & Alerts

### Metrics to Track
- Query response time (avg, p50, p95, p99)
- Cache hit rate
- Confidence score distribution
- Escalation rate
- Error rate
- Timeout rate

### Alerts
- Alert if response time > 10s for 5 consecutive queries
- Alert if error rate > 5%
- Alert if confidence score < 0.70 for > 10% of queries
- Alert if cache hit rate < 40%

---

## Documentation Updates

- [ ] Update API documentation with plan type filtering
- [ ] Update README with Tema community support
- [ ] Update VAPI tool description
- [ ] Create troubleshooting guide
- [ ] Update test documentation

---

**Next Steps:** Begin implementation with HIGH priority fixes.
**Review Date:** After each fix is deployed
**Final Review:** End of Week 3
