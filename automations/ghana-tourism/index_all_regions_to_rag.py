#!/usr/bin/env python3
"""
Index ALL Ghana Tourism data to RAG (including all expanded regional data).
Comprehensive indexing script for October 2025 expansion - 34 destinations across 10 regions.

Updated: October 2, 2025
"""

import os
import sys
import json
import asyncio
import logging

# Add paths
sys.path.insert(0, '/opt/kasaai')
sys.path.insert(0, '/opt/kasaai/apps/core_backend')

from backend.services.helpdesk_rag_service import helpdesk_rag_service, KnowledgeDocument

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Collection name
GHANA_TOURISM_COLLECTION = "ghana_tourism_production"


async def load_all_destinations_to_rag(data_path: str) -> int:
    """
    Load ALL destination data from all region files into RAG.

    Includes:
    - Original destinations.json (10 destinations)
    - ashanti_region.json (5 destinations)
    - upper_east_region.json (5 destinations)
    - northern_region_extended.json (4 destinations)
    - western_region_extended.json (5 destinations)
    - eastern_region_extended.json (5 destinations)

    Total: 34 destinations across 10 regions
    """
    documents = []

    # File list with region names
    destination_files = [
        ('destinations.json', 'Original Regions'),
        ('ashanti_region.json', 'Ashanti'),
        ('upper_east_region.json', 'Upper East'),
        ('northern_region_extended.json', 'Northern Extended'),
        ('western_region_extended.json', 'Western Extended'),
        ('eastern_region_extended.json', 'Eastern Extended')
    ]

    for filename, region_label in destination_files:
        filepath = os.path.join(data_path, filename)

        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            continue

        with open(filepath, 'r') as f:
            data = json.load(f)

        destinations = data.get('destinations', [])
        logger.info(f"Loading {len(destinations)} destinations from {filename} ({region_label})")

        for dest in destinations:
            # Create comprehensive document for each destination
            content = f"""
Destination: {dest['name']}
Region: {dest.get('region', 'N/A')}
City: {dest.get('city', 'N/A')}
Categories: {', '.join(dest.get('category', []))}

Description:
{dest.get('description', '')}

Highlights:
{chr(10).join('- ' + h for h in dest.get('highlights', []))}

Activities:
{chr(10).join('- ' + a for a in dest.get('activities', []))}

Best Time to Visit: {dest.get('best_time_to_visit', 'N/A')}
Estimated Visit Duration: {dest.get('estimated_visit_duration', 'N/A')}
Entry Fee: {dest.get('entry_fee', 'N/A')}
Accessibility: {dest.get('accessibility', 'N/A')}

Location Details:
{dest.get('location_details', 'N/A')}
"""

            doc = KnowledgeDocument(
                title=dest['name'],
                content=content.strip(),
                category="destination",
                tags=dest.get('category', []) + [dest.get('region', '').lower()],
                metadata={
                    "type": "destination",
                    "name": dest['name'],
                    "region": dest.get('region'),
                    "city": dest.get('city'),
                    "categories": dest.get('category', []),
                    "source_file": filename
                }
            )
            documents.append(doc)

    # Update RAG knowledge base
    logger.info(f"Indexing {len(documents)} destination documents to RAG...")
    await helpdesk_rag_service.update_knowledge_base(
        company_name=GHANA_TOURISM_COLLECTION,
        documents=documents
    )

    return len(documents)


