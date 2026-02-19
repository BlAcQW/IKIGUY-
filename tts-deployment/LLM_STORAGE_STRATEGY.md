# LLM Model Storage & Management Strategy

**Created:** 2025-10-20
**Status:** Planning Phase
**Current Disk Usage:** 888GB / 1.7TB (55% used, 752GB available)

---

## 📊 Current Situation

### Server Storage:
- **Total:** 1.7TB
- **Used:** 888GB (55%)
- **Available:** 752GB
- **Docker Storage:** 324GB (Images: 234GB, Containers: 8.8GB)

### Current Setup:
- **Open WebUI:** Running on port 8007 ✅
- **Ollama:** NOT installed ❌
- **Model Storage:** None yet

---

## 🎯 Storage Requirements for LLM Fine-tuning

### Model Sizes (Estimated):

| Model | Base Size | Fine-tuned | Training Data | Checkpoints | Total |
|-------|-----------|-----------|---------------|-------------|-------|
| **Llama 3.2 3B** | 6GB | 6GB | 2GB | 10GB | 24GB |
| **Aya-23 8B** | 16GB | 16GB | 3GB | 20GB | 55GB |
| **Mistral 7B** | 14GB | 14GB | 3GB | 18GB | 49GB |
| **Llama 3.2 Vision 11B** | 22GB | - | - | - | 22GB |
| **DeepSeek Coder 6.7B** | 13GB | - | - | - | 13GB |
| **Base Models (backup)** | 20GB | - | - | - | 20GB |

**Total Required:** ~183GB for all models + training data

### Additional Storage Needs:
- **Training artifacts:** 20GB (logs, metrics, experiments)
- **Dataset storage:** 10GB (Ghanaian training data)
- **Model versions:** 30GB (multiple checkpoints)
- **Inference cache:** 10GB (API response caching)

**Grand Total:** ~253GB

---

## ✅ Current Server Capacity: SUFFICIENT

**Available:** 752GB
**Required:** 253GB
**Margin:** 499GB (66% free after LLMs)

**Decision:** ✅ **Use current server storage - no external storage needed yet**

---

## 🏗️ Recommended Storage Structure

### Option 1: Local Storage (RECOMMENDED for now)

```bash
/opt/kasaai/
├── models/                          # Main models directory
│   ├── llm/                         # LLM models
│   │   ├── base/                    # Base models
│   │   │   ├── llama-3.2-3b/
│   │   │   ├── aya-23-8b/
│   │   │   └── mistral-7b/
│   │   ├── fine-tuned/              # Fine-tuned models
│   │   │   ├── kasaai-llama-twi/
│   │   │   ├── kasaai-aya-ghana/
│   │   │   └── kasaai-mistral-ghana/
│   │   └── checkpoints/             # Training checkpoints
│   │       ├── llama-twi-epoch-1/
│   │       ├── llama-twi-epoch-2/
│   │       └── llama-twi-epoch-3/
│   ├── tts/                         # TTS models (existing)
│   └── asr/                         # ASR models
│
├── training/                        # Training data and artifacts
│   ├── datasets/
│   │   ├── ghanaian-culture/
│   │   │   ├── twi-proverbs.jsonl
│   │   │   ├── ga-conversations.jsonl
│   │   │   └── ewe-culture.jsonl
│   │   └── preprocessed/
│   ├── logs/                        # Training logs
│   └── experiments/                 # Experiment tracking
│
└── cache/                           # Inference cache
    ├── llm-responses/
    └── embeddings/
```

**Advantages:**
- ✅ Fast access (local SSD)
- ✅ No additional cost
- ✅ Easy to manage
- ✅ Low latency
- ✅ 752GB available (sufficient)

**Disadvantages:**
- ⚠️ No automatic backups
- ⚠️ Single point of failure
- ⚠️ Limited scalability

---

## 📦 Option 2: Hetzner Storage Box (BACKUP/ARCHIVE)

**Use Case:** Long-term storage and backups

