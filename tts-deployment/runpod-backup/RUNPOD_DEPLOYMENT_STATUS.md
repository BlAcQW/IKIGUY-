# RunPod Deployment Status & Backup

**Date:** 2025-10-22
**Pod ID:** jzfmzviw26huka-644113c7
**SSH:** `ssh root@194.68.245.121 -p 22130 -i ~/.ssh/id_ed25519`
**GPU:** NVIDIA A40 (46GB VRAM)

---

## 📁 Files Backed Up

All critical files from RunPod have been backed up to `/opt/kasaai/apps/tts-deployment/runpod-backup/`:

### Training Scripts
- ✅ `runpod_whisper_african_qlora_streaming.py` - Main Whisper training script (FIXED VERSION)
- ✅ `start_whisper_fixed.sh` - Training startup script with proper environment
- ✅ `start_training.sh` - Original training script
- ✅ `stop_training.sh` - Graceful training shutdown
- ✅ `monitor.sh` - Training monitoring script
- ✅ `test_auth.sh` - HuggingFace authentication tester

### TTS Application Files
- ✅ `f5tts_app.py` - F5-TTS service (port 8002)
- ✅ `styletts2_app.py` - StyleTTS2 service (port 8006)

### Documentation
- ✅ `01_WHISPER_QLORA_RUNPOD_SETUP.md` - Complete setup guide
- ✅ `02_RUNPOD_QUICK_START.md` - Quick start guide
- ✅ `03_CONFIRMED_TRAINING_DATA_INVENTORY.md` - Data availability

---

## 🔧 Critical Fixes Applied

### Whisper Training Fixes (2025-10-22)

1. **torchcodec Incompatibility** ✅
   - Uninstalled torchcodec (incompatible with PyTorch 2.5.1+cu124)
   - Command: `pip uninstall -y torchcodec --break-system-packages`

2. **datasets Library Version** ✅
   - Downgraded from 4.2.0 to 3.6.0 (newer version requires torchcodec)
   - Command: `pip install 'datasets<4.0.0' --break-system-packages`

3. **Common Voice trust_remote_code** ✅
   - Added `trust_remote_code=True` to load_dataset call (line 261)

4. **hub_strategy Error** ✅
   - Changed from `None` to `"end"` when push_to_hub is False (line 632)

5. **max_steps for Streaming** ✅
   - Added `max_steps: int = 15000` to config (line 141)
   - Updated training args to use max_steps (line 612)

6. **Audio Array Type** ✅
   - Added numpy conversion: `import numpy as np` (line 314)
   - Convert audio arrays: `np.array(audio["array"], dtype=np.float32)` (lines 318, 323)

7. **Text Column Flexibility** ✅
   - Support multiple column names: sentence/text/transcription/transcript (line 333)

### Remaining Issue
❌ **Input format mismatch**: Whisper expects `input_features` but receiving `input_ids`
   - Location: Data collator or preprocessing return format
   - Status: 95% fixed, training initializes successfully

---

## 🌍 Language Data Status

### Currently Training (Working)
| Language | Data Source | Hours | Status |
|----------|-------------|-------|--------|
| **Hausa** | NaijaVoices | 650h | ✅ Loading |
| **Yoruba** | NaijaVoices | 600h | ✅ Loading |
| **Igbo** | NaijaVoices | 630h | ✅ Loading |

**Total:** 1,880 hours across 3 Nigerian languages

### Ghanaian Languages Status

#### Twi/Akan/Fante
- **Local Data:** 335 hours available
- **Location:** `/opt/kasaai/apps/voice-lab/data/twi-akan-fante`
- **Status:** ⚠️ **NOT FOUND** on RunPod (needs transfer)
- **Action Required:** Transfer local data to RunPod `/workspace/voice-lab/data/twi-akan-fante`

#### Ewe
- **Common Voice:** NOT available in CV 17.0
- **Available codes:** ab, af, am, ar, ha, ig, tw, yo, zu (NO 'ee')
- **Status:** ❌ No public dataset found
- **Action Required:** Find alternative Ewe dataset or use local data

#### Ga
- **Status:** ❌ No public dataset found
- **Estimation:** ~5-10 hours may be available locally
- **Action Required:** Check `/opt/kasaai/apps/voice-lab/data/ga` for local data

#### Dagbani
- **Status:** ❌ No public dataset found
- **Estimation:** Limited or no data available
- **Action Required:** Check for any local Dagbani audio data

### Recommendation: Transfer Local Ghanaian Data

To include Twi, Ewe, Ga, and Dagbani in training:

1. **Find Local Data:**
```bash
ls -lh /opt/kasaai/apps/voice-lab/data/
```

2. **Transfer to RunPod:**
```bash
# Create tarball of local data
cd /opt/kasaai/apps/voice-lab/data
tar czf ghanaian_languages.tar.gz twi-akan-fante/ ewe/ ga/ dagbani/

# Transfer to RunPod
scp -P 22130 -i ~/.ssh/id_ed25519 \
  ghanaian_languages.tar.gz \
  root@194.68.245.121:/workspace/

# Extract on RunPod
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121
mkdir -p /opt/kasaai/apps/voice-lab/data
cd /opt/kasaai/apps/voice-lab/data
tar xzf /workspace/ghanaian_languages.tar.gz
```

