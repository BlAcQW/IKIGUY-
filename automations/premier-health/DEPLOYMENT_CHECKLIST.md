# Premier Health VAPI Squad - Deployment Checklist

**Date:** 2025-10-20
**Assistant ID to Use:** d9cc5399-14b8-49b0-8e6b-e541dd9703b6

---

## Pre-Deployment ✓ (Completed)

- [x] Analyze city distribution across regions
- [x] Create regional city segmentation (324 cities → 6 regions)
- [x] Generate router assistant configuration
- [x] Generate 6 regional assistant configurations
- [x] Create squad template configuration
- [x] Create deployment automation script
- [x] Create testing validation script
- [x] Write comprehensive documentation

**Files Created:** 16 files, 105KB total

---

## Deployment Steps ⏳ (Ready to Execute)

### Step 1: Review Configuration
```bash
cd /opt/kasaai/apps/automations/premier-health

# Review configurations
ls -lh config_*.json
cat regional_cities_export.json | jq '.metadata'
```

- [ ] Verify 8 config files exist
- [ ] Check regional city counts are correct
- [ ] Confirm all regions < 100 cities

### Step 2: Deploy to VAPI
```bash
python3 deploy_squad.py
```

**Choose option 1:** Deploy complete squad

- [ ] Router assistant created
- [ ] 6 regional assistants created
- [ ] Squad created with all members
- [ ] deployment_record.json saved

**Expected output:**
```
✅ Router Assistant: router-abc123...
✅ Regional Assistants (6): ...
✅ Squad: squad-vwx234...
```

### Step 3: Validate Deployment
```bash
python3 test_squad.py
```

- [ ] All 7 assistants fetch successfully
- [ ] Keywords loaded correctly (30-96 per region)
- [ ] Squad has 7 members
- [ ] Transfer destinations configured
- [ ] All tests pass

---

## Manual Testing ⏳ (After Deployment)

### Test Scenario 1: Greater Accra
**Action:** Call squad → Say "I'm in Madina"
- [ ] Router transfers to Greater Accra assistant
- [ ] Context preserved (assistant knows user is in Madina)
- [ ] City "Madina" transcribed correctly
- [ ] RAG finds facilities in Madina
- [ ] Phone numbers provided

### Test Scenario 2: Ashanti
**Action:** Call squad → Say "I need help in Kumasi"
- [ ] Router transfers to Ashanti assistant
- [ ] City "Kumasi" transcribed correctly
- [ ] RAG finds facilities in Kumasi

### Test Scenario 3: Northern
**Action:** Call squad → Say "I'm from Tamale"
- [ ] Router transfers to Northern assistant
- [ ] City "Tamale" transcribed correctly
- [ ] RAG finds facilities in Tamale

### Test Scenario 4: Western/Central
**Action:** Call squad → Say "I'm in Takoradi"
- [ ] Router transfers to Western/Central assistant
- [ ] City "Takoradi" transcribed correctly

### Test Scenario 5: Eastern/Volta
**Action:** Call squad → Say "I need a doctor in Ho"
- [ ] Router transfers to Eastern/Volta assistant
- [ ] City "Ho" transcribed correctly

### Test Scenario 6: Bono
**Action:** Call squad → Say "I'm calling from Sunyani"
- [ ] Router transfers to Bono assistant
- [ ] City "Sunyani" transcribed correctly

---

## Post-Deployment Monitoring ⏳

### Week 1 Metrics
- [ ] Transfer success rate > 95%
- [ ] City transcription accuracy > 85%
- [ ] RAG query success > 90%
- [ ] Average call duration < 5 min
- [ ] Zero critical errors

### Issues Log
| Date | Issue | Region | Resolution | Status |
|------|-------|--------|------------|--------|
|      |       |        |            |        |

---

## Rollout Plan ⏳

### Phase 1: Internal Testing (Day 1-3)
- [ ] 20+ test calls across all regions
- [ ] Document any issues
- [ ] Fix bugs and redeploy if needed
- [ ] Get stakeholder approval

### Phase 2: Soft Launch (Day 4-7)
- [ ] Route 10% of traffic to squad
- [ ] Monitor hourly for first day
- [ ] Compare with current system
- [ ] Increase to 25% if successful

### Phase 3: Full Rollout (Week 2-3)
- [ ] 50% traffic
- [ ] 75% traffic
- [ ] 100% traffic
- [ ] Monitor daily

### Phase 4: Optimization (Week 4+)
- [ ] Review call logs
- [ ] Update prompts if needed
- [ ] Add missing cities
- [ ] Test AssemblyAI alternative

---

## Success Criteria ✅

### Must Have
- ✅ All 324 cities covered
- ⏳ Transfer success rate > 95%
- ⏳ No critical errors in production
- ⏳ User satisfaction maintained or improved

### Nice to Have
- ⏳ City transcription accuracy > 90%
- ⏳ Average call duration < 4 min
- ⏳ Cost per call < $0.12

---

## Rollback Plan 🔄

### If Deployment Fails
```bash
# Revert to current assistant
# ID: baa69b3a-8944-4557-9ef9-3a5aa6956eb3
# (Keep current 80-city configuration active)
```

### If Testing Fails
- Identify which region(s) have issues
- Redeploy only affected regional assistants
- Re-run test_squad.py

### If Production Issues
- Monitor VAPI dashboard for errors
- Check call logs for failed transfers
- Reduce traffic percentage
- Fix and redeploy

---

## Documentation References

- 📘 `SQUAD_QUICK_START.md` - 5-minute deployment guide
- 📗 `SQUAD_IMPLEMENTATION_README.md` - Complete reference
- 📙 `SQUAD_ROUTING_ANALYSIS.md` - Feasibility analysis
- 📕 `IMPLEMENTATION_SUMMARY.md` - Executive summary

---

## Deployment Sign-Off

### Pre-Deployment Review
- [ ] All configurations reviewed
- [ ] Deployment script tested
- [ ] Documentation complete
- [ ] Stakeholders notified

**Reviewed By:** _________________ **Date:** _______

### Post-Deployment Validation
- [ ] All tests passed
- [ ] Manual testing complete
- [ ] Monitoring in place
- [ ] Ready for soft launch

**Validated By:** _________________ **Date:** _______

### Production Approval
- [ ] Soft launch successful
- [ ] Metrics meet criteria
- [ ] No critical issues
- [ ] Approved for full rollout

**Approved By:** _________________ **Date:** _______

---

## Quick Commands

```bash
# Navigate to project
cd /opt/kasaai/apps/automations/premier-health

# Deploy
python3 deploy_squad.py

# Test
python3 test_squad.py

# Check deployment
cat deployment_record.json | jq

# View configs
ls -lh config_*.json

# View city distribution
python3 regional_city_segmentation.py
```

---

**Status:** ✅ Ready for Deployment
**Next Action:** Run `python3 deploy_squad.py`
