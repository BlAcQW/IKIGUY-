#!/usr/bin/env python3
"""
Index Ghana Tourism Board data into RAG knowledge base.

This script loads destinations, accommodations, and practical info data
and indexes them into the helpdesk RAG service using Gemini embeddings
for semantic search capabilities.
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime

# Add paths
sys.path.insert(0, '/opt/kasaai')
sys.path.insert(0, '/opt/kasaai/apps/core_backend')

from apps.core_backend.backend.services.helpdesk_rag_service import (
    helpdesk_rag_service,
    KnowledgeDocument
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Collection name for Ghana Tourism data
GHANA_TOURISM_COLLECTION = "ghana_tourism_production"


async def load_destinations_to_rag(data_path: str) -> int:
    """
    Load destination data into RAG knowledge base.

    Args:
        data_path: Path to data directory

    Returns:
        Number of documents indexed
    """
    try:
        filepath = os.path.join(data_path, 'destinations.json')
        with open(filepath, 'r') as f:
            data = json.load(f)

        destinations = data.get('destinations', [])
        documents = []

        for dest in destinations:
            # Create comprehensive content for semantic search
            content = f"""
Destination: {dest['name']}
Region: {dest['region']}
Categories: {', '.join(dest['category'])}
Description: {dest['description']}

Highlights:
{chr(10).join(['- ' + h for h in dest['highlights']])}

Activities:
{chr(10).join(['- ' + a for a in dest['activities']])}

Best Time to Visit: {dest.get('best_time_to_visit', 'Year-round')}
Estimated Visit Duration: {dest.get('estimated_visit_duration', '1-2 hours')}
Entry Fee: {dest.get('entry_fee', 'Free')}
Accessibility: {dest.get('accessibility', 'Accessible')}

Location Details: {dest.get('location_details', '')}
"""

            doc = KnowledgeDocument(
                title=f"{dest['name']} - {dest['region']} Ghana",
                content=content.strip(),
                category="destination",
                source="ghana_tourism_board",
                tags=[
                    "ghana",
                    "tourism",
                    "destination",
                    dest['region'].lower().replace(' ', '_'),
                    *[cat.lower() for cat in dest['category']]
                ],
                metadata={
                    "destination_id": dest['id'],
                    "region": dest['region'],
                    "categories": dest['category'],
                    "entry_fee": dest.get('entry_fee', 'Free'),
                    "indexed_at": datetime.utcnow().isoformat()
                }
            )
            documents.append(doc)

        logger.info(f"Indexing {len(documents)} destination documents...")
        await helpdesk_rag_service.update_knowledge_base(
            company_name=GHANA_TOURISM_COLLECTION,
            documents=documents
        )

        logger.info(f"✅ Successfully indexed {len(documents)} destinations")
        return len(documents)

    except Exception as e:
        logger.error(f"❌ Error loading destinations: {e}")
        raise


async def load_accommodations_to_rag(data_path: str) -> int:
    """
    Load accommodation data into RAG knowledge base.

    Args:
        data_path: Path to data directory

    Returns:
        Number of documents indexed
    """
    try:
        filepath = os.path.join(data_path, 'accommodations.json')
        with open(filepath, 'r') as f:
            data = json.load(f)

        accommodations = data.get('accommodations', [])
        documents = []

        for acc in accommodations:
            # Format room types
            room_info = []
            for room in acc.get('room_types', []):
                room_info.append(f"{room['type']}: GHS {room['price_range_ghs']} per night")

            # Create comprehensive content
            content = f"""
Accommodation: {acc['name']}
Type: {acc['type'].title()}
Star Rating: {acc['star_rating']}-star
Location: {acc['city']}, {acc['region']} Region

Description: {acc['description']}

Amenities:
{chr(10).join(['- ' + a for a in acc['amenities']])}

Room Types and Prices:
{chr(10).join(['- ' + r for r in room_info])}

Contact Information:
Phone: {acc.get('phone', 'Contact for details')}
Email: {acc.get('email', 'Contact for details')}
Website: {acc.get('website', 'Not available')}

Additional Features:
{acc.get('additional_info', 'Standard hospitality services available')}
"""

            doc = KnowledgeDocument(
                title=f"{acc['name']} - {acc['type'].title()} in {acc['city']}",
                content=content.strip(),
                category="accommodation",
                source="ghana_tourism_board",
                tags=[
                    "ghana",
                    "tourism",
                    "accommodation",
                    acc['type'].lower(),
                    acc['region'].lower().replace(' ', '_'),
                    f"{acc['star_rating']}_star"
                ],
                metadata={
                    "accommodation_id": acc['id'],
                    "type": acc['type'],
                    "star_rating": acc['star_rating'],
                    "region": acc['region'],
                    "city": acc['city'],
                    "indexed_at": datetime.utcnow().isoformat()
                }
            )
            documents.append(doc)

        logger.info(f"Indexing {len(documents)} accommodation documents...")
        await helpdesk_rag_service.update_knowledge_base(
            company_name=GHANA_TOURISM_COLLECTION,
            documents=documents
        )

        logger.info(f"✅ Successfully indexed {len(documents)} accommodations")
        return len(documents)

    except Exception as e:
        logger.error(f"❌ Error loading accommodations: {e}")
        raise


async def load_practical_info_to_rag(data_path: str) -> int:
    """
    Load practical information into RAG knowledge base.

    Args:
        data_path: Path to data directory

    Returns:
        Number of documents indexed
    """
    try:
        filepath = os.path.join(data_path, 'practical_info.json')
        with open(filepath, 'r') as f:
            data = json.load(f)

        documents = []

        # Visa information
        visa_info = data.get('visa_requirements', {})
        if visa_info:
            content = f"""
