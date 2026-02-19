# Premier Health Insurance Assistant - Flowise Workflow Guide

## 🎯 Overview

This workflow creates an AI assistant named "Ama" that can:
- Answer questions about Premier Health insurance plans
- Search the knowledge base for hospitals and providers
- Remember conversation context
- Provide personalized recommendations

## 📋 Prerequisites

- ✅ Flowise running at https://flowise.ailabsafrica.com
- ✅ Ollama with llama3.1:8b model
- ✅ Premier Health KB API accessible
- ✅ Login credentials: admin / FlowiseAdmin2025!

---

## 🚀 Quick Start: Import Pre-built Workflow

### Option 1: Import JSON (Fastest - 2 minutes)

1. **Login to Flowise**: https://flowise.ailabsafrica.com
2. **Click "Import"** (top right)
3. **Select file**: `/opt/kasaai/apps/tts-deployment/flowise-workflows/premier-health-assistant.json`
4. **Click "Import"**
5. **Save** the workflow
6. **Test** with sample queries

### Option 2: Build Manually (Recommended for Learning - 15 minutes)

Follow the step-by-step guide below.

---

## 🔨 Manual Build Instructions

### Step 1: Create New Chatflow

1. Login to https://flowise.ailabsafrica.com
2. Click **"+ Add New Chatflow"**
3. Name it: **"Premier Health Assistant"**

### Step 2: Add Ollama Chat Model

**Action:**
- Drag **"Chat Ollama"** from left sidebar (Chat Models section)
- Place it in the canvas

**Configuration:**
```
Model Name: llama3.1:8b
Base URL: http://ollama:11434
Temperature: 0.7
```

**Why this model?**
- llama3.1:8b provides good quality responses
- Fast enough for real-time chat
- Handles insurance domain well

---

### Step 3: Create Knowledge Base Search Tool

**Action:**
- Drag **"Custom Tool"** from left sidebar (Tools section)

**Configuration:**

**Tool Name:**
```
search_premier_health_kb
```

**Tool Description:**
```
Search the Premier Health Insurance knowledge base for information about healthcare providers, hospitals, insurance plans, coverage details, and locations. Input should be a search query in natural language.
```

**JavaScript Code:**
```javascript
const axios = require('axios');

// Function to query Premier Health knowledge base
const searchKnowledgeBase = async (query) => {
    try {
        console.log(`Searching Premier Health KB for: ${query}`);

        const response = await axios.post(
            'https://flow-api.ailabsafrica.com/knowledge-base/helpdesk_premier_health_production/query',
            {
                query: query,
                top_k: 5  // Return top 5 results
            },
            {
                headers: {
                    'Content-Type': 'application/json'
                },
                timeout: 30000  // 30 second timeout
            }
        );

        // API returns {success, response, confidence_score, sources_used, etc}
        if (response.data && response.data.success && response.data.response) {
            const result = response.data.response;
            const confidence = response.data.confidence_score || 0;
            const sources = response.data.sources_used || [];

            console.log(`KB returned results with confidence: ${confidence}`);

            // Return the formatted response from the API
            let output = result;

            // Add source information if available
            if (sources.length > 0) {
                output += `\n\nSources: ${sources.join(', ')}`;
            }

            return output;
        } else if (response.data && response.data.error_message) {
            return `KB Error: ${response.data.error_message}`;
        } else {
            return 'No information found in the knowledge base for this query.';
        }
    } catch (error) {
        console.error('Error querying knowledge base:', error.message);

        // Provide helpful error messages
        if (error.code === 'ECONNABORTED') {
            return 'Search timed out. Please try a more specific query.';
        }
        if (error.response) {
            return `KB Error: ${error.response.status} - ${error.response.statusText}`;
        }
        return `Error searching knowledge base: ${error.message}`;
    }
};

// Execute search with the input query
return await searchKnowledgeBase($input);
```

**What this does:**
- Connects to Premier Health knowledge base API
- Searches for relevant information
- Returns formatted results
- Handles errors gracefully

---

### Step 4: Add Memory

**Action:**
- Drag **"Buffer Memory"** from left sidebar (Memory section)

**Configuration:**
```
Memory Key: chat_history
Session ID: (leave default)
```

**Why Memory?**
- Remembers previous messages in conversation
- Enables follow-up questions
- Provides context-aware responses

---

### Step 5: Create Conversational Agent

**Action:**
- Drag **"Conversational Agent"** from left sidebar (Agents section)

**Connect Components:**
1. Connect **Ollama Chat** output → Agent's "Chat Model" input
2. Connect **Custom Tool** output → Agent's "Tools" input
3. Connect **Buffer Memory** output → Agent's "Memory" input

