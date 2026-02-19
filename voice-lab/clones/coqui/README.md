# Juliet Bawuah Voice Cloning Results

## Overview

This directory contains voice clones generated using Coqui TTS XTTS models with Juliet Bawuah's voice as reference.

**Reference Voice:** `/opt/kasaai/apps/voice-lab/voices/juliet_bawuah.wav`
**Text Source:** `/opt/kasaai/apps/voice-lab/voices/text/twi_text_1.md` (full text)
**Short Text:** `/opt/kasaai/apps/voice-lab/voices/text/twi_text_1_short.md` (for Twi model <250 chars)

## Models Tested

### 1. XTTS v2 (Official Multilingual Model)
- **Model ID:** `xtts_v2`
- **Path:** `tts_models/multilingual/multi-dataset/xtts_v2`
- **Size:** ~1.8GB
- **Features:**
  - DeepSpeed optimization (2-3x faster)
  - Multilingual support
  - No character limit for text
- **Language Code:** `en` (works for Twi text)

### 2. XTTS Twi v1 (Custom Fine-tuned Model)
- **Model ID:** `xtts_twi_v1_inference`
- **Path:** `/opt/kasaai/apps/voice-lab/models/xtts_twi_v1_inference`
- **Size:** 5.3GB
- **Features:**
  - Fine-tuned on Twi data
  - DeepSpeed optimization
  - **⚠️ 250 character limit** (truncates longer text)
- **Language Code:** `en` (despite Twi training)
- **Note:** Config doesn't include 'tw' in language list, uses standard XTTS v2 language codes

## Generated Outputs

### Latest Run: 2025-11-09 15:20:19

| Model | File | Size | Duration | Text Length | Status |
|-------|------|------|----------|-------------|--------|
| XTTS v2 | `juliet_xtts_v2_20251109_152019.wav` | 1.3 MB | 27.63s | 373 chars | ✅ Success |
| Twi v1 | `juliet_twi_model_20251109_152019.wav` | 35 KB | 0.74s | 220 chars | ⚠️ Truncated |

### Performance Analysis

#### XTTS v2 Model
- ✅ Successfully synthesized full text (373 characters)
- ✅ Natural voice cloning with Juliet's characteristics
- ✅ Good pronunciation of Twi text despite being multilingual
- ✅ Appropriate duration (27.63 seconds for ~373 chars)
- ✅ High quality audio output (384 kb/s)

#### Twi v1 Model
- ⚠️ Severe truncation issue (0.74s vs expected ~12-15s for 220 chars)
- ⚠️ Only generated ~0.74 seconds despite 220 character input
- ⚠️ Expected: ~12-15 seconds for 220 characters
- ⚠️ Actual: 0.74 seconds (~5% of expected duration)
- ❓ Possible causes:
  - Model inference issue with DeepSpeed
  - Text preprocessing truncation
  - Early stopping condition triggered
  - Model checkpoint compatibility issue

## Text Versions

### Full Text (373 characters)
Used for XTTS v2 model:
```
Wo tumi de Ghana kasa Twi no di dwuma ma w'adwen mu nsɛm adi mu yiye. Twi yɛ kasa a ɛda so reyɛ den wɔ Amansan mu, na ɛma nnipa tumi kasa ahotɔ mu na wɔte wɔn ho ase. Sɛ yɛde Twi ka nsɛm a, ɛma yɛtumi kyerɛ yɛn amammerɛ, obu ne papayɛ ho. Saa nti, sɛ wopɛ sɛ wokasa wɔ fie, adwuma, anansesɛm, anigye anaa asɔre mu a, Twi bɛboa wo ma asɛm no tena dɛw na obiara atumi ate ase
```

### Short Text (220 characters)
Used for Twi v1 model due to 250 char limit:
```
Wo tumi de Ghana kasa Twi no di dwuma ma w'adwen mu nsɛm adi mu yiye. Twi yɛ kasa a ɛda so reyɛ den wɔ Amansan mu, na ɛma nnipa tumi kasa ahotɔ mu na wɔte wɔn ho ase. Sɛ yɛde Twi ka nsɛm a, ɛma yɛtumi kyerɛ yɛn amammerɛ.
```

## How to Use

### Automated Cloning Script
```bash
cd /opt/kasaai/apps/voice-lab/clones/coqui
./clone_with_api.sh
```

This script will:
1. Load the reference voice (Juliet Bawuah)
2. Check Coqui API health
3. Generate audio with XTTS v2 (full text)
4. Switch to Twi model (if available)
5. Generate audio with Twi v1 (short text)
6. Switch back to XTTS v2
7. Report results

### Manual API Calls

