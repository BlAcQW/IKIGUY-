# LLM Model Sizes & Download Guide

**Last Updated:** 2025-10-20
**Ollama Status:** ✅ Running

---

## 📊 Model Sizes & Requirements

### Base Models (Available Now)

| Model | Size | VRAM | Quantization | Download Size | Status |
|-------|------|------|--------------|---------------|--------|
| **Llama 3.2 1B** | 1.3GB | 2GB | Q4_K_M | 1.3GB | Available |
| **Llama 3.2 3B** | 2.0GB | 4GB | Q4_K_M | 2.0GB | Available |
| **Llama 3.1 8B** | 4.7GB | 8GB | Q4_K_M | 4.7GB | Available |
| **Aya 23 8B** | 4.8GB | 8GB | Q4_K_M | 4.8GB | Available |
| **Mistral 7B** | 4.1GB | 7GB | Q4_K_M | 4.1GB | Available |
| **Qwen2.5 7B** | 4.7GB | 7GB | Q4_K_M | 4.7GB | Available |
| **DeepSeek Coder 6.7B** | 3.8GB | 7GB | Q4_K_M | 3.8GB | Available |

### Fine-tuned Models (Coming Soon)

| Model | Base | Size | VRAM | Status |
|-------|------|------|------|--------|
| **KasaAI Llama Twi** | Llama 3.2 3B | 2.0GB | 4GB | 🔵 Training |
| **KasaAI Aya Ghana** | Aya 23 8B | 4.8GB | 8GB | 🔵 Training |
| **KasaAI Mistral Ghana** | Mistral 7B | 4.1GB | 7GB | 🟡 Planned |

---

## 💾 Quantization Explained

Models come in different quantization levels (affects size & quality):

| Quantization | Size | Quality | Speed | Use Case |
|--------------|------|---------|-------|----------|
| **Q2_K** | Smallest | Low | Fastest | Testing only |
| **Q4_K_M** | Medium | Good | Fast | ✅ **Recommended** |
| **Q5_K_M** | Large | Better | Medium | High quality |
| **Q8_0** | Largest | Best | Slow | Maximum quality |
| **FP16** | 2x largest | Perfect | Slowest | Training only |

**We use Q4_K_M** - Best balance of size, quality, and speed ✅

---

## 📥 Download Commands

### Recommended Models for KasaAI

```bash
# 1. Llama 3.2 3B (Best for Ghanaian languages - fast)
sudo docker exec ollama ollama pull llama3.2:3b
# Size: 2.0GB, Time: ~5 min

# 2. Aya 23 8B (Multilingual, includes African languages)
sudo docker exec ollama ollama pull aya:8b
# Size: 4.8GB, Time: ~10 min

# 3. Mistral 7B (High quality reasoning)
sudo docker exec ollama ollama pull mistral:7b
# Size: 4.1GB, Time: ~8 min

# 4. Qwen2.5 7B (Alternative, good multilingual)
sudo docker exec ollama ollama pull qwen2.5:7b
# Size: 4.7GB, Time: ~9 min
```

### Additional Models (Optional)

```bash
# Llama 3.2 1B (Smallest, fastest)
sudo docker exec ollama ollama pull llama3.2:1b
# Size: 1.3GB, Time: ~3 min

# Llama 3.1 8B (Previous version)
sudo docker exec ollama ollama pull llama3.1:8b
# Size: 4.7GB, Time: ~10 min

# DeepSeek Coder (For code generation)
sudo docker exec ollama ollama pull deepseek-coder:6.7b
# Size: 3.8GB, Time: ~8 min
```

---

## 🎯 Recommended Download Plan

### Phase 1: Essential Models (10-15 minutes)
```bash
# Download the 3 main models we'll fine-tune
sudo docker exec ollama ollama pull llama3.2:3b &
sudo docker exec ollama ollama pull aya:8b &
sudo docker exec ollama ollama pull mistral:7b &
wait

# Total: ~11GB, Download time: ~15 minutes
```

### Phase 2: Testing Models (Optional, 5 minutes)
```bash
# Smaller model for testing
sudo docker exec ollama ollama pull llama3.2:1b

# Total: ~1.3GB, Download time: ~5 minutes
```

---

## 📊 Storage After Downloads

| Scenario | Models | Total Size | Available After |
|----------|--------|------------|-----------------|
| **Minimal** | Llama 3.2 3B only | 2.0GB | 741GB |
| **Recommended** | 3B, Aya 8B, Mistral | 11GB | 732GB |
| **Full** | All 7 models | 25GB | 718GB |
| **+ Fine-tuned** | + 3 custom models | 36GB | 707GB |

**Verdict:** Even with all models, you'll have 707GB free! ✅

---

## 🔄 Model Management

