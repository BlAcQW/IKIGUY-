# Voice Lab Training & Deployment - Master Plan

**Created:** 2025-10-19
**Last Updated:** 2025-10-23
**Vision:** Build world-class ASR, TTS, and LLM models for Ghanaian and West African languages

---

## 🎯 MISSION

Train and deploy production-ready voice AI models for underserved African languages, starting with Ghana and expanding across West Africa.

---

## 🚀 QUICK START FOR NEW DEVELOPERS

### Current Situation (October 23, 2025)

**Active Training:**
- ⚠️ **Nigerian Whisper** training CRASHED at step 1000/15,000
- 🔄 **UGData Extraction** in progress (Dagbani 20% transferred, Akan/Dagaare downloading)
- ⏸️ **Ghanaian Whisper** training ready but waiting for UGData completion

**Access Required:**
1. **SSH Key:** `~/.ssh/id_ed25519` (for RunPod and local server access)
2. **RunPod Account:** Access to pod `jzfmzviw26huka-644113c7`
3. **Hetzner Storage:** CIFS mount credentials for `/mnt/hetzner_storage/`

**To Resume Work:**

1. **Check RunPod Training Status:**
   ```bash
   ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121
   # Check if checkpoint exists
   ls -la /workspace/outputs/whisper-small-african-qlora/checkpoint-1000/
   # Check training log
   tail -f /workspace/whisper_nigerian_training.log
   ```

2. **Monitor Data Downloads (Local Server):**
   ```bash
   # Check Akan/Dagaare TAR downloads
   ls -lh /opt/kasaai/apps/voice-lab/data/ugdata/tar_downloads/

   # Check Dagbani rsync progress
   du -sh /mnt/hetzner_storage/voice-lab/datasets/ugdata_extracted/Dagbani/

   # Monitor extraction log
   tail -f /tmp/ugdata_local_extraction.log
   ```

3. **Review Training Scripts:**
   - **Nigerian (current):** `/opt/kasaai/apps/voice-lab/runpod_training/runpod_whisper_nigerian_only.py`
   - **Ghanaian (next):** `/opt/kasaai/apps/voice-lab/scripts/train_faster_whisper_ghanaian.py`
   - **Deployment:** `/opt/kasaai/apps/voice-lab/scripts/deploy_faster_whisper_runpod.sh`

4. **Fix & Restart Training:**
   See Section 1.1 for details on the eval_dataset crash issue

**Critical Files to Review:**
- `/opt/kasaai/apps/tts-deployment/TASKS.md` (this file) - Master plan
- `/opt/kasaai/apps/voice-lab/data/DATASET_INDEX.md` - Data inventory
- `/opt/kasaai/apps/voice-lab/scripts/FASTER_WHISPER_TRAINING.md` - Training guide

---

## 📊 CURRENT STATUS OVERVIEW

| Category | Status | Progress |
|----------|--------|----------|
| **ASR Training** | ✅ **RUNNING** | Nigerian languages (20+/15,000 steps, ~10h remaining) |
| **TTS Deployment** | ✅ **COMPLETE** | All 8 systems deployed & tested |
| **Data Pipeline** | 🔄 **ACTIVE** | Dagbani 20%, Akan/Dagaare downloading |
| **Infrastructure** | ✅ **READY** | RunPod A40 (running) + Hetzner 10TB |
| **LLM Training** | ⏸️ **PLANNED** | Awaiting ASR/TTS completion |

**Immediate Actions Needed:**
1. ✅ ~~Fix Nigerian training eval_dataset issue~~ → FIXED & RUNNING
2. 🔄 Monitor Nigerian training progress (currently at step 20+/15,000)
3. 🔄 Monitor UGData downloads (Akan/Dagaare downloading)
4. 🔄 Complete Dagbani rsync to Hetzner (20% done)

---

## 🗄️ DATA INVENTORY

### Available Now

| Dataset | Languages | Hours | Size | Status |
|---------|-----------|-------|------|--------|
| **Twi-Akan-Fante** | Twi, Akan, Fante | 335h | 480GB | ✅ Ready |
| **NaijaVoices** | Hausa, Yoruba, Igbo | 1,880h | Streaming | ✅ Training |
| **CMU Wilderness** | 13 Ghanaian langs | 200+h | 1.2GB | ✅ Ready |
| **Ayiku Yoruba** | Yoruba (Bible) | 4h | 15GB | ✅ Ready |
| **Enoch Ewe** | Ewe | 20h | 15GB | ✅ Ready |

### In Progress

| Dataset | Languages | Expected Hours | Status |
|---------|-----------|----------------|--------|
| **UGSpeechData** | Dagbani, Ewe, Dagaare, Ikposo | ~150h | 🔄 Extracting |
| **Akan.tar** | Akan | ~60h | 🔄 Downloading (18%) |
| **Dagaare.tar** | Dagaare | ~50h | 🔄 Downloading (17%) |

**TOTAL AVAILABLE:** 2,700+ hours across 20+ African languages

---

## 📋 PHASE 1: ASR TRAINING - FASTER WHISPER

### Status: 🔄 IN PROGRESS

### 1.1 Nigerian Languages (CURRENT) ✅ RUNNING

**Status:** Training SUCCESSFULLY restarted and running at step ~20+/15,000
**Model:** whisper-small + QLoRA (3.5M trainable params, 1.44%)
**Languages:** Hausa (650h), Yoruba (600h), Igbo (630h)
**Restarted:** October 23, 2025 00:44 UTC (Fixed eval_dataset crash)
**Speed:** ~2.5 seconds/step
**ETA:** ~10.4 hours remaining (October 23, ~11:00 UTC)
**RunPod Pod:** jzfmzviw26huka-644113c7
**GPU:** NVIDIA A40 (46GB VRAM) @ $0.79/hour
**Process:** PID 28609 (running, 8.6GB RAM usage)

**RunPod Connection Info:**
- **SSH:** `ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121`
- **Host:** 194.68.245.121
- **Port:** 22130
- **Pod ID:** jzfmzviw26huka-644113c7

**Training Files on RunPod:**
- **Training Script (FIXED):** `/workspace/runpod_whisper_nigerian_only_FIXED.py` ✅
- **Restart Script:** `/workspace/restart_nigerian_training.sh` ✅
- **Log File:** `/workspace/whisper_nigerian_training.log`
- **Output Directory:** `/workspace/outputs/whisper-small-african-qlora/`
- **Data Source:** HuggingFace `castorini/naijavoices` dataset (streaming mode)

**Local Backup:**
- **Original Script:** `/opt/kasaai/apps/voice-lab/runpod_training/runpod_whisper_nigerian_only.py`
- **Fixed Script:** `/opt/kasaai/apps/voice-lab/runpod_training/runpod_whisper_nigerian_only_FIXED.py` ✅

**Issue Resolution (Oct 23, 00:45 UTC):**
✅ **FIXED** - Two issues resolved:
1. ~~`ValueError: Trainer: evaluation requires an eval_dataset`~~ → Fixed by setting `evaluation_strategy="no"`
2. ~~`AssertionError: EarlyStoppingCallback requires load_best_model_at_end = True`~~ → Fixed by removing EarlyStoppingCallback

**Changes Made:**
- Set `evaluation_strategy="no"` (was "steps")
- Set `load_best_model_at_end=False` (was True)
- Removed `EarlyStoppingCallback` from callbacks
- Commented out eval-related parameters

**Next Steps:**
- [ ] Monitor training progress (check every few hours)
- [ ] Complete 15,000 training steps (~10 hours remaining)
- [ ] Download final checkpoint from RunPod
- [ ] Evaluate WER on held-out test set
- [ ] Deploy to production API