VISA REQUIREMENTS FOR GHANA

General Information:
{visa_info.get('general_info', '')}

Visa Types:
"""
            for visa_type, details in visa_info.get('visa_types', {}).items():
                content += f"\n{visa_type.replace('_', ' ').title()}:\n"
                content += f"Cost: {details.get('cost', 'Contact embassy')}\n"
                content += f"Processing Time: {details.get('processing_time', 'Varies')}\n"
                content += f"Validity: {details.get('validity', 'Check with embassy')}\n"
                content += f"Details: {details.get('details', '')}\n"

            doc = KnowledgeDocument(
                title="Ghana Visa Requirements and Information",
                content=content.strip(),
                category="practical_info",
                source="ghana_tourism_board",
                tags=["ghana", "tourism", "visa", "travel", "requirements"],
                metadata={"type": "visa", "indexed_at": datetime.utcnow().isoformat()}
            )
            documents.append(doc)

        # SIM Card information
        sim_info = data.get('sim_cards', {})
        if sim_info:
            providers = sim_info.get('providers', [])
            content = f"""
MOBILE SIM CARDS IN GHANA

General Information:
{sim_info.get('general_info', '')}

Network Providers:
"""
            for provider in providers:
                content += f"\n{provider['name']}:\n"
                content += f"Coverage: {provider.get('coverage', 'Nationwide')}\n"
                content += f"Tourist Package: GHS {provider['tourist_package']['price_ghs']} - {provider['tourist_package']['benefits']}\n"

                if provider.get('data_plans'):
                    content += "Data Plans:\n"
                    for plan in provider['data_plans'][:3]:  # Top 3 plans
                        content += f"  - {plan['data']}: GHS {plan['price_ghs']} for {plan['validity']}\n"

            doc = KnowledgeDocument(
                title="Ghana Mobile SIM Cards and Data Plans",
                content=content.strip(),
                category="practical_info",
                source="ghana_tourism_board",
                tags=["ghana", "tourism", "sim_card", "mobile", "data", "connectivity"],
                metadata={"type": "sim_cards", "indexed_at": datetime.utcnow().isoformat()}
            )
            documents.append(doc)

        # Currency information
        currency_info = data.get('currency_exchange', {})
        if currency_info:
            content = f"""
CURRENCY AND MONEY IN GHANA

Currency: {currency_info.get('currency', 'Ghana Cedi (GHS)')}

Exchange Rate Information:
{str(currency_info.get('exchange_rate_approximation', ''))}

Where to Exchange Money:
{chr(10).join(['- ' + (loc['type'] if isinstance(loc, dict) else str(loc)) for loc in currency_info.get('where_to_exchange', [])])}

Payment Methods:
{chr(10).join(['- ' + method for method in currency_info.get('payment_methods_accepted', [])])}

ATM Availability:
{currency_info.get('atm_availability', 'Widely available in major cities')}

Tips:
{chr(10).join(['- ' + tip for tip in currency_info.get('tips', [])])}
"""

            doc = KnowledgeDocument(
                title="Ghana Currency, Exchange, and Payment Information",
                content=content.strip(),
                category="practical_info",
                source="ghana_tourism_board",
                tags=["ghana", "tourism", "currency", "money", "exchange", "payment"],
                metadata={"type": "currency", "indexed_at": datetime.utcnow().isoformat()}
            )
            documents.append(doc)

        # Safety and Security
        safety_info = data.get('safety_security', {})
        if safety_info:
            content = f"""
SAFETY AND SECURITY IN GHANA

General Safety:
{chr(10).join(['- ' + tip for tip in safety_info.get('general_safety', [])])}

Health Precautions:
{chr(10).join(['- ' + tip for tip in safety_info.get('health', [])])}

Road Safety:
{chr(10).join(['- ' + tip for tip in safety_info.get('road_safety', [])])}

Scam Awareness:
{chr(10).join(['- ' + tip for tip in safety_info.get('scam_awareness', [])])}