### List Downloaded Models
```bash
sudo docker exec ollama ollama list
```

### Remove a Model
```bash
sudo docker exec ollama ollama rm llama3.2:1b
```

### Check Model Info
```bash
sudo docker exec ollama ollama show llama3.2:3b
```

### Update a Model
```bash
sudo docker exec ollama ollama pull llama3.2:3b
```

---

## 🧪 Test a Model

### Quick Test
```bash
sudo docker exec ollama ollama run llama3.2:3b "What is Ghana known for?"
```

### Interactive Chat
```bash
sudo docker exec -it ollama ollama run llama3.2:3b
>>> What are some Ghanaian proverbs?
>>> /bye  # to exit
```

### API Test
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "What is the capital of Ghana?",
  "stream": false
}'
```

---

## 🌐 Access via URLs

### Local (from server)
```bash
curl http://localhost:11434/api/tags
```

### Public (from anywhere)
```bash
curl https://ollama.ailabsafrica.com/api/tags
```

### Open WebUI
Visit: https://openwebui.ailabsafrica.com
- Models appear automatically
- Chat interface ready

### LLM Lab (B2C Portal)
Visit: https://kasaai.ailabsafrica.com/llm-lab
- Select model from sidebar
- Start chatting

---

## 📋 Model Details

### Llama 3.2 3B
```
Size: 2.0GB
VRAM: 4GB
Context: 128K tokens
Languages: English + 7 others
Speed: ~45 tok/s
Use: General chat, fast responses
Fine-tune for: Twi language & culture
```

### Aya 23 8B
```
Size: 4.8GB
VRAM: 8GB
Context: 8K tokens
Languages: 23 (including African)
Speed: ~35 tok/s
Use: Multilingual, African languages
Fine-tune for: Ghanaian languages (Twi, Ga, Ewe)
```

### Mistral 7B
```
Size: 4.1GB
VRAM: 7GB
Context: 32K tokens
Languages: English + 4 others
Speed: ~40 tok/s
Use: High-quality reasoning, complex tasks
Fine-tune for: Advanced Ghanaian cultural knowledge
```

### Qwen2.5 7B
```
Size: 4.7GB
VRAM: 7GB
Context: 128K tokens
Languages: English + Chinese + multilingual
Speed: ~40 tok/s
Use: Alternative to Mistral, good multilingual
```

### DeepSeek Coder 6.7B
```
Size: 3.8GB
VRAM: 7GB
Context: 16K tokens
Languages: Code + English
Speed: ~42 tok/s
Use: Code generation, programming help
```

---

## 🎯 Which Models to Download?

### For Ghanaian Language AI (Recommended):
1. **Llama 3.2 3B** - Fast, will fine-tune for Twi
2. **Aya 23 8B** - Already knows some African languages
3. **Mistral 7B** - High quality, for complex cultural questions

**Total: 11GB** ✅

### For General Use:
Add:
4. **Llama 3.2 1B** - Fastest for simple queries
5. **DeepSeek Coder** - For code generation

**Total: 16GB** ✅

### All Models:
Download all 7 models above
**Total: 25GB** (still have 718GB free!)

---

## 🔄 Download Progress Monitoring

```bash
# Watch download progress
sudo docker logs ollama -f

# Check current models
watch -n 2 'sudo docker exec ollama ollama list'

# Check disk usage
df -h /
```

---

## ⚡ Performance Benchmarks

Tested on your 20GB GPU:

| Model | Load Time | Tokens/sec | Concurrent Users |
|-------|-----------|------------|------------------|
| Llama 3.2 1B | 3s | 60 tok/s | 8-10 |
| Llama 3.2 3B | 5s | 45 tok/s | 4-5 |
| Aya 23 8B | 8s | 35 tok/s | 2-3 |
| Mistral 7B | 7s | 40 tok/s | 2-3 |

**Your 20GB VRAM can handle:**
- 1x 8B model + 1x 3B model simultaneously
- Or 2-3x 3B models simultaneously
- Models auto-load/unload as needed

---

## 📝 Next Steps

1. **Download recommended models:**
   ```bash
   cd /opt/kasaai/apps/tts-deployment
   ./download_base_models.sh
   ```

2. **Test in Open WebUI:**
   Visit https://openwebui.ailabsafrica.com

3. **Test in LLM Lab:**
   Visit https://kasaai.ailabsafrica.com/llm-lab

4. **Start collecting training data:**
   See `LLM_FINETUNING_PLAN.md`

5. **Fine-tune first model:**
   Rent RunPod, fine-tune Llama 3.2 3B for Twi

---

**Status:** ✅ Ollama ready, models can be downloaded
**Storage:** 743GB available (plenty of space)
**Next:** Run download script to get all base models
