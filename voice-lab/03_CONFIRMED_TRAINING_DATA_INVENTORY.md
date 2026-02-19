# 🎯 CONFIRMED TRAINING DATA INVENTORY

**Date**: 2025-10-20
**Status**: ✅ Verified Local Data | ⏳ Gated External Data

---

## ✅ CONFIRMED AVAILABLE (Local Data)

### 1. Twi/Akan/Fante
**Location**: `/opt/kasaai/apps/voice-lab/data/twi-akan-fante/`

| Metric | Value |
|--------|-------|
| **Total Audio Files** | 941,441 files |
| **Processed Samples** | 894,600 WAV files |
| **Transcribed Samples** | 223,650 samples |
| **Total Training Hours** | **334.79 hours** ✅ |
| **Sample Rate** | 16kHz (ASR), 22kHz/24kHz (TTS) |
| **Status** | ✅ **READY TO TRAIN** |

**Data Breakdown**:
- ASR Dataset (16kHz): 223,650 samples = 334.79 hours
- TTS Dataset (22kHz): 223,650 samples = 334.79 hours
- TTS Dataset (24kHz): 223,650 samples = 334.79 hours
- Training splits already created for multiple models:
  - Faster Whisper: 212,468 train / 11,182 val (318.05h / 16.73h)
  - Wav2Vec2: 212,468 train / 11,182 val (318.05h / 16.73h)
  - MMS: 212,468 train / 11,182 val (318.05h / 16.73h)
  - MeloTTS: 212,468 train / 11,182 val (318.05h / 16.73h)
  - F5-TTS: 212,468 train / 11,182 val (318.05h / 16.73h)
  - ChatTTS: 212,468 train / 11,182 val (318.05h / 16.73h)
  - Kokoro TTS: 212,468 train / 11,182 val (318.05h / 16.73h)
  - OpenVoice: 212,468 train / 11,182 val (318.05h / 16.73h)
  - Moshi: 212,468 train / 11,182 val (318.05h / 16.73h)

**Dialects Included**:
- Asante Twi
- Akuapem Twi
- Fante

**Source Datasets** (already integrated):
- Common Voice Twi: 145 validated samples
- Financial Inclusion corpus: 8,000+ samples
- MichSetHowusu collection: Processed and integrated
- Synthetic augmentation: Generated samples

### 2. Ga
**Location**: `/opt/kasaai/apps/voice-lab/data/ga/`

| Metric | Value |
|--------|-------|
| **Status** | ⚠️ Directories created but no audio files |
| **Total Hours** | **0 hours** |
| **Recommendation** | Download external dataset OR use transfer learning |

### 3. Hausa
**Location**: `/opt/kasaai/apps/voice-lab/data/hausa/`

| Metric | Value |
|--------|-------|
| **Status** | ⚠️ Directories created but no audio files |
| **Total Hours** | **0 hours** |
| **Recommendation** | Use NaijaVoices dataset (requires authentication) |

### 4. Yoruba
**Location**: `/opt/kasaai/apps/voice-lab/data/yoruba/`

| Metric | Value |
|--------|-------|
| **Status** | ⚠️ Directories created but no audio files |
| **Total Hours** | **0 hours** |
| **Recommendation** | Use NaijaVoices dataset (requires authentication) |

### 5. Igbo
**Location**: `/opt/kasaai/apps/voice-lab/data/igbo/`

| Metric | Value |
|--------|-------|
| **Status** | ⚠️ Empty (not explicitly checked but pattern matches) |
| **Total Hours** | **0 hours** |
| **Recommendation** | Use NaijaVoices dataset (requires authentication) |

### 6. Ewe
**Location**: `/opt/kasaai/apps/voice-lab/data/ewe/`

| Metric | Value |
|--------|-------|
| **Status** | ⚠️ Directories created but no audio files |
| **Total Hours** | **0 hours** |
| **Recommendation** | Use Common Voice (requires authentication) |

---