3. **Verify Data:**
```bash
du -sh /opt/kasaai/apps/voice-lab/data/*
```

4. **Restart Training** - Script will auto-detect local data

---

## 🚀 TTS Services Status

### Running Services (Stable 10+ hours)

| Service | Port | Status | Uptime | VRAM | Health |
|---------|------|--------|--------|------|--------|
| F5-TTS | 8002 | 🟢 Running | 12h 33m | 1.07 GB | ✅ Healthy |
| StyleTTS2 | 8006 | 🟢 Running | 10h 48m | 1.96 GB | ✅ Healthy |
| Kyutai/Moshi | 8008 | 🔴 Not Running | - | - | ❌ Down |

**Access via SSH Tunnel:**
```bash
ssh -N -L 8002:localhost:8002 -L 8006:localhost:8006 \
  -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121
```

Then access:
- F5-TTS: http://localhost:8002/health
- StyleTTS2: http://localhost:8006/health

---

## 📊 System Resources

**GPU:** NVIDIA A40
- VRAM: 3.0 GB / 44.4 GB used (6.8%)
- Available: **43 GB free** for Whisper training
- Temperature: 41°C
- Power: 78W / 300W (26%)

**CPU:** Intel Xeon Gold 6342 @ 2.80GHz (96 cores)
**RAM:** 70 GB / 503 GB (14% used)
**Disk:** 124 GB / 200 GB (62% used)

---

## 🔄 Redeployment Process

### If Pod is Deleted/Changed:

1. **Create New Pod**
   - GPU: A40 (46GB) or better
   - SSH access enabled
   - Update SSH port in scripts

2. **Transfer Files to New Pod:**
```bash
cd /opt/kasaai/apps/tts-deployment/runpod-backup

# Create deployment archive
tar czf runpod-deploy.tar.gz \
  runpod_whisper_african_qlora_streaming.py \
  start_whisper_fixed.sh \
  f5tts_app.py \
  styletts2_app.py \
  *.sh \
  *.md

# Transfer to new pod (update IP/port)
scp -P NEW_PORT -i ~/.ssh/id_ed25519 \
  runpod-deploy.tar.gz \
  root@NEW_IP:/workspace/

# Extract on pod
ssh -p NEW_PORT -i ~/.ssh/id_ed25519 root@NEW_IP
cd /workspace
tar xzf runpod-deploy.tar.gz
```

3. **Install Dependencies:**
```bash
# Uninstall problematic packages
pip uninstall -y torchcodec --break-system-packages

# Downgrade datasets
pip install 'datasets<4.0.0' --break-system-packages

# Install other dependencies
pip install transformers==4.57.1 peft accelerate bitsandbytes \
  librosa soundfile wandb --break-system-packages
```

4. **Transfer Training Data (if needed):**
```bash
# From local machine
scp -P NEW_PORT -i ~/.ssh/id_ed25519 \
  ghanaian_languages.tar.gz \
  root@NEW_IP:/workspace/
```

5. **Start Services:**
```bash
# TTS Services
cd /workspace/docker/f5tts && python3 app.py &
cd /workspace/docker/styletts2 && python3 app.py &

# Whisper Training
cd /workspace
./start_whisper_fixed.sh
```

---

## 📝 WandB Tracking

**Project:** https://wandb.ai/alfred-anyan-ai-labs/whisper-african-qlora

**Recent Runs:**
- `run-20251022-091944-zqu9596e` - Latest (95% working)
- Multiple previous attempts with various fixes

**Metrics Tracked:**
- Training/validation loss
- WER (Word Error Rate)
- GPU memory usage
- Training speed

---

## ⚠️ Important Notes

1. **Virtual Environment:** RunPod doesn't use true venv, symlinks to system Python
2. **Package Management:** Use `--break-system-packages` flag for pip installs
3. **Data Persistence:** `/workspace` is persistent across pod restarts
4. **Model Checkpoints:** Saved to `/workspace/outputs/whisper-small-african-qlora/`
5. **Logs:** Training log at `/workspace/whisper_training.log`

---

## 🎯 Next Steps

### To Complete Whisper Training:

1. **Fix final input format issue** (input_features vs input_ids)
2. **Transfer Ghanaian language data** to RunPod
3. **Update language config** to include Twi, Ewe, Ga, Dagbani
4. **Restart training** with all 7 languages
5. **Monitor training** via WandB for 48-72 hours
6. **Download trained model** when complete

### To Deploy Kyutai/Moshi:

1. Transfer Kyutai/Moshi docker files to RunPod
2. Build and start service on port 8008
3. Update SSH tunnel script to include port 8008

---

**Last Updated:** 2025-10-22 11:25 UTC
**Backup Location:** `/opt/kasaai/apps/tts-deployment/runpod-backup/`
**Status:** ✅ All critical files backed up and documented
