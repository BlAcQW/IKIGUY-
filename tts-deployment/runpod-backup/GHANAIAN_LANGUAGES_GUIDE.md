# Ghanaian Languages Training Guide

**Date:** 2025-10-22
**Status:** Data Available - Ready to Transfer to RunPod

---

## 📊 Local Data Inventory

We have significant Ghanaian language data available locally:

| Language | Directory | Size | Estimated Hours | Status |
|----------|-----------|------|-----------------|--------|
| **Twi/Akan/Fante** | `/opt/kasaai/apps/voice-lab/data/twi-akan-fante` | **480 GB** | **~335-400 hours** | ✅ Available |
| **Ga** | `/opt/kasaai/apps/voice-lab/data/ga` | **792 MB** | **~5-10 hours** | ✅ Available |
| **Ewe** | `/opt/kasaai/apps/voice-lab/data/ewe` | **32 KB** | **~0.5 hours** | ⚠️ Very limited |
| **Dagbani** | N/A | **0** | **0 hours** | ❌ Not found |

**Total Available:** ~340-410 hours of Ghanaian language audio

---

## 🚨 Current Training Status

### Running on RunPod (Nigerian Languages)
Currently training on 3 Nigerian languages from NaijaVoices dataset:
- **Hausa:** 650 hours (streaming from HuggingFace)
- **Yoruba:** 600 hours (streaming from HuggingFace)
- **Igbo:** 630 hours (streaming from HuggingFace)

### Missing Ghanaian Languages
The training script is configured for 5 languages but only 3 are loading because:
1. **Twi data path not found** on RunPod: `/opt/kasaai/apps/voice-lab/data/twi-akan-fante`
2. **Ewe not available** in Common Voice 17.0 (no 'ee' language code)
3. **Ga/Dagbani** not configured in training script

---

## 🔧 How to Add Ghanaian Languages

### Step 1: Transfer Twi/Akan/Fante Data (480GB)

This is the largest and most important dataset.

**Option A: Direct Transfer (Slow but Simple)**
```bash
# Create tarball (will take time due to size)
cd /opt/kasaai/apps/voice-lab/data
tar czf twi-akan-fante.tar.gz twi-akan-fante/

# Transfer to RunPod (may take hours depending on connection)
scp -P 22130 -i ~/.ssh/id_ed25519 \
  twi-akan-fante.tar.gz \
  root@194.68.245.121:/workspace/

# Extract on RunPod
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121
mkdir -p /opt/kasaai/apps/voice-lab/data
cd /opt/kasaai/apps/voice-lab/data
tar xzf /workspace/twi-akan-fante.tar.gz
```

**Option B: Rsync (Better for Large Files)**
```bash
# Rsync with compression and resume support
rsync -avz --progress -e "ssh -p 22130 -i ~/.ssh/id_ed25519" \
  /opt/kasaai/apps/voice-lab/data/twi-akan-fante/ \
  root@194.68.245.121:/opt/kasaai/apps/voice-lab/data/twi-akan-fante/
```

**Option C: Mount Network Storage (Recommended for 480GB)**
```bash
# If RunPod supports network mount, mount the local voice-lab data
# This avoids copying 480GB and allows real-time access
```

### Step 2: Transfer Ga Data (792MB)

Much smaller, quick transfer:
```bash
cd /opt/kasaai/apps/voice-lab/data
tar czf ga.tar.gz ga/

scp -P 22130 -i ~/.ssh/id_ed25519 \
  ga.tar.gz \
  root@194.68.245.121:/workspace/

# Extract on RunPod
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121
cd /opt/kasaai/apps/voice-lab/data
tar xzf /workspace/ga.tar.gz
```

### Step 3: Update Training Script for Ewe

Since Ewe is not in Common Voice 17.0, we need to either:

**Option A: Skip Ewe (Recommended)**
- Remove Ewe from language configuration (only 32KB anyway)
- Focus on languages with sufficient data

**Option B: Transfer Local Ewe Data**
```bash
# Check what's in the Ewe directory
ls -lh /opt/kasaai/apps/voice-lab/data/ewe/

# If there's actual audio data, transfer it
tar czf ewe.tar.gz ewe/
scp -P 22130 -i ~/.ssh/id_ed25519 ewe.tar.gz root@194.68.245.121:/workspace/
```

### Step 4: Add Ga to Training Configuration

Currently, Ga is not in the training script. To add it:

```python
# In runpod_whisper_african_qlora_streaming.py
# Update the languages list (around line 110):

languages: List[Dict] = field(default_factory=lambda: [
    {"code": "tw", "name": "Twi", "weight": 1.0, "hours": 335, "source": "local"},
    {"code": "ha", "name": "Hausa", "weight": 1.0, "hours": 650, "source": "naijavoices"},
    {"code": "yo", "name": "Yoruba", "weight": 1.0, "hours": 600, "source": "naijavoices"},
    {"code": "ig", "name": "Igbo", "weight": 1.0, "hours": 630, "source": "naijavoices"},
    {"code": "gaa", "name": "Ga", "weight": 0.5, "hours": 10, "source": "local"},  # ADD THIS
    # Remove or comment out Ewe if no data:
    # {"code": "ee", "name": "Ewe", "weight": 0.1, "hours": 2, "source": "common_voice"},
])
```

