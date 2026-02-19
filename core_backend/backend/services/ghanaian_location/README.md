# Ghanaian Location Services Module

Comprehensive STT correction, phonetic matching, and TTS optimization for Ghanaian location names in healthcare and voice applications.

## 🎯 Features

- **Multi-Algorithm Phonetic Matching**: Soundex, NYSIIS, Double Metaphone, and custom Ghanaian patterns
- **TTS Pronunciation Optimization**: SSML generation with difficulty-based speech rate adjustment
- **Database-Backed Learning**: MongoDB storage with user feedback learning
- **Tool-Specific Adapters**: Customized behavior for Premier Health, VAPI, and general use
- **Comprehensive STT Corrections**: Learns from mishearings and user corrections

## 📁 Module Structure

```
ghanaian_location/
├── __init__.py                 # Main module exports and factory functions
├── core_service.py             # Main orchestration service
├── phonetic_matcher.py         # Multi-algorithm phonetic matching
├── pronunciation_service.py    # TTS optimization with SSML
├── integration_helpers.py      # Easy integration functions
├── database/
│   ├── models.py              # Pydantic models for all data
│   └── repositories.py       # MongoDB data access layer
├── adapters/
│   ├── base_adapter.py        # Abstract adapter interface
│   ├── premier_health_adapter.py  # Healthcare-specific behavior
│   ├── vapi_adapter.py        # Voice-optimized behavior
│   └── general_adapter.py     # Standard behavior
└── scripts/
    ├── migrate_location_data.py   # CSV data migration
    └── setup_database.py         # Database initialization
```

## 🚀 Quick Start

### 1. Install Dependencies

The required dependencies should already be in requirements.txt:

```python
# Already included:
phonetics>=1.0.5              # For phonetic matching algorithms
unidecode>=1.3.6               # For accent/unicode normalization
rapidfuzz                      # For fuzzy string matching (replaces python-Levenshtein)
```

### 2. Setup Database

```python
from backend.services.ghanaian_location.scripts.setup_database import setup_database
await setup_database()
```

### 3. Basic Usage

```python
from backend.services.ghanaian_location import create_location_service, quick_location_lookup
from backend.database import get_database

# Quick lookup
db = await get_database()
result = await quick_location_lookup(db, "zorwulu", context='premier_health')
print(f"Match: {result.corrected_location} (confidence: {result.confidence:.2f})")

# Full service with adapter
service, adapter = create_location_service(db, 'premier_health')
await service.initialize()

healthcare_result = await adapter.process_location(
    "find doctors in dzorwulu",
    {'provider_type': 'doctor', 'urgency': 'routine'}
)
```

### 4. Premier Health Integration

```python
from backend.services.ghanaian_location.integration_helpers import PremierHealthLocationHelper

helper = PremierHealthLocationHelper(db)
await helper.initialize()

# Process healthcare location query
result = await helper.process_healthcare_location(
    location_query="dzorwulu hospital",
    provider_type="specialist",
    specialty="cardiology",
    urgency="routine"
)

# Format complete response
providers = []  # Your provider search results
response = await helper.format_provider_response(result, providers, {
    'specialty': 'cardiology',
    'availability': 'Available today'
})
```

### 5. VAPI Voice Integration

```python
from backend.services.ghanaian_location import create_location_service

# Create VAPI-optimized service
service, vapi_adapter = create_location_service(db, 'vapi')
await service.initialize()

# Process voice query (with typical STT errors)
voice_result = await vapi_adapter.process_location("um, I think it's zorwulu")

# Get voice-friendly confirmation
confirmation = await vapi_adapter.create_voice_confirmation_prompt(voice_result)
print(f"Voice response: {confirmation}")

# Optimize response text for TTS
response_text = "I found 3 healthcare providers in Dzorwulu area"
optimized = await vapi_adapter.optimize_response_text(response_text)
```

## 🎯 Key Components

### Core Service (GhanaianLocationService)

Main orchestration service that coordinates all components:

- `process_location_query()`: Complete location matching with pronunciation
- `optimize_response_for_tts()`: TTS optimization for response text
- `learn_from_user_correction()`: Learn from user feedback
- `get_service_statistics()`: Performance and usage stats

### Phonetic Matcher (PhoneticMatcher)

Multi-algorithm matching with caching:

- **Algorithms**: Soundex, NYSIIS, Double Metaphone, custom Ghanaian patterns
- **Fuzzy Matching**: RapidFuzz for character-based similarity
- **STT Corrections**: Database-backed common mishearing corrections
- **Learning**: Updates from user corrections

