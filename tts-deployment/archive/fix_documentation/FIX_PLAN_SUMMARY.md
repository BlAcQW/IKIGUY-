# TTS Deployment - Fix Plan Summary

**Created:** 2025-10-20
**Status:** Ready to Execute

---

## 🎯 Quick Overview

This plan addresses **3 known issues** blocking full TTS deployment:

1. **MeloTTS Language Bug** (LOW) - Misleading error message, easy fix
2. **OpenVoice Build Failure** (MEDIUM) - PyAV dependency issue, moderate fix
3. **RunPod Access** (HIGH) - Blocks 3 advanced TTS systems, needs credentials

**Estimated Total Time:** 8-12 hours
**Expected Outcome:** 7/9 TTS systems fully deployed (up from current 4/9)

---

## 📋 Three-Phase Approach

### **PHASE 1: Quick Wins** (1-2 hours)
- ✅ Fix MeloTTS language validation bug
  - Add lazy model loading
  - Test all 6 languages
  - Rebuild and deploy

- ✅ Document RunPod requirements
  - List required credentials
  - Document setup steps
  - Prepare deployment scripts

**Deliverables:**
- Working MeloTTS synthesis
- RunPod deployment guide

---

### **PHASE 2: Medium Complexity** (2-4 hours)
- ✅ Fix OpenVoice PyAV build issue
  - Try pre-built wheels first
  - Fallback to Cython version pinning
  - Build and test container

- ✅ Obtain RunPod credentials
  - Contact infrastructure team OR
  - Provision new RunPod instance
  - Test SSH connection

**Deliverables:**
- Working OpenVoice container
- Active RunPod instance with SSH access

---

### **PHASE 3: Full Deployment** (4-6 hours)
- ✅ Deploy OpenVoice with SSL
  - Start container
  - Configure nginx
  - Obtain SSL certificate
  - Test voice cloning

- ✅ Deploy RunPod services
  - F5-TTS (flow-matching TTS)
  - StyleTTS2 (high-quality TTS)
  - Kyutai/Moshi (conversational AI)

- ✅ Configure infrastructure
  - SSH tunnels from local → RunPod
  - Nginx reverse proxy
  - SSL certificates for all 3 services

- ✅ Testing & documentation
  - Health checks pass 100%
  - End-to-end synthesis tests
  - Update all documentation

**Deliverables:**
- 7/9 TTS services fully operational
- 100% SSL coverage
- Complete documentation

---

## 🔧 Technical Solutions

### MeloTTS Fix
```python
# Add lazy model loading to /synthesize endpoint
if request.language not in loaded_models:
    load_model(request.language)
```
**Impact:** Immediate fix, no breaking changes

### OpenVoice Fix
```dockerfile
# Use pre-built PyAV wheel instead of source build
RUN pip3 install av==11.0.0
RUN pip3 install -e .
```
**Impact:** Faster builds, avoids Cython errors

### RunPod Deployment
```bash
# 1. Provision instance: RTX A6000 (48GB, $0.80/hr)
# 2. Install Docker + NVIDIA runtime
# 3. Deploy services via docker-compose
# 4. Configure SSH tunnels
# 5. Setup SSL certificates
```
**Impact:** +3 advanced TTS systems, +48GB GPU capacity

---

## 📊 Expected Results

### Before Fixes
- **Services Running:** 4/9 (44%)
- **GPU Usage:** 3-4GB / 20GB local
- **TTS Capabilities:** Basic synthesis + voice cloning

### After Fixes
- **Services Running:** 7/9 (78%)
- **GPU Usage:** 3-4GB local + 10-15GB RunPod
- **TTS Capabilities:**
  - Basic synthesis (MeloTTS, Kokoro)
  - Voice cloning (Coqui, OpenVoice)
  - High-quality synthesis (F5-TTS, StyleTTS2)
  - Real-time conversational (Kyutai/Moshi)