### 1.2 Ghanaian Languages (NEXT)

**Priority:** HIGH
**Start Date:** After Nigerian model completes (Oct 26+)
**Model:** whisper-small + QLoRA

**Languages & Data:**
- ✅ Twi-Akan-Fante: 335h (212k samples) - READY
- 🔄 Dagbani: ~50h (18k files) - Extracting
- 🔄 Ewe: ~60h (34k files) - Enoch + UGData
- 🔄 Dagaare: ~50h - Downloading
- 🔄 Ikposo: ~40h - Queued

**Training Approach:**
```
Option A: Twi Only (Fast Start)
- Duration: ~10-12 hours
- Cost: ~$8-10
- Use: Validate pipeline

Option B: Multi-language (Recommended)
- Languages: Twi + Dagbani + Ewe + Dagaare + Ikposo
- Duration: ~80-100 hours
- Cost: ~$63-79
- Benefit: Best multilingual performance
```

**Tasks:**
- [ ] Wait for UGData extraction to complete
- [ ] Create manifests for Dagbani, Ewe, Dagaare, Ikposo
- [ ] Update training script paths for Ghanaian data
- [ ] Test SSH mount to Hetzner from RunPod
- [ ] Start training (Option B recommended)

**Script:** `/opt/kasaai/apps/voice-lab/scripts/train_faster_whisper_ghanaian.py` ✅ READY

### 1.3 Whisper Medium (LATER)

**Priority:** MEDIUM
**When:** After Small model proves successful
**Model:** whisper-medium + QLoRA
**Rationale:** Better accuracy for production, larger model capacity

**Languages:**
- All Nigerian (1,880h)
- All Ghanaian (535h)
- Total: 2,415h

**Estimated:**
- Duration: ~150-200 hours
- Cost: ~$120-160
- Expected WER: 10-15% (better than Small)

---

## 📋 PHASE 2: TTS TRAINING

### Status: ⏸️ PLANNED (After ASR)

### 2.1 Coqui XTTS v2 (Voice Cloning)

**Priority:** HIGH
**Why First:** Pre-trained multilingual, needs fine-tuning only

**Data:** Twi-Akan-Fante (201k samples, 335h)
**Manifest:** `coqui_xtts_train.txt` ✅ READY
**Training Time:** ~40-60 hours
**GPU:** A40 (16GB VRAM sufficient)

**Tasks:**
- [ ] Review Coqui XTTS fine-tuning docs
- [ ] Setup training script with QLoRA (if supported)
- [ ] Mount Hetzner data on RunPod
- [ ] Start training
- [ ] Evaluate voice quality
- [ ] Deploy updated model

**Success Criteria:**
- [ ] Natural-sounding Twi synthesis
- [ ] Voice cloning < 10 seconds of reference
- [ ] Real-time inference speed

### 2.2 F5-TTS (High Quality)

**Priority:** HIGH
**Why:** State-of-the-art quality, non-autoregressive (fast)

**Data:** Twi-Akan-Fante (201k samples)
**Manifest:** `f5_tts_train.csv` ✅ READY
**Training Time:** ~60-80 hours
**GPU:** A40 (may need gradient checkpointing)

**Tasks:**
- [ ] Research F5-TTS training requirements
- [ ] Setup training environment
- [ ] Adapt data loading for F5 format
- [ ] Train base model
- [ ] Evaluate quality vs Coqui
- [ ] Deploy if quality is better

### 2.3 MeloTTS (Fast Inference)

**Priority:** MEDIUM
**Why:** Fast, lightweight, good for real-time

**Data:** Twi-Akan-Fante (201k samples)
**Manifest:** `melo_tts_train.csv` ✅ READY
**Training Time:** ~30-40 hours
**GPU:** Lighter than F5/Coqui

**Tasks:**
- [ ] Setup MeloTTS training
- [ ] Train on Twi data
- [ ] Benchmark inference speed
- [ ] Compare quality vs others
- [ ] Deploy if speed advantage is significant

### 2.4 OpenVoice (Voice Conversion)

**Priority:** LOW
**Why:** More specialized use case (voice conversion)

**Tasks:**
- [ ] Evaluate need for voice conversion
- [ ] If needed, train on Twi voices
- [ ] Test conversion quality

### 2.5 Kokoro & StyleTTS2

**Priority:** LOW
**Why:** Experimental, less critical

**Tasks:**
- [ ] Research training requirements
- [ ] Decide if worth the effort
- [ ] Train if resources available

### 2.6 Kyutai Moshi (Conversational AI)

**Priority:** MEDIUM
**Why:** Full-duplex conversational AI, real-time voice interaction

**Data:** Twi-Akan-Fante (201k samples, 335h)
**Training Time:** ~80-120 hours (complex model - audio + language)
**GPU:** A40 or A100 (high VRAM needed)

**Architecture:**
- Multimodal model (speech-to-speech)
- Streaming audio processing
- Real-time latency optimization

**Tasks:**
- [ ] Research Kyutai Moshi training requirements
- [ ] Setup training environment with streaming capabilities
- [ ] Prepare audio-text paired data
- [ ] Train speech encoder + language model + speech decoder
- [ ] Test full-duplex conversational performance
- [ ] Optimize for low-latency inference
- [ ] Deploy to moshi.ailabsafrica.com (already deployed base model)

**Success Criteria:**
- [ ] Full-duplex conversation with <500ms latency
- [ ] Natural turn-taking behavior
- [ ] Voice quality > 3.5 MOS
- [ ] Twi language understanding and generation

**Deployment Status:** ✅ Base model deployed at moshi.ailabsafrica.com (needs Twi fine-tuning)

### 2.7 Chatterbox (Multi-speaker TTS)

**Priority:** MEDIUM
**Why:** Multi-speaker capabilities, emotional expressiveness

**Data:** Twi-Akan-Fante (201k samples, 335h, multiple speakers)
**Training Time:** ~50-70 hours
**GPU:** A40 (16GB+ VRAM)

**Capabilities:**
- Multi-speaker voice synthesis
- Emotional control (happy, sad, neutral, etc.)
- Prosody variation
- Speaker interpolation

**Tasks:**
- [ ] Research Chatterbox training architecture
- [ ] Prepare multi-speaker dataset with speaker IDs
- [ ] Extract speaker embeddings for Twi voices
- [ ] Train multi-speaker TTS model
- [ ] Implement emotion control mechanisms
- [ ] Test speaker consistency and quality
- [ ] Deploy to production API

**Success Criteria:**
- [ ] Support 10+ distinct Twi speakers
- [ ] MOS > 3.8 for speaker similarity
- [ ] Emotional control functional
- [ ] Real-time inference speed

---

## 📋 PHASE 3: LLM FINE-TUNING

### Status: ⏸️ PLANNED (After Voice Models)

### 3.1 Twi Language Model

**Priority:** HIGH (After TTS)
**Base Model:** Llama 3 8B or Gemma 2 7B
**Method:** QLoRA fine-tuning

**Data Sources:**
- Bible translations (high quality Twi)
- Financial inclusion texts
- News articles
- Conversational data (if available)

**Purpose:**
- Better language understanding
- Integration with voice systems
- Conversational AI in Twi

**Tasks:**
- [ ] Collect Twi text corpus
- [ ] Clean and prepare data
- [ ] Setup QLoRA training
- [ ] Train base model
- [ ] Evaluate language quality
- [ ] Deploy to Open WebUI

### 3.2 Multi-language West African Model

**Priority:** MEDIUM
**Base Model:** Larger Llama or Gemma
**Languages:** Twi, Hausa, Yoruba, Igbo, Ewe

