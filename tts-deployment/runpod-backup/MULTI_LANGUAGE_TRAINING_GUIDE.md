# Multi-Language Training Workflow Guide

**Date:** 2025-10-22
**Status:** ✅ Production Ready
**Purpose:** Train Whisper models on 5 Ghanaian/Nigerian languages using multiple data sources

---

## 📋 Overview

This guide documents the complete workflow for training Whisper models using data from multiple sources:

| Language | Data Source | Size | Files |
|----------|-------------|------|-------|
| **Twi** | Hetzner Storage Box | ~200-300GB | ~941K |
| **Ga** | Hetzner Storage Box | TBD | TBD |
| **Igbo** | HuggingFace (Common Voice 17.0) | ~10-20GB | ~10K |
| **Hausa** | HuggingFace (Common Voice 17.0) | ~10-20GB | ~10K |
| **Yoruba** | HuggingFace (Common Voice 17.0) | ~10-20GB | ~10K |

**Total Estimated:** ~250-350GB, ~1M files

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐       ┌────────────────────────┐  │
│  │  Hetzner Storage     │       │  HuggingFace Hub       │  │
│  │  Box                 │       │                        │  │
│  │  • Twi (334h)        │       │  • Igbo (CV 17.0)      │  │
│  │  • Ga (TBD)          │       │  • Hausa (CV 17.0)     │  │
│  └──────────────────────┘       │  • Yoruba (CV 17.0)    │  │
│           │                      └────────────────────────┘  │
│           │                                │                 │
│           ▼                                ▼                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              RunPod GPU Instance                     │    │
│  │  /workspace/training-data/                          │    │
│  │    ├── twi/         (from Hetzner via rsync)       │    │
│  │    ├── ga/          (from Hetzner via rsync)       │    │
│  │    ├── ig/          (from HF via datasets lib)     │    │
│  │    ├── ha/          (from HF via datasets lib)     │    │
│  │    └── yo/          (from HF via datasets lib)     │    │
│  └─────────────────────────────────────────────────────┘    │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Training (Whisper QLoRA)                   │    │
│  │  • Multi-language fine-tuning                       │    │
│  │  • Checkpoints saved to /workspace/outputs/         │    │
│  └─────────────────────────────────────────────────────┘    │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Local Backup (Git)                         │    │
│  │  • Scripts backed up via rsync                      │    │
│  │  • Checkpoints backed up                            │    │
│  │  • Manifests backed up                              │    │
│  │  Location: /opt/kasaai/apps/tts-deployment/        │    │
│  │            runpod-backup/                            │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Set Up Training Data on RunPod

```bash
# SSH into RunPod
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121

# Run the multi-language setup script
/workspace/setup_multi_language_training.sh
```

This script will:
- ✅ Verify prerequisites (rsync, Python, datasets library)
- ✅ Sync Twi data from Hetzner (~2-4 hours for full dataset)
- ✅ Sync Ga data from Hetzner (if available)
- ✅ Download Igbo, Hausa, Yoruba from HuggingFace
- ✅ Generate dataset summary

### 2. Start Training

```bash
# Update training script to use /workspace/training-data/
# Then start training
cd /workspace
./run_training.sh
```

### 3. Backup Everything Locally (for Git)

```bash
# Run from your local machine
/opt/kasaai/apps/tts-deployment/runpod-backup/backup_runpod_to_local.sh
```

This will backup:
- All Python training scripts
- Shell scripts
- Configuration files
- Training outputs/checkpoints
- Log files
- Data manifests (CSV only, not audio files)

---

## 📁 File Structure

### On RunPod (`/workspace/`)

```
/workspace/
├── training-data/              # All training datasets
│   ├── twi/                   # From Hetzner
│   │   ├── processed_audio/
│   │   │   ├── asr_16k/
│   │   │   └── tts_22k/
│   │   └── manifests/
│   │       ├── asr_16k_dataset.csv
│   │       └── tts_22k_dataset.csv
│   ├── ga/                    # From Hetzner
│   ├── ig/                    # From HuggingFace
│   ├── ha/                    # From HuggingFace
│   ├── yo/                    # From HuggingFace
│   └── DATASET_SUMMARY.txt    # Generated summary
│
├── runpod_whisper_african_qlora_streaming.py  # Training script
├── run_training.sh                            # Training launcher
├── setup_multi_language_training.sh           # Data setup script
├── outputs/                                    # Training outputs
│   └── whisper-african-qlora/
│       ├── checkpoint-1000/
│       ├── checkpoint-2000/
│       └── final/
└── *.log                                       # Training logs
```

