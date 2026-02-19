#!/usr/bin/env python3
"""
Demo script for Ghanaian Location Services

Shows how to use the location services for different scenarios.
Run with: python -m backend.services.ghanaian_location.demo
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add paths for imports
current_dir = Path(__file__).parent
backend_dir = current_dir.parent.parent

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(current_dir))

# Mock database for demo
class MockDatabase:
    """Mock database for demonstration purposes"""
    pass

class MockRepository:
    """Mock repository for demonstration purposes"""
    def __init__(self, db):
        self.db = db

    async def setup_indexes(self):
        return None

    async def get_all_active_locations(self):
        # Return sample locations
        from database.models import GhanaianLocation
        return [
            GhanaianLocation(
                canonical_name="DZORWULU",
                display_name="Dzorwulu",
                aliases=["ZORWULU"],
                phonetic_codes={"soundex": "D264", "metaphone": "TSRL"},
                pronunciation={"difficulty_score": 0.9}
            ),
            GhanaianLocation(
                canonical_name="MADINA",
                display_name="Madina",
                aliases=["MADINA TOWN"],
                phonetic_codes={"soundex": "M350", "metaphone": "MTN"},
                pronunciation={"difficulty_score": 0.4}
            ),
            GhanaianLocation(
                canonical_name="KANESHIE",
                display_name="Kaneshie",
                aliases=["KANESHIE MARKET"],
                phonetic_codes={"soundex": "K522", "metaphone": "KNX"},
                pronunciation={"difficulty_score": 0.5}
            )
        ]

    async def get_stt_correction(self, misheard_input):
        # Return sample corrections
        corrections = {
            "zorwulu": {"correct_location": "DZORWULU", "confidence": 0.8},
            "madena": {"correct_location": "MADINA", "confidence": 0.9},
            "kanashi": {"correct_location": "KANESHIE", "confidence": 0.85}
        }
        if misheard_input in corrections:
            from database.models import STTCorrection
            data = corrections[misheard_input]
            return STTCorrection(
                misheard_input=misheard_input,
                correct_location=data["correct_location"],
                confidence=data["confidence"],
                phonetic_similarity=0.7,
                frequency=1,
                verified=True,
                source="demo_data"
            )
        return None

    async def get_location_by_name(self, name):
        return None

    async def find_locations_by_alias(self, alias):
        return []

    async def get_pronunciation_guide(self, location_name, language=None):
        return None

    async def update_usage_analytics(self, **kwargs):
        return None

    async def update_correction_usage(self, misheard_input, success=True):
        return None


async def demo_phonetic_matching():
    """Demonstrate phonetic matching capabilities"""
    print("\n" + "="*60)
    print("🔍 PHONETIC MATCHING DEMO")
    print("="*60)

    try:
        from phonetic_matcher import PhoneticMatcher

        mock_db = MockDatabase()
        mock_repo = MockRepository(mock_db)

        matcher = PhoneticMatcher(mock_repo)
        await matcher.initialize()

        # Test queries with common mishearings
        test_queries = [
            "zorwulu",      # Should match DZORWULU
            "madena",       # Should match MADINA
            "kanashi",      # Should match KANESHIE
            "unknown place" # Should find no matches
        ]

        for query in test_queries:
            print(f"\n🎯 Testing query: '{query}'")
            matches = await matcher.find_matches(query, max_matches=3)

            if matches:
                for i, match in enumerate(matches, 1):
                    print(f"   {i}. {match.location.canonical_name}")
                    print(f"      Confidence: {match.confidence:.2f}")
                    print(f"      Algorithm: {match.algorithm}")
                    print(f"      Match type: {match.match_type}")
            else:
                print("   ❌ No matches found")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_pronunciation_optimization():
    """Demonstrate pronunciation optimization"""
    print("\n" + "="*60)
    print("🗣️ PRONUNCIATION OPTIMIZATION DEMO")
    print("="*60)

    try:
        from pronunciation_service import PronunciationService

        mock_db = MockDatabase()
        mock_repo = MockRepository(mock_db)

        service = PronunciationService(mock_repo)

        # Test difficult location names
        test_locations = [
            "DZORWULU",
            "KOKOMLEMLE",
            "KWABENYA",
            "MADINA",
            "ACCRA"
        ]

        for location in test_locations:
            print(f"\n🎯 Optimizing: '{location}'")

            result = await service.optimize_for_tts(location, context='healthcare')

            print(f"   📝 Original: {result.original_text}")
            print(f"   ✨ Optimized: {result.optimized_text}")
            print(f"   📊 Difficulty: {result.difficulty_score:.2f}/1.0")
            print(f"   🎵 Speech Rate: {result.speech_rate:.2f}x")

            if result.phonetic_spelling:
                print(f"   🔤 Phonetic: {result.phonetic_spelling}")

            if result.alternatives:
                print(f"   🔄 Alternatives: {', '.join(result.alternatives[:2])}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_premier_health_integration():
    """Demonstrate Premier Health adapter"""
    print("\n" + "="*60)
    print("🏥 PREMIER HEALTH INTEGRATION DEMO")
    print("="*60)

    try:
        from core_service import GhanaianLocationService
        from adapters.premier_health_adapter import PremierHealthAdapter

        mock_db = MockDatabase()
        mock_repo = MockRepository(mock_db)

        # Create service and adapter
        core_service = GhanaianLocationService(mock_repo)
        await core_service.initialize()

        adapter = PremierHealthAdapter(core_service)

        # Test healthcare queries
        test_queries = [
            "find doctors in dzorwulu hospital",
            "medical facilities in madena",
            "urgent care near kanashie market",
            "specialists in accra central hospital"
        ]

        for query in test_queries:
            print(f"\n🎯 Healthcare Query: '{query}'")

            # Preprocess for healthcare context
            processed = await adapter.preprocess_query(query)
            print(f"   📝 Preprocessed: '{processed}'")

            # Process with healthcare context
            healthcare_context = {
                'provider_type': 'doctor',
                'specialty': 'general',
                'urgency': 'routine'
            }

            try:
                result = await adapter.process_location(processed, healthcare_context)

                if result.success:
                    print(f"   ✅ Match: {result.corrected_location}")
                    print(f"   📊 Confidence: {result.confidence:.2f}")
                    if result.geographic_context:
                        print(f"   🗺️ Context: {result.geographic_context}")
                else:
                    print(f"   ❌ No match: {result.error_message}")

            except Exception as e:
                print(f"   ⚠️ Processing error: {e}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_voice_integration():
    """Demonstrate VAPI voice adapter"""
    print("\n" + "="*60)
    print("🎙️ VOICE (VAPI) INTEGRATION DEMO")
    print("="*60)

    try:
        from core_service import GhanaianLocationService
        from adapters.vapi_adapter import VapiAdapter

        mock_db = MockDatabase()
        mock_repo = MockRepository(mock_db)

        # Create service and adapter
        core_service = GhanaianLocationService(mock_repo)
        await core_service.initialize()

        adapter = VapiAdapter(core_service)

        # Test voice queries (with typical STT errors)
        test_queries = [
            "um, I think it's zorwulu",
            "somewhere called madena",
            "that place they call kanashi",
            "uh, near the dzorulu area"
        ]

        for query in test_queries:
            print(f"\n🎯 Voice Query: '{query}'")

            # Preprocess for voice
            processed = await adapter.preprocess_query(query)
            print(f"   🎤 Processed: '{processed}'")

            try:
                result = await adapter.process_location(processed)

                # Create voice-friendly response
                if result.success:
                    confirmation = await adapter.create_voice_confirmation_prompt(result)
                    print(f"   🗣️ Voice Response: \"{confirmation}\"")
                else:
                    print(f"   ❌ No match found for voice query")

            except Exception as e:
                print(f"   ⚠️ Voice processing error: {e}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


async def demo_integration_helpers():
    """Demonstrate integration helper functions"""
    print("\n" + "="*60)
    print("🔧 INTEGRATION HELPERS DEMO")
    print("="*60)

    try:
        from integration_helpers import get_location_pronunciation_guide

        # Test pronunciation guides
        difficult_locations = ["DZORWULU", "KOKOMLEMLE", "ACCRA", "KWABENYA"]

        for location in difficult_locations:
            print(f"\n🎯 Pronunciation Guide: '{location}'")

            guide = get_location_pronunciation_guide(location)

            print(f"   📚 Has Guide: {guide['has_guide']}")
            print(f"   🔤 Phonetic: {guide['phonetic']}")
            print(f"   📊 Difficulty: {guide['difficulty']}")

            if guide.get('tips'):
                print(f"   💡 Tips: {guide['tips']}")

            if guide.get('alternatives'):
                print(f"   🔄 Alternatives: {', '.join(guide['alternatives'][:2])}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main demo function"""
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise for demo
        format='%(levelname)s: %(message)s'
    )

    print("🇬🇭 GHANAIAN LOCATION SERVICES DEMO")
    print("Comprehensive STT/TTS enhancement for Ghanaian place names")
    print("=" * 60)

    try:
        # Run all demos
        await demo_phonetic_matching()
        await demo_pronunciation_optimization()
        await demo_premier_health_integration()
        await demo_voice_integration()
        await demo_integration_helpers()

        print("\n" + "="*60)
        print("✅ DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print("🎯 Key Features Demonstrated:")
        print("   • Multi-algorithm phonetic matching")
        print("   • TTS pronunciation optimization with SSML")
        print("   • Healthcare-specific query processing")
        print("   • Voice-optimized response generation")
        print("   • Integration helpers for easy adoption")
        print("\n💡 Ready for integration with premier_health.py and VAPI!")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())