**Tasks:**
- [ ] Collect text data for all languages
- [ ] Balance dataset across languages
- [ ] Train multilingual model
- [ ] Evaluate cross-lingual transfer
- [ ] Deploy

---

## 📋 PHASE 4: INTEGRATION & PRODUCTION

### 4.1 API Deployment

**Status:** ✅ PARTIAL (TTS deployed, ASR pending)

**Deployed Services:**
- ✅ Coqui TTS (coqui.ailabsafrica.com)
- ✅ MeloTTS (melotts.ailabsafrica.com)
- ✅ F5-TTS (f5tts.ailabsafrica.com)
- ✅ StyleTTS2 (styletts.ailabsafrica.com)
- ✅ OpenVoice (openvoice.ailabsafrica.com)
- ✅ Kokoro (kokoro.ailabsafrica.com)
- ✅ Moshi (moshi.ailabsafrica.com)
- ✅ Crawl4AI (crawl4ai.ailabsafrica.com)

**Pending:**
- [ ] Deploy trained Whisper ASR models
- [ ] Deploy fine-tuned TTS models
- [ ] Deploy LLMs via Open WebUI

### 4.2 Model Registry

**Tasks:**
- [ ] Setup HuggingFace model hub
- [ ] Upload trained models
- [ ] Version control for models
- [ ] Document model cards
- [ ] Share with community

### 4.3 Monitoring & Evaluation

**Tasks:**
- [ ] Setup WER/BLEU tracking for ASR
- [ ] Setup MOS evaluation for TTS
- [ ] User feedback collection
- [ ] Performance monitoring
- [ ] Cost tracking

---

## 📋 PHASE 5: EXPANSION & RESEARCH

### 5.1 More African Languages

**Target Languages:**
- Ga (data ready)
- Dagaare (in progress)
- Ikposo (in progress)
- Wolof (to acquire)
- Swahili (minimal data, needs more)
- Others across West Africa

### 5.2 Advanced Capabilities

**ASR:**
- [ ] Speaker diarization
- [ ] Emotion recognition
- [ ] Code-switching handling

**TTS:**
- [ ] Multi-speaker synthesis
- [ ] Emotional control
- [ ] Prosody modeling

**LLM:**
- [ ] Conversational AI
- [ ] Language translation
- [ ] Cultural context awareness

---

## 🛠️ INFRASTRUCTURE

### RunPod GPU Instances

**Current Active Pod:**
- **Pod ID:** jzfmzviw26huka-644113c7
- **GPU:** NVIDIA A40 (46GB VRAM, 200GB storage)
- **Cost:** $0.79/hour
- **SSH Access:** `ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121`
- **Status:** ⚠️ Training crashed, pod still running
- **Started:** October 21, 2025
- **Total Cost to Date:** ~$67 (85 hours)

**RunPod File Structure:**
```
/workspace/
├── runpod_whisper_nigerian_only.py       # Current training script (28KB)
├── runpod_whisper_african_qlora_streaming_fixed.py  # Base script
├── start_nigerian_only.py                 # Script generator
├── whisper_nigerian_training.log          # Training log (64KB)
├── outputs/
│   └── whisper-small-african-qlora/
│       └── runs/                          # TensorBoard logs
│       └── checkpoint-1000/               # Step 1000 checkpoint (if exists)
├── training-data/
│   └── twi-akan-fante/                    # Twi data (not used in Nigerian training)
└── docker/                                # TTS API containers
```

**Data Sources on RunPod:**
- **Nigerian Languages:** HuggingFace `castorini/naijavoices` dataset (streaming mode, no local storage)
- **Twi Data:** Local copy at `/workspace/training-data/twi-akan-fante/` (from Hetzner, not used yet)

**Planned:**
- Spin up additional pods for TTS training
- Use spot instances where possible
- Cost optimization strategies

### Hetzner Storage

**Current:**
- Total: 10TB
- Used: ~600GB
- Available: 9.4TB
- SSH mount: ✅ Working

**Usage:**
- Store all training data
- Stream to RunPod during training
- Backup trained models

### Local Development Server (Hetzner Dedicated)

**Location:** `/opt/kasaai/`
**Storage:** 1.7TB (419GB available)
**Purpose:**
- Data preprocessing
- Manifest creation
- Small model testing
- Deployment management
- RunPod script backup

**Key Directory Structure:**
```
/opt/kasaai/apps/
├── voice-lab/
│   ├── data/
│   │   ├── twi-akan-fante/
│   │   │   ├── processed/processed_audio/asr_16k/  # 480GB, 212k samples
│   │   │   └── manifests/                          # 584MB manifests
│   │   ├── ugdata/
│   │   │   ├── extracted/Dagbani/                  # 5.4GB, 18k MP3s ✅
│   │   │   └── tar_downloads/                      # Akan.tar, Dagaare.tar downloading
│   │   ├── ewe_datasets/Enoch_Ewe/                 # 15GB, 19k MP3s
│   │   ├── ga_datasets/                            # CMU Wilderness Ga
│   │   ├── DATASET_INDEX.md                        # Data inventory
│   │   └── DATASET_DOWNLOAD_STATUS.md              # Download status
│   ├── scripts/
│   │   ├── train_faster_whisper_ghanaian.py        # Ghanaian training (14KB) ✅
│   │   ├── deploy_faster_whisper_runpod.sh         # RunPod deployment (4.4KB) ✅
│   │   └── FASTER_WHISPER_TRAINING.md              # Documentation (9.5KB) ✅
│   └── runpod_training/
│       └── runpod_whisper_nigerian_only.py         # Nigerian training backup (28KB) ✅
├── tts-deployment/
│   ├── TASKS.md                                    # This file
│   ├── WHISPER_TRAINING_STATUS.md
│   └── README.md
└── core_backend/                                   # Main API backend
```

**Hetzner Storage Box Mount:**
```
/mnt/hetzner_storage/voice-lab/
├── data/twi-akan-fante/manifests/                  # 584MB manifests
├── datasets/
│   ├── ugdata_extracted/Dagbani/                   # Rsync in progress (20%)
│   ├── ayiku_datasets/                             # 15GB Yoruba
│   └── enoch_datasets/                             # 15GB Ewe
└── models/                                         # Trained model backups (future)
```

**Access:**
- **SSH Key:** `~/.ssh/id_ed25519`
- **Hetzner Mount:** CIFS/SMB to `/mnt/hetzner_storage/`

---

## 📈 SUCCESS METRICS

### ASR Models
- **WER < 20%** for high-resource languages (Twi, Hausa, Yoruba, Igbo)
- **WER < 30%** for medium-resource languages (Ewe, Dagbani, Dagaare)
- **Real-time factor < 0.3** (process 1 minute audio in <18 seconds)

### TTS Models
- **MOS > 4.0** (Mean Opinion Score, 1-5 scale)
- **Real-time inference** (generate 1 minute audio in <5 seconds)
- **Voice cloning quality > 3.5 MOS** with <10 seconds reference

### LLM Models
- **Perplexity** comparable to English baselines
- **Human evaluation** for fluency and cultural appropriateness
- **Response time < 2 seconds** for chat

---

## 💰 BUDGET & TIMELINE

### Phase 1: ASR Training (Current - November 2025)

| Task | GPU Hours | Cost | Timeline |
|------|-----------|------|----------|
| Nigerian Whisper Small | 72h | $57 | Oct 22-25 ✅ Running |
| Ghanaian Whisper Small | 100h | $79 | Oct 26-30 |
| Whisper Medium (Combined) | 200h | $158 | November |
| **Total Phase 1** | **372h** | **$294** | **6 weeks** |

### Phase 2: TTS Training (December 2025 - February 2026)