---

## 💰 Cost Implications

### Current Costs
- **Local GPU:** Owned hardware (no recurring cost)
- **SSL Certificates:** Free (Let's Encrypt)
- **Total:** $0/month

### After RunPod Deployment
- **Local GPU:** $0/month
- **RunPod RTX A6000 (48GB):** ~$576/month (24/7)
- **Alternative (on-demand):** ~$0.80/hour when needed
- **SSL Certificates:** Free
- **Total:** $0-576/month (depending on usage pattern)

**Recommendation:** Use on-demand RunPod pods to minimize costs

---

## ⚠️ Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| MeloTTS fix breaks service | Low | Medium | Quick rollback via git |
| OpenVoice build still fails | Medium | Low | Skip for now, use Coqui |
| RunPod credentials unavailable | Medium | High | Provision new instance |
| SSH tunnels unstable | Low | Medium | Use cloudflared or ngrok |
| Cost overrun | Medium | Medium | Use on-demand instances |

---

## 📝 Task List (TODO)

### Phase 1 (Start Here)
- [ ] Read MeloTTS app.py and identify bug
- [ ] Implement lazy model loading fix
- [ ] Rebuild and test MeloTTS
- [ ] Write RunPod deployment guide

### Phase 2
- [ ] Update OpenVoice Dockerfile with PyAV fix
- [ ] Build OpenVoice container
- [ ] Contact team for RunPod credentials OR provision new pod
- [ ] Test SSH connection to RunPod

### Phase 3
- [ ] Deploy OpenVoice and configure SSL
- [ ] SSH into RunPod and setup environment
- [ ] Deploy F5-TTS, StyleTTS2, Kyutai/Moshi
- [ ] Configure SSH tunnels (runpod_tunnels.sh)
- [ ] Setup SSL certificates for RunPod services
- [ ] Run comprehensive health check (should show 7/9 healthy)
- [ ] Update README and DEPLOYMENT_STATUS
- [ ] Create final deployment report

---

## 🎯 Success Metrics

### Definition of Done
- ✅ All 3 issues resolved or documented
- ✅ MeloTTS synthesis works for all languages
- ✅ OpenVoice deployed or documented as blocked
- ✅ RunPod services deployed or documented as blocked
- ✅ Health check shows ≥7/9 services healthy
- ✅ All active services have SSL certificates
- ✅ Documentation updated with current status

### Quality Gates
- ✅ No regression in existing services
- ✅ All new services pass health checks
- ✅ End-to-end synthesis test passes for each service
- ✅ SSL certificates valid and auto-renewing
- ✅ Rollback procedures tested and documented

---

## 📖 Reference Documents

- **Detailed Plan:** [FIX_PLAN_2025-10-20.md](./FIX_PLAN_2025-10-20.md)
- **Current Status:** [DEPLOYMENT_STATUS_2025-10-20.md](./DEPLOYMENT_STATUS_2025-10-20.md)
- **Architecture:** [TTS_DEPLOYMENT_PLAN.md](./TTS_DEPLOYMENT_PLAN.md)
- **General Guide:** [README.md](./README.md)

---

## 🚀 Next Steps

1. **Review this summary** and the detailed fix plan
2. **Get approval** for RunPod costs (if needed)
3. **Start Phase 1** - MeloTTS fix (30 min, low risk)
4. **Proceed to Phase 2** - OpenVoice + RunPod access
5. **Complete Phase 3** - Full deployment

**Ready to start?** Begin with MeloTTS bug fix (see detailed plan for step-by-step instructions)

---

**Questions or Blockers?**
- MeloTTS fix: Check docker/melotts/app.py
- OpenVoice fix: Check docker/openvoice/Dockerfile
- RunPod access: Contact infrastructure team or provision at https://runpod.io

---

*Created by: Claude Code*
*Date: October 20, 2025*
*Estimated Completion: 1-2 days*
