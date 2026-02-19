# 🇬🇭 Ghana Tourism Board - Voice Agent Automation

A comprehensive voice agent system for the Ghana Tourism Board providing tourist information, destination recommendations, accommodation search, and practical travel assistance.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Custom Tools](#custom-tools)
- [Data Sources](#data-sources)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Deployment](#deployment)

---

## 🎯 Overview

This automation provides a complete voice agent solution for Ghana Tourism Board, featuring:

- **11 Custom Tools** for tourism information
- **Gemini RAG System** - Google Gemini 2.5 Flash powered semantic search
- **46+ RAG Documents** with Gemini embeddings (136 vector chunks)
- **PostgreSQL + pgvector** for vector storage
- **VAPI Integration** ready for voice deployment
- **100% AI-Enhanced** responses (confidence score: 1.00)
- **Expanded Coverage** - Now includes Ashanti Region (Kumasi), Transportation, Restaurants

**Agent Personality**: Akua - A warm, knowledgeable Ghanaian tourism expert powered by Gemini

---

## ✨ Features

### Information Services
- 🏖️ **Destination Search** - 15 major tourist attractions (7 regions)
- 🏨 **Accommodation Search** - 15 hotels, resorts, lodges with price filtering
- 🛂 **Visa Information** - Requirements by nationality
- 📱 **SIM Card Info** - Providers, plans, pricing
- 💱 **Currency Exchange** - Rates, where to exchange
- 🚨 **Safety Tips** - General, health, road safety, scams
- 📞 **Emergency Contacts** - Police, ambulance, fire, tourist police
- 🚗 **Transportation Guide** - Flights, buses, ride-hailing, car rentals
- 🍽️ **Restaurant Recommendations** - 10 Accra restaurants, dining tips

### Communication Tools
- 📧 **Email Itineraries** - Send detailed travel information
- 🆘 **Human Escalation** - Route complex queries to tourism officers

### AI-Powered Features
- 🔍 **Semantic Search** - Find relevant content using natural language
- 🧠 **RAG System** - Context-aware responses using PostgreSQL + pgvector
- 💬 **Voice-Optimized** - Responses designed for natural conversation

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     VAPI Voice Platform                      │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Akua - Ghana Tourism Agent                           │  │
│  │  (System Prompt + 11 Custom Tools)                    │  │
│  └──────────────────┬───────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────────┘
                     │
                     │ HTTPS Webhook
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              KasaAI Core Backend (FastAPI)                   │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Custom Tools Endpoints                                 │ │
│  │  /custom-tools/ghana-tourism-board/<tool_name>        │ │
│  └────────────┬──────────────────┬────────────────────────┘ │
│               │                  │                           │
│               │                  │                           │
│  ┌────────────▼───────┐   ┌─────▼──────────────┐          │
│  │  voice_agent_tools │   │  EmailService       │          │
│  │  (Python Class)    │   │  (Email sending)    │          │
│  └────────────┬───────┘   └─────────────────────┘          │
│               │                                              │
└───────────────┼──────────────────────────────────────────────┘
                │
                │
      ┌─────────┴─────────┐
      │                   │
      ▼                   ▼
┌─────────────┐    ┌──────────────────────┐
│  MongoDB    │    │  PostgreSQL          │
│             │    │                      │
│  Tools      │    │  RAG Tables:         │
│  Registry   │    │  - destinations      │
│  (11 tools) │    │  - accommodations    │
│             │    │  - practical_info    │
│             │    │  - faqs              │
│             │    │                      │
│             │    │  pgvector extension  │
│             │    │  (1536-dim embeddings)│
└─────────────┘    └──────────────────────┘
```

---

## 🛠️ Custom Tools

### 1. `search_destinations`
Search for tourist destinations by query, region, or category.

**Parameters**:
- `query` (string, required): Natural language search
- `region` (string, optional): Specific region
- `category` (string, optional): beach, historical, nature, etc.
- `max_results` (integer, optional): Default 5

**Example**:
```json
{
  "query": "beaches near Accra",
  "max_results": 3
}
```

### 2. `get_destination_details`
Get comprehensive details about a specific destination.

**Parameters**:
- `destination_name` (string, required): Name of destination

**Example**:
```json
{
  "destination_name": "Kakum National Park"
}
```

### 3. `search_accommodation`
Search hotels, resorts, and lodges with budget filtering.

**Parameters**:
- `location` (string, optional): City or region
- `accommodation_type` (string, optional): hotel, resort, lodge, guesthouse
- `budget_max_ghs` (integer, optional): Maximum price per night
- `max_results` (integer, optional): Default 5

**Example**:
```json
{
  "location": "Accra",
  "accommodation_type": "hotel",
  "budget_max_ghs": 800
}
```

### 4. `get_accommodation_details`
Get full details about a specific accommodation.

**Parameters**:
- `accommodation_name` (string, required): Hotel/resort name

### 5. `get_visa_requirements`
Get visa information based on nationality.

**Parameters**:
- `nationality` (string, optional): Country of citizenship

### 6. `get_sim_card_info`
Get SIM card provider information and pricing.

**Parameters**:
- `preferred_provider` (string, optional): MTN, Vodafone, AirtelTigo

### 7. `get_safety_security_tips`
Get safety and security information.

**Parameters**:
- `category` (string, optional): general, health, road, scams

### 8. `get_emergency_contacts`
Get emergency phone numbers (police, ambulance, fire, tourist police).

**Parameters**: None

### 9. `get_currency_exchange_info`
Get currency exchange rates and information.

**Parameters**: None

### 10. `send_tourism_info_email`
Email detailed tourism information to travelers.

**Parameters**:
- `recipient_email` (string, required): Email address
- `subject` (string, required): Email subject
- `destinations` (array, optional): List of destinations to include
- `accommodations` (array, optional): List of accommodations to include
- `additional_info` (object, optional): Visa, SIM, safety info

### 11. `escalate_to_tourism_officer`
Escalate complex queries to human tourism officers.

**Parameters**:
- `issue_type` (string, required): booking, custom_itinerary, group_travel, etc.
- `description` (string, required): Query description
- `contact_info` (string, required): Caller contact details

---

## 📊 Data Sources

### Destinations (15 records)
**Greater Accra (2):**
- Kwame Nkrumah Memorial Park (historical)
- Labadi Beach (popular beach)

**Central Region (3):**
- Kakum National Park (canopy walkway)
- Cape Coast Castle (UNESCO heritage)
- Elmina Castle (UNESCO heritage)

**Ashanti Region (5) - NEW:**
- Manhyia Palace Museum (royal heritage)
- Kejetia Market (largest in West Africa)
- Lake Bosumtwi (meteorite crater lake)
- Okomfo Anokye Sword Site (legendary site)
- Asante Traditional Buildings (UNESCO)

**Other Regions (5):**
- Mole National Park (Northern, elephant viewing)
- Wli Waterfalls (Volta, highest waterfall)
- Lake Volta (Volta, boat cruises)
- Aburi Botanical Gardens (Eastern, cool climate)
- Busua Beach (Western, surfing)

### Accommodations (15 records)
**Greater Accra (4):**
- 5-star: Kempinski Hotel Gold Coast City
- 4-star: Labadi Beach Hotel, Alisa Hotels, African Regent Hotel

**Ashanti Region (5) - NEW:**
- 4-star: Golden Tulip Kumasi City, Four Villages Inn
- 3-star: Lancaster Kumasi, Miklin Hotel, Lake Bosumtwi Paradise Resort

**Other Regions (6):**
- Royal Senchi Resort, Coconut Grove Beach Resort, Zaina Lodge
- Ankobra Beach Resort, Peduase Lodge, Volta Serene Hotel

### Transportation (4 comprehensive guides)
- **Domestic Flights**: PassionAir, Africa World Airlines, 4 airports
- **Intercity Buses**: VIP, STC, OA Transport, Metro Mass Transit
- **Ride-Hailing**: Uber, Bolt, Yango (available in major cities)
- **Car Rentals & Taxis**: Budget, Europcar, traditional taxis, tips

### Restaurants (10 in Accra)
- **Ghanaian/West African**: Chez Afrique, Asanka Local
- **Nigerian**: Buka Restaurant
- **Ivorian**: Chez Clarisse
- **Ethiopian**: Azmera Restaurant
- **Italian**: Mamma Mia, Bella Roma
- **Japanese**: Santoku
- **International**: Skybar 25, Bloom Bar

### Practical Information (6 categories)
- Visa Requirements (e-visa, visa on arrival, visa-free)
- Mobile SIM Cards (MTN, Vodafone, AirtelTigo)
- Currency Exchange (Ghana Cedi rates, ATMs, payment methods)
- Safety & Security (crime, health, road safety, scams)
- Weather & Climate (seasons, what to pack)
- Cultural Etiquette (greetings, dress code, tipping)

---

## 🤖 Gemini RAG Integration

### Why Gemini RAG?

The Ghana Tourism system uses **Google Gemini 2.5 Flash** for AI-powered semantic search, providing:

- **Natural Language Understanding** - Tourists ask questions naturally, not with keywords
- **Context-Aware Responses** - AI understands intent and provides relevant information
- **100% Enhanced Responses** - Achieved 1.00 confidence score in testing
- **Voice-Optimized** - Responses designed for conversational interfaces
- **Cost-Effective** - Gemini provides excellent performance at lower cost

### RAG Architecture

```
User Query: "beaches for swimming and relaxation"
     │
     ▼
┌─────────────────────────────────────┐
│  voice_agent_tools_rag.py           │
│  (RAG-Enhanced Tools)               │
└─────────────┬───────────────────────┘
              │
              │ Query with context
              ▼
┌─────────────────────────────────────┐
│  helpdesk_rag_service                │
│  (Gemini-powered semantic search)   │
└─────────────┬───────────────────────┘
              │
              │ Vector similarity search
              ▼
┌─────────────────────────────────────┐
│  PostgreSQL + pgvector               │
│  Collection: ghana_tourism_production│
│  - 46 documents, 136 vector chunks   │
│  - 15 destination documents          │
│  - 15 accommodation documents        │
│  - 4 transportation guides           │
│  - 11 restaurant documents           │
│  - 1 practical info document         │
└─────────────────────────────────────┘
```

### Original vs RAG-Enhanced

**Original Tools (voice_agent_tools.py)**:
- Keyword-based search
- Exact string matching
- Limited natural language understanding
- Static responses

**RAG-Enhanced Tools (voice_agent_tools_rag.py)**:
- ✅ Semantic search with Gemini embeddings
- ✅ Natural language queries ("wildlife safari" → Mole National Park)
- ✅ Context-aware responses with AI insights
- ✅ Confidence scoring (achieved 1.00 in testing)
- ✅ Automatic fallback to original methods
- ✅ NEW: `get_general_tourism_guidance()` for ANY question

### RAG Performance Metrics

From testing (test_rag_tools.py):
```
✅ AI-Enhanced: 7/7 tests (100%)
✅ Confidence Score: 1.00 (perfect)
✅ Response Time: ~2-3 seconds
✅ Natural Language: Fully supported
```

Test examples:
- "I want to see wildlife and go on safari" → Mole National Park
- "beautiful beaches for swimming" → Busua Beach, Labadi Beach
- "What should I pack for rainy season?" → Detailed packing guidance
- "Important cultural customs?" → Comprehensive etiquette advice

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 12+ with pgvector extension
- MongoDB 4.4+
- Google Gemini API key (for RAG)
- VAPI API key

### 1. Install Dependencies
```bash
pip install fastapi uvicorn motor asyncpg google-generativeai langchain-google-genai
```

### 2. Set Environment Variables
```bash
export GEMINI_API_KEY="your-gemini-api-key"
export MONGODB_URL="mongodb://admin:password@localhost:27017/kasaai_core?authSource=admin"
export VAPI_API_KEY="your-vapi-key"
```

### 3. Create PostgreSQL RAG Tables
```bash
python3 apps/core_backend/backend/migrations/add_ghana_tourism_rag_tables.py
```

### 4. Index Data to RAG Knowledge Base
```bash
# For original data (25 documents)
python3 apps/automations/ghana-tourism/index_to_rag.py

# For expanded data (46 documents) - RECOMMENDED
python3 apps/automations/ghana-tourism/index_expanded_data_to_rag.py
```

Expected output (expanded):
```
📍 Destinations: 15 (original + Ashanti region)
🏨 Accommodations: 15 (original + Ashanti region)
🚗 Transportation: 4 guides (flights, buses, ride-hailing, car rentals)
🍽️  Restaurants: 11 documents (10 restaurants + dining tips)
ℹ️  Practical Info: 1 document
📊 Total Documents: 46 → 136 vector chunks
🔍 Ready for semantic search with GEMINI
```

### 5. Register Tools with MongoDB
```bash
python3 apps/automations/ghana-tourism/register_tools.py
```

### 6. Verify VAPI Registration
All 11 tools should have `vapi_tool_id`:
```python
# Check MongoDB
db.custom_tools.find({"client_id": "ghana-tourism-board"}).pretty()
```

### 7. Test RAG Integration (Optional)
```bash
python3 apps/automations/ghana-tourism/test_rag_tools.py
```

---

## 💻 Usage

### Creating a Voice Agent

1. **Via QuickAutomationDeployment UI**:
   - Navigate to B2C Portal
   - Click "Quick Deploy"
   - Select Industry: "Tourism"
   - Choose "Ghana Tourism Board" template
   - Customize system prompt (optional)
   - Deploy

2. **Via API**:
```python
import requests

response = requests.post(
    "https://api.ailabsafrica.com/automations/quick-deploy",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "name": "Ghana Tourism Agent",
        "industry": "tourism",
        "custom_tools": [
            "0f990d82-280c-4067-84f9-dac988fd2552",  # search_destinations
            "e6f657ba-f7db-4e68-908f-4066ac00b80b",  # get_destination_details
            # ... other tool IDs
        ],
        "system_prompt": "You are Akua, a Ghana Tourism Board expert..."
    }
)
```

### Testing Tools Locally

#### Using RAG-Enhanced Tools (Recommended)

```python
from apps.automations.ghana_tourism.voice_agent_tools_rag import GhanaTourismToolsRAG

tools = GhanaTourismToolsRAG()

# Natural language destination search
result = tools.search_destinations(
    query="I want to see wildlife and go on safari",
    max_results=3
)
print(result["voice_response"])
print(f"AI Enhanced: {result['ai_enhanced']}")
print(f"Confidence: {result.get('confidence_score', 0)}")

# Get visa info with AI guidance
result = tools.get_visa_requirements(nationality="United States")
print(result["voice_response"])

# Search accommodation with semantic understanding
result = tools.search_accommodation(
    location="Accra",
    accommodation_type="hotel",
    budget_max_ghs=800,
    max_results=3
)
print(result["voice_response"])

# NEW: Ask any tourism question
result = tools.get_general_tourism_guidance(
    "What should I pack for a trip to Ghana during the rainy season?"
)
print(result["voice_response"])
print(f"Confidence: {result.get('confidence_score', 0)}")
```

#### Using Original Tools (Fallback)

```python
from apps.automations.ghana_tourism.voice_agent_tools import GhanaTourismTools

tools = GhanaTourismTools()

# Traditional keyword-based search
result = tools.search_destinations(query="beaches", max_results=3)
print(result["voice_response"])
```

---

## 🌐 API Endpoints

All tools are exposed as HTTP endpoints:

```
POST /custom-tools/ghana-tourism-board/search_destinations
POST /custom-tools/ghana-tourism-board/get_destination_details
POST /custom-tools/ghana-tourism-board/search_accommodation
POST /custom-tools/ghana-tourism-board/get_accommodation_details
POST /custom-tools/ghana-tourism-board/get_visa_requirements
POST /custom-tools/ghana-tourism-board/get_sim_card_info
POST /custom-tools/ghana-tourism-board/get_safety_security_tips
POST /custom-tools/ghana-tourism-board/get_emergency_contacts
POST /custom-tools/ghana-tourism-board/get_currency_exchange_info
POST /custom-tools/ghana-tourism-board/send_tourism_info_email
POST /custom-tools/ghana-tourism-board/escalate_to_tourism_officer
```

**Authentication**: Bearer token required

---

## 🧪 Testing

### Unit Tests
```bash
pytest apps/automations/ghana-tourism/tests/
```

### Integration Tests
Test against live MongoDB and PostgreSQL:
```bash
pytest apps/automations/ghana-tourism/tests/integration/
```

### Voice Agent Tests
Test via VAPI platform or using VAPI CLI

---

## 🚢 Deployment

### Production Checklist

- [x] PostgreSQL RAG tables created
- [x] Data indexed to Gemini RAG (46 documents, 136 chunks)
- [x] Expanded data coverage (Ashanti region, transportation, restaurants)
- [x] RAG-enhanced tools implemented
- [x] Tools registered in MongoDB (11 tools)
- [x] Tools synced with VAPI (11 vapi_tool_ids)
- [x] System prompt configured
- [ ] Email service configured
- [ ] HTTPS endpoints accessible
- [ ] Rate limiting enabled
- [ ] Monitoring configured

### RAG-Specific Checklist

- [x] Gemini API key configured
- [x] helpdesk_rag_service initialized
- [x] ghana_tourism_production collection created
- [x] 46 documents indexed with embeddings (136 vector chunks)
- [x] Regional coverage: 7/16 Ghana regions (43.75%)
- [x] Transportation guide (flights, buses, ride-hailing)
- [x] Restaurant recommendations (10 Accra restaurants)
- [x] RAG tools tested (100% AI-enhanced)
- [x] Confidence scoring validated (1.00)
- [ ] Production RAG monitoring
- [ ] RAG response caching (optional)

### Monitoring

#### RAG Knowledge Base Health
```python
# Check RAG collection status
from apps.core_backend.backend.services.helpdesk_rag_service import helpdesk_rag_service

# Query test
result = await helpdesk_rag_service.query_knowledge_base(
    company_name="ghana_tourism_production",
    query="test query"
)
print(f"RAG Status: {result.success}")
print(f"Confidence: {result.confidence_score}")
```

#### MongoDB Tool Statistics
```javascript
// Check tool call statistics
db.custom_tools.aggregate([
  {$match: {client_id: "ghana-tourism-board"}},
  {$group: {_id: "$name", calls: {$sum: "$call_count"}}}
])

// Check RAG enhancement rate
db.tool_calls.aggregate([
  {$match: {client_id: "ghana-tourism-board"}},
  {$group: {
    _id: "$ai_enhanced",
    count: {$sum: 1}
  }}
])
```

#### PostgreSQL Vector Store
```sql
-- Check document count
SELECT COUNT(*) FROM langchain_pg_collection
WHERE name = 'ghana_tourism_production';

-- Check embedding dimensions
SELECT COUNT(*),
       AVG(array_length(embedding, 1)) as avg_dim
FROM langchain_pg_embedding;
```

---

## 📝 Files Structure

```
apps/automations/ghana-tourism/
├── README.md                          # This file
├── DATA_ANALYSIS.md                   # Data gaps analysis & action plan
├── voice_agent_tools.py               # Original 11 custom tools
├── voice_agent_tools_rag.py           # RAG-enhanced tools (RECOMMENDED)
├── index_to_rag.py                    # Original RAG indexing script (25 docs)
├── index_expanded_data_to_rag.py      # Expanded RAG indexing (46 docs) ✨ NEW
├── test_rag_tools.py                  # RAG integration test script
├── system_prompt_template.md          # Akua agent system prompt
├── register_tools.py                  # MongoDB registration script
├── sync_with_vapi.py                  # VAPI sync script
├── load_data_simple.py                # PostgreSQL data loader (legacy)
├── load_data_to_postgres.py           # Full data loader (legacy)
├── data/
│   ├── destinations.json              # 10 destinations (Greater Accra, Central, etc.)
│   ├── accommodations.json            # 10 accommodations (various regions)
│   ├── ashanti_region.json            # 5 destinations + 5 accommodations ✨ NEW
│   ├── transportation.json            # Comprehensive transport guide ✨ NEW
│   ├── restaurants.json               # 10 Accra restaurants + tips ✨ NEW
│   └── practical_info.json            # 6 practical info categories
└── tests/
    ├── test_tools.py                  # Unit tests
    └── integration/
        └── test_rag_search.py         # RAG integration tests
```

---

## 🎯 VAPI Tool IDs

```
search_destinations          → 0f990d82-280c-4067-84f9-dac988fd2552
get_destination_details      → e6f657ba-f7db-4e68-908f-4066ac00b80b
search_accommodation         → 3db2b3cd-daf8-491d-8daa-b746b1d150b2
get_accommodation_details    → 7e50fda0-71b5-4929-8d52-32bf66caf801
get_visa_requirements        → 764c2704-ff9d-4204-a8aa-9df77f0478bb
get_sim_card_info            → ae49d7ee-9773-45ea-916d-e8c86026c1e8
get_safety_security_tips     → fca1e36b-dfd3-4494-b391-e75e66dbc4db
get_emergency_contacts       → 65da87ab-b833-4a7f-8ada-f669b89b0ee4
get_currency_exchange_info   → 84d0f207-606b-4a03-8a9b-2ceff3e669d2
send_tourism_info_email      → a5af2e8f-9fd2-4599-93ad-b5128a6916f5
escalate_to_tourism_officer  → 98c59c0c-d4ee-4890-86a0-de31fd3bf49b
```

---

## 📚 Additional Resources

- [Ghana Tourism Authority](https://www.visitghana.com)
- [Ghana Immigration Service](https://www.immigration.gov.gh)
- [VAPI Documentation](https://docs.vapi.ai)
- [pgvector Documentation](https://github.com/pgvector/pgvector)

---

## 🤝 Support

For issues or questions:
- Email: support@ailabsafrica.com
- GitHub Issues: [kasaai/issues](https://github.com/ailabsafrica/kasaai/issues)

---

## 📄 License

Copyright © 2025 AI Labs Africa. All rights reserved.

---

**Built with ❤️ by AI Labs Africa for Ghana Tourism Board**

*Akwaaba! Welcome to Ghana!* 🇬🇭