---

## 📋 Revised Training Plan

### Option 1: Nigerian + Twi Only (Recommended First)
**Total:** ~1,985-2,050 hours

| Language | Hours | Source | Transfer Time |
|----------|-------|--------|---------------|
| Hausa | 650h | NaijaVoices (streaming) | None (already working) |
| Yoruba | 600h | NaijaVoices (streaming) | None (already working) |
| Igbo | 630h | NaijaVoices (streaming) | None (already working) |
| Twi/Akan/Fante | 335-400h | Local | 2-6 hours (480GB) |

**Training Time:** ~65-70 hours
**Cost:** ~$50-55 (A40 @ $0.79/hr)

### Option 2: All Available Languages
**Total:** ~2,000-2,065 hours

| Language | Hours | Source | Transfer Time |
|----------|-------|--------|---------------|
| Hausa | 650h | NaijaVoices | None |
| Yoruba | 600h | NaijaVoices | None |
| Igbo | 630h | NaijaVoices | None |
| Twi/Akan/Fante | 335-400h | Local | 2-6 hours |
| Ga | 5-10h | Local | 5 minutes |

**Training Time:** ~70-75 hours
**Cost:** ~$55-60 (A40 @ $0.79/hr)

---

## ⚡ Quick Start: Add Twi Now

If you want to add Twi data to the current training run:

```bash
# 1. Stop current training
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121
pkill -9 -f runpod_whisper

# 2. Start rsync transfer (run in background, will take hours)
nohup rsync -avz --progress -e "ssh -p 22130 -i ~/.ssh/id_ed25519" \
  /opt/kasaai/apps/voice-lab/data/twi-akan-fante/ \
  root@194.68.245.121:/opt/kasaai/apps/voice-lab/data/twi-akan-fante/ \
  > twi_transfer.log 2>&1 &

# 3. Monitor transfer
tail -f twi_transfer.log

# 4. Once transfer completes, verify
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121
du -sh /opt/kasaai/apps/voice-lab/data/twi-akan-fante/

# 5. Restart training - script will auto-detect Twi data
cd /workspace
./start_whisper_fixed.sh
```

---

## 🔍 Data Verification

After transferring data, verify it's properly structured:

```bash
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121

# Check directory structure
ls -lh /opt/kasaai/apps/voice-lab/data/

# Check Twi data structure
ls -lh /opt/kasaai/apps/voice-lab/data/twi-akan-fante/
# Should contain: train/, validation/, metadata.csv, etc.

# Check audio files exist
find /opt/kasaai/apps/voice-lab/data/twi-akan-fante/train/ -name "*.wav" | head -5
find /opt/kasaai/apps/voice-lab/data/twi-akan-fante/train/ -name "*.mp3" | head -5
```

---

## 📊 Expected Training Results

### With All 5 Languages (Ha, Yo, Ig, Tw, Ga)

**Expected WER (Word Error Rate):**
| Language | Expected WER | Confidence | Reason |
|----------|--------------|------------|--------|
| **Hausa** | 15-20% | ✅ High | 650h high-quality data |
| **Yoruba** | 18-23% | ✅ High | 600h high-quality data |
| **Igbo** | 16-22% | ✅ High | 630h high-quality data |
| **Twi/Akan** | 20-30% | 🟡 Medium | 335-400h local data + cross-lingual transfer |
| **Ga** | 30-40% | 🟡 Medium | Only 5-10h + transfer learning from Twi |

**Overall Model:** Strong multilingual Whisper for West African languages

---

## ⚠️ Important Notes

### Data Format Requirements
The training script expects data in HuggingFace datasets format:
- `train/` folder with audio files
- `validation/` folder with audio files
- CSV or JSON metadata with columns: `audio`, `text`/`sentence`/`transcription`

If local data is in different format, may need preprocessing.

### Storage Considerations
- RunPod `/workspace` is persistent but limited
- 480GB Twi data + models + checkpoints = ~500GB total
- Ensure RunPod instance has sufficient storage (recommend 1TB)

### Network Transfer Time
- 480GB @ 100 Mbps = ~11 hours
- 480GB @ 1 Gbps = ~1 hour
- Consider leaving transfer running overnight

### Checkpointing Strategy
With more languages and data:
- Checkpoint every 2,500 steps (instead of 5,000)
- Keep last 3 checkpoints (in case of failure)
- Auto-push to HuggingFace Hub for backup

---

## 🎯 Recommendation

**Start with Nigerian Languages + Twi** (Option 1):
1. Already have 1,880h Nigerian data streaming successfully
2. Add 335-400h Twi data (significant Ghanaian representation)
3. Test the model quality
4. If successful, add Ga in a second training run

**Benefits:**
- Faster initial training (less data transfer)
- Covers both Nigerian and Ghanaian languages
- Can validate approach before adding smaller languages
- More cost-effective (~$50 vs ~$60)

---

**Last Updated:** 2025-10-22 11:30 UTC
**Data Location:** `/opt/kasaai/apps/voice-lab/data/`
**Status:** ✅ Ready to transfer to RunPod
