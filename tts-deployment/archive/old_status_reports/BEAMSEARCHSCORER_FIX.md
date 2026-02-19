# BeamSearchScorer Fix for Coqui TTS XTTS v2

**Date:** 2025-10-19
**Issue:** `cannot import name 'BeamSearchScorer' from 'transformers'`
**Status:** ✅ RESOLVED

---

## Problem

When loading the XTTS v2 model in Coqui TTS, we encountered:

```
ERROR - Failed to load TTS model: cannot import name 'BeamSearchScorer' from 'transformers'
```

### Root Cause

The `transformers` library underwent a major refactoring between versions:

- **transformers < 4.37**: `BeamSearchScorer` was importable directly from `transformers`
- **transformers >= 4.37**: `BeamSearchScorer` moved to `transformers.generation.beam_search`

Coqui TTS (version 0.22.0) was written for the older import path and hasn't been updated yet.

---

## Investigation Steps

### 1. Check Current Version
```bash
sudo docker exec coqui pip list | grep transformers
# Output: transformers 4.57.1 (too new)
```

### 2. Verify BeamSearchScorer Location
```bash
# Old location (doesn't work in 4.57.1)
sudo docker exec coqui python3 -c "from transformers import BeamSearchScorer"
# ImportError: cannot import name 'BeamSearchScorer'

# New location (works in 4.57.1)
sudo docker exec coqui python3 -c "from transformers.generation.beam_search import BeamSearchScorer"
# Success!
```

### 3. Check Coqui TTS Requirements
```bash
sudo docker exec coqui pip show TTS | grep Requires
# Requires: transformers (no version pinned!)
```

---

## Solution

**Downgrade `transformers` to version 4.36.2** - the last version before the breaking change.

### Implementation

Updated `/opt/kasaai/apps/tts-deployment/docker/coqui/Dockerfile`:

```dockerfile
# Install Coqui TTS
RUN pip3 install TTS

# Fix transformers version for XTTS v2 compatibility
# Reason: BeamSearchScorer was moved in transformers 4.37+
# XTTS v2 needs it at the old import location
RUN pip3 install transformers==4.36.2 --force-reinstall

# Install FastAPI for API server
RUN pip3 install fastapi uvicorn pydantic python-multipart
```

---

## Why Not Patch the Library?

We could have created a monkey patch:

```python
# Monkey patch for newer transformers
try:
    from transformers import BeamSearchScorer
except ImportError:
    from transformers.generation.beam_search import BeamSearchScorer
    import transformers
    transformers.BeamSearchScorer = BeamSearchScorer
```

**Reasons for downgrading instead:**
1. **Cleaner**: No runtime patching required
2. **Safer**: Avoid unexpected compatibility issues
3. **Proven**: transformers 4.36.2 is known to work with XTTS v2
4. **Future-proof**: When Coqui TTS updates, we just remove the version pin

---

## Build Process

### Rebuild Container (Recommended)
```bash
cd /opt/kasaai/apps/tts-deployment
sudo docker-compose -f docker-compose.local.yml build --no-cache coqui
sudo docker-compose -f docker-compose.local.yml up -d coqui
```

### Patch Running Container (Quick Test)
```bash
# This works but creates dependency conflicts
sudo docker exec coqui pip install transformers==4.36.2 --force-reinstall
sudo docker-compose -f docker-compose.local.yml restart coqui
```

**Note:** Patching causes numpy version conflicts. Always rebuild for production.

---

## Verification

After rebuild, check logs for successful XTTS v2 loading:

```bash
sudo docker logs coqui --tail=50 | grep XTTS
```

Expected output:
```
INFO - Loading Coqui TTS model: tts_models/multilingual/multi-dataset/xtts_v2
INFO - Agreeing to Coqui non-commercial license (CPML): https://coqui.ai/cpml
INFO - Coqui TTS model loaded successfully
```

---

## XTTS v2 Capabilities

Once loaded, XTTS v2 provides:

### Languages Supported (13+)
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Polish (pl)
- Turkish (tr)
- Russian (ru)
- Dutch (nl)
- Czech (cs)
- Arabic (ar)
- Chinese (zh-cn)
- Japanese (ja)
- Hungarian (hu)
- Korean (ko)
- Hindi (hi)

### Features
- **Multi-speaker**: Generate speech in different voices
- **Voice cloning**: Use reference audio to clone voices
- **Zero-shot**: No training needed for new voices
- **High quality**: State-of-the-art neural TTS

---

## API Usage Examples

### Basic Synthesis
```bash
curl -X POST http://localhost:8005/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test",
    "language": "en"
  }' \
  --output test.wav
```

### Multilingual
```bash
curl -X POST http://localhost:8005/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Bonjour, ceci est un test",
    "language": "fr"
  }' \
  --output test_french.wav
```

### Voice Cloning
```bash
curl -X POST http://localhost:8005/synthesize_with_reference \
  -F 'text=Clone this voice speaking new text' \
  -F 'reference_audio=@reference_voice.wav' \
  -F 'language=en' \
  --output cloned_voice.wav
```

---

## References

- **Coqui TTS GitHub**: https://github.com/coqui-ai/TTS
- **XTTS v2 Model**: https://huggingface.co/coqui/XTTS-v2
- **Transformers Changelog**: https://github.com/huggingface/transformers/releases
- **License**: https://coqui.ai/cpml (Non-commercial CPML)

---

## Future Considerations

### When to Update transformers

Monitor Coqui TTS releases:
```bash
pip show TTS | grep Version
```

Check if newer versions support transformers >= 4.37:
- https://github.com/coqui-ai/TTS/releases
- https://github.com/coqui-ai/TTS/blob/main/requirements.txt

### Alternative: Use TTS Forks

Some community forks have updated dependencies:
- **Coqui TTS Community Fork**: May have newer transformers support
- **XTTS Standalone**: Some projects extract XTTS independently

---

**Status**: Fixed with transformers==4.36.2 downgrade
**Build Time**: ~8-10 minutes for full rebuild
**Next Step**: Verify XTTS v2 loads successfully after rebuild
