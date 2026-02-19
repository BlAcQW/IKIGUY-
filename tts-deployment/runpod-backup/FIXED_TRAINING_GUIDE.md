# Fixed Whisper Training Script - RunPod + Hetzner Storage

**Date:** 2025-10-22
**Status:** ✅ Ready for Testing
**Version:** 2.0 (Storage-Optimized)

---

## 🔧 What Was Fixed

### 1. **Training Script Bug**
- **Problem:** `TypeError: WhisperForConditionalGeneration.forward() got an unexpected keyword argument 'input_ids'`
- **Root Cause:** Audio column wasn't being properly loaded before preprocessing, causing format mismatches
- **Fix:** Implemented proper on-demand audio loading with Hetzner remote fetching

### 2. **Storage Limitation Problem**
- **Problem:** RunPod has storage quotas, can't fit 476GB Twi dataset
- **Solution:** Implemented **manifest-first + on-demand audio fetching**
  - Syncs only CSV manifests (~10MB) instead of full dataset
  - Fetches audio files from Hetzner on-demand during training
  - Caches fetched files locally to avoid re-downloading
  - Total local storage needed: **<50GB** vs 476GB

### 3. **Data Loading Architecture**
- **Old Approach:** Load all data locally → Process → Train
- **New Approach:**
  ```
  Hetzner Storage Box (476GB)
         ↓ (rsync manifests only)
  RunPod Workspace (~10MB manifests)
         ↓ (on-demand audio fetch during training)
  Training Pipeline
  ```

---

## 📊 Storage Comparison

| Component | Old Approach | New Approach | Savings |
|-----------|--------------|--------------|---------|
| Twi Dataset | 476GB local | ~10MB manifests + ~30GB cache | ~436GB |
| HuggingFace Data | Download all | Stream directly | No local storage |
| **Total RunPod Storage** | **>500GB** | **<50GB** | **90% reduction** |

---

## 🚀 Quick Start

### Step 1: Verify Hetzner Connection

```bash
# SSH into RunPod
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121

# Test Hetzner connection
sftp -P 23 -i ~/.ssh/hetzner_key u497034-sub1@u497034-sub1.your-storagebox.de << 'EOF'
ls /home/voice-lab/data/
bye
EOF
```

Expected output:
```
drwxrwxr-x ... twi-akan-fante
drwxrwxr-x ... ga
drwxrwxr-x ... twi-test-dataset
```

### Step 2: Run Tests

```bash
# On RunPod
cd /workspace
python test_hetzner_data_loading.py
```

This will:
1. ✅ Check SSH keys
2. ✅ Sync manifests from Hetzner
3. ✅ Test audio file fetching
4. ✅ Verify preprocessing works

### Step 3: Start Training

```bash
# On RunPod
cd /workspace

# Option A: Train with all languages (Twi + Hausa + Yoruba + Igbo)
python runpod_whisper_african_qlora_streaming_fixed.py

# Option B: Train Twi only (faster testing)
# Edit the script to comment out other languages in config
```

---

## 🏗️ Architecture Overview

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Hetzner Storage Box                                         │
│ u497034-sub1.your-storagebox.de                            │
│                                                             │
│ /home/voice-lab/data/twi-akan-fante/                      │
│ ├── processed/manifests/asr_16k_dataset.csv (10MB)        │
│ ├── processed/processed_audio/ (476GB)                     │
│ └── raw/ (archives)                                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Step 1: Rsync manifests only
                          │ (--include *.csv --exclude *)
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ RunPod Workspace                                            │
│ /workspace/training-data/                                   │
│                                                             │
│ ├── twi-akan-fante/                                        │
│ │   ├── processed/manifests/asr_16k_dataset.csv           │
│ │   └── processed/processed_audio/ (cached files)         │
│ └── cache/ (HuggingFace cache)                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Step 2: Training starts
                          │
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Training Loop                                               │
│                                                             │
│ For each batch:                                            │
│   1. DataLoader requests sample                            │
│   2. Check if audio exists locally                         │
│   3. If not: rsync from Hetzner on-demand                 │
│   4. Cache locally for future epochs                       │
│   5. Preprocess → Train                                    │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. **HetznerDataSync Class**
```python
class HetznerDataSync:
    def sync_manifests_only(language: str) -> bool
        # Syncs only CSV/JSON files, excludes audio

    def get_audio_from_hetzner(audio_path: str, language: str) -> str
        # Fetches single audio file on-demand
        # Returns local cached path
```

#### 2. **MultiLanguageDatasetLoader**
```python
class MultiLanguageDatasetLoader:
    def load_hetzner_data(language_code: str) -> Dataset
        # Loads manifests, returns Dataset with lazy audio loading

    def preprocess_audio(batch: Dict) -> Dict
        # Handles on-demand audio fetching during preprocessing
```

---

## 🔍 What Changed in the Code

### Before (Broken)
```python
def load_local_data(self, language_code: str):
    local_path = Path(f"/opt/kasaai/apps/voice-lab/data/{dir_name}")  # ❌ Wrong path on RunPod

    df = pd.read_csv(manifest_path)
    ds = Dataset.from_pandas(df)
    ds = ds.cast_column("audio_path", Audio(sampling_rate=16000))  # ❌ Loads ALL audio immediately
    return ds
```

