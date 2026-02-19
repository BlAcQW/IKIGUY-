#!/usr/bin/env python3
"""
Test Premier Health RAG integration end-to-end.
Tests various query types to ensure RAG system is working properly.
"""

import sys
import os
import asyncio

# Add paths for imports
sys.path.append('/opt/kasaai/apps/core_backend')

from backend.services.helpdesk_rag_service import helpdesk_rag_service

# Test queries covering different aspects
TEST_QUERIES = [
    {
        "name": "Policy Coverage Question",
        "query": "What does Premier Health Insurance cover?",
        "expected_keywords": ["inpatient", "outpatient", "emergency", "specialist"]
    },
    {
        "name": "Provider Location Query",
        "query": "Find me healthcare providers in East Legon",
        "expected_keywords": ["East Legon", "providers", "Premium", "facilities"]
    },
    {
        "name": "Specialty Query",
        "query": "I need a gynecologist",
        "expected_keywords": ["Gynecology", "women", "health", "providers"]
    },
    {
        "name": "Emergency Query",
        "query": "What should I do in a medical emergency?",
        "expected_keywords": ["193", "emergency", "ambulance", "hospital"]
    },
    {
        "name": "Pharmacy Query",
        "query": "How do I get my medications from the pharmacy?",
        "expected_keywords": ["pharmacy", "prescription", "medication", "network"]
    },
    {
        "name": "Claims Query",
        "query": "How do I submit a claim for reimbursement?",
        "expected_keywords": ["claim", "receipt", "submit", "reimburse"]
    },
    {
        "name": "Contact Information Query",
        "query": "How can I contact Premier Health customer service?",
        "expected_keywords": ["contact", "customer", "service", "phone"]
    },
    {
        "name": "Area-Specific Provider Query",
        "query": "Are there any hospitals in Madina?",
        "expected_keywords": ["Madina", "providers", "clinic", "pharmacy"]
    }
]

async def test_rag_query(query_name, query, expected_keywords):
    """Test a single RAG query."""
    print(f"\n{'='*70}")
    print(f"TEST: {query_name}")
    print(f"{'='*70}")
    print(f"Query: {query}")

    try:
        result = await helpdesk_rag_service.query_knowledge_base(
            company_name="premier_health_production",
            query=query
        )

        print(f"\n✅ Status: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"📊 Confidence Score: {result.confidence_score:.2f}")
        print(f"🔍 Escalation Required: {result.requires_escalation}")
        if result.escalation_reason:
            print(f"   Reason: {result.escalation_reason}")
        print(f"📚 Sources Used: {len(result.sources_used)}")
        for i, source in enumerate(result.sources_used[:3], 1):
            print(f"   {i}. {source}")
        print(f"⏱️  Processing Time: {result.processing_time:.3f}s")

        print(f"\n💬 Response:")
        print(f"{'-'*70}")
        print(result.response[:500] + "..." if len(result.response) > 500 else result.response)
        print(f"{'-'*70}")

        # Check if expected keywords are in the response
        response_lower = result.response.lower()
        found_keywords = [kw for kw in expected_keywords if kw.lower() in response_lower]

        print(f"\n🔑 Keyword Verification:")
        print(f"   Expected: {expected_keywords}")
        print(f"   Found: {found_keywords}")
        print(f"   Match Rate: {len(found_keywords)}/{len(expected_keywords)}")

        if len(found_keywords) >= len(expected_keywords) * 0.5:  # 50% match threshold
            print(f"   ✅ PASS - Relevant response generated")
            return True
        else:
            print(f"   ⚠️  WEAK - Response may not be fully relevant")
            return False

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

async def run_all_tests():
    """Run all RAG integration tests."""
    print("🧪 Premier Health RAG Integration Tests")
    print("=" * 70)
    print(f"Total Tests: {len(TEST_QUERIES)}")
    print(f"Testing RAG collection: premier_health_production")

    results = []
    for test_case in TEST_QUERIES:
        passed = await test_rag_query(
            test_case["name"],
            test_case["query"],
            test_case["expected_keywords"]
        )
        results.append((test_case["name"], passed))
        await asyncio.sleep(1)  # Brief pause between tests

    # Summary
    print(f"\n\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\n{'='*70}")
    print(f"Results: {passed_count}/{total_count} tests passed ({passed_count/total_count*100:.1f}%)")

    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED - RAG system is working correctly!")
    elif passed_count >= total_count * 0.8:
        print("✅ MOSTLY PASSING - RAG system is working well with minor issues")
    elif passed_count >= total_count * 0.5:
        print("⚠️  PARTIAL SUCCESS - RAG system needs improvement")
    else:
        print("❌ TESTS FAILED - RAG system requires attention")

    return passed_count == total_count

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