| Task | GPU Hours | Cost | Timeline |
|------|-----------|------|----------|
| Coqui XTTS Twi | 60h | $47 | December |
| F5-TTS Twi | 80h | $63 | December |
| MeloTTS Twi | 40h | $32 | January |
| Kyutai Moshi Twi | 100h | $79 | January-February |
| Chatterbox Twi | 60h | $47 | February |
| **Total Phase 2** | **340h** | **$268** | **10 weeks** |

### Phase 3: LLM Training (January - February 2026)

| Task | GPU Hours | Cost | Timeline |
|------|-----------|------|----------|
| Llama 3 8B Twi | 100h | $79 | January |
| Multi-language Model | 150h | $119 | February |
| **Total Phase 3** | **250h** | **$198** | **8 weeks** |

### **GRAND TOTAL:** ~960 GPU hours, ~$760, 24 weeks (6 months)

---

## 🚧 BLOCKERS & DEPENDENCIES

### Current Blockers

1. **UGData Extraction** 🔄
   - Status: Dagbani 20% transferred, Akan/Dagaare downloading
   - Blocking: Ghanaian Whisper training
   - ETA: 6-8 hours

2. **Nigerian Training Completion** 🔄
   - Status: Step 525/15,000 (3.5%)
   - Blocking: RunPod availability for next training
   - ETA: October 25, 2025

### Dependencies

- ✅ Training scripts created (Ghanaian Whisper)
- ✅ Deployment infrastructure ready
- ✅ Data pipeline established
- ⏸️ TTS training scripts (need to create)
- ⏸️ LLM training scripts (need to create)

---

## 📚 DOCUMENTATION REFERENCES

- **Data Inventory:** `/opt/kasaai/apps/voice-lab/data/DATASET_INDEX.md`
- **Training Status:** `/opt/kasaai/apps/tts-deployment/WHISPER_TRAINING_STATUS.md`
- **Deployment:** `/opt/kasaai/apps/tts-deployment/README.md`
- **Ghanaian Whisper:** `/opt/kasaai/apps/voice-lab/scripts/FASTER_WHISPER_TRAINING.md`

---

## 🎯 IMMEDIATE NEXT ACTIONS

### This Week (Oct 23-27)

1. ✅ Monitor Nigerian Whisper training (ongoing)
2. 🔄 Complete UGData extraction (Dagbani, Ewe, Ikposo)
3. 🔄 Download Akan.tar and Dagaare.tar (18% complete)
4. ⏸️ Create manifests for UGData languages
5. ⏸️ Test Hetzner SSH mount from RunPod

### Next Week (Oct 28 - Nov 3)

1. Download Nigerian Whisper checkpoint
2. Evaluate Nigerian model WER
3. Deploy Nigerian model to API
4. Start Ghanaian Whisper training (5 languages)

### Month of November

1. Complete Ghanaian Whisper Small
2. Start Whisper Medium (combined Nigerian + Ghanaian)
3. Research TTS training requirements
4. Prepare TTS training scripts

---

## ✅ COMPLETED MILESTONES

### October 2025

- [x] **Oct 3:** Processed 480GB Twi-Akan-Fante dataset
- [x] **Oct 19-20:** Deployed 8 TTS systems to production
- [x] **Oct 20:** Setup LLM Lab with Open WebUI
- [x] **Oct 21:** Created RunPod deployment guides
- [x] **Oct 22:** Started Nigerian Whisper training (1,880h, 3 languages)
- [x] **Oct 23:** Created Ghanaian Whisper training scripts with QLoRA

---

**Last Updated:** 2025-10-23 01:00 UTC
**Next Review:** When Nigerian training completes (~11:00 UTC Oct 23)
**Owner:** AI Labs Africa Voice Lab Team

**Recent Changes (Oct 23, 01:00):**
- 🎉 **FIXED & RESTARTED:** Nigerian training now running successfully (step 20+/15,000)
- ✅ **RESOLVED:** Fixed eval_dataset crash by setting `evaluation_strategy="no"`
- ✅ **RESOLVED:** Removed EarlyStoppingCallback that required evaluation
- ✅ **CREATED:** Fixed training script and restart script on RunPod
- ✅ **BACKED UP:** Both original and fixed scripts to local `/opt/kasaai/apps/voice-lab/runpod_training/`
- ✅ **ADDED:** Comprehensive Quick Start for New Developers section
- ✅ **ADDED:** Complete RunPod file structure and connection details
- ✅ **ADDED:** Local file organization map with all training scripts
- ✅ **ADDED:** Kyutai Moshi (Section 2.6) & Chatterbox (Section 2.7) TTS training plans
- ✅ **UPDATED:** Phase 2 budget: 340 GPU hours, $268 over 10 weeks
- ✅ **UPDATED:** Grand Total: 960 GPU hours, $760 over 6 months

---

## Chatterbox TTS Setup

**Date:** 2025-11-08
**Status:** ✅ Completed

### Overview
Successfully set up Chatterbox, Resemble AI's open-source multilingual TTS model with 23 language support and zero-shot voice cloning capabilities.

### Implementation Details

#### Repository Setup
- **Source:** https://github.com/resemble-ai/chatterbox
- **Location:** `/opt/kasaai/apps/tts-deployment/chatterbox`
- **License:** MIT
- **Model:** 0.5B Llama backbone trained on 0.5M hours of data

#### Features Enabled
- ✅ Multilingual Support: 23 languages (Arabic, Chinese, English, French, German, Spanish, Hindi, Japanese, etc.)
- ✅ Zero-shot Voice Cloning: Clone any voice from reference audio
- ✅ Emotion Control: Exaggeration parameter for expressive speech
- ✅ Audio Watermarking: Built-in Perth watermarks
- ✅ Gradio Web Interface: User-friendly web UI

#### Docker Configuration
- **Container:** `chatterbox`
- **Port:** 8004
- **GPU:** Required (CUDA 12.1)
- **Python:** 3.11
- **Base Image:** nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

#### Build & Deployment
```bash
# Build container
sudo docker-compose -f docker-compose.local.yml build chatterbox

# Start service
sudo docker-compose -f docker-compose.local.yml up -d chatterbox

# View logs
sudo docker-compose -f docker-compose.local.yml logs -f chatterbox

# Check status
sudo docker ps | grep chatterbox
```

#### Access Points
- **Local:** http://localhost:8004
- **Production:** https://chatterbox.ailabsafrica.com (nginx configured)

#### Technical Notes
1. **Dependency Resolution:** Modified installation to handle conflict between Gradio 5.44.1 and russian-text-stresser (spacy dependency)
2. **Launch Configuration:** Disabled auto-launch in multilingual_app.py to control port configuration
3. **Model Loading:** First startup takes ~30-60 seconds to download models from Hugging Face
4. **GPU Support:** Requires NVIDIA GPU with CUDA support

#### Files Modified/Created
- `/opt/kasaai/apps/tts-deployment/docker/chatterbox/Dockerfile` - Updated
- `/opt/kasaai/apps/tts-deployment/docker/chatterbox/app.py` - Updated
- `/opt/kasaai/apps/tts-deployment/docker/chatterbox/README.md` - Updated  
- `/opt/kasaai/apps/tts-deployment/docker-compose.local.yml` - Updated build context
- `/etc/nginx/sites-available/chatterbox.ailabsafrica.com.conf` - Enhanced with Gradio support

#### Next Steps for Production
1. ☐ Enable nginx site: `sudo ln -s /etc/nginx/sites-available/chatterbox.ailabsafrica.com.conf /etc/nginx/sites-enabled/`
2. ☐ Obtain SSL certificate: `sudo certbot --nginx -d chatterbox.ailabsafrica.com`
3. ☐ Reload nginx: `sudo systemctl reload nginx`
4. ☐ Test production URL: https://chatterbox.ailabsafrica.com

