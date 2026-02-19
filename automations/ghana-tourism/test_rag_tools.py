#!/usr/bin/env python3
"""
Test script for RAG-enhanced Ghana Tourism tools.
Demonstrates Gemini-powered semantic search capabilities.
"""

import sys
import os
import asyncio

# Add paths
sys.path.insert(0, '/opt/kasaai')
sys.path.insert(0, '/opt/kasaai/apps/core_backend')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from voice_agent_tools_rag import GhanaTourismToolsRAG

def print_result(title: str, result: dict):
    """Pretty print test results."""
    print("\n" + "=" * 80)
    print(f"TEST: {title}")
    print("=" * 80)
    print(f"Success: {result.get('success', False)}")
    print(f"AI Enhanced: {result.get('ai_enhanced', False)}")
    if result.get('confidence_score'):
        print(f"Confidence Score: {result['confidence_score']:.2f}")
    print("\nVoice Response:")
    print("-" * 80)
    print(result.get('voice_response', 'No response'))
    print("-" * 80)

    if result.get('destinations'):
        print(f"\nFound {len(result['destinations'])} destinations")
    if result.get('accommodations'):
        print(f"\nFound {len(result['accommodations'])} accommodations")
    if result.get('sources'):
        print(f"\nSources: {', '.join(result['sources'])}")


def main():
    """Run test queries."""
    print("=" * 80)
    print("🇬🇭 Ghana Tourism RAG Tools - Test Suite")
    print("Powered by Google Gemini")
    print("=" * 80)

    # Initialize tools
    tools = GhanaTourismToolsRAG()

    # Test 1: Destination search with natural language
    print("\n\n🔍 Test 1: Natural language destination search")
    result1 = tools.search_destinations(
        query="I want to see wildlife and go on safari",
        max_results=3
    )
    print_result("Wildlife Safari Search", result1)

    # Test 2: Beach destination search
    print("\n\n🏖️ Test 2: Beach destination search")
    result2 = tools.search_destinations(
        query="beautiful beaches for swimming and relaxation",
        category="beach",
        max_results=3
    )
    print_result("Beach Search", result2)

    # Test 3: Accommodation search with budget
    print("\n\n🏨 Test 3: Budget-friendly accommodation")
    result3 = tools.search_accommodation(
        location="Accra",
        accommodation_type="hotel",
        budget_max_ghs=800,
        max_results=3
    )
    print_result("Budget Hotel Search", result3)

    # Test 4: Destination details
    print("\n\n📍 Test 4: Destination details")
    result4 = tools.get_destination_details("Kakum National Park")
    print_result("Kakum Details", result4)

    # Test 5: Visa information
    print("\n\n🛂 Test 5: Visa requirements")
    result5 = tools.get_visa_requirements(nationality="United States")
    print_result("US Visa Requirements", result5)

    # Test 6: General tourism guidance (NEW RAG-only feature)
    print("\n\n💬 Test 6: General tourism question")
    result6 = tools.get_general_tourism_guidance(
        "What should I pack for a trip to Ghana during the rainy season?"
    )
    print_result("General Tourism Guidance", result6)

    # Test 7: Another general question
    print("\n\n💬 Test 7: Cultural question")
    result7 = tools.get_general_tourism_guidance(
        "What are some important cultural customs I should know when visiting Ghana?"
    )
    print_result("Cultural Customs", result7)

    # Summary
    print("\n\n" + "=" * 80)
    print("✅ TEST SUITE COMPLETE")
    print("=" * 80)
    print("\nRAG Enhancement Status:")
    results = [result1, result2, result3, result4, result5, result6, result7]
    enhanced_count = sum(1 for r in results if r.get('ai_enhanced'))
    print(f"  AI-Enhanced: {enhanced_count}/{len(results)}")
    print(f"  Traditional: {len(results) - enhanced_count}/{len(results)}")
    print("\nThe RAG-enhanced tools provide more natural, context-aware responses")
    print("powered by Google Gemini's semantic understanding.")


if __name__ == "__main__":
    main()
