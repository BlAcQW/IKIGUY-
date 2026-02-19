# Ghana Cities STT Mapping System

**Version**: 1.0.0
**Date**: October 2025
**Author**: AI Labs Africa
**Purpose**: Improve voice assistant location accuracy for Premier Health provider searches

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [Solution](#solution)
4. [Files Structure](#files-structure)
5. [Quick Start](#quick-start)
6. [Integration Guide](#integration-guide)
7. [API Reference](#api-reference)
8. [Examples](#examples)
9. [Testing](#testing)
10. [CSV Maintenance](#csv-maintenance)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

---

## 📖 Overview

The Ghana Cities STT (Speech-to-Text) Mapping System is a comprehensive solution for normalizing voice assistant location queries to their correct city names. It addresses the common problem where speech-to-text engines mishear or misinterpret Ghanaian city names, leading to failed healthcare provider searches.

### Key Features

- **106 cities/regions** mapped across Ghana
- **~890 STT variations** covering common mishearings
- **Fuzzy matching** for variations not in the database
- **Regional groupings** for geographic queries
- **Confidence scoring** for match quality
- **Batch processing** for multiple queries
- **CSV export** for easy maintenance

---

## 🎯 Problem Statement

### The Challenge

When users interact with voice assistants to find healthcare providers, STT engines often mishear Ghanaian city names:

- **User says**: "Find doctors in Madina"
- **STT outputs**: "medina", "madonna", "moderna"
- **Result**: Failed search or wrong location

### Example Mishearings

| Correct City | Common STT Mishearings |
|--------------|------------------------|
| MADINA | medina, madonna, moderna, marina |
| WINNEBA | winnipeg, winnebago, winnepeg |
| CIRCLE | circus, sircle, sir kill |
| DZORWULU | jaw wulu, zor wulu, joe wulu |
| KOFORIDUA | coffee ridua, ko for idea |

### Impact

- **Poor user experience**: Frustration when searches fail
- **Lost conversions**: Users give up and don't book appointments
- **Missed provider opportunities**: Providers don't get discovered
- **Support burden**: Increased customer service inquiries

---

## ✅ Solution

The STT Mapping System provides:

1. **Comprehensive mapping** of all Premier Health locations to their STT variations
2. **Easy-to-use Python API** for normalizing user input
3. **Fuzzy matching fallback** for unknown variations
4. **CSV reference file** for non-technical team members to maintain
5. **Test suite** ensuring data integrity and consistency

---

## 📁 Files Structure

```
/opt/kasaai/apps/automations/premier-health/
│
├── ghana_cities_stt_mapping.py       # Main mapping module (106 cities, ~890 variations)
├── city_normalizer.py                # Helper module with convenience functions
├── tests/
│   └── test_city_normalizer.py       # Comprehensive test suite (49 tests)
│
└── data/
    ├── ghana_cities_stt_mapping.csv  # CSV reference file for easy editing
    ├── premier_health_master_provider_list.csv
    ├── premier_health_specialties.csv
    └── by_region/                    # 106 regional CSV files
```

---

## 🚀 Quick Start

### Installation

No installation required - the modules are ready to use!

### Basic Usage

```python
from city_normalizer import normalize

# Normalize STT input
city = normalize("medina")
print(city)  # Output: "MADINA"

# More examples
normalize("circus")        # "CIRCLE"
normalize("winnipeg")      # "WINNEBA"
normalize("jaw wulu")      # "DZORWULU"
normalize("coffee ridua")  # "KOFORIDUA"
```

### Using the CityNormalizer Class

```python
from city_normalizer import CityNormalizer

normalizer = CityNormalizer()

# Normalize with confidence score
city, confidence, method = normalizer.normalize_with_confidence("medina")
print(f"{city} (confidence: {confidence:.2f}, method: {method})")
# Output: MADINA (confidence: 1.00, method: exact)

# Get all variations for a city
variations = normalizer.get_variations("MADINA")
print(variations)
# Output: ['medina', 'madonna', 'moderna', 'marina', ...]

# Find region for a city
region = normalizer.get_region_for_city("MADINA")
print(region)
# Output: GREATER_ACCRA
```

---

## 🔧 Integration Guide

### VAPI Voice Assistant Integration

#### Step 1: Import the normalizer

```python
from apps.automations.premier_health.city_normalizer import CityNormalizer

normalizer = CityNormalizer()
```

#### Step 2: Normalize user input

```python
# VAPI provides the user's query
user_query = "Find doctors in medina"

# Extract location from query (you may use NLP)
stt_location = "medina"  # Extracted from query

# Normalize to correct city
correct_city = normalizer.normalize_city(stt_location)
# correct_city = "MADINA"
```

#### Step 3: Use in knowledge base query

```python
# Query knowledge base with correct city name
from apps.core_backend.backend.services.helpdesk_rag_service import HelpdeskRAGService

rag_service = HelpdeskRAGService()

# Build query with normalized city
query = f"Healthcare providers in {correct_city}"

result = await rag_service.query_knowledge_base(
    company_name="premier_health_production",
    query=query
)

# Return result to VAPI
return result.response
```

#### Complete VAPI Integration Example

```python
async def handle_vapi_location_query(user_input: str) -> str:
    """
    Handle VAPI location query with STT normalization.

    Args:
        user_input: User's voice query (e.g., "Find doctors in medina")

    Returns:
        Response text for VAPI to speak
    """
    from apps.automations.premier_health.city_normalizer import CityNormalizer
    from apps.core_backend.backend.services.helpdesk_rag_service import HelpdeskRAGService

    normalizer = CityNormalizer()
    rag_service = HelpdeskRAGService()

    # Extract location from user input (simplified - use NLP in production)
    # Example: "Find doctors in medina" -> "medina"
    words = user_input.lower().split()
    if "in" in words:
        location_idx = words.index("in") + 1
        stt_location = words[location_idx] if location_idx < len(words) else None
    else:
        return "I couldn't identify a location in your query. Please try again."

    # Normalize location with confidence
    city, confidence, method = normalizer.normalize_with_confidence(stt_location)

    if not city:
        # Try fuzzy matching
        matches = normalizer.find_closest_match(stt_location, threshold=0.7)
        if matches:
            city = matches[0][0]
            confidence = matches[0][1]
            method = "fuzzy"
        else:
            return f"I couldn't find a location matching '{stt_location}'. Could you please repeat?"

    # Get region for context
    region = normalizer.get_region_for_city(city)

    # Query knowledge base
    query = f"Healthcare providers in {city}"
    result = await rag_service.query_knowledge_base(
        company_name="premier_health_production",
        query=query
    )

    # Build response
    if result.sources:
        response = f"Here are healthcare providers in {city}, {region}:\n\n{result.response}"
    else:
        response = f"I found {city} in {region}, but no providers are listed for this area yet."

    return response
```

### Backend API Integration

#### Option 1: Middleware Approach

Create a middleware that automatically normalizes location parameters:

```python
# apps/core_backend/backend/middleware/location_normalizer.py

from fastapi import Request
from apps.automations.premier_health.city_normalizer import normalize

async def normalize_location_middleware(request: Request, call_next):
    """
    Middleware to normalize location parameters in requests.
    """
    # Check query parameters
    if "location" in request.query_params:
        original_location = request.query_params["location"]
        normalized_location = normalize(original_location)

        if normalized_location:
            # Replace query params with normalized version
            request._query_params = request.query_params.copy()
            request._query_params["location"] = normalized_location

    response = await call_next(request)
    return response
```

#### Option 2: Route-Level Integration

Add normalization directly to your knowledge base query route:

```python
# apps/core_backend/backend/routes/knowledge_base.py

from apps.automations.premier_health.city_normalizer import CityNormalizer

normalizer = CityNormalizer()

@router.post("/{company_name}/query")
async def query_knowledge_base(
    company_name: str,
    request: QueryRequest
):
    query = request.query

    # Extract location from query (use NLP or pattern matching)
    location = extract_location_from_query(query)  # Your implementation

    if location:
        # Normalize location
        normalized_city = normalizer.normalize_city(location)

        if normalized_city:
            # Replace location in query with normalized version
            query = query.replace(location, normalized_city)

    # Continue with normal query processing
    result = await helpdesk_rag_service.query_knowledge_base(
        company_name=company_name,
        query=query
    )

    return result
```

### Frontend Integration

If you need to normalize locations in the frontend:

```typescript
// apps/b2c-portal/src/utils/locationNormalizer.ts

// Import the mapping (you'll need to export it as JSON)
import { ghanaSTTMapping } from './ghana_stt_mapping.json';

export function normalizeLocation(sttInput: string): string | null {
    // Convert to uppercase for lookup
    const normalized = sttInput.toUpperCase();

    // Check if it's a variation
    if (ghanaSTTMapping.reverse[normalized]) {
        return ghanaSTTMapping.reverse[normalized];
    }

    // Check if it's already a correct city name
    if (ghanaSTTMapping.cities.includes(normalized)) {
        return normalized;
    }

    return null;
}
```

---

## 📚 API Reference

### CityNormalizer Class

#### `normalize_city(input_text: str, case_sensitive: bool = False) -> Optional[str]`

Normalize an STT input to the correct city name.

**Parameters:**
- `input_text` (str): STT input text
- `case_sensitive` (bool): Whether to perform case-sensitive matching (default: False)

**Returns:**
- `Optional[str]`: Correct city name or None if not found

**Example:**
```python
normalizer.normalize_city("medina")  # Returns: "MADINA"
```

---

#### `get_variations(city: str) -> List[str]`

Get all STT variations for a given city.

**Parameters:**
- `city` (str): Correct city name

**Returns:**
- `List[str]`: List of STT variations

**Example:**
```python
normalizer.get_variations("MADINA")
# Returns: ['medina', 'madonna', 'moderna', ...]
```

---

#### `is_valid_city(city: str) -> bool`

Check if a city name is valid.

**Parameters:**
- `city` (str): City name to check

**Returns:**
- `bool`: True if valid city, False otherwise

---

#### `is_valid_variation(variation: str) -> bool`

Check if an STT variation exists in mappings.

**Parameters:**
- `variation` (str): STT variation to check

**Returns:**
- `bool`: True if valid variation, False otherwise

---

#### `get_cities_by_region(region: str) -> List[str]`

Get all cities in a specific region.

**Parameters:**
- `region` (str): Region name (e.g., "GREATER_ACCRA", "ASHANTI")

**Returns:**
- `List[str]`: List of cities in that region

**Example:**
```python
normalizer.get_cities_by_region("VOLTA")
# Returns: ['HO', 'HOHOE']
```

---

#### `find_closest_match(input_text: str, threshold: float = 0.6, limit: int = 5) -> List[Tuple[str, float]]`

Find closest matching cities using fuzzy matching.

**Parameters:**
- `input_text` (str): STT input text
- `threshold` (float): Minimum similarity score (0.0 to 1.0)
- `limit` (int): Maximum number of matches to return

**Returns:**
- `List[Tuple[str, float]]`: List of (city_name, similarity_score) tuples

**Example:**
```python
normalizer.find_closest_match("winnepeg", threshold=0.7)
# Returns: [('WINNEBA', 0.95), ...]
```

---

#### `normalize_with_confidence(input_text: str, fuzzy_threshold: float = 0.8) -> Tuple[Optional[str], float, str]`

Normalize with confidence score and method used.

**Parameters:**
- `input_text` (str): STT input text
- `fuzzy_threshold` (float): Threshold for fuzzy matching

**Returns:**
- `Tuple[Optional[str], float, str]`: (city_name, confidence, method)

**Example:**
```python
city, confidence, method = normalizer.normalize_with_confidence("medina")
# Returns: ("MADINA", 1.0, "exact")
```

---

#### `get_region_for_city(city: str) -> Optional[str]`

Get the region for a given city.

**Parameters:**
- `city` (str): City name

**Returns:**
- `Optional[str]`: Region name or None if not found

---

#### `batch_normalize(input_texts: List[str], include_confidence: bool = False) -> List[Dict]`

Normalize multiple STT inputs in batch.

**Parameters:**
- `input_texts` (List[str]): List of STT inputs
- `include_confidence` (bool): Include confidence scores

**Returns:**
- `List[Dict]`: List of normalization results

**Example:**
```python
results = normalizer.batch_normalize(["medina", "circus", "unknown"])
# Returns: [
#     {'input': 'medina', 'city': 'MADINA', 'region': 'GREATER_ACCRA'},
#     {'input': 'circus', 'city': 'CIRCLE', 'region': 'GREATER_ACCRA'},
#     {'input': 'unknown', 'city': None, 'region': None}
# ]
```

---

### Convenience Functions

Quick access functions without instantiating the class:

```python
from city_normalizer import normalize, get_variations, find_closest

# Quick normalize
city = normalize("medina")  # Returns: "MADINA"

# Quick get variations
variations = get_variations("MADINA")  # Returns: ['medina', ...]

# Quick fuzzy match
matches = find_closest("winnepeg")  # Returns: [('WINNEBA', 0.95), ...]
```

---

## 💡 Examples

### Example 1: Basic Location Normalization

```python
from city_normalizer import normalize

# User says: "Find doctors in Madina"
# STT outputs: "medina"
stt_input = "medina"
correct_city = normalize(stt_input)

print(f"User said: {stt_input}")
print(f"Correct city: {correct_city}")
# Output:
# User said: medina
# Correct city: MADINA
```

### Example 2: With Confidence Scoring

```python
from city_normalizer import CityNormalizer

normalizer = CityNormalizer()

# User says something unclear
stt_input = "winnepeg"  # Close but not exact

city, confidence, method = normalizer.normalize_with_confidence(stt_input)

if confidence >= 0.9:
    print(f"High confidence: {city}")
elif confidence >= 0.7:
    print(f"Medium confidence: {city} - asking for confirmation")
else:
    print(f"Low confidence: {city} - suggesting alternatives")
```

### Example 3: Batch Processing

```python
from city_normalizer import CityNormalizer

normalizer = CityNormalizer()

# Process multiple queries from analytics logs
queries = [
    "medina",
    "circus",
    "jaw wulu",
    "coffee ridua",
    "unknown123"
]

results = normalizer.batch_normalize(queries, include_confidence=True)

# Analyze success rate
successful = sum(1 for r in results if r['city'] is not None)
success_rate = (successful / len(results)) * 100

print(f"Success rate: {success_rate:.1f}%")
print(f"Successful: {successful}/{len(results)}")
```

### Example 4: Fuzzy Matching Fallback

```python
from city_normalizer import CityNormalizer

normalizer = CityNormalizer()

def smart_normalize(user_input: str) -> str:
    """
    Normalize with fuzzy matching fallback.
    """
    # Try exact match first
    city = normalizer.normalize_city(user_input)

    if city:
        return f"Found: {city}"

    # Try fuzzy matching
    matches = normalizer.find_closest_match(user_input, threshold=0.7, limit=3)

    if not matches:
        return "No matches found"

    if len(matches) == 1:
        return f"Did you mean {matches[0][0]}?"

    # Multiple matches - ask user to clarify
    options = [m[0] for m in matches]
    return f"Did you mean one of these? {', '.join(options)}"

# Test
print(smart_normalize("madenna"))  # Typo
# Output: Did you mean MADINA?
```

### Example 5: Regional Search

```python
from city_normalizer import CityNormalizer

normalizer = CityNormalizer()

# User says: "Show me all providers in Greater Accra"
region = "GREATER_ACCRA"
cities = normalizer.get_cities_by_region(region)

print(f"Cities in {region}: {len(cities)}")
print(f"Sample cities: {', '.join(cities[:5])}")

# Query providers for each city
for city in cities:
    # Your provider search logic here
    pass
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
/opt/kasaai/apps/venv/bin/python -m pytest tests/test_city_normalizer.py -v

# Run specific test class
/opt/kasaai/apps/venv/bin/python -m pytest tests/test_city_normalizer.py::TestCityNormalizer -v

# Run with coverage
/opt/kasaai/apps/venv/bin/python -m pytest tests/test_city_normalizer.py --cov=city_normalizer --cov-report=html
```

### Test Coverage

The test suite includes:

- **Expected use cases** (13 tests): Basic functionality
- **Edge cases** (15 tests): Unusual but valid inputs
- **Failure cases** (9 tests): Invalid inputs and error conditions
- **Integration tests** (4 tests): Real-world scenarios
- **Convenience functions** (4 tests): Quick access functions
- **Data integrity** (4 tests): Mapping consistency

**Total**: 49 tests with 100% pass rate

---

## 📝 CSV Maintenance

### Editing the CSV File

The `ghana_cities_stt_mapping.csv` file is designed for easy editing by non-technical team members.

**Location**: `/opt/kasaai/apps/automations/premier-health/data/ghana_cities_stt_mapping.csv`

**Columns**:
- `Correct_City`: The official city name (e.g., MADINA)
- `STT_Variation`: The STT mishearing (e.g., medina)
- `Variation_Type`: Type of variation (phonetic, english_word, spelling, etc.)
- `Confidence_Score`: How common the variation is (0.5 to 0.9)
- `Region`: Geographic region

### Adding New Variations

1. Open the CSV file in Excel or Google Sheets
2. Add a new row with:
   - `Correct_City`: The correct city name (UPPERCASE)
   - `STT_Variation`: The new mishearing (lowercase)
   - `Variation_Type`: Choose from: phonetic, english_word, spelling, space_variation, abbreviated, compound
   - `Confidence_Score`: 0.9 (common), 0.7 (medium), 0.5 (rare)
   - `Region`: The region name

3. Save the CSV file

4. Re-generate the Python mapping:
```bash
cd /opt/kasaai/apps/automations/premier-health
/opt/kasaai/apps/venv/bin/python regenerate_mapping_from_csv.py
```

### Adding New Cities

1. Add all variations for the city in the CSV file
2. Add the city to the appropriate regional grouping in `ghana_cities_stt_mapping.py`
3. Run tests to verify:
```bash
/opt/kasaai/apps/venv/bin/python -m pytest tests/test_city_normalizer.py -v
```

---

## ✅ Best Practices

### 1. Always Normalize User Input

```python
# ❌ Bad - using raw STT input
query = f"Providers in {user_input}"

# ✅ Good - normalize first
city = normalize(user_input)
if city:
    query = f"Providers in {city}"
```

### 2. Use Confidence Scoring

```python
# ✅ Good - check confidence before acting
city, confidence, method = normalizer.normalize_with_confidence(user_input)

if confidence >= 0.9:
    # High confidence - proceed
    search_providers(city)
elif confidence >= 0.7:
    # Medium - ask for confirmation
    return f"Did you mean {city}?"
else:
    # Low - suggest alternatives
    matches = normalizer.find_closest_match(user_input)
    return f"Did you mean one of these? {', '.join([m[0] for m in matches])}"
```

### 3. Provide Fallbacks

```python
# ✅ Good - always have a fallback
city = normalize(user_input)

if not city:
    # Try fuzzy matching
    matches = normalizer.find_closest_match(user_input, threshold=0.7)

    if matches:
        city = matches[0][0]
    else:
        # Ask user to rephrase
        return "I couldn't find that location. Could you please spell it?"
```

### 4. Log Unknown Variations

```python
# ✅ Good - log for future improvements
city = normalize(user_input)

if not city:
    logger.warning(f"Unknown STT variation: {user_input}")
    # Add to analytics for review
    analytics.track_unknown_location(user_input)
```

### 5. Cache Results

```python
# ✅ Good - cache normalized results
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_normalize(input_text: str) -> Optional[str]:
    return normalize(input_text)
```

---

## 🔍 Troubleshooting

### Issue: Normalization returns None

**Possible causes:**
1. The variation is not in the mapping
2. Input contains extra characters (spaces, punctuation)
3. Input is empty or None

**Solutions:**
```python
# Clean input first
clean_input = user_input.strip().lower()
city = normalize(clean_input)

# Try fuzzy matching
if not city:
    matches = normalizer.find_closest_match(clean_input, threshold=0.6)
    if matches:
        city = matches[0][0]
```

### Issue: Wrong city returned

**Possible cause:** Multiple cities have similar variations

**Solution:** Use confidence scoring and ask for clarification:
```python
city, confidence, method = normalizer.normalize_with_confidence(user_input)

if confidence < 0.9:
    # Ask user to confirm
    return f"Did you mean {city} in {normalizer.get_region_for_city(city)}?"
```

### Issue: Performance is slow

**Possible cause:** Fuzzy matching on large datasets

**Solution:**
1. Use exact matching first (fast)
2. Only fall back to fuzzy matching if exact fails
3. Cache results
4. Limit fuzzy matching results

```python
# Fast path - exact match
city = normalize(user_input)

if not city:
    # Slow path - fuzzy match with limit
    matches = normalizer.find_closest_match(user_input, threshold=0.8, limit=3)
```

### Issue: Tests failing after CSV update

**Possible causes:**
1. Duplicate variations in the CSV
2. Inconsistent casing
3. Missing regional assignments

**Solution:** Run data integrity tests:
```bash
/opt/kasaai/apps/venv/bin/python -m pytest tests/test_city_normalizer.py::TestDataIntegrity -v
```

---

## 📞 Support

For issues or questions:

- **Email**: ailabsafrica@gmail.com
- **Documentation**: This file
- **Test Suite**: `tests/test_city_normalizer.py`
- **Module**: `city_normalizer.py`

---

## 📊 Statistics

- **Total Cities**: 188 (including compound names like "NORTH LEGON")
- **Base Regions**: 106 (unique geographic areas)
- **Total Variations**: ~890 STT variations
- **Average Variations per City**: ~4.7
- **Regions Covered**: 8 (Greater Accra, Central, Ashanti, Brong-Ahafo, Eastern, Western, Volta, Northern)
- **Test Coverage**: 49 tests (100% pass rate)
- **Data Quality**: 100% (all variations map to valid cities)

---

## 🎯 Future Enhancements

1. **Machine Learning Integration**: Train ML model on actual STT logs
2. **Real-time Learning**: Automatically add new variations from user feedback
3. **Multi-language Support**: Add Twi, Ga, and other local language variations
4. **Voice Similarity Scoring**: Use phonetic similarity algorithms
5. **API Endpoint**: REST API for external integrations
6. **Analytics Dashboard**: Track normalization success rates
7. **Mobile App Integration**: Offline normalization for mobile apps

---

**Last Updated**: October 16, 2025
**Version**: 1.0.0
**Status**: ✅ PRODUCTION READY