#### Troubleshooting
- **Model download issues:** Check internet connectivity and disk space (~2GB needed)
- **GPU not detected:** Verify CUDA drivers with `nvidia-smi`
- **Port conflicts:** Modify docker-compose.local.yml port mapping

---

---

## Task: Deploy Gradio Web UIs for TTS Services
**Date:** 2025-11-08  
**Status:** ✅ **Phase 1 Complete** - Coqui UI & Kokoro UI Deployed  
**Priority:** High  
**Objective:** Add user-friendly Gradio interfaces to existing TTS services without breaking API integrations

### Summary
Successfully deployed production-ready Gradio web interfaces for Coqui TTS and Kokoro TTS, following the naming convention `{service}-ui.ailabsafrica.com` for improved readability.

### Completed Work

#### 1. ✅ Coqui TTS Gradio UI
**Live URL:** https://coqui-ui.ailabsafrica.com  
**API Backend:** https://coqui.ailabsafrica.com (unchanged)  
**Container:** coqui-ui (Port 8015, Healthy)  

**Features Implemented:**
- 17 language support with language selector
- Zero-shot voice cloning via reference audio upload or microphone
- Real-time character counter (max 5000 chars)
- Advanced audio controls: temperature, repetition penalty, length penalty, speed
- Audio preview and download (WAV format)
- Connection health monitoring
- WebSocket support for real-time updates

