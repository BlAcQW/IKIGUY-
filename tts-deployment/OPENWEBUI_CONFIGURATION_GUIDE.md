# Open WebUI Configuration Guide

**Updated:** 2025-10-20
**For:** KasaAI TTS Lab Integration

---

## Overview

This guide explains how to configure Open WebUI to work with your TTS services and LLM models.

## Table of Contents

1. [LLM Model Setup](#llm-model-setup)
2. [TTS Integration](#tts-integration)
3. [Model Selection Options](#model-selection-options)
4. [Ollama Setup (Optional)](#ollama-setup-optional)

---

## LLM Model Setup

### Option 1: Use OpenAI-Compatible API (Recommended)

Since your KasaAI API doesn't have a `/v1/models` endpoint yet, you have two approaches:

#### A. Add OpenAI API Key

1. Log in to Open WebUI: https://openwebui.ailabsafrica.com
2. Click your profile icon (top right) → **Settings**
3. Go to **Connections** tab
4. Under **OpenAI API**, add your OpenAI API key
5. Save

This gives you immediate access to GPT-4, GPT-3.5, etc.

#### B. Configure Custom LLM Endpoint

If you have your own LLM service running:

1. Go to **Settings** → **Connections**
2. Under **OpenAI API**:
   - **API Base URL**: `https://api.ailabsafrica.com/v1` (or your LLM endpoint)
   - **API Key**: Your API key
3. Save and test

### Option 2: Install Ollama for Local Models

Ollama lets you run LLMs locally on your GPU. This is recommended since you have a 20GB GPU available.

#### Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version

# Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama
```

#### Pull Models

```bash
# Small, fast model (4GB)
ollama pull llama3.2:3b

# Medium quality model (7GB)
ollama pull llama3.2:7b

# High quality model (requires 13GB+ VRAM)
ollama pull llama3.1:8b

# Or use Mistral
ollama pull mistral:7b

# Check installed models
ollama list
```

#### Configure Open WebUI to Use Ollama

1. Open WebUI should auto-detect Ollama at `http://localhost:11434`
2. If not, go to **Settings** → **Connections**
3. Under **Ollama API**:
   - **Ollama Base URL**: `http://localhost:11434`
   - Click **Verify Connection**
4. Your models will appear in the model selector

---

## TTS Integration

Open WebUI supports TTS through multiple methods:

### Method 1: OpenAI TTS API (Easiest)

1. Go to **Settings** → **Audio**
2. Under **Text-to-Speech**:
   - **TTS Engine**: OpenAI
   - **API Key**: Your OpenAI key
   - **Voice**: Select from alloy, echo, fable, onyx, nova, shimmer
3. Save

### Method 2: Custom TTS API (Your TTS Services)

You have multiple TTS services already deployed:

- **Coqui TTS**: https://coqui.ailabsafrica.com (Voice cloning, Twi support)
- **MeloTTS**: https://melotts.ailabsafrica.com (Fast multilingual)
- **OpenVoice**: https://openvoice.ailabsafrica.com (Voice cloning)
- **Kokoro TTS**: https://kokoro.ailabsafrica.com

#### Configure Custom TTS in Open WebUI

Open WebUI v0.6.34 supports custom TTS through **Functions** (custom Python scripts).

**Create TTS Function:**

1. Go to **Workspace** → **Functions**
2. Click **+ Add Function**
3. Name it "KasaAI TTS"
4. Add this code:

```python
"""
title: KasaAI TTS Integration
author: KasaAI
version: 1.0.0
"""

import requests
import json

class Tools:
    def __init__(self):
        pass

    def synthesize_speech(self, text: str, provider: str = "coqui", voice: str = None) -> str:
        """
        Synthesize speech using KasaAI TTS services.

        Args:
            text: Text to synthesize
            provider: TTS provider (coqui, melotts, openvoice, kokoro)
            voice: Voice ID (optional, depends on provider)

        Returns:
            Audio file URL
        """

        # Provider endpoints
        endpoints = {
            "coqui": "https://coqui.ailabsafrica.com/synthesize",
            "melotts": "https://melotts.ailabsafrica.com/synthesize",
            "openvoice": "https://openvoice.ailabsafrica.com/synthesize",
            "kokoro": "https://kokoro.ailabsafrica.com/synthesize"
        }

        if provider not in endpoints:
            return f"Error: Unknown provider '{provider}'"

        try:
            # Prepare request
            payload = {
                "text": text,
                "language": "en"  # or "tw" for Twi
            }

            if voice:
                payload["speaker_id"] = voice

            # Make request
            response = requests.post(
                endpoints[provider],
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("audio_url", "Audio generated successfully")
            else:
                return f"Error: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Error: {str(e)}"
```

5. Click **Save**

Now you can use it in chat:
```
Can you synthesize this text with Coqui TTS: "Hello, welcome to KasaAI"
```

### Method 3: WebSocket TTS (Advanced)

For real-time streaming TTS, you can configure Open WebUI to use your TTS services via WebSocket. This requires modifying the Open WebUI environment variables.

---

## Model Selection Options

### Current Setup

Based on your existing infrastructure:

#### 1. **Use Ollama for LLMs** (Recommended)
   - ✅ Runs locally on your 20GB GPU
   - ✅ No API costs
   - ✅ Fast inference
   - ✅ Privacy (no data leaves your server)
   - ✅ Supports many models (Llama, Mistral, Gemma, etc.)

#### 2. **Use OpenAI API for LLMs**
   - ✅ Best quality (GPT-4)
   - ✅ No local setup needed
   - ❌ API costs
   - ❌ Data sent to OpenAI

#### 3. **Hybrid Approach** (Best of Both)
   - Use Ollama for general queries (fast, free)
   - Use OpenAI for complex tasks (quality)
   - Switch models in the UI dropdown

### Recommended Models for Your GPU (20GB VRAM)

Since you have 20GB VRAM and already running TTS services, you can run:

**Single Model (Recommended):**
- **Llama 3.2 7B** (7GB VRAM) - Best balance
- Leaves 13GB for TTS services ✅

**If TTS services are on separate GPU:**
- **Llama 3.1 8B** (13GB VRAM) - Higher quality
- **Mistral 7B** (7GB VRAM) - Fast and efficient

**Small Models (if needed):**
- **Llama 3.2 3B** (4GB VRAM) - Very fast
- **Phi-3 Mini** (4GB VRAM) - Excellent for coding

---

## Ollama Setup (Optional)

If you want local LLM inference:

### 1. Install Ollama

```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Start service
sudo systemctl enable ollama
sudo systemctl start ollama

# Check status
sudo systemctl status ollama
```

### 2. Pull Your First Model

```bash
# Recommended for your setup (7GB VRAM)
ollama pull llama3.2:7b

# Wait for download (will take 5-10 minutes)
```

### 3. Test Ollama

```bash
# Test the model
ollama run llama3.2:7b "Hello, how are you?"

# List models
ollama list
```

### 4. Configure in Open WebUI

1. Go to https://openwebui.ailabsafrica.com
2. Open **Settings** → **Connections**
3. Ollama should auto-detect at `http://localhost:11434`
4. Click **Verify Connection**
5. Your models will appear in the dropdown!

### 5. Add More Models (Optional)

```bash
# Fast coding assistant
ollama pull codellama:7b

# Multilingual support
ollama pull aya:8b

# Math and reasoning
ollama pull deepseek-coder:6.7b
```

---

## Step-by-Step: Complete Setup

### Quick Setup (5 minutes)

1. **Install Ollama:**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   sudo systemctl start ollama
   ollama pull llama3.2:7b
   ```

2. **Configure Open WebUI:**
   - Go to https://openwebui.ailabsafrica.com
   - Settings → Connections → Verify Ollama connection
   - Select "llama3.2:7b" from model dropdown

3. **Add TTS:**
   - Settings → Audio → Enable TTS
   - Choose OpenAI TTS (if you have API key)
   - OR create custom function (see above)

### Advanced Setup (30 minutes)

1. **Install Ollama + Multiple Models**
2. **Configure GPU memory limits**
3. **Set up custom TTS function**
4. **Configure model-specific parameters**
5. **Test with your Twi/Ghanaian voices**

---

## GPU Memory Considerations

Your current GPU usage:

```
Total VRAM: 20GB
├── MeloTTS:    ~3GB
├── Coqui TTS:  ~4GB
├── OpenVoice:  ~4GB
├── Kokoro:     ~3GB
└── Available:  ~6GB (enough for Llama 3.2 3B or with offloading)
```

**Recommendation:**
- If all TTS services must run simultaneously, use **Llama 3.2 3B** (4GB)
- If you can stop some TTS services, use **Llama 3.2 7B** (7GB)
- For best experience, dedicate GPU to either TTS or LLM, use CPU for the other

---

## Testing Your Setup

### Test Ollama:
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:7b",
  "prompt": "Hello! Tell me about Ghana."
}'
```

### Test TTS from Open WebUI:
1. Type a message in chat
2. Click the speaker icon to hear the response
3. Or use the function: "Synthesize with Coqui: Hello"

### Test Model Selection:
1. Open chat
2. Click the model dropdown (top of chat)
3. Select different models
4. Send messages to test each one

---

## Troubleshooting

### Ollama not detected:
```bash
# Check if running
sudo systemctl status ollama

# Restart
sudo systemctl restart ollama

# Check logs
sudo journalctl -u ollama -f
```

### GPU out of memory:
```bash
# Stop some TTS services temporarily
sudo docker stop openvoice kokoro

# This frees ~7GB for LLM
ollama run llama3.2:7b
```

### Models not showing in Open WebUI:
1. Refresh the page
2. Check Settings → Connections
3. Verify Ollama URL: `http://localhost:11434`
4. Pull at least one model: `ollama pull llama3.2:3b`

---

## Next Steps

1. ✅ **Install Ollama** (if you want local models)
2. ✅ **Pull a model**: `ollama pull llama3.2:7b`
3. ✅ **Test in Open WebUI**: Select model and chat
4. ✅ **Add TTS**: Configure audio settings
5. ✅ **Create custom functions** for your TTS services

## Support

- **Ollama Docs**: https://ollama.com/docs
- **Open WebUI Docs**: https://docs.openwebui.com
- **Model Library**: https://ollama.com/library

---

**Questions?** Check the [Open WebUI Deployment Guide](./OPENWEBUI_DEPLOYMENT.md) for management commands.