async def load_all_accommodations_to_rag(data_path: str) -> int:
    """
    Load ALL accommodation data from all region files into RAG.

    Includes:
    - Original accommodations.json (10 accommodations)
    - ashanti_region.json (5 accommodations)
    - upper_east_region.json (3 accommodations)
    - northern_region_extended.json (2 accommodations)
    - western_region_extended.json (4 accommodations)
    - eastern_region_extended.json (3 accommodations)

    Total: 27 accommodations across 10 regions
    """
    documents = []

    # File list with region names
    accommodation_files = [
        ('accommodations.json', 'Original Regions'),
        ('ashanti_region.json', 'Ashanti'),
        ('upper_east_region.json', 'Upper East'),
        ('northern_region_extended.json', 'Northern Extended'),
        ('western_region_extended.json', 'Western Extended'),
        ('eastern_region_extended.json', 'Eastern Extended')
    ]

    for filename, region_label in accommodation_files:
        filepath = os.path.join(data_path, filename)

        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            continue

        with open(filepath, 'r') as f:
            data = json.load(f)

        accommodations = data.get('accommodations', [])
        logger.info(f"Loading {len(accommodations)} accommodations from {filename} ({region_label})")

        for acc in accommodations:
            # Build room types description
            room_types_desc = "\n".join(
                f"- {rt['type']}: GHS {rt['price_range_ghs']} per night"
                for rt in acc.get('room_types', [])
            )

            content = f"""
Accommodation: {acc['name']}
Type: {acc.get('type', 'N/A').title()}
Star Rating: {acc.get('star_rating', 'N/A')} stars
City: {acc.get('city', 'N/A')}
Region: {acc.get('region', 'N/A')}

Description:
{acc.get('description', '')}

Amenities:
{chr(10).join('- ' + a for a in acc.get('amenities', []))}

Room Types and Pricing:
{room_types_desc}

Contact Information:
Phone: {acc.get('phone', 'N/A')}
Email: {acc.get('email', 'N/A')}
Website: {acc.get('website', 'N/A')}

Additional Information:
{acc.get('additional_info', 'N/A')}
"""

            doc = KnowledgeDocument(
                title=acc['name'],
                content=content.strip(),
                category="accommodation",
                tags=[acc.get('type', ''), acc.get('region', '').lower(), f"{acc.get('star_rating', 0)}-star"],
                metadata={
                    "type": "accommodation",
                    "name": acc['name'],
                    "accommodation_type": acc.get('type'),
                    "star_rating": acc.get('star_rating'),
                    "city": acc.get('city'),
                    "region": acc.get('region'),
                    "source_file": filename
                }
            )
            documents.append(doc)

    # Update RAG knowledge base
    logger.info(f"Indexing {len(documents)} accommodation documents to RAG...")
    await helpdesk_rag_service.update_knowledge_base(
        company_name=GHANA_TOURISM_COLLECTION,
        documents=documents
    )

    return len(documents)


async def load_transportation_to_rag(data_path: str) -> int:
    """Load transportation data into RAG knowledge base."""
    filepath = os.path.join(data_path, 'transportation.json')

    if not os.path.exists(filepath):
        logger.warning(f"Transportation file not found: {filepath}")
        return 0

    with open(filepath, 'r') as f:
        data = json.load(f)

    documents = []

    # Domestic flights document
    flights = data.get('domestic_flights', {})
    if flights:
        airlines_desc = "\n\n".join(
            f"{a['name']}:\n- Type: {a['type']}\n- Routes: {', '.join(a['routes'])}\n- Website: {a['website']}\n- Phone: {a['phone']}\n- {a['booking_info']}"
            for a in flights.get('airlines', [])
        )

        airports_desc = "\n".join(
            f"- {ap['name']} ({ap['code']}), {ap['location']}: {', '.join(ap['services'])}"
            for ap in flights.get('major_airports', [])
        )

        content = f"""
DOMESTIC FLIGHTS IN GHANA

Airlines:
{airlines_desc}

Major Airports:
{airports_desc}
"""
        documents.append(KnowledgeDocument(
            title="Domestic Flights in Ghana",
            content=content.strip(),
            category="transportation",
            tags=["domestic_flights", "airlines", "airports"],
            metadata={"type": "transportation", "subcategory": "domestic_flights"}
        ))

    # Intercity buses document
    buses = data.get('intercity_buses', {})
    if buses:
        companies_desc = "\n\n".join(
            f"{c['name']} ({c['type']}):\nRoutes: {len(c.get('routes', []))} destinations\nAmenities: {', '.join(c['amenities'])}\nPhone: {c['phone']}\nBooking: {c['booking']}"
            for c in buses.get('companies', [])
        )

        content = f"""
INTERCITY BUS TRANSPORTATION IN GHANA

Bus Companies:
{companies_desc}

Tips:
{chr(10).join('- ' + tip for tip in data.get('general_tips', []))}
"""
        documents.append(KnowledgeDocument(
            title="Intercity Bus Transportation in Ghana",
            content=content.strip(),
            category="transportation",
            tags=["intercity_buses", "bus_companies", "ground_transport"],
            metadata={"type": "transportation", "subcategory": "intercity_buses"}
        ))

    # Ride-hailing services document
    ride_hailing = data.get('ride_hailing', {})
    if ride_hailing:
        services_desc = "\n\n".join(
            f"{s['name']}:\n- Available in: {', '.join(s['availability'])}\n- Vehicle Types: {', '.join(s['vehicle_types'])}\n- Payment: {', '.join(s['payment_methods'])}\n- Price: {s['price_estimate']}"
            for s in ride_hailing.get('services', [])
        )

        content = f"""
RIDE-HAILING SERVICES IN GHANA

Available Services:
{services_desc}

Traditional Taxis:
{ride_hailing.get('traditional_taxis', {}).get('description', '')}
Typical Rates: {ride_hailing.get('traditional_taxis', {}).get('typical_rates', '')}

Tips:
{chr(10).join('- ' + tip for tip in ride_hailing.get('traditional_taxis', {}).get('tips', []))}
"""
        documents.append(KnowledgeDocument(
            title="Ride-Hailing and Taxi Services in Ghana",
            content=content.strip(),
            category="transportation",
            tags=["ride_hailing", "taxis", "uber", "bolt", "yango"],
            metadata={"type": "transportation", "subcategory": "ride_hailing"}
        ))

    # General transportation tips
    if data.get('general_tips'):
        content = f"""
GENERAL TRANSPORTATION TIPS FOR GHANA

{chr(10).join('- ' + tip for tip in data['general_tips'])}

Airport Transfers:
{chr(10).join(f"- {opt['type']}: {opt['description']} ({opt['price_range']})" for opt in data.get('airport_transfers', {}).get('options', []))}
"""
        documents.append(KnowledgeDocument(
            title="General Transportation Tips for Ghana",
            content=content.strip(),
            category="transportation",
            tags=["tips", "airport_transfers", "general_info"],
            metadata={"type": "transportation", "subcategory": "general_tips"}
        ))

    # Update RAG knowledge base
    logger.info(f"Indexing {len(documents)} transportation documents to RAG...")
    await helpdesk_rag_service.update_knowledge_base(
        company_name=GHANA_TOURISM_COLLECTION,
        documents=documents
    )

    return len(documents)


