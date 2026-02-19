# Ollama Model Management Guide

**Last Updated:** 2025-10-20

---

## 🎯 TL;DR - Ollama Model Management

**YES**, Ollama has comprehensive model management:
- ✅ **Modelfile** - Package custom/fine-tuned models
- ✅ **GGUF Format** - Standard model format (like pickle for LLMs)
- ✅ **Built-in commands** - create, push, pull, delete models
- ✅ **Version control** - Tag and manage versions
- ✅ **Import/Export** - Easy transfer between servers
- ✅ **Registry** - Share models publicly or privately

**No pickling needed** - Ollama uses GGUF (optimized binary format)

---

## 📦 Ollama Model Format

### GGUF (GPT-Generated Unified Format)
- **Replace for pickle** - Standard LLM binary format
- **Optimized** - Efficient loading and inference
- **Quantized** - Different sizes (Q4, Q5, Q8, FP16)
- **Portable** - Works across platforms

```
model.gguf          # The model weights (like .pkl but optimized)
```

---

## 🔧 Modelfile - Package Your Fine-tuned Models

### What is a Modelfile?
Think of it like a **Dockerfile for LLMs**:
- Defines model configuration
- Sets parameters (temperature, context, etc.)
- Adds system prompts
- Packages everything together

### Example: Package Fine-tuned Ghanaian Model

#### Step 1: Convert Fine-tuned Model to GGUF
```bash
# After fine-tuning on RunPod, convert to GGUF format
python convert-hf-to-gguf.py \
  /workspace/kasaai-llama-twi-v1 \
  --outfile kasaai-llama-twi-v1.gguf \
  --outtype q4_K_M

# This creates: kasaai-llama-twi-v1.gguf (~2GB)
```

#### Step 2: Create Modelfile
```dockerfile
# Modelfile for KasaAI Llama Twi
FROM ./kasaai-llama-twi-v1.gguf

# Model metadata
TEMPLATE """{{ if .System }}<|start_header_id|>system<|end_header_id|>

{{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>

{{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>

{{ .Response }}<|eot_id|>"""

# System prompt with Ghanaian cultural context
SYSTEM """You are KasaAI, a helpful AI assistant with deep knowledge of Ghanaian culture, languages, and customs. You understand Twi proverbs, can code-switch naturally between English and Twi, and provide culturally appropriate responses. You know about Ghanaian history, traditions, social norms, and current affairs."""

# Parameters optimized for conversational AI
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"

# Metadata
PARAMETER num_keep 24
PARAMETER seed 42
```

#### Step 3: Create Model in Ollama
```bash
# Import your fine-tuned model
sudo docker exec ollama ollama create kasaai-llama-twi:v1.0 -f Modelfile

# Now it's available like any other model!
sudo docker exec ollama ollama list
# NAME                    ID              SIZE      MODIFIED
# kasaai-llama-twi:v1.0   abc123          2.0GB     1 minute ago
```

#### Step 4: Use It
```bash
# Chat
sudo docker exec ollama ollama run kasaai-llama-twi:v1.0

# API
curl http://localhost:11434/api/generate -d '{
  "model": "kasaai-llama-twi:v1.0",
  "prompt": "What does \"Obi nkyere abofra Nyame\" mean?"
}'
```

---

## 🏷️ Model Versioning

### Tag Different Versions
```bash
# Create versions
ollama create kasaai-llama-twi:v1.0 -f Modelfile-v1.0
ollama create kasaai-llama-twi:v1.1 -f Modelfile-v1.1
ollama create kasaai-llama-twi:v2.0 -f Modelfile-v2.0

# Tag latest
ollama cp kasaai-llama-twi:v2.0 kasaai-llama-twi:latest

# List versions
ollama list | grep kasaai-llama-twi
# kasaai-llama-twi:v1.0    ...
# kasaai-llama-twi:v1.1    ...
# kasaai-llama-twi:v2.0    ...
# kasaai-llama-twi:latest  ... (points to v2.0)
```

---

## 📤 Export / Import Models

### Export Model (Package for Transfer)
```bash
# Method 1: Save to file (includes everything)
ollama save kasaai-llama-twi:v1.0 > kasaai-llama-twi-v1.0.tar

# Method 2: Show Modelfile (for recreation)
ollama show kasaai-llama-twi:v1.0 --modelfile > Modelfile

# Method 3: Copy GGUF file directly
cp ~/.ollama/models/blobs/sha256-abc123... kasaai-llama-twi-v1.0.gguf
```

### Import on Another Server
```bash
# Method 1: Load from file
cat kasaai-llama-twi-v1.0.tar | ollama load

# Method 2: Create from Modelfile + GGUF
ollama create kasaai-llama-twi:v1.0 -f Modelfile

# Method 3: Pull from registry (if pushed)
ollama pull ailabsafrica/kasaai-llama-twi:v1.0
```

---

## 🌐 Share Models (Private Registry)

