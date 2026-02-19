# VAPI Squad Quick Start Guide

**5-Minute Guide to Deploying Premier Health Multi-Assistant Squad**

---

## What This Does

Solves Deepgram's 100 keyterm limit by creating:
- **1 Router** → Asks which region → Transfers to specialist
- **6 Regional Assistants** → Each handles 30-96 cities in their region
- **Total Coverage:** All 324 cities across Ghana

---

## Quick Deploy

```bash
cd /opt/kasaai/apps/automations/premier-health

# 1. Generate configurations (already done ✓)
python3 squad_assistants_config.py

# 2. Deploy to VAPI
python3 deploy_squad.py
# Choose option 1: Deploy complete squad

# 3. Test
python3 test_squad.py

# 4. Get squad ID from deployment_record.json
cat deployment_record.json | grep squad_id
```

---

## Files Created

✅ **7 Assistant Configs:**
- `config_router_assistant.json` (router)
- `config_greater_accra_assistant.json` (96 cities)
- `config_ashanti_assistant.json` (70 cities)
- `config_northern_regions_assistant.json` (30 cities)
- `config_western_and_central_assistant.json` (51 cities)
- `config_eastern_and_volta_assistant.json` (41 cities)
- `config_bono_bono_east_and_ahafo_assistant.json` (36 cities)

✅ **Squad Config:**
- `config_squad_template.json`

✅ **Scripts:**
- `deploy_squad.py` - Deploys everything
- `test_squad.py` - Validates deployment

---

## Test It

### Via VAPI Dashboard
1. Go to https://dashboard.vapi.ai/squads
2. Find "Premier Health Navigator Squad"
3. Click "Test Call"
4. Say: "I'm in Madina and need a doctor"
5. Should transfer to Greater Accra assistant → Find Madina providers

### Test Scenarios
| Say This | Router Transfers To | Expected Result |
|----------|-------------------|-----------------|
| "I'm in Madina" | Greater Accra | Finds Madina facilities |
| "I'm in Kumasi" | Ashanti | Finds Kumasi facilities |
| "I'm from Tamale" | Northern Regions | Finds Tamale facilities |
| "I'm in Takoradi" | Western/Central | Finds Takoradi facilities |
| "I'm in Ho" | Eastern/Volta | Finds Ho facilities |
| "I'm from Sunyani" | Bono | Finds Sunyani facilities |

---

## Regional Coverage

| Region | Cities | Example Cities |
|--------|--------|----------------|
| **Greater Accra** | 96 | Accra, Tema, Madina, Legon, Dansoman |
| **Ashanti** | 70 | Kumasi, Obuasi, Mampong, Tafo |
| **Northern** | 30 | Tamale, Bolgatanga, Wa, Bawku |
| **Western/Central** | 51 | Takoradi, Sekondi, Cape Coast |
| **Eastern/Volta** | 41 | Koforidua, Ho, Hohoe, Nkawkaw |
| **Bono/Ahafo** | 36 | Sunyani, Techiman, Berekum |
| **TOTAL** | **324** | All Ghana cities covered ✓ |

---

## How It Works

```
User Calls
    ↓
Router: "Which region?"
    ↓
User: "I'm in Madina"
    ↓
Router: [Detects "Madina" → Greater Accra region]
    ↓
Router: "Connecting to Greater Accra specialist..."
    ↓
[TRANSFER - Context preserved]
    ↓
Greater Accra Assistant: "Hello! How can I help you in Greater Accra?"
    ↓
User: "I need a general practitioner"
    ↓
Greater Accra Assistant: [Uses RAG with 96 Accra-area city keywords]
    ↓
"I found 7 general practitioners in Madina. Here are the first three..."
```

---

## Cost

| Calls/Month | Cost/Month | Notes |
|-------------|-----------|-------|
| 1,000 | $100 | Small scale |
| 10,000 | $1,000 | Medium scale |
| 100,000 | $10,000 | Large scale |

**Alternative:** AssemblyAI would be $2.50/month for 10,000 calls (40x cheaper)
See `VAPI_STT_ALTERNATIVES.md` for details.

---

## Troubleshooting

### Transfer Fails
```bash
python3 test_squad.py  # Check squad config
```

### Cities Not Recognized
Check regional assistant has keywords:
```bash
cat config_greater_accra_assistant.json | grep -A 100 keywords
```

### Wrong Region Transfer
City might be in wrong region group:
```bash
python3 regional_city_segmentation.py  # See city assignments
```

---

## Documentation

📄 **Full Docs:**
- `SQUAD_IMPLEMENTATION_README.md` - Complete guide
- `SQUAD_ROUTING_ANALYSIS.md` - Feasibility analysis
- `VAPI_STT_ALTERNATIVES.md` - Alternative solutions

🔗 **VAPI:**
- [Squads Docs](https://docs.vapi.ai/squads)
- [Dashboard](https://dashboard.vapi.ai)

---

## Next Steps

1. ✅ Deploy: `python3 deploy_squad.py`
2. ✅ Test: `python3 test_squad.py`
3. ✅ Make test calls to all 6 regions
4. ✅ Monitor call logs in VAPI dashboard
5. 💡 Consider AssemblyAI for cost savings (see alternatives doc)

---

**Status:** ✅ Ready to deploy
**Deploy Time:** ~5 minutes
**Test Time:** ~15 minutes
**Go Live:** After successful testing

🚀 Run `python3 deploy_squad.py` now to get started!
