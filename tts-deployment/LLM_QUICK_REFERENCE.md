# LLM Fine-Tuning Quick Reference

**For:** Ghanaian Language Conversational AI
**See:** `LLM_FINETUNING_PLAN.md` for complete details

---

## 🎯 Recommended Models

| Model | Size | VRAM | Best For | Cost |
|-------|------|------|----------|------|
| **Llama 3.2 3B** | 3B | 4GB | Fast, General | $200-300 |
| **Aya-23 8B** | 8B | 8GB | Ghanaian Languages | $300-400 |
| **Mistral 7B** | 7B | 7GB | High Quality | $250-350 |

**Total:** $750-1,050 for all 3 models

---

## 📊 Quick Comparison

| Feature | Llama 3.2 | Aya-23 | Mistral |
|---------|-----------|--------|---------|
| **Multilingual** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **African Languages** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Reasoning** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Speed** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Context** | 128K | 8K | 32K |
| **License** | Apache 2.0 | Apache 2.0 | Apache 2.0 |

---

## ⚡ Quick Start

### 1. Setup (Day 1)
```bash
# Get RunPod GPU
# Sign up at runpod.io
# Select: 48GB GPU (RTX A6000 or similar)

# Install training tools
pip install axolotl unsloth transformers peft bitsandbytes

# Download base model
huggingface-cli download meta-llama/Llama-3.2-3B-Instruct
```

### 2. Prepare Data (Week 1)
```bash
# Collect 1,500-3,000 samples:
cultural_knowledge/
├── proverbs.jsonl         (500)
├── social_customs.jsonl   (400)
├── local_knowledge.jsonl  (600)
├── language_patterns.jsonl (500)
└── conversations.jsonl    (1000)
```

### 3. Train (Week 2)
```bash
# QLoRA training
python train_qlora.py \
  --model meta-llama/Llama-3.2-3B-Instruct \
  --dataset cultural_knowledge.jsonl \
  --output kasaai-llama-3b-twi-v1 \
  --epochs 3 \
  --batch_size 4

# Takes: 24-36 hours
# Cost: $200-300 on RunPod
```

### 4. Test (Week 3)
```bash
# Load and test
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("kasaai-llama-3b-twi-v1")
tokenizer = AutoTokenizer.from_pretrained("kasaai-llama-3b-twi-v1")

# Test with Twi prompt
prompt = "What does 'Obi nkyere abofra Nyame' mean?"
response = model.generate(prompt)
```

### 5. Deploy (Week 4)
```bash
# Add to Open WebUI via Ollama
ollama create kasaai-twi -f Modelfile
ollama run kasaai-twi

# Or deploy to production API
# See deployment section in main plan
```

---

## 📝 Data Format Example

```jsonl
{
  "instruction": "What does the Twi proverb 'Obi nkyere abofra Nyame' mean?",
  "input": "",
  "output": "This proverb literally means 'No one teaches a child about God' in Twi. It conveys that some knowledge is innate or natural. It's often used when someone shows natural talent or wisdom without formal training."
}

{
  "instruction": "How do I greet an elderly person in Ghana?",
  "input": "Context: First meeting, formal",
  "output": "In Ghana, when greeting an elderly person:\n\n1. Use 'Maakye' (Good morning) or 'Maaha' (Good afternoon)\n2. Add 'Nana' (respectful term for elder)\n3. Slightly bow or lower your gaze\n4. Wait for their response before continuing\n\nExample: 'Maakye, Nana. Ɛte sɛn?'\n\nShowing respect to elders is very important in Ghanaian culture."
}
```

---

## 💰 Budget Breakdown

| Item | Cost |
|------|------|
| **RunPod GPU** | $400-600 |
| **Data Collection** | $500-1000 |
| **Native Speakers** | $300-500 |
| **Tools & Storage** | $150-300 |
| **Experiments** | $200-300 |
| **TOTAL** | **$1,550-2,700** |

---

## 📅 Timeline

```
Month 1: Preparation
├── Week 1: Setup infrastructure
├── Week 2: Collect data (1,500+ samples)
├── Week 3: Prepare training datasets
└── Week 4: Validate data quality

Month 2: Fine-Tuning
├── Week 1: Train Llama 3.2 3B
├── Week 2: Train Aya-23 8B
├── Week 3: Train Mistral 7B (optional)
└── Week 4: Initial evaluation

Month 3: Production
├── Week 1: Native speaker evaluation
├── Week 2: Iterate based on feedback
├── Week 3: Deploy to production
└── Week 4: Monitor and optimize
```

---

## ✅ Success Criteria

### Technical:
- ✅ Perplexity <15 on Twi text
- ✅ >85% cultural accuracy
- ✅ >80% language quality
- ✅ <500ms inference (3B model)

### Business:
- ✅ >75% task completion
- ✅ >4/5 user satisfaction
- ✅ <$0.01 per 1K tokens

### Cultural:
- ✅ >90% appropriateness
- ✅ >85% native approval
- ✅ Proper proverb usage
- ✅ Natural code-switching

---

## 🚀 Deployment Options

### Option 1: Ollama (Easiest)
```bash
# Convert to Ollama format
ollama create kasaai-twi -f Modelfile
ollama run kasaai-twi

# Use in Open WebUI automatically
```

### Option 2: API (Production)
```python
# Add to core_backend
from transformers import AutoModelForCausalLM

class GhanaianLLMService:
    def __init__(self):
        self.model = AutoModelForCausalLM.from_pretrained(
            "kasaai-llama-3b-twi-v1",
            device_map="auto",
            load_in_4bit=True
        )

    def generate(self, prompt):
        return self.model.generate(prompt, max_length=512)

# Endpoint: POST /api/llm/generate
```

### Option 3: Hybrid
- **Llama 3B:** Local GPU (fast, cheap)
- **Aya 8B:** RunPod (quality, Ghanaian)
- **Auto-route:** Based on query language

---

## 🎓 Training Resources

### Documentation:
- [Axolotl Docs](https://github.com/OpenAccess-AI-Collective/axolotl)
- [Unsloth](https://github.com/unslothai/unsloth)
- [PEFT Tutorial](https://huggingface.co/docs/peft)

### Datasets:
- [Masakhane](https://github.com/masakhane-io/masakhane) - African NLP
- [AfriSenti](https://github.com/afrisenti-semeval/afrisent-semeval-2023)
- Twi Bible, Wikipedia

### Community:
- [r/LocalLLaMA](https://reddit.com/r/LocalLLaMA)
- [Masakhane Slack](https://join.slack.com/t/masakhane-nlp/shared_invite/)
- [Hugging Face Discord](https://hf.co/join/discord)

---

## 📞 Next Steps

1. **Review full plan:** `LLM_FINETUNING_PLAN.md`
2. **Set up RunPod:** Get 48GB GPU
3. **Start data collection:** 1,500+ samples
4. **Begin with Llama 3.2 3B:** Proven and affordable
5. **Iterate quickly:** Test → Feedback → Improve

---

**Questions?** See the complete plan for detailed implementation steps!