### Pronunciation Service (PronunciationService)

TTS optimization with SSML generation:

- **Difficulty Scoring**: 0.0 (easy) to 1.0 (very difficult)
- **SSML Generation**: Phoneme markup, speech rate, pauses
- **Alternative Descriptions**: "the Dzorwulu area" for very difficult names
- **Speech Rate**: Slower for difficult names (0.7x-1.0x)

### Adapters

Tool-specific behavior customization:

- **PremierHealthAdapter**: Healthcare query preprocessing, medical terminology
- **VapiAdapter**: Voice-optimized responses, conversational formatting
- **GeneralAdapter**: Standard behavior for API endpoints

## 📊 Database Schema

### GhanaianLocation
- `canonical_name`: Standard uppercase name (e.g., "DZORWULU")
- `display_name`: User-friendly name (e.g., "Dzorwulu")
- `aliases`: Alternative names and spellings
- `phonetic_codes`: Pre-computed phonetic algorithm results
- `pronunciation`: Difficulty scores and TTS metadata
- `geographic`: Region and area classification
- `context`: Tool-specific metadata (healthcare provider counts, etc.)

### STTCorrection
- `misheard_input`: What STT incorrectly outputs
- `correct_location`: What it should be corrected to
- `confidence`: Correction reliability score
- `frequency`: Usage tracking for learning
- `source`: How the correction was learned

### PronunciationGuide
- `location_name`: Location to pronounce
- `phonetic_spelling`: Human-readable (e.g., "ZOR-wu-lu")
- `ipa_notation`: International Phonetic Alphabet
- `ssml_markup`: TTS engine markup
- `difficulty_score`: 0.0-1.0 pronunciation difficulty
- `recommended_speech_rate`: Speed multiplier

## 🔧 Configuration

### Phonetic Matching Thresholds
```python
confidence_threshold = 0.6      # Minimum confidence for matches
fuzzy_threshold = 70           # RapidFuzz threshold (0-100)
```

### TTS Speech Rates by Difficulty
```python
speech_rates = {
    0.9: 0.7,   # Very difficult -> 70% speed
    0.8: 0.8,   # Difficult -> 80% speed
    0.7: 0.85,  # Moderately difficult -> 85% speed
    0.6: 0.9,   # Somewhat difficult -> 90% speed
    0.5: 0.95,  # Slightly difficult -> 95% speed
}
```

## 🧪 Testing

Comprehensive test suite available:

```bash
# Run tests
pytest tests/test_ghanaian_location_services.py -v

# Test specific component
pytest tests/test_ghanaian_location_services.py::TestPhoneticMatcher -v
```

## 📈 Performance

### Caching Strategy
- **Location Data**: Cached in memory after first load
- **Phonetic Codes**: Pre-computed and cached
- **Database Queries**: Indexed for optimal performance

### Analytics Tracking
- Query success/failure rates
- Average processing time
- User correction frequency
- Location popularity metrics

## 🔄 Migration from Existing Systems

### From area_mapping.py
1. Extract location data: `python scripts/migrate_location_data.py`
2. Verify migration: Check database statistics
3. Update integration points to use new API

### Integration Points
Replace existing location processing with:
```python
# Old approach
from area_mapping import AreaMapper
mapper = AreaMapper()
result = mapper.correct_area_name(user_input)

# New approach
from backend.services.ghanaian_location import quick_location_lookup
result = await quick_location_lookup(db, user_input, 'premier_health')
corrected_name = result.corrected_location if result.success else user_input
```

## 🚨 Error Handling

The service provides robust error handling with fallback behavior:

```python
result = await service.process_location_query("invalid input")
if not result.success:
    print(f"Error: {result.error_message}")
    # Fallback to original input or show alternatives
```

## 🎯 Roadmap

### Phase 1 ✅ (Completed)
- [x] Core phonetic matching engine
- [x] Database schema and repositories
- [x] TTS pronunciation optimization
- [x] Tool-specific adapters
- [x] Integration helpers
- [x] Comprehensive test suite

### Phase 2 (Future)
- [ ] Real-time analytics dashboard
- [ ] Advanced ML-based corrections
- [ ] Multi-language support (Twi, Ga, Ewe)
- [ ] Audio pronunciation samples
- [ ] Integration with external mapping APIs

## 📞 Support

For integration support or questions:
- Check the integration helpers in `integration_helpers.py`
- Run the test suite to verify functionality
- Review adapter implementations for customization examples

---

**Ready for production use with Premier Health and VAPI integration!** 🚀