async def load_restaurants_to_rag(data_path: str) -> int:
    """Load restaurants data into RAG knowledge base."""
    filepath = os.path.join(data_path, 'restaurants.json')

    if not os.path.exists(filepath):
        logger.warning(f"Restaurants file not found: {filepath}")
        return 0

    with open(filepath, 'r') as f:
        data = json.load(f)

    documents = []

    # Individual restaurant documents
    for restaurant in data.get('restaurants', []):
        content = f"""
Restaurant: {restaurant['name']}
Location: {restaurant['location']}, {restaurant['region']}
Cuisine: {', '.join(restaurant['cuisine_type'])}
Price Range: {restaurant['price_range']} (Average: GHS {restaurant['average_meal_cost_ghs']})

Description:
{restaurant['description']}

Specialties:
{chr(10).join('- ' + s for s in restaurant['specialties'])}

Dining Options: {', '.join(restaurant['dining_options'])}
Opening Hours: {restaurant['opening_hours']}

Amenities:
{chr(10).join('- ' + a for a in restaurant['amenities'])}

Dietary Options: {', '.join(restaurant.get('dietary_options', []))}
Popular For: {', '.join(restaurant.get('popular_for', []))}

Contact:
Phone: {restaurant.get('contact', {}).get('phone', 'N/A')}
Website: {restaurant.get('contact', {}).get('website', 'N/A')}
"""
        documents.append(KnowledgeDocument(
            title=restaurant['name'],
            content=content.strip(),
            category="restaurant",
            tags=restaurant['cuisine_type'] + [restaurant['price_range'], restaurant['location']],
            metadata={
                "type": "restaurant",
                "name": restaurant['name'],
                "cuisine": restaurant['cuisine_type'],
                "price_range": restaurant['price_range'],
                "location": restaurant['location']
            }
        ))

    # Dining tips document
    if data.get('dining_tips'):
        content = f"""
DINING TIPS FOR GHANA

{chr(10).join('- ' + tip for tip in data['dining_tips'])}

Price Guide:
{chr(10).join(f"{k}: {v}" for k, v in data.get('price_guide', {}).items())}

Traditional Ghanaian Food:
{chr(10).join('- ' + dish for dish in data.get('food_categories', {}).get('ghanaian_traditional', []))}

Street Food:
{chr(10).join('- ' + food for food in data.get('food_categories', {}).get('street_food', []))}
"""
        documents.append(KnowledgeDocument(
            title="Dining Tips and Ghanaian Food Guide",
            content=content.strip(),
            category="restaurant",
            tags=["dining_tips", "ghanaian_food", "street_food"],
            metadata={"type": "dining_tips", "subcategory": "restaurants"}
        ))

    # Update RAG knowledge base
    logger.info(f"Indexing {len(documents)} restaurant documents to RAG...")
    await helpdesk_rag_service.update_knowledge_base(
        company_name=GHANA_TOURISM_COLLECTION,
        documents=documents
    )

    return len(documents)