### On Local Machine (`/opt/kasaai/apps/tts-deployment/runpod-backup/`)

```
runpod-backup/
├── setup_multi_language_training.sh    # Setup script (pushed to RunPod)
├── backup_runpod_to_local.sh           # Backup script (run locally)
├── backups/                             # Timestamped backups
│   ├── 20251022_131721/                # Backup from specific time
│   │   ├── runpod_whisper_african_qlora_streaming.py
│   │   ├── run_training.sh
│   │   ├── *.log
│   │   └── outputs/
│   └── latest -> 20251022_131721/      # Symlink to latest
│
├── runpod_whisper_african_qlora_streaming.py  # Latest version (for Git)
├── run_training.sh                             # Latest version (for Git)
└── MULTI_LANGUAGE_TRAINING_GUIDE.md           # This file
```

---

## 📜 Detailed Workflow

### Phase 1: Initial Setup (One-Time)

**On Local Machine:**

```bash
# 1. Ensure Hetzner-RunPod SSH keys are set up
# (Already completed - see EXTERNAL_STORAGE_MOUNTING_GUIDE.md)

# 2. Upload setup script to RunPod
scp -P 22130 -i ~/.ssh/id_ed25519 \
  /opt/kasaai/apps/tts-deployment/runpod-backup/setup_multi_language_training.sh \
  root@194.68.245.121:/workspace/

# 3. Make it executable
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 \
  "chmod +x /workspace/setup_multi_language_training.sh"
```

### Phase 2: Data Preparation (2-5 hours)

**On RunPod:**

```bash
# SSH into RunPod
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121

# Run setup script
/workspace/setup_multi_language_training.sh
```

**What it does:**

1. **Verifies Prerequisites**
   - Checks SSH keys for Hetzner
   - Installs rsync if needed
   - Installs HuggingFace `datasets` library

2. **Syncs Twi from Hetzner**
   - Source: `u497034-sub1@u497034-sub1.your-storagebox.de:/home/voice-lab/data/twi-akan-fante/`
   - Destination: `/workspace/training-data/twi/`
   - Time: ~2-4 hours for 200-300GB
   - Speed: ~15-20 MB/s

3. **Syncs Ga from Hetzner** (if available)
   - Source: `/home/voice-lab/data/ga/`
   - Destination: `/workspace/training-data/ga/`

4. **Downloads from HuggingFace**
   - Igbo: `mozilla-foundation/common_voice_17_0:ig`
   - Hausa: `mozilla-foundation/common_voice_17_0:ha`
   - Yoruba: `mozilla-foundation/common_voice_17_0:yo`
   - Time: ~30-60 minutes total

5. **Generates Summary**
   - Creates `DATASET_SUMMARY.txt` with stats
   - Shows total size, file counts per language

### Phase 3: Training (48-72 hours)

**On RunPod:**

```bash
# Start training
cd /workspace
./run_training.sh
```

**Monitor progress:**

```bash
# View logs in real-time
tail -f /workspace/whisper_training.log

# Check GPU usage
watch -n 1 nvidia-smi

# Check disk usage
df -h /workspace
```

### Phase 4: Backup to Local (30-60 minutes)

**On Local Machine:**

```bash
# Run backup script
/opt/kasaai/apps/tts-deployment/runpod-backup/backup_runpod_to_local.sh
```

**What it backs up:**

✅ **Scripts:**
- `runpod_whisper_african_qlora_streaming.py`
- `run_training.sh`
- `setup_multi_language_training.sh`
- All shell scripts

✅ **Outputs:**
- Training checkpoints
- Final models
- Logs

✅ **Manifests:**
- CSV files
- Dataset summaries
- Configuration files

❌ **Not backed up** (too large):
- Raw audio files (already on Hetzner)
- HuggingFace cache

### Phase 5: Commit to Git

```bash
# Navigate to runpod-backup
cd /opt/kasaai/apps/tts-deployment/runpod-backup

# Check what's new
git status

# Add new files
git add .

# Commit
git commit -m "Update RunPod training scripts and checkpoints"

# Push
git push
```

---

## 🔧 Maintenance & Updates

### Update Training Script

```bash
# 1. Edit locally
vim /opt/kasaai/apps/tts-deployment/runpod-backup/runpod_whisper_african_qlora_streaming.py

# 2. Upload to RunPod
scp -P 22130 -i ~/.ssh/id_ed25519 \
  runpod_whisper_african_qlora_streaming.py \
  root@194.68.245.121:/workspace/

# 3. Test on RunPod
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 \
  "cd /workspace && python3 runpod_whisper_african_qlora_streaming.py --help"
```

