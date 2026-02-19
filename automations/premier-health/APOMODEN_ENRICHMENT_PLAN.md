1. GPS coordinates - For distance-based search and navigation
  2. Operating hours - Currently mostly empty, critical for voice
  queries about "open now"
  3. Email addresses and websites - Currently sparse, important for
  digital-first users
  4. Service details - More granular than just specialty names (e.g.,
  "accepts walk-ins", "emergency services")
  5. Insurance plan specifics - Currently just shows "Premier Health
  Insurance" for all
  6. Real-time availability - Appointment booking status, current wait
  times
  7. Reviews/ratings - User feedback and quality indicators
  8. Photos - Visual identification of facilities
  9. Accessibility information - Wheelchair access, parking
  availability
  10. Language support - Which languages staff speak beyond English

  The current dataset is functional but basic - enrichment would
  significantly improve user experience and make the voice agent more
  practical for real-world healthcare decisions.


  STT training for cities in ghana
  locations in accra, phoenetic mapping and fuzzy search



   STT/TTS Enhancement Plan for Ghanaian Location Names                │
     │                                                                     │
     │ 🎯 Problem Analysis                                                 │
     │                                                                     │
     │ The system struggles with Ghanaian location names due to:           │
     │ 1. STT Misrecognition: "Kumasi" → "Comasie", "Madina" → "Medina",   │
     │ "Circle" → "Circus"                                                 │
     │ 2. TTS Mispronunciation: Incorrect phonetic rendering of local      │
     │ names                                                               │
     │ 3. Limited Context: Voice models lack Ghanaian linguistic context   │
     │ 4. Accent Variations: Different pronunciations by Ghanaian vs       │
     │ international speakers                                              │
     │                                                                     │
     │ 📋 Implementation Plan                                              │
     │                                                                     │
     │ Phase 1: STT Enhancement (Speech-to-Text)                           │
     │                                                                     │
     │ Files to modify: unified_whisper_service.py, new                    │
     │ ghanaian_location_processor.py                                      │
     │                                                                     │
     │ 1. Create Ghanaian Location Phonetic Dictionary                     │
     │   - Build comprehensive phonetic mappings for 200+ Ghanaian         │
     │ locations                                                           │
     │   - Include common STT misinterpretations (already started in       │
     │ area_mapping.py)                                                    │
     │   - Add fuzzy matching with phonetic similarity scoring             │
     │ 2. Post-Processing Pipeline                                         │
     │   - Implement STT post-processor that corrects common location      │
     │ mishearings                                                         │
     │   - Use Levenshtein distance + phonetic matching for location names │
     │   - Apply confidence scoring to avoid false corrections             │
     │ 3. Custom Vocabulary Injection                                      │
     │   - Extend Whisper with Ghanaian location vocabulary                │
     │   - Use custom word boosting for location-specific terms            │
     │   - Implement location context awareness                            │
     │                                                                     │
     │ Phase 2: TTS Enhancement (Text-to-Speech)                           │
     │                                                                     │
     │ Files to modify: twi_tts_service.py, new                            │
     │ ghanaian_pronunciation_service.py                                   │
     │                                                                     │
     │ 1. Pronunciation Dictionary                                         │
     │   - Create SSML-based pronunciation guide for 200+ locations        │
     │   - Include IPA (International Phonetic Alphabet) notations         │
     │   - Support multiple accent variations (Twi, Ga, Ewe influences)    │
     │ 2. Multi-Provider TTS Strategy                                      │
     │   - Use Khaya AI for Ghanaian-trained pronunciation                 │
     │   - Fallback to ElevenLabs with custom pronunciation guides         │
     │   - Implement pronunciation quality scoring                         │
     │ 3. Voice Context Switching                                          │
     │   - Detect when speaking location names vs regular content          │
     │   - Apply different voice models/settings for location              │
     │ pronunciation                                                       │
     │   - Use slower speech rate for unfamiliar location names            │
     │                                                                     │
     │ Phase 3: Location Intelligence Layer                                │
     │                                                                     │
     │ Files to create: location_intelligence_service.py, enhance          │
     │ area_mapping.py                                                     │
     │                                                                     │
     │ 1. Smart Location Disambiguation                                    │
     │   - Implement location confidence scoring                           │
     │   - Use geographic context (nearby areas) for validation            │
     │   - Apply business logic for healthcare provider coverage areas     │
     │ 2. Multi-Language Support                                           │
     │   - Support location names in Twi, Ga, Ewe, and English             │
     │   - Implement cross-language phonetic matching                      │
     │   - Use local language pronunciation when available                 │
     │ 3. User Feedback Loop                                               │
     │   - Log STT/TTS accuracy for location names                         │
     │   - Implement correction mechanism from user interactions           │
     │   - Build dynamic improvement based on usage patterns               │
     │                                                                     │
     │ Phase 4: Integration Enhancements                                   │
     │                                                                     │
     │ Files to modify: premier_health.py, call_management.py              │
     │                                                                     │
     │ 1. VAPI Integration                                                 │
     │   - Add location name pronunciation hints to VAPI responses         │
     │   - Implement slower speech for difficult location names            │
     │   - Use phonetic spelling in voice responses when needed            │
     │ 2. Healthcare Context                                               │
     │   - Prioritize healthcare-relevant locations                        │
     │   - Add medical facility proximity awareness                        │
     │   - Implement location-based service availability checks            │
     │                                                                     │
     │ 🔧 Technical Implementation                                         │
     │                                                                     │
     │ New Services to Create:                                             │
     │                                                                     │
     │ 1. GhanaianLocationProcessor - STT post-processing                  │
     │ 2. GhanaianPronunciationService - TTS pre-processing                │
     │ 3. LocationIntelligenceService - Smart location handling            │
     │ 4. PhoneticMatcher - Advanced fuzzy matching for locations          │
     │                                                                     │
     │ Database Additions:                                                 │
     │                                                                     │
     │ 1. location_phonetics table - Phonetic mappings                     │
     │ 2. location_pronunciations table - TTS pronunciation guides         │
     │ 3. location_feedback table - User correction tracking               │
     │ 4. location_contexts table - Geographic and cultural context        │
     │                                                                     │
     │ Configuration Updates:                                              │
     │                                                                     │
     │ 1. Enable custom vocabulary in Whisper models                       │
     │ 2. Add Ghanaian location-specific TTS settings                      │
     │ 3. Configure pronunciation quality thresholds                       │
     │ 4. Set up location name confidence scoring                          │
     │                                                                     │
     │ 📊 Expected Improvements:                                           │
     │                                                                     │
     │ - 90%+ accuracy for common Ghanaian locations in STT                │
     │ - Natural pronunciation for location names in TTS                   │
     │ - Intelligent fallbacks when pronunciation is uncertain             │
     │ - Context-aware corrections based on healthcare provider coverage   │
     │ - Multi-accent support for diverse Ghanaian speakers                │
     │                                                                     │
     │ 🚀 Implementation Order:                                            │
     │                                                                     │
     │ 1. Create phonetic dictionary (immediate impact)                    │
     │ 2. Implement STT post-processing (high impact)                      │
     │ 3. Add TTS pronunciation guides (user experience)                   │
     │ 4. Build intelligence layer (long-term accuracy)                    │
     │ 5. Integration testing with real VAPI calls       