**Technical Stack:**
- Python 3.11 with Gradio 5.44.1
- Docker container on tts_network
- Nginx reverse proxy with SSL (Let's Encrypt)
- Certificate expires: 2026-02-06

**Files Created:**
- `/opt/kasaai/apps/tts-deployment/docker/coqui-ui/app.py` (278 lines)
- `/opt/kasaai/apps/tts-deployment/docker/coqui-ui/Dockerfile`
- `/etc/nginx/sites-available/coqui-ui.ailabsafrica.com.conf`
- Updated `/opt/kasaai/apps/tts-deployment/docker-compose.local.yml`

---

#### 2. ✅ Kokoro TTS Gradio UI
**Live URL:** https://kokoro-ui.ailabsafrica.com  
**API Backend:** https://kokoro.ailabsafrica.com (unchanged)  
**Container:** kokoro-ui (Port 8021, Healthy)  

**Features Implemented:**
- 11 voice options with preview (af, af_bella, af_nicole, af_sarah, am_adam, am_michael, bf_emma, bf_isabella, bm_george, bm_lewis, am_santa)
- Speed control slider (0.5x - 2.0x)
- Simple, clean interface optimized for quick synthesis
- Audio preview and download (WAV format)
- Fast generation leveraging Kokoro-82M model
- Connection health monitoring

**Technical Stack:**
- Python 3.11 with Gradio 5.44.1
- Docker container on tts_network
- Nginx reverse proxy with SSL (Let's Encrypt)
- Certificate expires: 2026-02-06

**Files Created:**
- `/opt/kasaai/apps/tts-deployment/docker/kokoro-ui/app.py` (278 lines)
- `/opt/kasaai/apps/tts-deployment/docker/kokoro-ui/Dockerfile`
- `/etc/nginx/sites-available/kokoro-ui.ailabsafrica.com.conf`
- Updated `/opt/kasaai/apps/tts-deployment/docker-compose.local.yml`

---

### Zero Breaking Changes ✅
**Critical Success:** All existing API integrations remain fully functional. The following services continue to work unchanged:
- `/apps/shared` - 5 files with hardcoded TTS URLs
- `/apps/core_backend` - 11 files (services, routes, models)
- `/apps/b2c-portal` - 3 files (TypeScript configs, React components)

**URL Architecture:**
```
API Endpoints (Unchanged):
  https://coqui.ailabsafrica.com    → Port 8005 (API)
  https://kokoro.ailabsafrica.com   → Port 8010 (API)
  
Gradio UIs (New):
  https://coqui-ui.ailabsafrica.com  → Port 8015 (UI)
  https://kokoro-ui.ailabsafrica.com → Port 8021 (UI)
```

---

### Infrastructure & Operations

**Docker Management:**
```bash
# View UI container logs
sudo docker-compose -f docker-compose.local.yml logs -f coqui-ui
sudo docker-compose -f docker-compose.local.yml logs -f kokoro-ui

# Check container health
sudo docker ps | grep -E "coqui-ui|kokoro-ui"

# Restart containers
sudo docker-compose -f docker-compose.local.yml restart coqui-ui
sudo docker-compose -f docker-compose.local.yml restart kokoro-ui

# Rebuild containers (after code changes)
sudo docker-compose -f docker-compose.local.yml build coqui-ui
sudo docker-compose -f docker-compose.local.yml build kokoro-ui
```

**Nginx Management:**
```bash
# Test nginx configuration
sudo nginx -t

# Reload nginx (after config changes)
sudo systemctl reload nginx

# Check SSL certificates
sudo certbot certificates | grep -E "coqui-ui|kokoro-ui"
```

---

### Testing & Validation

**Automated Health Checks:**
- Both containers have built-in healthcheck endpoints
- Nginx monitors container availability
- Docker automatically restarts unhealthy containers

**Manual Testing Performed:**
1. ✅ HTTPS access verified for both UIs
2. ✅ Container health status: healthy
3. ✅ Local and public access working
4. ✅ SSL certificates valid until 2026-02-06
5. ✅ WebSocket connections functional
6. ✅ API backend connectivity confirmed

**Recommended User Testing:**
- [ ] Test voice synthesis with various languages (Coqui)
- [ ] Test voice cloning with reference audio (Coqui)
- [ ] Test all 11 voices (Kokoro)
- [ ] Test speed controls (Kokoro)
- [ ] Verify audio download functionality
- [ ] Test concurrent user access
- [ ] Verify mobile responsiveness

---

### Future Phases

#### Phase 2: OpenVoice UI (Pending)
**Proposed URL:** openvoice-ui.ailabsafrica.com  
**Port:** 8013  
**Complexity:** Low-Moderate  
**Approach:** Use official Gradio demo from OpenVoice repo  
**API Backend:** https://openvoice.ailabsafrica.com (port 8003)

#### Phase 3: MeloTTS UI (Pending)
**Proposed URL:** melotts-ui.ailabsafrica.com  
**Port:** 8011  
**Complexity:** Low  
**Approach:** Use official web UI from MeloTTS repo  
**API Backend:** https://melotts.ailabsafrica.com (port 8001)

---

### Documentation

**Implementation Plan:** `/opt/kasaai/apps/tts-deployment/TTS_GRADIO_UI_IMPLEMENTATION_PLAN.md`
- Complete usage analysis (35+ API references across codebase)
- Detailed implementation guides for each service
- Risk assessment and mitigation strategies
- Port allocation and naming conventions

**Key Decisions:**
1. ✅ Naming convention: `{service}-ui.ailabsafrica.com` (easier to read)
2. ✅ Zero-risk approach: Keep existing API URLs unchanged
3. ✅ Separate containers for isolation and easy management
4. ✅ Gradio 5.44.1 for modern, responsive UI

---

### Metrics & Success Criteria

**Deployment Success:**
- ✅ 2/2 containers deployed successfully
- ✅ 2/2 SSL certificates obtained and configured
- ✅ 2/2 Gradio UIs accessible via HTTPS
- ✅ 0 breaking changes to existing integrations
- ✅ 100% container health status

**User Impact:**
- **Before:** Only API access (technical users only)
- **After:** User-friendly web interface + API access (all users)

**Developer Impact:**
- Zero code changes required in existing applications
- All 35+ hardcoded API references continue to work
- Easy to add more UIs following same pattern

---

### Next Steps

1. **Complete User Testing**
   - Test all features in both UIs
   - Gather user feedback
   - Identify any issues or improvements

2. **Deploy Phase 2: OpenVoice UI**
   - Follow same pattern as Coqui and Kokoro
   - Estimated time: 2-3 days

3. **Deploy Phase 3: MeloTTS UI**
   - Follow same pattern as Coqui and Kokoro
   - Estimated time: 1-2 days

4. **Update User Documentation**
   - Create user guides for each UI
   - Add screenshots and examples
   - Update main README

---

**Implementation Time:** ~4 hours  
**Lines of Code:** ~600 (including Dockerfiles and configs)  
**Containers Added:** 2  
**SSL Certificates:** 2  
**Zero Downtime:** ✅  
**Production Ready:** ✅  


---

## Task: Deploy Gradio Web UIs for TTS Services - PHASE 2 COMPLETE
**Date:** 2025-11-08  
**Status:** ✅ **ALL 4 UIs DEPLOYED** - Coqui, Kokoro, OpenVoice & MeloTTS  
**Priority:** High  
**Objective:** Add user-friendly Gradio interfaces to all major TTS services

### Phase 2 Summary: OpenVoice & MeloTTS UIs

Successfully completed Phase 2 deployment adding OpenVoice and MeloTTS Gradio interfaces.

---

#### 3. ✅ OpenVoice TTS Gradio UI
**Live URL:** https://openvoice-ui.ailabsafrica.com  
**API Backend:** https://openvoice.ailabsafrica.com (unchanged)  
**Container:** openvoice-ui (Port 8013, Healthy)  

**Features Implemented:**
- 2 synthesis modes: Preset voices & Custom voice cloning
- 11 pre-loaded speaker embeddings (EN-US, EN-BR, EN-AU, EN-India, EN-Default, ES, FR, JP, KR, ZH, EN-Newest)
- Custom voice cloning from uploaded audio or microphone recording
- Support for English and Chinese base TTS
- Speed control (0.5x - 2.0x)
- Two-stage architecture: Base TTS + Tone Color Converter
- Audio preview and download (WAV format)
- Tab-based interface for easy mode switching

**Technical Stack:**
- Python 3.11 with Gradio 5.44.1
- OpenVoice V2 Tone Color Converter
- Docker container on tts_network
- Nginx reverse proxy with SSL (Let's Encrypt)
- Certificate expires: 2026-02-06

**Files Created:**
- `/opt/kasaai/apps/tts-deployment/docker/openvoice-ui/app.py` (416 lines)
- `/opt/kasaai/apps/tts-deployment/docker/openvoice-ui/Dockerfile`
- `/etc/nginx/sites-available/openvoice-ui.ailabsafrica.com.conf`
- Updated `/opt/kasaai/apps/tts-deployment/docker-compose.local.yml`

---

#### 4. ✅ MeloTTS Gradio UI
**Live URL:** https://melotts-ui.ailabsafrica.com  
**API Backend:** https://melotts.ailabsafrica.com (unchanged)  
**Container:** melotts-ui (Port 8011, Healthy)  

**Features Implemented:**
- 6 language support (English, Spanish, French, Chinese, Japanese, Korean)
- Dynamic speaker selection (automatically updates when language changes)
- Multiple speakers per language:
  - English: EN-US, EN-BR, EN_INDIA, EN-AU, EN-Default
  - Spanish, French, Chinese, Japanese, Korean: Multiple speakers each
- Speed control slider (0.5x - 2.0x)
- Real-time character counter (max 3000 chars)
- Fast synthesis with MeloTTS
- Audio preview and download (WAV format)
- Clean, simple interface optimized for multilingual TTS

**Technical Stack:**
- Python 3.11 with Gradio 5.44.1
- MeloTTS with lazy model loading
- Docker container on tts_network
- Nginx reverse proxy with SSL (Let's Encrypt)
- Certificate expires: 2026-02-06

**Files Created:**
- `/opt/kasaai/apps/tts-deployment/docker/melotts-ui/app.py` (364 lines)
- `/opt/kasaai/apps/tts-deployment/docker/melotts-ui/Dockerfile`
- `/etc/nginx/sites-available/melotts-ui.ailabsafrica.com.conf`
- Updated `/opt/kasaai/apps/tts-deployment/docker-compose.local.yml`

---

### 🎉 Complete Implementation Summary

**All 4 TTS Gradio UIs Successfully Deployed:**

```
✅ Coqui UI       → https://coqui-ui.ailabsafrica.com     (Port 8015)
✅ Kokoro UI      → https://kokoro-ui.ailabsafrica.com    (Port 8021)
✅ OpenVoice UI   → https://openvoice-ui.ailabsafrica.com (Port 8013)
✅ MeloTTS UI     → https://melotts-ui.ailabsafrica.com   (Port 8011)
```

**API Endpoints (All Unchanged):**
```
✅ Coqui API      → https://coqui.ailabsafrica.com        (Port 8005)
✅ Kokoro API     → https://kokoro.ailabsafrica.com       (Port 8010)
✅ OpenVoice API  → https://openvoice.ailabsafrica.com    (Port 8003)
✅ MeloTTS API    → https://melotts.ailabsafrica.com      (Port 8001)
```

---

### 📊 Total Stats

**Containers Deployed:** 4 UI containers  
**SSL Certificates:** 4 (all expire 2026-02-06)  
**Total Code:** ~1,336 lines across 4 Gradio apps  
**Zero Breaking Changes:** ✅ All 35+ API integrations remain functional  
**Container Health:** 100% (all 4 healthy)  
**Deployment Time:** ~6 hours total  

---

### 🎯 Feature Comparison

| Feature | Coqui UI | Kokoro UI | OpenVoice UI | MeloTTS UI |
|---------|----------|-----------|--------------|------------|
| **Languages** | 17 | 1 (English) | 2 (EN, ZH) | 6 (EN, ES, FR, ZH, JP, KR) |
| **Speakers** | Voice cloning | 11 voices | 11 presets + cloning | 5+ per language |
| **Voice Cloning** | ✅ | ❌ | ✅ | ❌ |
| **Speed Control** | ✅ | ✅ | ✅ | ✅ |
| **Max Characters** | 5000 | Unlimited | 2000 | 3000 |
| **Special Features** | Advanced audio controls | Fast synthesis | Two-stage conversion | Multilingual |
| **Use Case** | High-quality multilingual with cloning | Fast, multi-voice | Voice cloning & conversion | General multilingual TTS |

---

### 🚀 User Access Points

All UIs are now publicly accessible with HTTPS:

1. **Coqui UI:** https://coqui-ui.ailabsafrica.com
   - Best for: High-quality TTS with voice cloning in 17 languages

2. **Kokoro UI:** https://kokoro-ui.ailabsafrica.com
   - Best for: Fast synthesis with 11 unique voices

3. **OpenVoice UI:** https://openvoice-ui.ailabsafrica.com
   - Best for: Voice cloning and tone color conversion

4. **MeloTTS UI:** https://melotts-ui.ailabsafrica.com
   - Best for: Multilingual TTS in 6 languages

---

### 💻 Management Commands

**View all UI containers:**
```bash
sudo docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep ui
```

**Restart all UIs:**
```bash
sudo docker-compose -f docker-compose.local.yml restart coqui-ui kokoro-ui openvoice-ui melotts-ui
```

**View logs for all UIs:**
```bash
sudo docker-compose -f docker-compose.local.yml logs -f coqui-ui kokoro-ui openvoice-ui melotts-ui
```

**Rebuild all UIs:**
```bash
sudo docker-compose -f docker-compose.local.yml build coqui-ui kokoro-ui openvoice-ui melotts-ui
```

---

### ✅ Success Metrics

**Technical Success:**
- ✅ 4/4 containers deployed and healthy
- ✅ 4/4 SSL certificates obtained and configured
- ✅ 4/4 Gradio UIs accessible via HTTPS
- ✅ 0 breaking changes to existing integrations
- ✅ 100% container health status
- ✅ WebSocket support working on all UIs

**User Impact:**
- **Before:** Only API access (developers/technical users only)
- **After:** User-friendly web interfaces + API access (accessible to all users)

**Coverage:**
- ✅ Voice Cloning: Coqui + OpenVoice
- ✅ Multilingual: Coqui (17), MeloTTS (6), OpenVoice (2)
- ✅ Fast Synthesis: Kokoro + MeloTTS
- ✅ Advanced Control: Coqui (temperature, penalties, etc.)
- ✅ Multiple Voices: Kokoro (11), MeloTTS (5+ per language), OpenVoice (11 presets)

---

### 📝 Next Steps

**Immediate:**
1. ✅ All UIs deployed and accessible
2. ☐ User testing and feedback collection
3. ☐ Performance monitoring and optimization
4. ☐ Create user documentation/tutorials

**Future Enhancements:**
1. ☐ Add audio history/favorites
2. ☐ Batch processing support
3. ☐ Custom voice training interface
4. ☐ API key generation for power users
5. ☐ Usage analytics dashboard

---

**Implementation Complete:** 2025-11-08
**Total Implementation Time:** ~6 hours (from planning to deployment)
**Zero Downtime:** ✅
**Production Ready:** ✅
**All Services Live:** ✅

---

## 📋 PHASE 6: TTS SYSTEM IMPROVEMENTS & OPTIMIZATIONS

**Status:** Planning
**Start Date:** 2025-11-08
**Priority:** High
**Based on:** Comprehensive TTS landscape review and community feedback

### 🎯 Overview

Following industry analysis and TTS arena rankings, this phase focuses on:
1. Adding top-ranked TTS models currently missing from our lab
2. Optimizing existing systems for better performance
3. Implementing advanced features (emotion control, RVC pipeline)

### 📊 Current State Analysis

**What We Have:**
- ✅ F5-TTS (API + Gradio UI) - Good quality, moderate speed
- ✅ StyleTTS2 - Human-level expressiveness
- ✅ Kokoro - Fast synthesis, TTS Arena #1 (no voice cloning)
- ✅ Coqui XTTS - Voice cloning (NOT optimized, slow inference)
- ✅ OpenVoice - Fast voice cloning
- ✅ MeloTTS - Multilingual support

**What's Missing (High Priority):**
- ❌ GPT-SoVITS - Community #1 favorite, superior voice cloning
- ❌ Fish Speech - Community #2 favorite, fast + high quality
- ❌ Zos - New model with emotion sliders (highly requested)
- ❌ Alltalk TTS - XTTS V2 optimized implementation
- ❌ RVC Pipeline - Voice conversion for improved similarity
- ❌ DeepSpeed Optimization - 2x→5x speed improvement for XTTS

### 🚀 Priority 1: GPT-SoVITS Deployment

**Why:** Community #1 favorite, exceptional voice cloning quality

**Tasks:**
- [ ] Research GPT-SoVITS requirements (GPU, dependencies)
- [ ] Clone official repository and review documentation
- [ ] Create Docker container for GPT-SoVITS
- [ ] Implement FastAPI wrapper for API access
- [ ] Deploy Gradio UI on RunPod
- [ ] Create nginx configuration (port 8014)
- [ ] Obtain SSL certificate for gptsovits.ailabsafrica.com
- [ ] Performance benchmarking vs current models
- [ ] Documentation and integration guide

**Expected Specs:**
- Model Size: ~1.5GB
- VRAM Usage: ~6GB
- Inference Speed: ~3-4x real-time
- Quality: Superior voice cloning with few-shot learning

**Timeline:** Week 1-2 (10-15 hours)

### 🚀 Priority 2: Fish Speech Deployment

**Why:** Community #2 favorite, fast inference + high quality

**Tasks:**
- [ ] Research Fish Speech architecture and requirements
- [ ] Set up Fish Speech environment
- [ ] Create Docker container
- [ ] Implement FastAPI API endpoints
- [ ] Deploy Gradio UI on RunPod
- [ ] Create nginx configuration (port 8015)
- [ ] Obtain SSL certificate for fishspeech.ailabsafrica.com
- [ ] Benchmark speed and quality
- [ ] Integration documentation

**Expected Specs:**
- Model Size: ~1.2GB
- VRAM Usage: ~4GB
- Inference Speed: ~5-6x real-time (fast)
- Quality: High naturalness, good prosody

**Timeline:** Week 2-3 (8-12 hours)

### 🚀 Priority 3: Zos with Emotion Controls

**Why:** Cutting-edge emotion control sliders, highly requested feature

**Tasks:**
- [ ] Research Zos model availability and licensing
- [ ] Set up development environment
- [ ] Implement emotion control API (sliders: happiness, sadness, anger, etc.)
- [ ] Create custom Gradio UI with emotion sliders
- [ ] Deploy on RunPod
- [ ] Create nginx configuration (port 8016)
- [ ] Obtain SSL certificate for zos.ailabsafrica.com
- [ ] Test emotion controls with various prompts
- [ ] User guide for emotion parameter tuning

**Expected Specs:**
- Model Size: ~2GB
- VRAM Usage: ~5GB
- Inference Speed: ~3x real-time
- Features: 5+ emotion parameters, fine-grained control

**Timeline:** Week 3-4 (12-16 hours)

### ⚡ Priority 4: XTTS + DeepSpeed Optimization

**Why:** Current XTTS is 2x real-time, DeepSpeed can achieve 5x (2.5x improvement)

**Tasks:**
- [ ] Install DeepSpeed in tts-venv
- [ ] Research XTTS DeepSpeed integration examples
- [ ] Modify existing Coqui TTS setup to use DeepSpeed
- [ ] Configure inference optimization settings
- [ ] Benchmark before/after performance
- [ ] Update API to use optimized model
- [ ] Test voice cloning quality (ensure no degradation)
- [ ] Update documentation with new specs

**Expected Improvement:**
- Current: ~2x real-time (slow)
- Target: ~5x real-time (fast)
- Quality: No degradation
- VRAM: May increase slightly

**Timeline:** Week 2-3 (6-8 hours)

### 🎵 Priority 5: RVC Pipeline Integration

**Why:** Post-processing to improve voice similarity and quality

**Tasks:**
- [ ] Research RVC (Retrieval-based Voice Conversion) models
- [ ] Set up RVC environment on RunPod
- [ ] Create RVC training pipeline for reference voices
- [ ] Implement API endpoint: TTS → RVC post-processing
- [ ] Test pipeline with all TTS models
- [ ] Benchmark quality improvement
- [ ] Create fine-tuning UI for custom voice models
- [ ] Documentation for end-to-end voice cloning workflow

**Expected Features:**
- Voice conversion after TTS synthesis
- Custom voice model training
- Improved speaker similarity
- Optional post-processing step

**Timeline:** Week 4-5 (15-20 hours)

### 🔍 Priority 6: Alltalk TTS Evaluation

**Why:** Claims to be optimized XTTS V2 implementation

**Tasks:**
- [ ] Research Alltalk TTS architecture
- [ ] Compare with our current XTTS setup
- [ ] Test deployment on RunPod
- [ ] Benchmark vs XTTS + DeepSpeed
- [ ] Evaluate ease of use and API design
- [ ] Decision: Replace XTTS or keep as alternative?
- [ ] Documentation of findings

**Timeline:** Week 5-6 (4-6 hours evaluation)

### 📅 Implementation Timeline

**Phase 1: Core Improvements (Weeks 1-2)**
- GPT-SoVITS deployment
- XTTS + DeepSpeed optimization
- Initial performance benchmarking

**Phase 2: Expansion (Weeks 3-4)**
- Fish Speech deployment
- Zos with emotion controls
- Advanced feature testing

**Phase 3: Advanced Features (Weeks 5-6)**
- RVC pipeline integration
- Fine-tuning UI development
- Alltalk TTS evaluation
- Comprehensive documentation

### 💰 Budget Estimates

**RunPod A40 GPU:** $0.79/hour

**Development Costs:**
- GPT-SoVITS: 15h × $0.79 = ~$12
- Fish Speech: 12h × $0.79 = ~$9.50
- Zos: 16h × $0.79 = ~$12.50
- XTTS+DeepSpeed: 8h × $0.79 = ~$6.50
- RVC Pipeline: 20h × $0.79 = ~$16
- Alltalk Eval: 6h × $0.79 = ~$5

**Total Development:** ~$61.50

**Monthly Runtime Costs (all services running 24/7):**
- Current 4 services: 730h × $0.79 = ~$577/month
- With 3 new services: 730h × $0.79 = ~$577/month (same pod)

**Note:** All services can run on single A40 GPU (46GB VRAM sufficient)

### 📈 Expected Performance Improvements

| Model | Speed (Before) | Speed (After) | Quality | Voice Cloning |
|-------|---------------|---------------|---------|---------------|
| XTTS | 2x real-time | 5x real-time (DeepSpeed) | Same | ✅ |
| GPT-SoVITS | N/A | 3-4x real-time | Superior | ✅ |
| Fish Speech | N/A | 5-6x real-time | High | ✅ |
| Zos | N/A | 3x real-time | High + Emotions | ❌ |
| F5-TTS | 4x real-time | Same | High | ✅ |
| StyleTTS2 | 3x real-time | Same | Excellent | ✅ |

### 🎨 New Features to Implement

**1. Emotion Control Interface:**
- Happiness slider (0-100)
- Sadness slider (0-100)
- Anger slider (0-100)
- Surprise slider (0-100)
- Neutral slider (0-100)
- Available for: Zos, potentially StyleTTS2

**2. RVC Post-Processing:**
- Optional voice conversion step
- Custom voice model training UI
- Upload reference audio → train RVC model → apply to any TTS output

**3. Fine-Tuning Interface:**
- Upload voice samples (5-10 minutes)
- One-click fine-tuning
- Model management dashboard
- Available for: GPT-SoVITS, XTTS

**4. Unified TTS Lab Dashboard:**
- Single interface to access all 9+ TTS models
- Side-by-side comparison tool
- Batch synthesis across multiple models
- Performance metrics display

### 🧪 Testing & Validation

**Quality Benchmarks:**
- [ ] MOS (Mean Opinion Score) testing with 10+ users
- [ ] Speaker similarity measurements (cosine similarity)
- [ ] Intelligibility tests (WER - Word Error Rate)
- [ ] Naturalness ratings (1-5 scale)
- [ ] Emotion accuracy testing (for Zos)

**Performance Benchmarks:**
- [ ] RTF (Real-Time Factor) for all models
- [ ] GPU memory usage profiles
- [ ] Concurrent request handling
- [ ] Cold start latency
- [ ] Average response time

**Integration Tests:**
- [ ] API endpoint functionality (all models)
- [ ] Gradio UI responsiveness
- [ ] SSL certificate validity
- [ ] Load balancing behavior
- [ ] Error handling and recovery

### 📚 Documentation Requirements

**For Each New Model:**
- [ ] API reference with examples
- [ ] Gradio UI user guide
- [ ] Voice cloning tutorial
- [ ] Best practices and tips
- [ ] Troubleshooting guide

**System Documentation:**
- [ ] Update README.md services table
- [ ] Update CLAUDE.md with new ports
- [ ] Create TTS_MODEL_COMPARISON.md
- [ ] Update nginx configuration docs
- [ ] Create EMOTION_CONTROLS.md guide

### 🔧 Infrastructure Updates Needed

**RunPod Configuration:**
- [ ] Expose ports 8014-8016 (3 new services)
- [ ] Update nginx.conf with new server blocks
- [ ] Ensure 46GB VRAM sufficient for all models
- [ ] Configure persistent storage for model weights

**Local Server Configuration:**
- [ ] Create 3 new nginx configs (gptsovits, fishspeech, zos)
- [ ] Obtain 3 new SSL certificates
- [ ] Update DNS records (3 new subdomains)
- [ ] Test CORS and proxy settings

**Monitoring:**
- [ ] Add new services to health check endpoints
- [ ] Configure alerting for model failures
- [ ] Set up performance monitoring dashboards
- [ ] Track GPU utilization per model

### ✅ Success Criteria

**Deployment Success:**
- All 3 new models deployed and accessible via HTTPS
- XTTS speed improved from 2x to 5x real-time
- RVC pipeline functional with custom voice training
- Zero downtime during deployment
- All existing services remain operational

**Quality Success:**
- MOS score ≥4.0 for GPT-SoVITS
- MOS score ≥4.0 for Fish Speech
- Emotion control demonstrably affects output (Zos)
- RVC improves speaker similarity by ≥10%
- No quality degradation from DeepSpeed optimization

**User Experience Success:**
- All Gradio UIs intuitive and functional
- API documentation complete and accurate
- Response time ≤5 seconds for 10-second audio
- Emotion sliders provide real-time preview
- Fine-tuning completes in <30 minutes

### 🚨 Risks & Mitigation

**Risk 1: GPU VRAM Limits**
- Current usage: ~30GB / 46GB with 4 services
- New services: +15GB estimated
- Mitigation: Load models on-demand, unload unused models
- Fallback: Upgrade to A100 (80GB VRAM) if needed

**Risk 2: Model Compatibility**
- Some models may conflict (PyTorch versions, dependencies)
- Mitigation: Use separate virtual environments per model
- Test thoroughly in staging before production

**Risk 3: Licensing Issues**
- GPT-SoVITS, Fish Speech may have usage restrictions
- Mitigation: Review licenses before deployment
- Use only models with commercial-friendly licenses

**Risk 4: Performance Degradation**
- Too many concurrent models may slow inference
- Mitigation: Implement request queuing and load balancing
- Monitor response times and scale if needed

### 📊 KPIs to Track

**Performance KPIs:**
- Average RTF (Real-Time Factor) across all models
- 95th percentile response time
- GPU utilization (target: 60-80%)
- Concurrent request capacity

**Quality KPIs:**
- Average MOS score across models
- Speaker similarity score (cosine distance)
- User satisfaction rating
- Error rate / failed synthesis attempts

**Business KPIs:**
- API usage per model
- User adoption of new models
- Cost per synthesis (GPU hours / requests)
- User retention and engagement

---

**Phase 6 Summary:**
- **New Models:** GPT-SoVITS, Fish Speech, Zos
- **Optimizations:** XTTS + DeepSpeed (2.5x speed improvement)
- **New Features:** Emotion controls, RVC pipeline, fine-tuning UI
- **Timeline:** 6 weeks
- **Budget:** ~$62 development + $577/month runtime (no increase)
- **Expected Outcome:** 9+ TTS models, comprehensive voice lab, industry-leading capabilities