### Recommended Plan:
- **BX20:** 1TB for €6.38/month (~$7/month)
- **Purpose:**
  - Model backups
  - Training dataset archives
  - Old checkpoints
  - Model version history

### Setup:
```bash
# Mount Storage Box via SSHFS
mkdir -p /mnt/storage-box
sshfs u123456@u123456.your-storagebox.de:/home \
  /mnt/storage-box \
  -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3

# Backup script
rsync -avz --progress \
  /opt/kasaai/models/llm/fine-tuned/ \
  /mnt/storage-box/llm-models-backup/
```

### Storage Box Structure:
```
/mnt/storage-box/
├── llm-models-backup/              # Backup of fine-tuned models
├── training-datasets/              # Training data backup
├── checkpoints-archive/            # Old checkpoints
├── model-versions/                 # Version history
└── snapshots/                      # Daily snapshots
```

---

## 🚀 Recommended Strategy: HYBRID

### Phase 1: Local Storage (Now - Month 3)
**Use local server storage for:**
- Active models (fine-tuned + base)
- Current training runs
- Inference serving
- Fast iteration

**Cost:** $0
**Performance:** Excellent
**Capacity:** Sufficient (752GB available)

### Phase 2: Add Storage Box (Month 3+)
**Use Hetzner Storage Box BX20 for:**
- Daily model backups
- Training dataset archives
- Old checkpoints (keep only latest 3 locally)
- Model version history
- Disaster recovery

**Cost:** €6.38/month (~$7/month)
**Performance:** Good for backups (sync overnight)
**Capacity:** 1TB

---

## 🔧 Implementation Plan

### Week 1: Setup Local Storage
```bash
# 1. Create directory structure
sudo mkdir -p /opt/kasaai/models/{llm/{base,fine-tuned,checkpoints},tts,asr}
sudo mkdir -p /opt/kasaai/training/{datasets,logs,experiments}
sudo mkdir -p /opt/kasaai/cache/{llm-responses,embeddings}

# 2. Set permissions
sudo chown -R dev:dev /opt/kasaai/models
sudo chown -R dev:dev /opt/kasaai/training
sudo chown -R dev:dev /opt/kasaai/cache

# 3. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 4. Configure Ollama to use custom path
sudo mkdir -p /opt/kasaai/models/ollama
sudo systemctl edit ollama
# Add: Environment="OLLAMA_MODELS=/opt/kasaai/models/ollama"
sudo systemctl restart ollama

# 5. Setup Ollama nginx config
sudo cp /etc/nginx/sites-available/openwebui.ailabsafrica.com.conf \
       /etc/nginx/sites-available/ollama.ailabsafrica.com.conf
# Edit to point to port 11434
sudo ln -sf /etc/nginx/sites-available/ollama.ailabsafrica.com.conf \
            /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Week 2-4: Download Base Models
```bash
# Download base models to Ollama
ollama pull llama3.2:3b
ollama pull aya:8b
ollama pull mistral:7b

# Or download directly
cd /opt/kasaai/models/llm/base
huggingface-cli download meta-llama/Llama-3.2-3B-Instruct
huggingface-cli download CohereForAI/aya-23-8B
huggingface-cli download mistralai/Mistral-7B-Instruct-v0.3
```

### Month 2-3: Fine-tuning
```bash
# Fine-tune models (see LLM_FINETUNING_PLAN.md)
# Save to /opt/kasaai/models/llm/fine-tuned/
```

### Month 3+: Setup Backups
```bash
# 1. Order Hetzner Storage Box BX20
# 2. Setup SSHFS mount
# 3. Create backup script
# 4. Setup daily cron job
```

---

## 📝 Model Management Best Practices

### 1. Model Versioning
```
/opt/kasaai/models/llm/fine-tuned/kasaai-llama-twi/
├── v1.0/                   # First release
├── v1.1/                   # Bug fix
├── v2.0/                   # Major update
└── latest -> v2.0/         # Symlink to current
```

### 2. Checkpoint Management
Keep only the **3 most recent checkpoints** locally:
```bash
# Auto-cleanup old checkpoints
find /opt/kasaai/models/llm/checkpoints/ \
  -name "*.pt" -mtime +30 -delete