### Add New Language

1. **If from Hetzner:**
   - Upload data to Hetzner: `/home/voice-lab/data/<language>/`
   - Update `setup_multi_language_training.sh` to include new language
   - Re-run setup script on RunPod

2. **If from HuggingFace:**
   - Edit `setup_multi_language_training.sh`
   - Add to `HF_DATASETS` array
   - Re-run setup script

### Sync Updated Data

```bash
# On RunPod - sync only new/changed files
rsync -avzP --stats \
  -e "ssh -p 23 -i ~/.ssh/hetzner_key" \
  u497034-sub1@u497034-sub1.your-storagebox.de:/home/voice-lab/data/twi-akan-fante/ \
  /workspace/training-data/twi/
```

---

## 💾 Backup Schedule

**Recommended:**

1. **Before Training:** Backup scripts
2. **During Training:** Backup checkpoints every 1000 steps
3. **After Training:** Full backup (model + logs)
4. **Weekly:** Backup to Git

**Automated Backup (Optional):**

```bash
# Add to crontab on local machine
# Run backup daily at 2 AM
0 2 * * * /opt/kasaai/apps/tts-deployment/runpod-backup/backup_runpod_to_local.sh
```

---

## 🐛 Troubleshooting

### Hetzner Connection Issues

```bash
# Test connection from RunPod
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 \
  "ssh -p 23 -i ~/.ssh/hetzner_key u497034-sub1@u497034-sub1.your-storagebox.de"
```

**If fails:**
- Check SSH key is in Hetzner authorized_keys
- Verify key path: `/root/.ssh/hetzner_key` on RunPod

### HuggingFace Download Fails

```bash
# On RunPod - install/update datasets library
pip install --upgrade datasets huggingface_hub

# Test manually
python3 << EOF
from datasets import load_dataset
ds = load_dataset("mozilla-foundation/common_voice_17_0", "ig", split="train[:10]")
print(f"Loaded {len(ds)} samples")
EOF
```

### Disk Space Issues

```bash
# On RunPod - check space
df -h /workspace

# Clear cache if needed
rm -rf /workspace/.cache
rm -rf /workspace/cache

# Clear old checkpoints (keep only latest)
find /workspace/outputs -name "checkpoint-*" -type d | sort -V | head -n -3 | xargs rm -rf
```

### Backup Script Issues

```bash
# On local machine - test connection
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 "echo 'Connected'"

# Run backup in verbose mode
bash -x /opt/kasaai/apps/tts-deployment/runpod-backup/backup_runpod_to_local.sh
```

---

## 📊 Cost Estimation

**One-Time Setup:**
- Data transfer time: 2-5 hours
- Cost: $0 (just time)

**Training:**
- GPU: A40 ($0.79/hour)
- Training time: 48-72 hours
- Cost: ~$38-57 per training run

**Storage:**
- Hetzner: ~$6/month (long-term backup)
- RunPod workspace: Included with GPU rental
- Local Git: Free

**Total per training run:** ~$40-60

---

## ✅ Checklist

### Before Starting Training

- [ ] SSH keys configured (RunPod ↔ Hetzner)
- [ ] `setup_multi_language_training.sh` uploaded to RunPod
- [ ] Backup script tested locally
- [ ] Sufficient disk space on RunPod (check with `df -h`)
- [ ] HuggingFace account configured (for dataset access)

### During Training

- [ ] Monitor training logs regularly
- [ ] Check GPU utilization
- [ ] Verify checkpoints are being saved
- [ ] Run backup script after major milestones

### After Training

- [ ] Full backup to local machine
- [ ] Verify all checkpoints backed up
- [ ] Commit important files to Git
- [ ] Upload final model to HuggingFace Hub (optional)
- [ ] Document results

---

## 🔗 Related Documentation

- [EXTERNAL_STORAGE_MOUNTING_GUIDE.md](./EXTERNAL_STORAGE_MOUNTING_GUIDE.md) - Hetzner-RunPod connection setup
- [GHANAIAN_LANGUAGES_GUIDE.md](./GHANAIAN_LANGUAGES_GUIDE.md) - Language-specific training details
- [01_WHISPER_QLORA_RUNPOD_SETUP.md](./01_WHISPER_QLORA_RUNPOD_SETUP.md) - Initial RunPod setup

---

**Created:** 2025-10-22
**Author:** AI Labs Africa
**Status:** ✅ Production Ready
**Last Updated:** 2025-10-22
