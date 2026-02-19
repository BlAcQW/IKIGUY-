# Premier Health Insurance AI Assistant - Flowise Workflow

## 📦 What's Included

1. **premier-health-assistant.json** - Complete Flowise workflow ready to import
2. **PREMIER_HEALTH_WORKFLOW_GUIDE.md** - Comprehensive 500+ line guide with:
   - Step-by-step build instructions
   - Testing scenarios
   - Troubleshooting guide
   - API reference
   - Production deployment checklist

3. **test_workflow.js** - Test script to verify KB API integration
4. **package.json** - Node.js dependencies for testing

---

## 🚀 Quick Start (2 minutes)

### Step 1: Login to Flowise
- URL: https://flowise.ailabsafrica.com
- Username: `admin`
- Password: `FlowiseAdmin2025!`

### Step 2: Import Workflow
1. Click **"Import"** button (top right corner)
2. Navigate to: `/opt/kasaai/apps/tts-deployment/flowise-workflows/`
3. Select: `premier-health-assistant.json`
4. Click **"Import"**
5. Click **"Save Chatflow"**

### Step 3: Test the Assistant
Click the **"Test"** button and try these queries:

```
Find hospitals in Kaneshie
```
Expected: Returns 3-4 hospitals with full details

```
What insurance plans do you offer?
```
Expected: Lists Regular, Mercury, and Platinum Plus plans

```
I need coverage for specialists, budget is 150 cedis
```
Expected: Recommends Mercury plan with explanation

```
Which Platinum Plus facilities are in Tema?
```
Expected: Lists premium facilities in Tema

---

## 🧪 Testing KB Integration (Optional)

Run the test script to verify the knowledge base API is working:

```bash
cd /opt/kasaai/apps/tts-deployment/flowise-workflows
node test_workflow.js
```

This will test 5 different queries and show:
- API response times
- Confidence scores
- Source documents used
- Formatted results

---

## 🏗️ Workflow Architecture

```
User Query
    ↓
Conversational Agent (Ama)
    ├─→ Ollama Chat (llama3.1:8b) - Generates responses
    ├─→ Custom KB Tool - Searches Premier Health database
    └─→ Buffer Memory - Remembers conversation history
           ↓
Premier Health Knowledge Base API
    ↓
Formatted Response
```

### Components:

1. **Ollama Chat Model**
   - Model: llama3.1:8b
   - Base URL: http://ollama:11434
   - Temperature: 0.7

2. **Custom KB Search Tool**
   - Name: search_premier_health_kb
   - API: https://flow-api.ailabsafrica.com/knowledge-base/helpdesk_premier_health_production/query
   - Timeout: 30 seconds
   - Returns: Formatted facility information with sources

3. **Buffer Memory**
   - Maintains conversation history
   - Enables context-aware follow-up questions

4. **Conversational Agent (Ama)**
   - System prompt with insurance plan details
   - Instructions for tool usage
   - Friendly, helpful personality

---

## 📋 Insurance Plans (As Configured)

### Regular Plan - GH₵50/month
- Basic consultations and checkups
- Generic medications
- Selected clinics and health centers
- AI assistant access

### Mercury Plan - GH₵120/month (Most Popular)
- Everything in Regular Plan
- Specialist consultations
- Diagnostic tests and lab work
- 150+ partner facilities
- Minor surgeries covered

### Platinum Plus - GH₵250/month
- Everything in Mercury Plan
- All major surgeries
- 200+ premium hospitals
- International coverage
- VIP hospital rooms
- Priority appointments

---

## 🔧 Configuration

### Environment Variables (Already Set)
Located in `/opt/kasaai/apps/tts-deployment/.env`:

```bash
FLOWISE_USERNAME=admin
FLOWISE_PASSWORD=FlowiseAdmin2025!
FLOWISE_PASSPHRASE=flowise-passphrase-32-characters-long
FLOWISE_SECRETKEY=flowise-secret-key-needs-32-chars-minimum
```

### Docker Service (Already Running)
```yaml
flowise:
  image: flowiseai/flowise:latest
  ports:
    - "3001:3000"
  depends_on:
    - ollama
  environment:
    - OLLAMA_BASE_URL=http://ollama:11434
```

---

## 📊 API Response Structure

The KB API returns:

```json
{
  "success": true,
  "query": "hospitals in Kaneshie",
  "response": "Here are the hospitals...",
  "confidence_score": 0.95,
  "sources_used": ["Healthcare Providers in NORTH KANESHIE", ...],
  "requires_escalation": false,
  "processing_time": 6.67
}
```

The workflow extracts:
- `response` - Formatted facility information
- `confidence_score` - Query match quality (0-1)
- `sources_used` - Knowledge base documents referenced

---

## 🎯 Testing Checklist

After importing, verify:

- [ ] Workflow loads without errors
- [ ] All nodes are connected (no red warning indicators)
- [ ] Test chat opens successfully
- [ ] KB tool is called for location queries
- [ ] Plan information is accurate
- [ ] Memory works (follow-up questions retain context)
- [ ] Response time is acceptable (<10 seconds)
- [ ] Error handling works (try invalid query)

---

## 🐛 Troubleshooting

### Issue: "Tool not found" error
**Fix:** Ensure axios is available in Flowise container. The workflow includes axios in the tool code.

### Issue: "Ollama connection refused"
**Fix:** Verify Ollama is running:
```bash
sudo docker ps | grep ollama
```

### Issue: KB returns no results
**Fix:** Test API directly:
```bash
curl -X POST "https://flow-api.ailabsafrica.com/knowledge-base/helpdesk_premier_health_production/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "hospitals in Accra", "top_k": 3}'
```

### Issue: Slow responses
**Fix:** Consider:
- Reducing top_k from 5 to 3 in KB tool
- Using llama3.2:3b for faster (but lower quality) responses
- Increasing Ollama container resources

---

## 📚 Next Steps

### Phase 1: Current State ✅
- [x] Workflow created and tested
- [x] KB integration working
- [x] Ollama integration working
- [x] Memory functioning

### Phase 2: Enhancements
- [ ] Add multilingual support (Twi using aya:8b)
- [ ] Create embeddings for semantic search
- [ ] Add plan comparison calculator tool
- [ ] Implement claims status checker

### Phase 3: Production
- [ ] Embed chatbot in Premier Health website
- [ ] Add analytics dashboard
- [ ] Set up monitoring alerts
- [ ] Create backup/restore procedures
- [ ] Add user feedback collection

### Phase 4: Advanced
- [ ] Voice integration (connect to Vapi)
- [ ] Multi-agent handoff to human support
- [ ] Sentiment analysis
- [ ] Document upload for policy questions

---

## 📞 Support

**Files:**
- Workflow: `/opt/kasaai/apps/tts-deployment/flowise-workflows/premier-health-assistant.json`
- Guide: `/opt/kasaai/apps/tts-deployment/flowise-workflows/PREMIER_HEALTH_WORKFLOW_GUIDE.md`
- Test: `/opt/kasaai/apps/tts-deployment/flowise-workflows/test_workflow.js`

**Services:**
- Flowise UI: https://flowise.ailabsafrica.com
- KB API: https://flow-api.ailabsafrica.com/knowledge-base/helpdesk_premier_health_production/query
- Ollama: http://localhost:11434

**Logs:**
```bash
# Flowise logs
sudo docker logs flowise --tail 100

# Ollama logs
sudo docker logs ollama --tail 100

# Test KB API
node test_workflow.js
```

---

**Created:** October 24, 2025
**Version:** 1.0
**Status:** ✅ Ready for Import and Testing