### After (Fixed)
```python
def load_hetzner_data(self, language_code: str):
    # Step 1: Sync manifests only
    self.hetzner_sync.sync_manifests_only(dir_name)  # ✅ Only ~10MB

    # Step 2: Load manifest
    df = pd.read_csv(manifest_path)
    df['language_dataset'] = dir_name  # ✅ Track source for on-demand fetching
    ds = Dataset.from_pandas(df)

    # ✅ DON'T cast audio column - we'll fetch on-demand
    return ds

def preprocess_audio(self, batch):
    # ✅ Fetch audio on-demand if needed
    if "original_path" in batch:
        local_path = self.hetzner_sync.get_audio_from_hetzner(
            batch["original_path"],
            batch["language_dataset"]
        )
        audio = load_audio(local_path)  # Only this one file

    # Continue with normal preprocessing
    input_features = self.processor.feature_extractor(audio, ...)
    return batch
```

---

## 📦 Dependencies

All required packages are already installed on RunPod:
- ✅ `transformers`
- ✅ `datasets`
- ✅ `peft`
- ✅ `evaluate`
- ✅ `bitsandbytes`
- ✅ `torchaudio`
- ✅ `librosa`

Additional system tools:
- ✅ `rsync` (for data syncing)
- ✅ `ssh` (for Hetzner connection)

---

## 💾 Storage Usage Monitoring

### Check RunPod Storage
```bash
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 "df -h /workspace"
```

### Check Training Data Cache Size
```bash
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 \
  "du -sh /workspace/training-data/"
```

### Clean Up Cache (if needed)
```bash
# Remove cached audio files (manifests will be preserved)
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 \
  "rm -rf /workspace/training-data/twi-akan-fante/processed/processed_audio/"

# Manifests will auto-sync on next run
```

---

## 🐛 Troubleshooting

### Issue: "SSH key not found"
```bash
# Check if key exists
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 \
  "ls -la /root/.ssh/hetzner_key"

# If not found, regenerate (see EXTERNAL_STORAGE_MOUNTING_GUIDE.md)
```

### Issue: "Manifest not found"
```bash
# Re-sync manifests
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 \
  "cd /workspace && python -c '
from runpod_whisper_african_qlora_streaming_fixed import HetznerDataSync
sync = HetznerDataSync()
sync.sync_manifests_only(\"twi-akan-fante\")
'"
```

### Issue: "Audio file fetch timeout"
- Audio files are fetched with 30s timeout
- If network is slow, some samples may be skipped
- They'll be automatically filtered out in data collator

### Issue: "Out of storage space"
```bash
# Check what's using space
du -sh /workspace/* | sort -h

# Clear HuggingFace cache if needed
rm -rf /workspace/cache/

# Clear old model checkpoints
rm -rf /workspace/outputs/whisper-small-african-qlora/checkpoint-*
```

---

## 📊 Expected Performance

### Training Speed
- **Batch size:** 16 (per device)
- **Gradient accumulation:** 2 (effective batch: 32)
- **Steps:** 15,000
- **Expected duration:** ~48-72 hours on A40

### Storage Consumption Over Time
| Training Progress | Storage Used |
|-------------------|--------------|
| 0% (start) | ~10GB (manifests + models) |
| 25% | ~20GB (cached audio + checkpoints) |
| 50% | ~30GB |
| 100% | ~50GB max |

### Data Fetching Overhead
- **First epoch:** Slower (fetching audio on-demand)
- **Subsequent epochs:** Faster (using cached audio)
- **Network speed:** 15-20 MB/s from Hetzner
- **Overhead:** ~5-10% slower than full local storage

---

## ✅ Verification Checklist

Before starting training:
- [ ] Hetzner SSH key exists on RunPod
- [ ] Can connect to Hetzner via sftp
- [ ] Test script passes all 5 tests
- [ ] RunPod has >100GB free space
- [ ] GPU is available and idle
- [ ] HuggingFace token configured (for NaijaVoices)

During training:
- [ ] Training starts without errors
- [ ] Loss is decreasing
- [ ] Storage usage stays under 100GB
- [ ] No "out of storage" errors

---

## 🎯 Next Steps

1. **Run the test script** to verify everything works
2. **Start training** with the fixed script
3. **Monitor** via wandb: https://wandb.ai/alfred-anyan-ai-labs/whisper-african-qlora
4. **Check storage** periodically to ensure it stays under quota

---

## 📝 Files

| File | Location | Purpose |
|------|----------|---------|
| **Fixed training script** | `/workspace/runpod_whisper_african_qlora_streaming_fixed.py` | Main training script |
| **Test script** | `/workspace/test_hetzner_data_loading.py` | Verify setup works |
| **Original script** | `/workspace/runpod_whisper_african_qlora_streaming.py` | Old version (reference) |

---

## 💰 Cost Estimate

| Item | Duration | Cost |
|------|----------|------|
| **RunPod A40** | 72 hours | ~$57 ($0.79/hr) |
| **Hetzner Storage** | 1 month | $6 |
| **Network Transfer** | Included | $0 |
| **Total** | Full training run | **~$63** |

---

## 📧 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review logs: `/workspace/whisper_training.log`
3. Check wandb for training metrics
4. Verify Hetzner connection is stable

---

**Ready to train!** 🚀

Run the test script first, then start training. The on-demand data fetching approach will keep storage usage low while still accessing the full 476GB Twi dataset from Hetzner.