Emergency Contacts:
{chr(10).join([f"- {k.replace('_', ' ').title()}: {v}" for k, v in safety_info.get('emergency_contacts', {}).items()])}
"""

            doc = KnowledgeDocument(
                title="Ghana Safety, Security, and Emergency Information",
                content=content.strip(),
                category="practical_info",
                source="ghana_tourism_board",
                tags=["ghana", "tourism", "safety", "security", "emergency", "health"],
                metadata={"type": "safety", "indexed_at": datetime.utcnow().isoformat()}
            )
            documents.append(doc)

        # Weather and Climate
        weather_info = data.get('weather_climate', {})
        if weather_info:
            content = f"""
GHANA WEATHER AND CLIMATE

Overview:
{weather_info.get('overview', '')}

Seasons:
{chr(10).join([f"- {season.get('name', 'Season')}: {season.get('months', '')} - {season.get('description', '')}" for season in weather_info.get('seasons', [])])}

Best Time to Visit:
{weather_info.get('best_time_to_visit', '')}

What to Pack:
{chr(10).join(['- ' + str(item) for item in weather_info.get('what_to_pack', [])])}

Regional Climate Differences:
{chr(10).join([f"- {region.get('region', 'Region')}: {region.get('description', '')}" for region in weather_info.get('regional_differences', [])])}
"""

            doc = KnowledgeDocument(
                title="Ghana Weather, Climate, and Packing Guide",
                content=content.strip(),
                category="practical_info",
                source="ghana_tourism_board",
                tags=["ghana", "tourism", "weather", "climate", "packing", "seasons"],
                metadata={"type": "weather", "indexed_at": datetime.utcnow().isoformat()}
            )
            documents.append(doc)

        # Cultural Etiquette
        culture_info = data.get('cultural_etiquette', {})
        if culture_info:
            content = f"""
GHANA CULTURAL ETIQUETTE AND CUSTOMS

Overview:
{culture_info.get('overview', '')}

Greetings and Social Customs:
{chr(10).join(['- ' + tip for tip in culture_info.get('greetings', [])])}

Dress Code:
{chr(10).join(['- ' + tip for tip in culture_info.get('dress_code', [])])}

Dining Etiquette:
{chr(10).join(['- ' + tip for tip in culture_info.get('dining_etiquette', [])])}

Photography Guidelines:
{chr(10).join(['- ' + tip for tip in culture_info.get('photography', [])])}

Tipping Practices:
{culture_info.get('tipping', '')}

Important Phrases:
{chr(10).join([f"- {phrase.get('english', '')}: {phrase.get('twi', '')} ({phrase.get('pronunciation', '')})" for phrase in culture_info.get('important_phrases', [])])}
"""

            doc = KnowledgeDocument(
                title="Ghana Cultural Etiquette and Social Customs",
                content=content.strip(),
                category="practical_info",
                source="ghana_tourism_board",
                tags=["ghana", "tourism", "culture", "etiquette", "customs", "language"],
                metadata={"type": "culture", "indexed_at": datetime.utcnow().isoformat()}
            )
            documents.append(doc)

        if documents:
            logger.info(f"Indexing {len(documents)} practical info documents...")
            await helpdesk_rag_service.update_knowledge_base(
                company_name=GHANA_TOURISM_COLLECTION,
                documents=documents
            )
            logger.info(f"✅ Successfully indexed {len(documents)} practical info documents")

        return len(documents)

    except Exception as e:
        logger.error(f"❌ Error loading practical info: {e}")
        raise


async def main():
    """Main indexing function."""
    print("=" * 80)
    print("🇬🇭 Ghana Tourism Board - RAG Knowledge Base Indexing")
    print("=" * 80)
    print()

    # Get data path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'data')

    if not os.path.exists(data_path):
        print(f"❌ Data directory not found: {data_path}")
        return

    print(f"📂 Data path: {data_path}")
    print(f"📦 Collection: {GHANA_TOURISM_COLLECTION}")
    print(f"🤖 AI Provider: {helpdesk_rag_service.ai_provider.upper()}")
    print()

    try:
        # Initialize RAG service collection
        print("🔧 Initializing RAG collection...")
        await helpdesk_rag_service._get_vectorstore(GHANA_TOURISM_COLLECTION)
        print("✅ RAG collection ready")
        print()

        # Load destinations
        print("📍 Indexing destinations...")
        dest_count = await load_destinations_to_rag(data_path)
        print()

        # Load accommodations
        print("🏨 Indexing accommodations...")
        acc_count = await load_accommodations_to_rag(data_path)
        print()

        # Load practical info
        print("ℹ️  Indexing practical information...")
        info_count = await load_practical_info_to_rag(data_path)
        print()

        # Summary
        total = dest_count + acc_count + info_count
        print("=" * 80)
        print("✅ INDEXING COMPLETE")
        print("=" * 80)
        print(f"📍 Destinations: {dest_count}")
        print(f"🏨 Accommodations: {acc_count}")
        print(f"ℹ️  Practical Info: {info_count}")
        print(f"📊 Total Documents: {total}")
        print()
        print(f"🎯 Collection: {GHANA_TOURISM_COLLECTION}")
        print(f"🔍 Ready for semantic search with {helpdesk_rag_service.ai_provider.upper()}")
        print()

    except Exception as e:
        print(f"\n❌ Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