### Push to Ollama Registry
```bash
# 1. Login (optional, for private models)
ollama login

# 2. Tag with namespace
ollama tag kasaai-llama-twi:v1.0 ailabsafrica/kasaai-llama-twi:v1.0

# 3. Push to registry
ollama push ailabsafrica/kasaai-llama-twi:v1.0

# Now anyone can pull it:
ollama pull ailabsafrica/kasaai-llama-twi:v1.0
```

### Push to Hugging Face (Alternative)
```bash
# 1. Push GGUF to Hugging Face
huggingface-cli upload \
  ailabsafrica/kasaai-llama-twi-gguf \
  kasaai-llama-twi-v1.0.gguf

# 2. Create Modelfile that references HF
cat > Modelfile <<EOF
FROM https://huggingface.co/ailabsafrica/kasaai-llama-twi-gguf/resolve/main/kasaai-llama-twi-v1.0.gguf
SYSTEM "You are KasaAI..."
PARAMETER temperature 0.7
EOF

# 3. Anyone can create from HF
ollama create kasaai-llama-twi -f Modelfile
```

---

## 🗂️ Model Storage Structure

### Docker Volume (Automatic)
```
/var/lib/docker/volumes/ollama_models/_data/
├── manifests/              # Model metadata
│   └── registry.ollama.ai/
│       └── library/
│           ├── llama3.2/
│           └── kasaai-llama-twi/
└── blobs/                  # Actual model files (GGUF)
    ├── sha256-abc123...    # Model weights
    ├── sha256-def456...    # Config
    └── sha256-ghi789...    # Template
```

### Host Mount (Accessible)
```
/opt/kasaai/models/ollama/
├── Modelfiles/             # Your custom Modelfiles
│   ├── kasaai-llama-twi-v1.0
│   ├── kasaai-aya-ghana-v1.0
│   └── kasaai-mistral-ghana-v1.0
└── gguf/                   # GGUF files
    ├── kasaai-llama-twi-v1.0.gguf
    ├── kasaai-aya-ghana-v1.0.gguf
    └── kasaai-mistral-ghana-v1.0.gguf
```

---

## 🔄 Complete Workflow: Fine-tune → Package → Deploy

### Step 1: Fine-tune on RunPod
```bash
# Fine-tune with LoRA/QLoRA
python train_qlora.py \
  --base_model meta-llama/Llama-3.2-3B-Instruct \
  --data ghanaian-culture.jsonl \
  --output kasaai-llama-twi-lora

# Merge LoRA with base model
python merge_lora.py \
  --base meta-llama/Llama-3.2-3B-Instruct \
  --lora kasaai-llama-twi-lora \
  --output kasaai-llama-twi-merged
```

### Step 2: Convert to GGUF
```bash
# Convert merged model to GGUF (Q4_K_M quantization)
python convert-hf-to-gguf.py \
  kasaai-llama-twi-merged \
  --outfile kasaai-llama-twi-v1.0.gguf \
  --outtype q4_K_M

# Result: 2GB GGUF file (vs 6GB original)
```

### Step 3: Transfer to Your Server
```bash
# Upload to Hugging Face (recommended)
huggingface-cli upload \
  ailabsafrica/kasaai-llama-twi-gguf \
  kasaai-llama-twi-v1.0.gguf

# Or direct SCP
scp kasaai-llama-twi-v1.0.gguf \
  user@your-server:/opt/kasaai/models/ollama/gguf/
```

### Step 4: Create Modelfile on Your Server
```bash
cd /opt/kasaai/models/ollama/Modelfiles

cat > kasaai-llama-twi-v1.0 <<'EOF'
FROM /opt/kasaai/models/ollama/gguf/kasaai-llama-twi-v1.0.gguf

TEMPLATE """{{ if .System }}<|start_header_id|>system<|end_header_id|>

{{ .System }}<|eot_id|>{{ end }}{{ if .Prompt }}<|start_header_id|>user<|end_header_id|>

{{ .Prompt }}<|eot_id|>{{ end }}<|start_header_id|>assistant<|end_header_id|>

{{ .Response }}<|eot_id|>"""

SYSTEM """You are KasaAI, a helpful AI assistant with deep knowledge of Ghanaian culture, languages, and customs. You understand Twi proverbs, can code-switch naturally between English and Twi, and provide culturally appropriate responses."""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096
PARAMETER stop "<|eot_id|>"
EOF
```

### Step 5: Import to Ollama
```bash
# Create model in Ollama
sudo docker exec ollama ollama create kasaai-llama-twi:v1.0 \
  -f /opt/kasaai/models/ollama/Modelfiles/kasaai-llama-twi-v1.0

# Verify
sudo docker exec ollama ollama list | grep kasaai
```

