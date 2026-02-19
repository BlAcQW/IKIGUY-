# Chatterbox TTS Setup

**Status:** Implemented ✅

## Overview
Chatterbox is Resemble AI's first production-grade open source TTS model supporting **23 languages** out of the box with zero-shot voice cloning capabilities.

## Implementation Details

### Repository
- **Source:** https://github.com/resemble-ai/chatterbox
- **License:** MIT
- **Model:** 0.5B Llama backbone trained on 0.5M hours of cleaned data

### Features
- **Multilingual Support:** 23 languages including Arabic, Chinese, English, French, German, Spanish, Hindi, Japanese, and more
- **Voice Cloning:** Zero-shot capability to clone voices from reference audio clips
- **Emotion Control:** Unique exaggeration/intensity parameter for expressive speech synthesis
- **Audio Watermarking:** Built-in Perth (Perceptual Threshold) watermarks for detecting synthetic speech

### Supported Languages
Arabic (ar), Danish (da), German (de), Greek (el), English (en), Spanish (es), Finnish (fi), French (fr), Hebrew (he), Hindi (hi), Italian (it), Japanese (ja), Korean (ko), Malay (ms), Dutch (nl), Norwegian (no), Polish (pl), Portuguese (pt), Russian (ru), Swedish (sv), Swahili (sw), Turkish (tr), Chinese (zh)

## Docker Configuration

### Container Details
- **Port:** 8004
- **Interface:** Gradio web UI
- **GPU:** Required (CUDA 12.1)
- **Python:** 3.11

### Build and Run
```bash
# Build the container
sudo docker-compose -f docker-compose.local.yml build chatterbox

# Start the service
sudo docker-compose -f docker-compose.local.yml up -d chatterbox

# View logs
sudo docker-compose -f docker-compose.local.yml logs -f chatterbox
```

### Access
- **Local:** http://localhost:8004
- **Production:** https://chatterbox.ailabsafrica.com (via nginx proxy)

## Usage

### Gradio Web Interface
The Gradio interface provides:
- Text input for synthesis (max 300 characters)
- Language selection (23 languages)
- Optional reference audio upload for voice cloning
- Exaggeration slider (0.25-2.0) for emotion control
- CFG/Pace slider for generation guidance
- Advanced options: temperature, random seed

### API Parameters
- **text_input:** Text to synthesize (max 300 chars)
- **language_id:** Language code (e.g., 'en', 'fr', 'es')
- **audio_prompt_path:** Optional reference audio for voice cloning
- **exaggeration:** Emotional intensity control (default: 0.5)
- **temperature:** Randomness in generation (default: 0.8)
- **cfg_weight:** CFG/Pace control (default: 0.5, set to 0 for language transfer)

## Technical Details

### Dependencies
- torch==2.6.0
- torchaudio==2.6.0
- transformers==4.46.3
- diffusers==0.29.0
- gradio==5.44.1
- s3tokenizer
- resemble-perth (audio watermarking)
- librosa, conformer, safetensors, and more

### Model Loading
The model is loaded on startup and cached in memory. First-time startup may take longer as models are downloaded from Hugging Face.

### Performance Notes
- Benchmarked against ElevenLabs and consistently preferred in evaluations
- Optimized for production use with alignment-informed inference
- Ultra-stable synthesis quality

## Troubleshooting

### Model Download Issues
If model download fails, ensure:
1. Internet connectivity
2. Sufficient disk space (~2GB for models)
3. HuggingFace is accessible

### GPU Issues
If GPU is not detected:
1. Check CUDA drivers: `nvidia-smi`
2. Verify docker GPU support: `docker run --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi`

### Port Conflicts
If port 8004 is in use, modify docker-compose.local.yml:
```yaml
ports:
  - "8004:8004"  # Change first 8004 to another port
```

---
**Created:** 2025-10-19
**Updated:** 2025-11-08 (Implemented with actual Chatterbox repository)