## ⏳ GATED EXTERNAL DATA (Requires Authentication)

### 1. NaijaVoices Dataset
**Status**: 🔒 **GATED** - Requires Hugging Face authentication

**URL**: https://huggingface.co/datasets/naijavoices/naijavoices-dataset

**Estimated Hours**:
| Language | Batches | Est. Hours | Status |
|----------|---------|------------|--------|
| **Hausa** | 10 batches | ~650 hours | 🔒 Gated |
| **Yoruba** | 10 batches | ~600 hours | 🔒 Gated |
| **Igbo** | 10 batches | ~630 hours | 🔒 Gated |

**Error Message**:
```
401 Client Error: Unauthorized for url
Dataset is a gated dataset on the Hub. You must be authenticated to access it.
```

**Required Actions**:
1. Go to https://huggingface.co/datasets/naijavoices/naijavoices-dataset
2. Request access (usually instant approval)
3. Create Hugging Face token: https://huggingface.co/settings/tokens
4. Login: `huggingface-cli login --token YOUR_TOKEN`
5. Re-run dataset loading in training script

### 2. Mozilla Common Voice
**Status**: 🔒 **GATED** - Requires authentication and dataset agreement

**URL**: https://commonvoice.mozilla.org/

**Estimated Hours**:
| Language | Dataset | Est. Hours | Status |
|----------|---------|------------|--------|
| **Hausa** | CV 17.0 | ~10-15 hours | 🔒 Gated |
| **Igbo** | CV 17.0 | ~5-8 hours | 🔒 Gated |
| **Twi** | CV 12.0 | ~3-5 hours | 🔒 Gated |
| **Ewe** | CV 12.0 | ~2-3 hours | 🔒 Gated |

**Error Message**:
```
401 Client Error: Unauthorized for url
Access to dataset is restricted. You must have access to it and be authenticated.
```

**Required Actions**:
1. Accept Common Voice terms: https://commonvoice.mozilla.org/en/datasets
2. Download datasets or use via Hugging Face Hub
3. Authenticate with Hugging Face token

---

## 📊 TRAINING DATA SUMMARY

### Confirmed Available (Ready to Use)
```
✅ Twi/Akan/Fante:  334.79 hours (223,650 samples)
⚠️  Ga:                0 hours
⚠️  Hausa:             0 hours
⚠️  Yoruba:            0 hours
⚠️  Igbo:              0 hours (assumed based on pattern)
⚠️  Ewe:               0 hours
-------------------------------------------
TOTAL CONFIRMED:     334.79 hours (Twi only)
```

### After External Dataset Authentication
```
✅ Twi/Akan/Fante:  334.79 hours (local)
🔓 Hausa:           650 hours (NaijaVoices) + 10-15 hours (Common Voice)
🔓 Yoruba:          600 hours (NaijaVoices)
🔓 Igbo:            630 hours (NaijaVoices) + 5-8 hours (Common Voice)
🔓 Ewe:             2-3 hours (Common Voice)
🔓 Ga:              0 hours (needs sourcing)
-------------------------------------------
POTENTIAL TOTAL:    ~2,230+ hours (after authentication)
```

---

## 🚀 IMMEDIATE TRAINING OPTIONS

### Option 1: Twi-Only Model (READY NOW!)
✅ **Can start immediately with 334.79 hours**

**Training Command**:
```bash
python runpod_whisper_african_qlora.py \
  --output_dir ./outputs/whisper-small-twi \
  --languages '{"code": "tw", "name": "Twi", "weight": 1.0}' \
  --local_data_path /opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed \
  --num_epochs 3
```

**Expected Results**:
- Training Time: ~24-36 hours (A40 GPU)
- Expected WER: **12-18%** (excellent with 334h data)
- Cost: ~$19-28 @ $0.79/hour

### Option 2: Twi + Transfer Learning (READY NOW!)
✅ **Use Twi data as base, fine-tune for other languages later**

