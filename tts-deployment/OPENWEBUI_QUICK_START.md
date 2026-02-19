# Open WebUI - Quick Start Guide

**For:** Adding models and TTS to your Open WebUI installation

---

## 🚀 Quick Setup (Choose Your Path)

### Path A: Local Models with Ollama (Recommended)

**Pros:** Free, private, fast, no API costs
**Cons:** Uses GPU memory (4-7GB)

```bash
# Run the setup script
cd /opt/kasaai/apps/tts-deployment
./scripts/setup_ollama.sh
```

That's it! Your models will appear in Open WebUI automatically.

---

### Path B: OpenAI API

**Pros:** Best quality (GPT-4), no local setup
**Cons:** API costs, data sent to OpenAI

1. Go to https://openwebui.ailabsafrica.com
2. Click your profile → **Settings**
3. Go to **Connections** → **OpenAI API**
4. Add your OpenAI API key
5. Save

Done! You can now use GPT-4, GPT-3.5, etc.

---

### Path C: Both (Hybrid - Best Option)

Do both Path A and Path B! Switch between them in the model dropdown:
- Use Ollama for quick/free queries
- Use GPT-4 for complex tasks

---

## 🎤 Adding TTS to Open WebUI

### Option 1: OpenAI TTS (Easiest - 2 minutes)

1. Go to **Settings** → **Audio**
2. Enable **Text-to-Speech**
3. Select **OpenAI** as TTS engine
4. Add your OpenAI API key
5. Choose a voice (alloy, echo, fable, onyx, nova, shimmer)
6. Save

Now every chat response can be spoken! Click the speaker icon.

---

### Option 2: KasaAI TTS Services (Your Custom TTS)

**Step 1: Add the TTS Function**

1. In Open WebUI, go to **Workspace** → **Functions**
2. Click **+ Create New Function**
3. Copy the code from `/opt/kasaai/apps/tts-deployment/openwebui_tts_function.py`
4. Paste it into the function editor
5. Click **Save**

**Step 2: Use TTS in Chat**

Now you can ask the AI to synthesize speech:

```
Synthesize this with Coqui TTS: "Welcome to KasaAI, your AI assistant for Ghana"

Synthesize in Twi: "Akwaaba"

List available voices for Coqui

Show me all TTS providers
```

The AI will use your custom TTS services automatically!

---

## 📊 Current Status

### Your TTS Services (Already Running):
- ✅ **Coqui TTS** - https://coqui.ailabsafrica.com (Twi support!)
- ✅ **MeloTTS** - https://melotts.ailabsafrica.com (Fast)
- ✅ **OpenVoice** - https://openvoice.ailabsafrica.com (Voice cloning)
- ✅ **Kokoro** - https://kokoro.ailabsafrica.com

### Your GPU:
- **Total:** 20GB VRAM
- **TTS Services:** ~14GB
- **Available for LLM:** ~6GB (enough for Llama 3.2 3B)

---

## 🎯 Recommended Setup

Based on your infrastructure:

1. **Install Ollama + Llama 3.2 3B** (4GB, fits in remaining GPU memory)
2. **Add OpenAI API** (optional, for GPT-4 when needed)
3. **Add KasaAI TTS function** (uses your existing TTS services)

This gives you:
- ✅ Free local LLM
- ✅ Premium GPT-4 option
- ✅ Your custom Twi TTS
- ✅ All running on your infrastructure

---

## 🔧 Installation Commands

### Install Ollama + Model (5 minutes):
```bash
# Automated setup
cd /opt/kasaai/apps/tts-deployment
./scripts/setup_ollama.sh

# Or manual:
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl start ollama
ollama pull llama3.2:3b  # 4GB model
```

### Verify Installation:
```bash
# Check Ollama is running
curl http://localhost:11434

# List models
ollama list

# Test a model
ollama run llama3.2:3b "Hello!"
```

### Check Open WebUI:
1. Go to https://openwebui.ailabsafrica.com
2. Settings → Connections
3. Should show "Connected" for Ollama
4. Model dropdown should show your models

---

## 💡 Usage Tips

### Selecting Models in Chat

Click the model dropdown at the top of the chat:
- **llama3.2:3b** - Fast, good for general chat
- **gpt-4** - Best quality (if you added OpenAI key)
- **mistral:7b** - Good balance (if installed)

### Using TTS

**With OpenAI TTS:**
- Type a message
- Click the speaker icon next to the response
- It speaks!

**With KasaAI TTS (via function):**
- Type: "Synthesize with Coqui: Hello from Ghana"
- Or: "Say 'Akwaaba' in Twi using Coqui TTS"
- The AI calls your TTS service and returns the audio URL

### Managing GPU Memory

If GPU is full:
```bash
# Stop some TTS services temporarily
sudo docker stop openvoice kokoro

# This frees ~7GB for a larger LLM
ollama pull llama3.2:7b
ollama run llama3.2:7b

# Restart TTS when done
sudo docker start openvoice kokoro
```

---

## 🎓 What Each Model Is Good For

**Llama 3.2 3B** (4GB):
- ✅ General conversation
- ✅ Simple questions
- ✅ Fast responses
- ❌ Complex reasoning

**Llama 3.2 7B** (7GB):
- ✅ Better reasoning
- ✅ More accurate
- ✅ Coding help
- ⚠️ Needs more VRAM

**GPT-4** (API):
- ✅ Best quality
- ✅ Complex tasks
- ✅ Long context
- 💰 Costs money

---

## 🆘 Troubleshooting

### "No models available"
```bash
# Check Ollama is running
sudo systemctl status ollama

# Pull a model
ollama pull llama3.2:3b

# Refresh Open WebUI page
```

### "Ollama connection failed"
```bash
# Restart Ollama
sudo systemctl restart ollama

# Check it's accessible
curl http://localhost:11434
```

### "Out of memory" error
```bash
# Check GPU usage
nvidia-smi

# Stop some services
sudo docker stop openvoice kokoro

# Or use smaller model
ollama pull llama3.2:3b
```

### TTS function not working
1. Check function is saved in Workspace → Functions
2. Make sure TTS services are running: `sudo docker ps | grep -E "coqui|melotts"`
3. Test endpoint manually: `curl https://coqui.ailabsafrica.com/health`

---

## 📚 Next Steps

Once setup is complete:

1. ✅ **Test LLM models** - Try different models, find your favorite
2. ✅ **Test TTS** - Synthesize some Twi speech!
3. ✅ **Configure settings** - Adjust temperature, top_p, etc.
4. ✅ **Create personas** - Make custom AI assistants
5. ✅ **Invite users** - Share Open WebUI with your team

---

## 🔗 Helpful Links

- **Open WebUI Docs:** https://docs.openwebui.com
- **Ollama Models:** https://ollama.com/library
- **Your TTS Services:** See `/opt/kasaai/apps/tts-deployment/README.md`
- **Configuration Guide:** See `OPENWEBUI_CONFIGURATION_GUIDE.md`

---

## ⚡ One-Line Install

If you just want to get started quickly:

```bash
curl -fsSL https://ollama.com/install.sh | sh && sudo systemctl start ollama && ollama pull llama3.2:3b
```

Then open https://openwebui.ailabsafrica.com and start chatting!

---

**Need Help?** Check the full configuration guide: `OPENWEBUI_CONFIGURATION_GUIDE.md`