### Step 6: Test
```bash
# CLI test
sudo docker exec ollama ollama run kasaai-llama-twi:v1.0 \
  "What does 'Obi nkyere abofra Nyame' mean?"

# API test
curl http://localhost:11434/api/generate -d '{
  "model": "kasaai-llama-twi:v1.0",
  "prompt": "Wo ho te sɛn?",
  "stream": false
}'
```

### Step 7: Deploy to LLM Lab
```bash
# Update LLM Lab config to include new model
# Model automatically appears in dropdown
# Users can now chat with KasaAI Llama Twi!
```

---

## 🎛️ Ollama Management Commands

### List Models
```bash
ollama list
```

### Show Model Details
```bash
ollama show kasaai-llama-twi:v1.0
ollama show kasaai-llama-twi:v1.0 --modelfile  # Show Modelfile
```

### Copy Model (Create Alias)
```bash
ollama cp kasaai-llama-twi:v1.0 kasaai-llama-twi:latest
```

### Delete Model
```bash
ollama rm kasaai-llama-twi:v1.0
```

### Pull Model (from registry)
```bash
ollama pull ailabsafrica/kasaai-llama-twi:v1.0
```

### Push Model (to registry)
```bash
ollama push ailabsafrica/kasaai-llama-twi:v1.0
```

---

## 🔐 Private Model Registry (Optional)

### Option 1: Ollama Registry (Coming Soon)
```bash
# Will support private repos
ollama push --private ailabsafrica/kasaai-llama-twi:v1.0
```

### Option 2: Hugging Face (Current Recommendation)
```bash
# Upload GGUF to private HF repo
huggingface-cli upload \
  ailabsafrica/kasaai-llama-twi-gguf \
  kasaai-llama-twi-v1.0.gguf \
  --private

# Reference in Modelfile
FROM https://huggingface.co/ailabsafrica/kasaai-llama-twi-gguf/resolve/main/kasaai-llama-twi-v1.0.gguf
```

### Option 3: Self-hosted Registry
```bash
# Host GGUF files on your server
FROM https://models.ailabsafrica.com/llm/kasaai-llama-twi-v1.0.gguf
```

---

## 📊 Model Management Best Practices

### 1. Version Everything
```
kasaai-llama-twi:v1.0    # First release
kasaai-llama-twi:v1.1    # Bug fix
kasaai-llama-twi:v2.0    # Major update
kasaai-llama-twi:latest  # Always points to current
```

### 2. Tag with Metadata
```
kasaai-llama-twi:v1.0-q4      # Q4 quantization
kasaai-llama-twi:v1.0-q8      # Q8 quantization (larger, better)
kasaai-llama-twi:v1.0-prod    # Production version
kasaai-llama-twi:v1.0-test    # Testing version
```

### 3. Backup to Multiple Places
```bash
# Local server
/opt/kasaai/models/ollama/gguf/kasaai-llama-twi-v1.0.gguf

# Hugging Face (cloud backup)
huggingface-cli upload ailabsafrica/kasaai-llama-twi-gguf

# Ollama registry (when available)
ollama push ailabsafrica/kasaai-llama-twi:v1.0
```

### 4. Document Changes
```bash
# Create CHANGELOG.md
## v1.0 (2025-10-20)
- Initial release
- Trained on 1,500 Twi samples
- Supports proverbs and cultural knowledge

## v1.1 (2025-11-01)
- Added Ga language support
- Improved code-switching
- 500 more training samples
```

---

## 🚀 Quick Reference

### Package Fine-tuned Model
```bash
# 1. Convert to GGUF
python convert-hf-to-gguf.py model/ --outfile model.gguf

# 2. Create Modelfile
cat > Modelfile <<EOF
FROM ./model.gguf
SYSTEM "..."
PARAMETER temperature 0.7
EOF

# 3. Import to Ollama
ollama create my-model:v1.0 -f Modelfile
```

### Share Model
```bash
# Upload GGUF to Hugging Face
huggingface-cli upload username/model-gguf model.gguf

# Or push to Ollama registry
ollama push username/model:v1.0
```

### Use Model
```bash
# CLI
ollama run my-model:v1.0

# API
curl http://localhost:11434/api/generate -d '{"model":"my-model:v1.0","prompt":"..."}'
```

---

## ✅ Summary

**Ollama Model Management:**
- ✅ Uses GGUF format (no pickling needed)
- ✅ Modelfile for packaging (like Dockerfile)
- ✅ Built-in versioning and tagging
- ✅ Easy import/export
- ✅ Registry support (Ollama + Hugging Face)
- ✅ Simple CLI commands

**For Your Fine-tuned Models:**
1. Fine-tune on RunPod (PyTorch/HF format)
2. Convert to GGUF (optimized binary)
3. Create Modelfile (add config/prompts)
4. Import to Ollama (`ollama create`)
5. Backup to Hugging Face (cloud storage)
6. Deploy to LLM Lab (ready to use!)

**No complex serialization needed** - Ollama handles everything! 🎉

---

**Next:** Download base models and prepare for fine-tuning!
