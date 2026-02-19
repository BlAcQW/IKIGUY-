# Quick Reference Card - Multi-Language Training

## 🚀 Essential Commands

### On RunPod

```bash
# SSH into RunPod
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121

# IMPORTANT: Use the FIXED script (v2.0 - Storage Optimized)
# Test setup first
python /workspace/test_hetzner_data_loading.py

# Start training (NEW - with Hetzner remote loading)
python /workspace/runpod_whisper_african_qlora_streaming_fixed.py

# Monitor training
tail -f /workspace/whisper_training.log

# Check GPU
nvidia-smi

# Check disk usage (should stay under 100GB)
df -h /workspace && du -sh /workspace/training-data
```

### On Local Machine

```bash
# Backup RunPod to local
/opt/kasaai/apps/tts-deployment/runpod-backup/backup_runpod_to_local.sh

# Upload script to RunPod
scp -P 22130 -i ~/.ssh/id_ed25519 <file> root@194.68.245.121:/workspace/

# Git commit
cd /opt/kasaai/apps/tts-deployment/runpod-backup
git add . && git commit -m "Update training files"
```

## 📁 Key Paths

| Location | Path |
|----------|------|
| **RunPod Data** | `/workspace/training-data/` |
| **RunPod Scripts** | `/workspace/*.py`, `/workspace/*.sh` |
| **RunPod Outputs** | `/workspace/outputs/` |
| **Local Backup** | `/opt/kasaai/apps/tts-deployment/runpod-backup/` |
| **Latest Backup** | `/opt/kasaai/apps/tts-deployment/runpod-backup/backups/latest/` |

## 📊 Data Sources

| Language | Source | Location |
|----------|--------|----------|
| Twi | Hetzner | `/home/voice-lab/data/twi-akan-fante/` |
| Ga | Hetzner | `/home/voice-lab/data/ga/` |
| Igbo | HuggingFace | `mozilla-foundation/common_voice_17_0:ig` |
| Hausa | HuggingFace | `mozilla-foundation/common_voice_17_0:ha` |
| Yoruba | HuggingFace | `mozilla-foundation/common_voice_17_0:yo` |

## 🔑 Credentials

| Service | Details |
|---------|---------|
| **RunPod SSH** | `root@194.68.245.121:22130` |
| **Hetzner SSH** | `u497034-sub1@u497034-sub1.your-storagebox.de:23` |
| **Keys** | `~/.ssh/id_ed25519` (local), `/root/.ssh/hetzner_key` (RunPod) |

## ⏱️ Time Estimates

| Task | Duration |
|------|----------|
| Setup Twi data (300GB) | 2-4 hours |
| Download HF datasets | 30-60 min |
| Training (full dataset) | 48-72 hours |
| Backup to local | 30-60 min |

## 💰 Costs

| Item | Cost |
|------|------|
| Hetzner Storage | $6/month |
| RunPod A40 GPU | $0.79/hour |
| Full training run | ~$40-60 |

## 🆘 Emergency

```bash
# Stop training
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 "pkill -f whisper"

# Quick backup
/opt/kasaai/apps/tts-deployment/runpod-backup/backup_runpod_to_local.sh

# Check what's running
ssh -p 22130 -i ~/.ssh/id_ed25519 root@194.68.245.121 "ps aux | grep python"
```

## 📖 Documentation

- **FIXED Training Guide:** `FIXED_TRAINING_GUIDE.md` ⭐ **START HERE**
- **Full Guide:** `MULTI_LANGUAGE_TRAINING_GUIDE.md`
- **Hetzner Setup:** `EXTERNAL_STORAGE_MOUNTING_GUIDE.md`
- **Backup Script:** `backup_runpod_to_local.sh`
- **Setup Script:** `setup_multi_language_training.sh`

## ⚠️ Important: Use Fixed Script (v2.0)

**OLD (Broken):** `/workspace/runpod_whisper_african_qlora_streaming.py`
- ❌ Tries to load from `/opt/kasaai/` (not accessible on RunPod)
- ❌ Loads all 476GB locally (exceeds storage quota)
- ❌ Has `input_ids` bug causing training to crash

**NEW (Fixed):** `/workspace/runpod_whisper_african_qlora_streaming_fixed.py`
- ✅ Loads from Hetzner Storage Box via SSH
- ✅ Only syncs manifests (~10MB), fetches audio on-demand
- ✅ Storage usage: <50GB vs 476GB
- ✅ All bugs fixed