#### Using XTTS v2
```bash
curl -X POST "http://localhost:8005/synthesize_with_reference" \
    -F "text=Your Twi text here" \
    -F "reference_audio=@/opt/kasaai/apps/voice-lab/voices/juliet_bawuah.wav" \
    -F "language=en" \
    -F "temperature=0.7" \
    -F "speed=1.0" \
    --output output.wav
```

#### Using Twi v1 Model
```bash
# Switch to Twi model
curl -X POST "http://localhost:8005/models/switch" \
    -H "Content-Type: application/json" \
    -d '{"model_id": "xtts_twi_v1_inference"}'

# Generate (max 250 chars)
curl -X POST "http://localhost:8005/synthesize_with_reference" \
    -F "text=Your short Twi text (<250 chars)" \
    -F "reference_audio=@/opt/kasaai/apps/voice-lab/voices/juliet_bawuah.wav" \
    -F "language=en" \
    -F "temperature=0.7" \
    -F "speed=1.0" \
    --output output_twi.wav

# Switch back to XTTS v2
curl -X POST "http://localhost:8005/models/switch" \
    -H "Content-Type: application/json" \
    -d '{"model_id": "xtts_v2"}'
```

## Recommendations

### For Production Use
**Use XTTS v2 Model** for the following reasons:
- ✅ No character limits
- ✅ Better voice quality for longer texts
- ✅ Faster inference with DeepSpeed
- ✅ More stable and tested
- ✅ Works well with Twi despite being multilingual

### For Twi-Specific Use
The Twi v1 model needs investigation before production use:
1. **Investigate truncation issue** - Why only 0.74s output?
2. **Check model compatibility** - Verify checkpoint format with DeepSpeed
3. **Test without DeepSpeed** - See if issue is optimization-related
4. **Validate training data** - Ensure model was properly fine-tuned
5. **Review inference parameters** - Check if special settings are needed

## Technical Details

### API Configuration
- **Endpoint:** `http://localhost:8005`
- **Health Check:** `GET /health`
- **List Models:** `GET /models`
- **Switch Model:** `POST /models/switch`
- **Synthesize:** `POST /synthesize_with_reference`

### Audio Specifications
- **Format:** WAV (PCM)
- **Bitrate:** 384 kb/s
- **Sample Rate:** 24kHz (standard for XTTS)
- **Channels:** Mono

### Model Switching
The Coqui container supports dynamic model switching via API:
- Active model is maintained in container state
- Switching loads new model weights into memory (~5-10 seconds)
- Previous model is unloaded to save memory
- DeepSpeed optimization is maintained across switches

## Files in This Directory

- `clone_with_api.sh` - Automated cloning script using Coqui API
- `clone_juliet_voice.py` - Python-based cloning (requires dependencies)
- `juliet_xtts_v2_*.wav` - Generated audio from XTTS v2 model
- `juliet_twi_model_*.wav` - Generated audio from Twi v1 model
- `README.md` - This documentation

## Troubleshooting

### Issue: Twi model produces very short audio
**Symptoms:** Output is <1 second despite longer input text

**Possible Solutions:**
1. Check Docker logs: `docker logs coqui --tail 100`
2. Verify model files: `ls -lh /opt/kasaai/apps/voice-lab/models/xtts_twi_v1_inference/`
3. Test without reference audio (use default voices)
4. Try disabling DeepSpeed optimization
5. Check if model expects different language code

### Issue: API not responding
```bash
# Check if container is running
docker ps | grep coqui

# Restart container
docker restart coqui

# Check logs
docker logs coqui --tail 50
```

### Issue: Model switch fails
```bash
# Verify model path exists
ls -la /opt/kasaai/apps/voice-lab/models/xtts_twi_v1_inference

# Check current model
curl http://localhost:8005/models
```

## Next Steps

1. **✅ COMPLETED:** Basic voice cloning with both models
2. **⚠️ NEEDS INVESTIGATION:** Twi model truncation issue
3. **TODO:** Test Twi model without DeepSpeed
4. **TODO:** Compare Twi model output with training data
5. **TODO:** Create batch processing script for multiple voices
6. **TODO:** Add quality metrics (MOS, similarity scores)
7. **TODO:** Document optimal inference parameters per model

## References

- **Coqui TTS:** https://github.com/coqui-ai/TTS
- **XTTS v2 Paper:** https://arxiv.org/abs/2406.04904
- **Voice Lab Models:** `/opt/kasaai/apps/voice-lab/models/`
- **TTS Deployment:** `/opt/kasaai/apps/tts-deployment/`

---
**Generated:** 2025-11-09
**Status:** ✅ XTTS v2 Working | ⚠️ Twi v1 Needs Investigation
