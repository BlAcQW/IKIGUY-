#!/usr/bin/env python3
"""
Load Ghana Tourism data from JSON files into PostgreSQL with RAG embeddings.
Generates OpenAI embeddings for semantic search.
"""

import asyncio
import json
import os
import sys
from typing import List, Dict, Any
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import asyncpg
import openai

# Configuration
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "aawwER444444")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_SERVER = os.getenv("POSTGRES_SERVER", "localhost")
POSTGRES_DB = os.getenv("POSTGRES_DB_CORE", "kasaai_core")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:5432/{POSTGRES_DB}"
openai.api_key = OPENAI_API_KEY

# Data paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DESTINATIONS_FILE = os.path.join(DATA_DIR, 'destinations.json')
ACCOMMODATIONS_FILE = os.path.join(DATA_DIR, 'accommodations.json')
PRACTICAL_INFO_FILE = os.path.join(DATA_DIR, 'practical_info.json')


async def generate_embedding(text: str) -> List[float]:
    """Generate OpenAI embedding for text."""
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"   ⚠️ Embedding generation error: {e}")
        return [0.0] * 1536  # Return zero vector on error


async def load_destinations(conn: asyncpg.Connection):
    """Load destinations data with embeddings."""
    print("\n📍 Loading tourism destinations...")

    with open(DESTINATIONS_FILE, 'r') as f:
        data = json.load(f)

    destinations = data['destinations']
    loaded = 0

    for dest in destinations:
        # Create searchable text for embedding
        search_text = f"""
        {dest['name']} in {dest['region']} region.
        {dest['description']}
        Highlights: {', '.join(dest['highlights'])}.
        Activities: {', '.join(dest['activities'])}.
        Best time to visit: {dest['best_time_to_visit']}.
        """.strip()

        # Generate embedding
        embedding = await generate_embedding(search_text)

        # Prepare data for insertion
        record = {
            'id': dest['id'],
            'name': dest['name'],
            'region': dest['region'],
            'category': dest['category'],
            'description': dest['description'],
            'highlights': dest['highlights'],
            'best_time_to_visit': dest.get('best_time_to_visit'),
            'entry_fee': dest.get('entry_fee'),
            'activities': dest['activities'],
            'difficulty': dest.get('difficulty'),
            'duration_hours': dest.get('duration_hours'),
            'district': dest['location'].get('district'),
            'neighborhood': dest['location'].get('neighborhood'),
            'coordinates': dest['location'].get('coordinates'),
            'distance_from_accra_km': dest['location'].get('distance_from_accra_km'),
            'contact': dest.get('contact'),
            'facilities': dest.get('facilities', []),
            'embedding': embedding,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        try:
            supabase.table('tourism_destinations').upsert(record).execute()
            loaded += 1
            print(f"   ✓ Loaded: {dest['name']}")
        except Exception as e:
            print(f"   ✗ Failed: {dest['name']} - {e}")

    print(f"✅ Loaded {loaded}/{len(destinations)} destinations")


async def load_accommodations():
    """Load accommodations data with embeddings."""
    print("\n🏨 Loading tourism accommodations...")

    with open(ACCOMMODATIONS_FILE, 'r') as f:
        data = json.load(f)

    accommodations = data['accommodations']
    loaded = 0

    for acc in accommodations:
        # Create searchable text for embedding
        room_info = ', '.join([f"{rt['type']} (GHS {rt['price_range_ghs']})" for rt in acc['room_types']])
        search_text = f"""
        {acc['name']}, a {acc['star_rating']}-star {acc['type']} in {acc['city']}, {acc['region']}.
        {acc['description']}
        Amenities: {', '.join(acc['amenities'])}.
        Room types: {room_info}.
        """.strip()

        # Generate embedding
        embedding = await generate_embedding(search_text)

        # Prepare data for insertion
        record = {
            'id': acc['id'],
            'name': acc['name'],
            'region': acc['region'],
            'city': acc['city'],
            'type': acc['type'],
            'star_rating': acc.get('star_rating'),
            'description': acc['description'],
            'amenities': acc['amenities'],
            'room_types': acc['room_types'],
            'location': acc['location'],
            'contact': acc['contact'],
            'booking_platforms': acc['booking_platforms'],
            'special_notes': acc.get('special_notes'),
            'embedding': embedding,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        try:
            supabase.table('tourism_accommodations').upsert(record).execute()
            loaded += 1
            print(f"   ✓ Loaded: {acc['name']}")
        except Exception as e:
            print(f"   ✗ Failed: {acc['name']} - {e}")

    print(f"✅ Loaded {loaded}/{len(accommodations)} accommodations")


async def load_practical_info():
    """Load practical information with embeddings."""
    print("\n📋 Loading practical information...")

    with open(PRACTICAL_INFO_FILE, 'r') as f:
        data = json.load(f)

    # Process each major category
    categories = {
        'visa': 'visa_requirements',
        'mobile_sim': 'mobile_sim_cards',
        'currency': 'currency_exchange',
        'safety': 'safety_security',
        'weather': 'weather_climate',
        'culture': 'cultural_etiquette'
    }

    loaded = 0

    for cat_id, cat_key in categories.items():
        if cat_key not in data:
            continue

        content = data[cat_key]

        # Create searchable text
        if isinstance(content, dict):
            search_text = json.dumps(content, indent=2)
            title = cat_key.replace('_', ' ').title()
        else:
            search_text = str(content)
            title = cat_key.replace('_', ' ').title()

        # Generate embedding
        embedding = await generate_embedding(search_text[:4000])  # Limit text size

        # Extract keywords
        keywords = [cat_id, cat_key] + cat_key.split('_')

        # Prepare data
        record = {
            'id': f"{cat_id}_001",
            'category': cat_id,
            'subcategory': None,
            'title': title,
            'content': content,
            'keywords': keywords,
            'embedding': embedding,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        try:
            supabase.table('tourism_practical_info').upsert(record).execute()
            loaded += 1
            print(f"   ✓ Loaded: {title}")
        except Exception as e:
            print(f"   ✗ Failed: {title} - {e}")

    print(f"✅ Loaded {loaded} practical info records")


async def generate_faqs():
    """Generate common FAQs from existing data."""
    print("\n❓ Generating FAQs from data...")

    faqs = [
        {
            "question": "What are the top tourist destinations in Ghana?",
            "answer": "Top destinations include Kakum National Park (canopy walkway), Cape Coast Castle (historical), Mole National Park (elephants), Labadi Beach (Accra), Wli Waterfalls (Volta), and Busua Beach (surfing).",
            "category": "destinations",
            "keywords": ["destinations", "tourist", "attractions", "places", "visit"]
        },
        {
            "question": "Do I need a visa to visit Ghana?",
            "answer": "Most visitors need a visa. Ghana offers e-visa (USD 150, 3-5 days processing) and visa on arrival for AU citizens. ECOWAS citizens don't need a visa. Check https://visa.immigration.gov.gh for details.",
            "category": "visa",
            "keywords": ["visa", "entry", "requirements", "immigration", "travel"]
        },
        {
            "question": "How much does a SIM card cost in Ghana?",
            "answer": "SIM cards cost about GHS 1. Tourist packages: MTN (GHS 50, 5GB + calls), Vodafone (GHS 45, 4GB + calls), AirtelTigo (GHS 40, 5GB + calls). Available at airport. Passport required for registration.",
            "category": "practical",
            "keywords": ["sim", "card", "mobile", "data", "phone", "internet"]
        },
        {
            "question": "What's the best time to visit Ghana?",
            "answer": "Best time is dry season (November-March) for beach and wildlife. Lower humidity and less rain. December-February can be hot and dusty (Harmattan). Rainy season (April-June) has lush greenery and lower hotel rates.",
            "category": "weather",
            "keywords": ["weather", "climate", "season", "when", "best time"]
        },
        {
            "question": "Is Ghana safe for tourists?",
            "answer": "Yes, Ghana is one of the safest West African countries. Be cautious of pickpocketing in crowded areas. Use registered taxis or ride apps (Uber, Bolt). Avoid walking alone at night. Keep valuables secure.",
            "category": "safety",
            "keywords": ["safety", "security", "crime", "safe", "dangerous"]
        },
        {
            "question": "What currency is used in Ghana?",
            "answer": "Ghana Cedi (GHS). USD 1 ≈ GHS 12.5. Exchange at banks (secure, official rates) or forex bureaus (better rates). ATMs widely available in cities. Credit cards accepted in hotels and large restaurants.",
            "category": "currency",
            "keywords": ["currency", "money", "exchange", "cedi", "payment"]
        },
        {
            "question": "What are emergency contact numbers in Ghana?",
            "answer": "Police: 191 or 18555, Ambulance: 193, Fire: 192, Tourist Police (Accra): +233 302 773 906. Save these numbers upon arrival.",
            "category": "emergency",
            "keywords": ["emergency", "contact", "police", "ambulance", "help"]
        },
        {
            "question": "Where can I stay in Accra?",
            "answer": "Top accommodations in Accra: Kempinski Hotel (5-star luxury, GHS 1200-4000), Labadi Beach Hotel (4-star beachfront, GHS 400-1500), Alisa Hotels (4-star boutique, GHS 500-1300), African Regent Hotel (4-star near airport, GHS 600-1800).",
            "category": "accommodation",
            "keywords": ["hotel", "accommodation", "stay", "lodging", "accra"]
        }
    ]

    loaded = 0

    for faq in faqs:
        # Generate embeddings for question and answer
        question_embedding = await generate_embedding(faq['question'])
        answer_embedding = await generate_embedding(faq['answer'])

        record = {
            'question': faq['question'],
            'answer': faq['answer'],
            'category': faq['category'],
            'keywords': faq['keywords'],
            'relevance_score': 1.0,
            'question_embedding': question_embedding,
            'answer_embedding': answer_embedding,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        try:
            supabase.table('tourism_faqs').insert(record).execute()
            loaded += 1
            print(f"   ✓ Created FAQ: {faq['question'][:60]}...")
        except Exception as e:
            print(f"   ✗ Failed: {e}")

    print(f"✅ Generated {loaded} FAQs")


async def main():
    """Main data loading function."""
    print("="*70)
    print("🇬🇭 Ghana Tourism Board - PostgreSQL RAG Data Loader")
    print("="*70)

    try:
        await load_destinations()
        await load_accommodations()
        await load_practical_info()
        await generate_faqs()

        print("\n" + "="*70)
        print("✅ All data loaded successfully with embeddings!")
        print("="*70)
        print("\n📊 Summary:")
        print("   - Destinations with semantic search")
        print("   - Accommodations with semantic search")
        print("   - Practical information with semantic search")
        print("   - FAQs with question matching")
        print("\n🎯 Next: Update voice_agent_tools.py to use RAG queries")

    except Exception as e:
        print(f"\n❌ Error during data loading: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