```

### 3. Dataset Versioning
```
/opt/kasaai/training/datasets/
├── ghanaian-culture-v1.0/
├── ghanaian-culture-v2.0/
└── ghanaian-culture-latest -> v2.0/
```

---

## 💾 Disk Space Monitoring

### Setup Alerts
```bash
# Add to cron: Check daily at 2 AM
0 2 * * * df -h / | awk 'NR==2 {if ($5+0 > 80) print "WARNING: Disk usage at "$5}' | mail -s "Disk Alert" admin@ailabsafrica.com
```

### Regular Cleanup
```bash
# Clean Docker images monthly
docker system prune -a --filter "until=720h"

# Clean old logs
find /opt/kasaai/training/logs/ -name "*.log" -mtime +90 -delete
```

---

## 🔐 Backup Strategy

### Daily Backups (automated):
- Fine-tuned models → Storage Box
- Training datasets → Storage Box
- Latest checkpoints → Storage Box

### Weekly Backups:
- Full model directory snapshot
- Database backup (if storing metadata)

### Monthly Archives:
- Complete version history
- All experiment results

---

## 💰 Cost Breakdown

### Current Setup (Phase 1):
- **Local Storage:** $0 (752GB available on existing server)
- **Training (RunPod):** $400-600 (one-time for fine-tuning)
- **Total Month 1-3:** $400-600

### Future Setup (Phase 2):
- **Local Storage:** $0
- **Storage Box BX20:** €6.38/month (~$7/month)
- **Total Ongoing:** $7/month

**Total Cost:**
- **Setup:** $400-600 (one-time)
- **Ongoing:** $7/month (backup only)

---

## ✅ Recommendations Summary

### Immediate Actions (Week 1):
1. ✅ **Create directory structure** on local server
2. ✅ **Install Ollama** for model serving
3. ✅ **Setup Ollama nginx** config for ollama.ailabsafrica.com
4. ✅ **Download base models** (Llama 3.2 3B to start)
5. ✅ **Test Ollama API** via Open WebUI

### Short-term (Month 1-2):
1. ⏳ **Start fine-tuning** Llama 3.2 3B Twi
2. ⏳ **Collect training data** (1,500+ samples)
3. ⏳ **Deploy fine-tuned model** to Ollama
4. ⏳ **Connect LLM Lab** to Ollama backend

### Long-term (Month 3+):
1. ⏳ **Order Storage Box** BX20 (1TB, $7/month)
2. ⏳ **Setup automated backups**
3. ⏳ **Fine-tune remaining models** (Aya-23, Mistral)
4. ⏳ **Implement monitoring** and alerts

---

## 🎯 Decision: Use Local Storage First

**Verdict:** ✅ **NO need for external storage yet**

**Reasons:**
1. ✅ 752GB available (3x more than needed)
2. ✅ Faster access (local SSD vs network)
3. ✅ Simpler setup
4. ✅ $0 cost
5. ✅ Can add Storage Box later if needed

**When to add Storage Box:**
- ✓ When disk usage > 70% (currently 55%)
- ✓ After fine-tuning all 3 models
- ✓ For disaster recovery/backups
- ✓ For long-term archival

---

## 📚 Next Steps

1. **Install Ollama** (see installation section above)
2. **Setup ollama.ailabsafrica.com** nginx config
3. **Download first base model** (Llama 3.2 3B)
4. **Test with Open WebUI**
5. **Start collecting training data**

See `LLM_FINETUNING_PLAN.md` for detailed fine-tuning steps.

---

**Storage Strategy:** ✅ Approved
**Cost Impact:** $0 (local storage sufficient)
**Timeline:** Ready to start immediately
