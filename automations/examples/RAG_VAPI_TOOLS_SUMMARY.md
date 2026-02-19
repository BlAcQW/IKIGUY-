# RAG Knowledge Base VAPI Tools Summary

**Created:** October 15, 2025
**Status:** ✅ Successfully Registered on VAPI Platform

## Overview

Two new VAPI tools have been created to enable voice assistants to query Knowledge Base RAG systems for Premier Health and Ghana Tourism Board. These tools provide intelligent, context-aware responses using Gemini 2.5 Flash LLM.

---

## 1. Premier Health RAG Tool

### Tool Details
- **Tool ID:** `560adfee-43bf-4614-baa8-0d5ccfbe9769`
- **Function Name:** `query_premier_health_knowledge_base`
- **Server URL:** `https://flow-api.ailabsafrica.com/knowledge-base/premier_health_production/query`
- **Timeout:** 20 seconds
- **Type:** Synchronous (async: false)

### Description
Query the Premier Health Insurance knowledge base for comprehensive information about healthcare providers, medical services, insurance coverage, and facilities in Ghana. Use this when customers ask about doctors, hospitals, clinics, medical specialists, provider locations, or insurance coverage details. This tool uses advanced RAG (Retrieval Augmented Generation) to provide accurate, up-to-date information from the Premier Health provider network.

### Parameters

```json
{
  "query": {
    "type": "string",
    "required": true,
    "description": "Natural language search query",
    "examples": [
      "Find me doctors in Madina",
      "Are there pediatricians near East Legon?",
      "Emergency hospitals in Accra",
      "What specialties does Premier Health cover?"
    ]
  },
  "company_name": {
    "type": "string",
    "required": false,
    "default": "premier_health_production",
    "description": "Company identifier for the knowledge base"
  }
}
```

### User Messages
- **Request Start:** "Searching Premier Health knowledge base..."
- **Request Complete:** "Found relevant information from Premier Health."
- **Request Failed:** "I couldn't access the Premier Health database. Let me try to help you another way."

### Knowledge Base Statistics
- **Total Documents:** 296 documents
- **Collections:** helpdesk_premier_health_production
- **Vector Store:** PostgreSQL + pgvector
- **LLM:** Google Gemini 2.5 Flash
- **Embeddings:** Google Gemini embedding-001
- **Response Format:** Confidence scores, sources, escalation flags

### Usage Examples

**Example 1: Find doctors by location**
```
User: "Are there any doctors in Madina?"
Assistant: [Calls query_premier_health_knowledge_base]
  query: "doctors in madina"
Response: Detailed list of doctors in Madina with specialties, locations, and contact info
```

**Example 2: Specialty search**
```
User: "I need a pediatrician"
Assistant: [Calls query_premier_health_knowledge_base]
  query: "pediatrician"
Response: List of pediatricians with locations and availability
```

**Example 3: Emergency services**
```
User: "Where is the nearest emergency hospital?"
Assistant: [Calls query_premier_health_knowledge_base]
  query: "emergency hospital near me"
Response: Emergency hospitals with 24/7 service, locations, and phone numbers
```

---

## 2. Ghana Tourism Board RAG Tool

### Tool Details
- **Tool ID:** `2bac26dc-5f8e-4d3d-82b2-ca55286ddf36`
- **Function Name:** `query_ghana_tourism_knowledge_base`
- **Server URL:** `https://flow-api.ailabsafrica.com/knowledge-base/ghana_tourism_board/query`
- **Timeout:** 20 seconds
- **Type:** Synchronous (async: false)

### Description
Query the Ghana Tourism Board knowledge base for comprehensive travel information including tourist destinations, attractions, accommodations, cultural sites, travel requirements, safety information, and practical travel tips for Ghana. Use this when travelers ask about places to visit, hotels, tourist attractions, visa requirements, local customs, safety tips, or general travel information about Ghana. This tool uses RAG technology to provide accurate, detailed tourism information.

### Parameters

```json
{
  "query": {
    "type": "string",
    "required": true,
    "description": "Natural language search query",
    "examples": [
      "What are the best tourist attractions in Ghana?",
      "Tell me about hotels in Cape Coast",
      "What are the visa requirements for Ghana?",
      "Cultural sites to visit in Kumasi"
    ]
  },
  "company_name": {
    "type": "string",
    "required": false,
    "default": "ghana_tourism_board",
    "description": "Company identifier for the knowledge base"
  }
}
```

### User Messages
- **Request Start:** "Searching Ghana Tourism Board information..."
- **Request Complete:** "Found relevant tourism information about Ghana."
- **Request Failed:** "I couldn't access the tourism database right now. Let me provide general information instead."

### Knowledge Base Statistics
- **Collection:** helpdesk_ghana_tourism_board
- **Vector Store:** PostgreSQL + pgvector
- **LLM:** Google Gemini 2.5 Flash
- **Embeddings:** Google Gemini embedding-001
- **Coverage:** Major tourist destinations, accommodations, practical information

### Usage Examples

**Example 1: Destination information**
```
User: "What are the best places to visit in Ghana?"
Assistant: [Calls query_ghana_tourism_knowledge_base]
  query: "best places to visit in Ghana"
Response: Top tourist destinations with descriptions, activities, and recommendations
```

**Example 2: Accommodation search**
```
User: "Can you recommend hotels in Accra?"
Assistant: [Calls query_ghana_tourism_knowledge_base]
  query: "hotels in Accra"
Response: List of hotels with ratings, amenities, locations, and price ranges
```

