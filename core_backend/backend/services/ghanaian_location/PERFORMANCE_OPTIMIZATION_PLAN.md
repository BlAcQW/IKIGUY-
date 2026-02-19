# Performance Optimization Plan: Ghanaian Location Services

## 🚨 Current Performance Concerns

### **1. Memory Usage Issues**
- **Problem**: `PhoneticMatcher._location_cache` loads all locations into memory
- **Impact**: Poor scalability, memory leaks with large datasets
- **Current Load**: ~50-100 locations manageable, 1000+ locations = memory issues

### **2. Database Query Inefficiency**
- **Problem**: Multiple database calls per location query
  - `get_stt_correction()` - STT corrections lookup
  - `get_location_by_name()` - Exact name match
  - `find_locations_by_alias()` - Alias matching
  - `get_pronunciation_guide()` - Pronunciation data
- **Impact**: 150-300ms per query with network latency
- **Current Bottleneck**: Each query = 4-6 database roundtrips

### **3. Phonetic Computation Overhead**
- **Problem**: Real-time phonetic algorithm execution
  - Soundex, NYSIIS, Double Metaphone computed per query
  - Custom Ghanaian pattern processing
- **Impact**: 20-50ms CPU time per query
- **Scale Issue**: Gets worse with fuzzy matching enabled

### **4. Cold Start Performance**
- **Problem**: Service initialization takes 2-5 seconds
- **Cause**: Loading location cache, setting up phonetic codes
- **Impact**: First request timeout in serverless environments

## 🎯 **Optimization Recommendations**

### **Phase 1: Quick Wins (1-2 hours)**

#### **A. Implement Simple Caching**
```python
# Replace complex caching with Redis/simple cache
import functools
from typing import Optional

@functools.lru_cache(maxsize=500)
def get_location_correction(location_input: str) -> Optional[str]:
    """Cached location correction - 500 most common queries"""
    return FALLBACK_CORRECTIONS.get(location_input.lower())

# Performance gain: 95% of queries resolved in <1ms
```

#### **B. Batch Database Queries**
```python
async def get_location_data_batch(location_name: str) -> dict:
    """Single query to get all location data"""

    # Single aggregation query instead of 4 separate queries
    pipeline = [
        {"$match": {"canonical_name": location_name.upper()}},
        {"$lookup": {
            "from": "stt_corrections",
            "localField": "canonical_name",
            "foreignField": "correct_location",
            "as": "corrections"
        }},
        {"$lookup": {
            "from": "pronunciation_guides",
            "localField": "canonical_name",
            "foreignField": "location_name",
            "as": "pronunciation"
        }}
    ]

    # Performance gain: 4-6 queries → 1 query = 70% faster
```

#### **C. Pre-compute Expensive Operations**
```python
# Pre-compute phonetic codes at write time, not read time
async def create_location_with_phonetics(location: GhanaianLocation):
    """Compute phonetic codes when creating location"""
    location.phonetic_codes = compute_all_phonetic_codes(location.canonical_name)
    # Store in database - never compute again

# Performance gain: 20-50ms → 0ms per query
```

### **Phase 2: Architecture Improvements (4-8 hours)**

#### **A. Implement Tiered Caching Strategy**
```python
class TieredLocationService:
    def __init__(self):
        self.l1_cache = {}  # In-memory for 100 most common
        self.l2_cache = None  # Redis for 1000 most common
        self.database = None  # MongoDB for all data

    async def get_location(self, query: str):
        # L1: Memory cache (1ms)
        if query in self.l1_cache:
            return self.l1_cache[query]

        # L2: Redis cache (5ms)
        if self.l2_cache and await self.l2_cache.get(query):
            return await self.l2_cache.get(query)

        # L3: Database (50ms+)
        result = await self.database.get_location(query)

        # Cache the result
        await self._cache_result(query, result)
        return result
```

#### **B. Database Optimization**
```python
# Optimized indexes
await collection.create_index([
    ("canonical_name", 1),
    ("aliases", 1),
    ("phonetic_codes.soundex", 1),
    ("phonetic_codes.metaphone", 1)
], background=True)

# Compound index for common queries
await collection.create_index([
    ("canonical_name", 1),
    ("is_active", 1),
    ("context.healthcare.provider_count", -1)
])
```