**System Message:**
```
You are Ama, a helpful Premier Health Insurance assistant. Your role is to help users find healthcare providers, understand insurance plans, and answer questions about coverage.

AVAILABLE INSURANCE PLANS:
• Regular Plan (GH₵50/month)
  - Basic consultations and checkups
  - Generic medications
  - Selected clinics and health centers
  - AI assistant access

• Mercury Plan (GH₵120/month) [MOST POPULAR]
  - Everything in Regular Plan
  - Specialist consultations
  - Diagnostic tests and lab work
  - 150+ partner facilities
  - Minor surgeries covered

• Platinum Plus (GH₵250/month)
  - Everything in Mercury Plan
  - All major surgeries
  - 200+ premium hospitals
  - International coverage
  - VIP hospital rooms
  - Priority appointments

INSTRUCTIONS:
1. When users ask about HOSPITALS/PROVIDERS: Use the search_premier_health_kb tool to find specific facilities and locations
2. When users ask about INSURANCE PLANS: Explain the plans above and help them choose based on their needs and budget
3. When users ask about COVERAGE: Provide clear information about what each plan covers
4. When users mention LOCATIONS: Use the tool to search for providers in specific areas

COMMUNICATION STYLE:
- Be friendly and conversational
- Use simple, clear language
- Ask clarifying questions when needed
- Provide specific recommendations
- Always verify information using the knowledge base tool when available

EXAMPLE INTERACTIONS:
User: "Find hospitals in Kaneshie"
You: Use search_premier_health_kb("Healthcare providers in Kaneshie"), then summarize results clearly

User: "What plan should I get for my family?"
You: Ask about family size, budget, and health needs, then recommend appropriate plan

User: "Is maternity covered?"
You: Explain coverage across different plans
```

---

### Step 6: Save and Test

**Action:**
1. Click **"Save Chatflow"** (top right)
2. Click **"Test"** button (bottom right)

**Test Queries:**

1. **Basic Query:**
   ```
   What insurance plans do you offer?
   ```
   **Expected:** Lists all 3 plans with prices

2. **Knowledge Base Search:**
   ```
   Find hospitals in Kaneshie
   ```
   **Expected:** Uses tool, returns actual facilities from KB

3. **Complex Query:**
   ```
   I need insurance for specialists, budget is 150 cedis
   ```
   **Expected:** Recommends Mercury plan, explains why

4. **Follow-up (tests memory):**
   ```
   What about dental coverage?
   ```
   **Expected:** Remembers context, explains dental coverage in recommended plan

5. **Location-specific:**
   ```
   Which Platinum Plus facilities are in Tema?
   ```
   **Expected:** Uses KB tool, returns Tema facilities

---

## 🎨 Workflow Diagram

```
┌─────────────────┐
│  User Query     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Conversational Agent              │
│   (Ama - Insurance Assistant)       │
│                                     │
│   System Instructions:              │
│   - Help with insurance plans      │
│   - Find healthcare providers      │
│   - Answer coverage questions      │
└─────┬────────────┬─────────┬───────┘
      │            │         │
      │            │         │
┌─────▼──────┐ ┌──▼─────┐ ┌─▼────────────┐
│ Ollama     │ │ Custom │ │ Buffer       │
│ llama3.1   │ │ Tool   │ │ Memory       │
│            │ │  KB    │ │              │
│ Generates  │ │Search  │ │ Remembers    │
│ responses  │ │        │ │ conversation │
└────────────┘ └──┬─────┘ └──────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Premier Health │
         │ Knowledge Base │
         │ API            │
         └────────────────┘
```

---

## 🧪 Testing Scenarios

### Scenario 1: Plan Comparison
```
User: "Compare all your plans for me"
Expected:
- Lists all 3 plans with clear differences
- Highlights Mercury as most popular
- Asks about user's specific needs
```

### Scenario 2: Hospital Search
```
User: "I'm looking for a hospital in Accra that takes Mercury plan"
Expected:
- Uses KB search tool
- Returns specific hospitals in Accra
- Mentions which accept Mercury plan
```

### Scenario 3: Budget-based Recommendation
```
User: "I have 100 cedis per month, what can I get?"
Expected:
- Recommends Regular plan (50 cedis)
- Explains what's covered
- Mentions Mercury is available with more budget
```

### Scenario 4: Multi-turn Conversation
```
User: "What's the Mercury plan?"
Ama: [Explains Mercury plan]
User: "How much is it?"
Ama: [Remembers context, says 120 cedis]
User: "What hospitals accept it?"
Ama: [Uses KB to find Mercury-accepting hospitals]
```

---

## 🔧 Troubleshooting

### Issue: Tool not being called

**Symptoms:** Agent doesn't search KB even when asked about locations

**Solution:**
1. Check tool description is clear
2. Verify API endpoint is accessible
3. Test tool independently first
4. Make system message more explicit about when to use tool

### Issue: Generic responses