**Example 3: Travel requirements**
```
User: "Do I need a visa to visit Ghana?"
Assistant: [Calls query_ghana_tourism_knowledge_base]
  query: "visa requirements for Ghana"
Response: Comprehensive visa information including requirements by nationality
```

---

## Technical Architecture

### RAG Query Endpoint

**Endpoint:** `POST https://flow-api.ailabsafrica.com/knowledge-base/{collection_name}/query`

**Request Format:**
```json
{
  "query": "natural language question",
  "company_name": "collection_identifier"
}
```

**Response Format:**
```json
{
  "success": true,
  "query": "original query",
  "response": "AI-generated response based on knowledge base",
  "confidence_score": 0.95,
  "sources_used": [
    "Document Title 1",
    "Document Title 2"
  ],
  "requires_escalation": false,
  "escalation_reason": null,
  "context_used": false,
  "processing_time": 5.2,
  "error_message": null
}
```

### LLM Configuration

**Primary LLM:** Google Gemini 2.5 Flash
- **Model:** gemini-2.5-flash
- **Temperature:** 0.1
- **Provider:** Google Generative AI

**Embeddings:** Google Gemini embedding-001
- **Dimension:** 1536
- **Model:** models/embedding-001

**Vector Store:** PostgreSQL + pgvector
- **Database:** kasaai_core (PostgreSQL 14+)
- **Extension:** pgvector
- **Collection Naming:** helpdesk_{company_name}

### Service Location
- **Backend:** `/opt/kasaai/apps/core_backend/backend/services/helpdesk_rag_service.py`
- **Routes:** `/opt/kasaai/apps/core_backend/backend/routes/knowledge_base.py`
- **Service:** kasaai-core-backend.service

---

## VAPI Integration

### Adding Tools to VAPI Assistant

To use these tools with a VAPI assistant, add the tool IDs to your assistant configuration:

```json
{
  "model": {
    "toolIds": [
      "560adfee-43bf-4614-baa8-0d5ccfbe9769",  // Premier Health RAG
      "2bac26dc-5f8e-4d3d-82b2-ca55286ddf36"   // Ghana Tourism RAG
    ]
  }
}
```

### Using VAPI CLI

```bash
# Set API key
export VAPI_API_KEY=42cf1e7c-2ef9-4bd7-ba30-52f2813605a2

# View Premier Health tool
curl -X GET "https://api.vapi.ai/tool/560adfee-43bf-4614-baa8-0d5ccfbe9769" \
  -H "Authorization: Bearer $VAPI_API_KEY"

# View Ghana Tourism tool
curl -X GET "https://api.vapi.ai/tool/2bac26dc-5f8e-4d3d-82b2-ca55286ddf36" \
  -H "Authorization: Bearer $VAPI_API_KEY"
```

---

## Testing

### Test Premier Health RAG Tool

```bash
curl -X POST "https://flow-api.ailabsafrica.com/knowledge-base/premier_health_production/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "doctors in madina",
    "company_name": "premier_health_production"
  }'
```

### Test Ghana Tourism RAG Tool

```bash
curl -X POST "https://flow-api.ailabsafrica.com/knowledge-base/ghana_tourism_board/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tourist attractions in ghana",
    "company_name": "ghana_tourism_board"
  }'
```

---

## Files Created

1. **Registration Script:** `/opt/kasaai/apps/automations/examples/register_rag_vapi_tools.py`
   - Python script to register tools on VAPI platform
   - Can be re-run to update tool configurations

2. **Registration Results:** `/opt/kasaai/apps/automations/examples/rag_tools_registration_result.json`
   - JSON file with tool IDs and registration status

3. **This Summary:** `/opt/kasaai/apps/automations/examples/RAG_VAPI_TOOLS_SUMMARY.md`
   - Complete documentation of the tools

---

## Next Steps

### 1. Add Tools to Existing VAPI Assistants

Update your Premier Health assistant:
```bash
# Get current assistant config
curl -X GET "https://api.vapi.ai/assistant/{assistant_id}" \
  -H "Authorization: Bearer $VAPI_API_KEY"

# Update with new tool ID
# Add "560adfee-43bf-4614-baa8-0d5ccfbe9769" to model.toolIds array
```

### 2. Test Voice Conversations

Make test calls to verify the tools work correctly:
- Ask about doctors in specific locations
- Query for tourist destinations
- Test error handling with obscure queries

### 3. Monitor Performance

Check Knowledge Base query logs:
- Response times
- Confidence scores
- Escalation rates
- Most common queries

### 4. Expand Knowledge Bases

Add more documents to improve coverage:
- Premier Health: More providers, services, coverage details
- Tourism: Additional destinations, seasonal information, cultural events

---

## Support

For issues or questions:
- **Backend Logs:** `sudo journalctl -u kasaai-core-backend -f`
- **Knowledge Base Admin:** https://api.ailabsafrica.com/knowledge-base/
- **VAPI Dashboard:** https://dashboard.vapi.ai/
- **API Documentation:** https://docs.vapi.ai/

---

## Changelog

**2025-10-15:**
- ✅ Created `query_premier_health_knowledge_base` tool
- ✅ Created `query_ghana_tourism_knowledge_base` tool
- ✅ Registered both tools on VAPI platform
- ✅ Verified tool configurations
- ✅ Fixed RAG service to use Gemini 2.5 Flash instead of Anthropic
- ✅ Tested end-to-end query flow

---

**Status:** 🟢 Production Ready
