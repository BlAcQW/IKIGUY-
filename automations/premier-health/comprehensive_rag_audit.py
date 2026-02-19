#!/usr/bin/env python3
"""
Comprehensive RAG Database Audit

Tests ALL city documents to verify:
1. Document exists in database
2. Document is retrievable via RAG query
3. Document returns actual provider data

This will identify which cities have embedding/indexing issues.
"""

import os
import sys
import asyncio
import httpx
import psycopg2
from typing import Dict, List

sys.path.append('/opt/kasaai/apps/core_backend')

RAG_ENDPOINT = "https://api.ailabsafrica.com/knowledge-base/premier_health_production/query"
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "aawwER444444")


def get_all_city_documents() -> List[Dict]:
    """Get all city documents from database using direct PostgreSQL query."""
    documents = []

    conn = psycopg2.connect(
        host="127.0.0.1",
        database="kasaai_core",
        user="postgres",
        password=POSTGRES_PASSWORD
    )
    cur = conn.cursor()

    # Query documents directly from database
    cur.execute("""
        SELECT id, document_id, title, content, tags, status
        FROM kb_documents
        WHERE collection_name = 'helpdesk_premier_health_production'
        AND title LIKE 'Healthcare Providers in %'
        ORDER BY title
    """)

    rows = cur.fetchall()

    for row in rows:
        doc_id, document_id, title, content, tags, status = row
        city_name = title.replace('Healthcare Providers in ', '').strip()

        documents.append({
            'id': document_id,
            'title': title,
            'city': city_name,
            'content_length': len(content) if content else 0,
            'tags': tags if tags else [],
            'status': status
        })

    cur.close()
    conn.close()

    return documents


async def test_rag_query(city: str) -> Dict:
    """Test RAG query for a city."""
    query = f"healthcare providers in {city}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                RAG_ENDPOINT,
                json={"query": query},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()

            # Check if the response mentions the city or has real provider data
            response_text = result.get('response', '') + ' '.join(result.get('sources_used', []))
            city_mentioned = city.upper() in response_text.upper()

            # Check for negative responses
            negative_indicators = [
                "do not have",
                "no information",
                "not listed",
                "not available",
                "cannot find",
                "is not listed among"
            ]

            has_negative = any(indicator in result.get('response', '').lower() for indicator in negative_indicators)

            return {
                "success": result.get('success', False),
                "confidence": result.get('confidence_score', 0),
                "sources": result.get('sources_used', []),
                "response_length": len(result.get('response', '')),
                "city_mentioned": city_mentioned,
                "has_negative_response": has_negative,
                "looks_good": city_mentioned and not has_negative and result.get('confidence_score', 0) > 0.7
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "looks_good": False
            }


async def main():
    """Main audit execution."""
    print("🔍 COMPREHENSIVE RAG DATABASE AUDIT")
    print("=" * 80)

    # Step 1: Get all documents
    print("\n1️⃣  Fetching all city documents from database...")
    documents = get_all_city_documents()  # Now synchronous
    print(f"   ✅ Found {len(documents)} city documents in database")

    # Step 2: Test each city
    print("\n2️⃣  Testing RAG queries for each city...")
    print("   (This will take a few minutes...)\n")

    results = {
        "working": [],
        "broken": [],
        "suspicious": []
    }

    for i, doc in enumerate(documents, 1):
        city = doc['city']
        print(f"   [{i}/{len(documents)}] Testing {city}...", end=" ", flush=True)

        rag_result = await test_rag_query(city)

        # Categorize result
        if rag_result.get('looks_good'):
            results['working'].append({
                'city': city,
                'doc_id': doc['id'],
                'confidence': rag_result.get('confidence'),
                'sources': rag_result.get('sources', [])
            })
            print("✅")
        elif rag_result.get('has_negative_response'):
            results['broken'].append({
                'city': city,
                'doc_id': doc['id'],
                'reason': 'Negative response (no information found)',
                'confidence': rag_result.get('confidence'),
                'sources': rag_result.get('sources', []),
                'response': rag_result.get('response', '')[:200]
            })
            print("❌ BROKEN")
        else:
            results['suspicious'].append({
                'city': city,
                'doc_id': doc['id'],
                'reason': 'City not mentioned or low confidence',
                'confidence': rag_result.get('confidence'),
                'sources': rag_result.get('sources', [])
            })
            print("⚠️  SUSPICIOUS")

        # Small delay to avoid overwhelming the API
        await asyncio.sleep(0.5)

    # Step 3: Generate report
    print("\n" + "=" * 80)
    print("📊 AUDIT RESULTS")
    print("=" * 80)

    print(f"\n✅ WORKING CITIES: {len(results['working'])}/{len(documents)}")
    print(f"❌ BROKEN CITIES: {len(results['broken'])}/{len(documents)}")
    print(f"⚠️  SUSPICIOUS CITIES: {len(results['suspicious'])}/{len(documents)}")

    # Show broken cities
    if results['broken']:
        print("\n" + "=" * 80)
        print("❌ BROKEN CITIES (Not retrievable via RAG)")
        print("=" * 80)
        for item in results['broken']:
            print(f"\n🔴 {item['city']}")
            print(f"   Document ID: {item['doc_id']}")
            print(f"   Confidence: {item['confidence']}")
            print(f"   Sources returned: {item['sources'][:2]}")
            print(f"   Response preview: {item.get('response', '')[:150]}...")

    # Show suspicious cities
    if results['suspicious']:
        print("\n" + "=" * 80)
        print("⚠️  SUSPICIOUS CITIES (Low confidence or city not mentioned)")
        print("=" * 80)
        for item in results['suspicious']:
            print(f"\n🟡 {item['city']}")
            print(f"   Document ID: {item['doc_id']}")
            print(f"   Confidence: {item['confidence']}")
            print(f"   Sources: {item['sources'][:2]}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("📈 SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Total documents tested: {len(documents)}")

    if len(documents) > 0:
        print(f"Working correctly: {len(results['working'])} ({len(results['working'])/len(documents)*100:.1f}%)")
        print(f"Definitely broken: {len(results['broken'])} ({len(results['broken'])/len(documents)*100:.1f}%)")
        print(f"Needs review: {len(results['suspicious'])} ({len(results['suspicious'])/len(documents)*100:.1f}%)")
    else:
        print("⚠️  No documents found to test!")
        print(f"Working correctly: {len(results['working'])}")
        print(f"Definitely broken: {len(results['broken'])}")
        print(f"Needs review: {len(results['suspicious'])}")

    # Critical cities check
    critical_cities = [
        'KOKOMLEMLE', 'MAAMOBI', 'NIMA', 'TUDU', 'MAKOLA', '37 AREA',
        'AMASAMAN', 'POKUASE', 'TAMALE', 'WA', 'BOLGATANGA', 'KUMASI'
    ]

    print("\n" + "=" * 80)
    print("🎯 CRITICAL CITIES STATUS")
    print("=" * 80)
    for city in critical_cities:
        if any(r['city'] == city for r in results['working']):
            print(f"✅ {city}: Working")
        elif any(r['city'] == city for r in results['broken']):
            print(f"❌ {city}: BROKEN")
        elif any(r['city'] == city for r in results['suspicious']):
            print(f"⚠️  {city}: Suspicious")
        else:
            print(f"❓ {city}: Not found in database")

    # Save results to file
    import json
    output_file = "/opt/kasaai/apps/automations/premier-health/rag_audit_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Full results saved to: {output_file}")
    print("\n✅ Audit complete!")


if __name__ == "__main__":
    asyncio.run(main())