async def load_practical_info_to_rag(data_path: str) -> int:
    """Load practical information into RAG knowledge base."""
    filepath = os.path.join(data_path, 'practical_info.json')

    if not os.path.exists(filepath):
        logger.warning(f"Practical info file not found: {filepath}")
        return 0

    with open(filepath, 'r') as f:
        data = json.load(f)

    # Create one comprehensive practical info document
    content = f"""
PRACTICAL INFORMATION FOR VISITING GHANA

VISA REQUIREMENTS:
{json.dumps(data.get('visa_requirements', {}), indent=2)}

MOBILE SIM CARDS:
{json.dumps(data.get('sim_cards', {}), indent=2)}

CURRENCY & EXCHANGE:
{json.dumps(data.get('currency_exchange', {}), indent=2)}

SAFETY & SECURITY:
{json.dumps(data.get('safety_security', {}), indent=2)}

WEATHER & CLIMATE:
{json.dumps(data.get('weather_climate', {}), indent=2)}

CULTURAL ETIQUETTE:
{json.dumps(data.get('cultural_etiquette', {}), indent=2)}
"""

    doc = KnowledgeDocument(
        title="Practical Information for Visiting Ghana",
        content=content.strip(),
        category="practical_info",
        tags=["visa", "sim_cards", "currency", "safety", "weather", "etiquette"],
        metadata={"type": "practical_info", "subcategory": "general"}
    )

    # Update RAG knowledge base
    logger.info("Indexing practical information document to RAG...")
    await helpdesk_rag_service.update_knowledge_base(
        company_name=GHANA_TOURISM_COLLECTION,
        documents=[doc]
    )

    return 1


async def main():
    """Main indexing function."""
    print("=" * 80)
    print("🇬🇭 Ghana Tourism Board - Comprehensive RAG Indexing")
    print("October 2025 Expansion - All Regions")
    print("=" * 80)

    # Data path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'data')

    # Index all data
    destinations_count = await load_all_destinations_to_rag(data_path)
    print(f"✅ Destinations indexed: {destinations_count}")

    accommodations_count = await load_all_accommodations_to_rag(data_path)
    print(f"✅ Accommodations indexed: {accommodations_count}")

    transportation_count = await load_transportation_to_rag(data_path)
    print(f"✅ Transportation documents indexed: {transportation_count}")

    restaurants_count = await load_restaurants_to_rag(data_path)
    print(f"✅ Restaurant documents indexed: {restaurants_count}")

    practical_count = await load_practical_info_to_rag(data_path)
    print(f"✅ Practical info documents indexed: {practical_count}")

    # Summary
    total_documents = (destinations_count + accommodations_count +
                      transportation_count + restaurants_count + practical_count)

    print("\n" + "=" * 80)
    print("📊 INDEXING COMPLETE")
    print("=" * 80)
    print(f"📍 Total Destinations: {destinations_count} (across 10 regions)")
    print(f"🏨 Total Accommodations: {accommodations_count}")
    print(f"🚗 Transportation Guides: {transportation_count}")
    print(f"🍽️  Restaurant Documents: {restaurants_count}")
    print(f"ℹ️  Practical Info: {practical_count}")
    print(f"📊 TOTAL DOCUMENTS: {total_documents}")
    print(f"🔍 Collection: {GHANA_TOURISM_COLLECTION}")
    print("\n✅ All data ready for semantic search with Google Gemini!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