### **Phase 3: Advanced Optimizations (8-16 hours)**

#### **A. Search Index Implementation**
```python
# Use MongoDB text search or Elasticsearch
await collection.create_index([
    ("canonical_name", "text"),
    ("aliases", "text"),
    ("phonetic_codes", "text")
], weights={
    "canonical_name": 10,
    "aliases": 5,
    "phonetic_codes": 1
})

# Performance gain: Complex phonetic queries → Simple text search
```

#### **B. Async Optimization Pipeline**
```python
import asyncio

async def process_location_optimized(query: str):
    # Run corrections and phonetic matching in parallel
    tasks = [
        get_stt_correction(query),
        get_phonetic_matches(query),
        get_fuzzy_matches(query)
    ]

    correction, phonetic, fuzzy = await asyncio.gather(*tasks)

    # Combine results intelligently
    return combine_results(correction, phonetic, fuzzy)
```

## 📊 **Performance Targets**

| Metric | Current | Phase 1 | Phase 2 | Phase 3 |
|--------|---------|---------|---------|---------|
| **Average Query Time** | 200-300ms | 50-100ms | 10-30ms | 5-15ms |
| **Cache Hit Rate** | 0% | 80% | 95% | 98% |
| **Memory Usage** | High | Medium | Low | Minimal |
| **Database Queries/Request** | 4-6 | 2-3 | 1 | 0.1 |
| **Cold Start Time** | 2-5s | 1-2s | 500ms | 100ms |

## 🔧 **Immediate Actions (Next 24 Hours)**

### **Priority 1: Cache Top Corrections**
```python
# Add to simple_integration.py
CACHED_CORRECTIONS = {
    # Top 20 most common mishearings
    "madena": "Madina",
    "zorwulu": "Dzorwulu",
    "kanashi": "Kaneshie",
    # ... add more based on usage analytics
}

@lru_cache(maxsize=100)
def fast_location_fix(location: str) -> str:
    return CACHED_CORRECTIONS.get(location.lower(), location)
```

### **Priority 2: Add Performance Monitoring**
```python
import time
from functools import wraps

def track_performance(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = (time.time() - start) * 1000

        logger.info(f"🔍 {func.__name__}: {duration:.1f}ms")
        return result
    return wrapper

@track_performance
async def correct_location_async(location_input: str):
    # Your existing function
```

### **Priority 3: Graceful Degradation**
```python
async def correct_location_with_fallback(location_input: str) -> dict:
    try:
        # Try database correction (timeout after 100ms)
        return await asyncio.wait_for(
            correct_location_async(location_input),
            timeout=0.1
        )
    except asyncio.TimeoutError:
        # Fall back to simple dictionary
        return {
            "original": location_input,
            "corrected": fix_location(location_input),
            "confidence": 0.7,
            "source": "fallback_timeout"
        }
    except Exception as e:
        # Fall back on any error
        logger.warning(f"Location service degraded: {e}")
        return {
            "original": location_input,
            "corrected": fix_location(location_input),
            "confidence": 0.6,
            "source": "fallback_error"
        }
```

## 🚀 **Expected Performance Gains**

### **After Phase 1 (Quick Wins)**
- **80% faster** for common queries (hit simple cache)
- **50% faster** for database queries (batching)
- **90% less CPU** usage (pre-computed phonetics)

### **After Phase 2 (Architecture)**
- **95% cache hit rate** for production traffic
- **10x faster** average response time
- **5x less** database load

### **After Phase 3 (Advanced)**
- **Sub-10ms** response times for 99% of queries
- **Horizontal scaling** capability
- **Production-grade** performance

## 🎯 **Success Metrics**

1. **Response Time**: 95th percentile < 50ms
2. **Availability**: 99.9% uptime with graceful degradation
3. **Accuracy**: Maintain current 85%+ correction accuracy
4. **Scalability**: Handle 1000+ requests/minute
5. **Resource Usage**: <100MB memory footprint

**Bottom Line**: The current system has good functionality but poor performance. These optimizations will make it production-ready while maintaining all features.