**Symptoms:** Agent gives general info instead of specific KB data

**Solution:**
1. Strengthen system message instructions
2. Add examples in system prompt
3. Lower temperature (0.5 instead of 0.7)

### Issue: KB API errors

**Symptoms:** Tool returns errors or timeouts

**Solution:**
```bash
# Test API directly
curl -X POST https://flow-api.ailabsafrica.com/knowledge-base/helpdesk_premier_health_production/query \
  -H "Content-Type: application/json" \
  -d '{"query": "hospitals in Accra"}'
```

### Issue: Memory not working

**Symptoms:** Agent doesn't remember previous messages

**Solution:**
1. Verify Buffer Memory is connected
2. Check Session ID is consistent
3. Test with explicit follow-up questions

---

## 📊 Performance Optimization

### Speed Improvements
- Use llama3.2:3b for faster responses (lower quality)
- Reduce top_k in KB search from 5 to 3
- Add caching for common queries

### Quality Improvements
- Increase temperature to 0.9 for more creative responses
- Add few-shot examples in system prompt
- Use RAG (Retrieval Augmented Generation) for better KB integration

### Cost Optimization
- Self-hosted Ollama = Free
- KB API calls = Track usage
- Consider caching frequent queries

---

## 🚀 Next Steps

### Phase 1: Basic Deployment (Now)
✅ Import workflow
✅ Test functionality
✅ Validate KB integration

### Phase 2: Enhancement (This Week)
- [ ] Add multilingual support (Twi using aya:8b model)
- [ ] Create embeddings for better KB search
- [ ] Add more tools (plan calculator, claims checker)

### Phase 3: Production (Next Week)
- [ ] Embed chatbot in Premier Health website
- [ ] Add analytics and logging
- [ ] Set up monitoring and alerts
- [ ] Create backup/export procedures

### Phase 4: Advanced Features (This Month)
- [ ] Voice integration (connect to Vapi)
- [ ] Document upload for policy questions
- [ ] Multi-agent workflows (handoff to human)
- [ ] Sentiment analysis and feedback loop

---

## 📝 API Reference

### Knowledge Base Query API

**Endpoint:**
```
POST https://flow-api.ailabsafrica.com/knowledge-base/helpdesk_premier_health_production/query
```

**Request:**
```json
{
  "query": "hospitals in Kaneshie",
  "top_k": 5
}
```

**Response:**
```json
{
  "success": true,
  "query": "hospitals in Kaneshie",
  "response": "Here are the hospitals and clinics located in the Kaneshie region:\n\n* **EDEN FAMILY HOSPITAL**\n  * **Specialties**: GP/OBS/GYN/PED\n  * **Phone**: 0302-224984\n  * **Location**: NORTH KANESHIE OFF ST. THERESA'S RD\n\n* **LAKESIDE CLINIC**\n  * **Specialties**: GP/OBS/GYN/PED\n  * **Phone**: 0302-230496/0302-253902\n  * **Location**: MOKOSE LINK, NORTH INDUSTRIAL AREA",
  "confidence_score": 0.95,
  "sources_used": [
    "Healthcare Providers in NORTH KANESHIE",
    "Healthcare Providers in INDUSTRIAL AREA",
    "Healthcare Providers in KANESHIE"
  ],
  "requires_escalation": false,
  "escalation_reason": null,
  "context_used": false,
  "processing_time": 6.67,
  "error_message": null
}
```

---

## 💡 Tips & Best Practices

1. **System Prompts:**
   - Be specific about tool usage
   - Include examples
   - Define conversation style clearly

2. **Tool Design:**
   - Single responsibility
   - Clear input/output
   - Robust error handling

3. **Testing:**
   - Test happy paths and edge cases
   - Verify tool calls are made when appropriate
   - Check memory retention

4. **Monitoring:**
   - Log all KB searches
   - Track response quality
   - Monitor latency

---

## 📞 Support

**Issues with workflow:**
- Check Flowise logs: `sudo docker logs flowise --tail 100`
- Test KB API independently
- Verify Ollama is running: `sudo docker ps | grep ollama`

**Need help?**
- Flowise docs: https://docs.flowiseai.com
- Premier Health KB API issues: Check flow-api logs

---

## ✅ Checklist

Before going live:
- [ ] Workflow imported and tested
- [ ] KB API returning valid results
- [ ] Ollama responding correctly
- [ ] Memory working (test multi-turn conversation)
- [ ] All 3 insurance plans accurately described
- [ ] Error handling tested
- [ ] Performance acceptable (<3s response time)
- [ ] Ready for embedding in website

---

**Created:** October 24, 2025
**Version:** 1.0
**Flowise URL:** https://flowise.ailabsafrica.com
**KB API:** https://flow-api.ailabsafrica.com/knowledge-base/helpdesk_premier_health_production/query