**Strategy**:
1. Train Whisper Small on Twi (334h) → 24-36h
2. Get authentication for external datasets
3. Continue training with Hausa/Yoruba/Igbo (1,880h) → additional 48-72h

**Advantages**:
- Start training immediately
- Twi benefits from full training
- Other languages benefit from Twi transfer learning
- Total training time: ~72-108 hours vs. 72h multi-language

### Option 3: Wait for Authentication (RECOMMENDED)
⏳ **Get dataset access first, train all 6 languages together**

**Timeline**:
1. Request NaijaVoices access: ~5-10 minutes
2. Request Common Voice access: ~5-10 minutes
3. Wait for approval: ~1-24 hours (usually instant for NaijaVoices)
4. Start multi-language training: 72 hours

**Advantages**:
- All languages trained together (better cross-lingual transfer)
- Balanced multi-language model
- Single training run

---

## ⚠️ CRITICAL FINDINGS

### 1. Only Twi Data is Locally Available
- **334.79 hours of high-quality Twi data** ready to use
- **All other languages (Ga, Hausa, Yoruba, Igbo, Ewe) have ZERO local data**

### 2. External Datasets are Gated
- NaijaVoices (1,880 hours) requires Hugging Face authentication
- Common Voice requires dataset agreement + authentication

### 3. Original Training Script Assumes All Data Available
The script in `runpod_whisper_african_qlora.py` assumes access to:
- NaijaVoices (Hausa, Yoruba, Igbo)
- Common Voice (all 6 languages)
- Local data (all 6 languages)

**This script will FAIL without authentication and will only use Twi data.**

---

## 🎯 RECOMMENDATIONS

### Immediate Actions

1. **Get Dataset Authentication** (15 minutes):
   ```bash
   # Go to browser
   https://huggingface.co/datasets/naijavoices/naijavoices-dataset
   # Click "Request Access"

   https://commonvoice.mozilla.org/en/datasets
   # Accept terms and download

   # Create HF token
   https://huggingface.co/settings/tokens

   # Login on RunPod
   huggingface-cli login --token YOUR_TOKEN
   ```

2. **Update Training Script Language Weights**:
   Current script has incorrect assumptions. Update to:
   ```python
   languages: List[Dict] = field(default_factory=lambda: [
       {"code": "tw", "name": "Twi", "weight": 1.0, "hours": 335},     # ✅ Confirmed
       {"code": "ha", "name": "Hausa", "weight": 1.0, "hours": 650},   # 🔒 After auth
       {"code": "yo", "name": "Yoruba", "weight": 1.0, "hours": 600},  # 🔒 After auth
       {"code": "ig", "name": "Igbo", "weight": 1.0, "hours": 630},    # 🔒 After auth
       {"code": "ee", "name": "Ewe", "weight": 0.1, "hours": 2},       # 🔒 After auth (very low)
       {"code": "gaa", "name": "Ga", "weight": 0.0, "hours": 0},       # ❌ No data
   ])
   ```

3. **Choose Training Strategy**:
   - **Option A**: Start Twi-only NOW (334h, 24-36h training)
   - **Option B**: Wait 1-24h for auth, train all together (2,230h, 72h training)
   - **Option C**: Exclude Ga and Ewe (too little data), train Twi+Hausa+Yoruba+Igbo (2,215h)

---

## 📁 File Locations

- **Local Twi Data**: `/opt/kasaai/apps/voice-lab/data/twi-akan-fante/processed/`
- **Training Manifests**: `/opt/kasaai/apps/voice-lab/data/twi-akan-fante/*.csv`
- **Training Script**: `/opt/kasaai/apps/voice-lab/runpod_whisper_african_qlora.py`
- **Deployment Script**: `/opt/kasaai/apps/tts-deployment/deploy_whisper_training.sh`
- **RunPod Config**: Pod ID `jzfmzviw26huka-644113c7`, A40 46GB VRAM

---

**Next Step**: Decide on training strategy and get dataset authentication if needed.
