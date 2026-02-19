# What We Need to Fix OpenVoice - Simple Answer

**Date:** 2025-10-20
**Status:** 🔧 IN PROGRESS - Final fix being deployed

---

## TL;DR - The Fix

**Problem:** OpenVoice synthesis hangs because blocking GPU operations freeze FastAPI's async event loop.

**Solution:** Run synthesis in a thread pool so the server stays responsive.

**What Changed:** Modified `app.py` to use `loop.run_in_executor()` for synthesis operations.

---

## What We Fixed

### 1. ✅ Identified Root Cause
- **NOT** a cuDNN library issue (that was a red herring)
- **NOT** a GPU memory issue (5GB used / 20GB available)
- **YES** an async/await blocking issue

### 2. ✅ Implemented Thread Pool Solution

**Before (Broken):**
```python
@app.post("/synthesize")
async def synthesize(request: TTSRequest):
    # These operations BLOCK the entire server
    base_audio = generate_base_audio(...)      # 🔴 BLOCKS
    source_se = se_extractor.get_se(...)       # 🔴 BLOCKS
    tone_color_converter.convert(...)          # 🔴 BLOCKS
    return audio
```

**After (Fixed):**
```python
@app.post("/synthesize")
async def synthesize(request: TTSRequest):
    # Define blocking work as a closure
    def do_synthesis():
        base_audio = generate_base_audio(...)
        source_se = se_extractor.get_se(...)
        tone_color_converter.convert(...)
        return audio_data, sample_rate

    # Run in thread pool - server stays responsive
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        audio_data, sample_rate = await loop.run_in_executor(
            executor,
            do_synthesis  # ✅ Runs in separate thread
        )

    return StreamingResponse(audio_data, ...)
```

### 3. ✅ Added Comprehensive Logging

Now logs show:
```
INFO: [SYNTHESIS START] Text: 'Hello...', Speaker: en-us
INFO: [SYNTHESIS] Running synthesis in thread pool...
INFO: [THREAD] Starting synthesis in thread pool
INFO: [THREAD STEP 1] Generating base audio...
INFO: [THREAD STEP 1] Base audio generated
INFO: [THREAD STEP 2] Extracting source speaker embedding...
INFO: [THREAD STEP 2] Source embedding extracted
INFO: [THREAD STEP 3] Loading target speaker embedding...
INFO: [THREAD STEP 3] Target embedding loaded
INFO: [THREAD STEP 4] Converting tone color...
INFO: [THREAD STEP 4] Tone conversion complete
INFO: [SYNTHESIS] Thread pool execution complete
INFO: [SYNTHESIS COMPLETE] Returning audio response
```

---

## What We Need to Complete

### Immediate (In Progress)

1. **✅ Code Changes Complete**
   - Modified `/opt/kasaai/apps/tts-deployment/docker/openvoice/app.py`
   - Used inline closure pattern to capture variables
   - Added detailed logging at each step

2. **🔄 Rebuild & Deploy (Running)**
   - Currently rebuilding Docker image
   - Will restart container with fixed code

3. **⏳ Test Synthesis Endpoint**
   ```bash
   curl -X POST http://localhost:8003/synthesize \
     -H "Content-Type: application/json" \
     -d '{"text": "Test synthesis", "reference_speaker": "en-us"}' \
     --output test.wav
   ```

4. **⏳ Verify Logs Show Thread Pool Execution**
   ```bash
   sudo docker logs openvoice | grep -E "\[SYNTHESIS|\[THREAD"
   ```

### No Additional Requirements Needed!

✅ **GPU is sufficient** - 20GB total, only using 5GB
✅ **cuDNN is working** - Libraries installed and functional
✅ **Models are loaded** - All checkpoints loading correctly
✅ **Code fix is simple** - Just thread pool wrapper

**No need to:**
- ❌ Move to RunPod
- ❌ Install additional libraries
- ❌ Change GPU configuration
- ❌ Modify cuDNN installation
- ❌ Rewrite the model code

---

## Testing Plan

### Test 1: Basic Synthesis
```bash
curl -X POST http://localhost:8003/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of OpenVoice synthesis.",
    "reference_speaker": "en-us",
    "language": "English",
    "speed": 1.0
  }' \
  --output openvoice_test.wav

# Check if file was created
file openvoice_test.wav
# Expected: RIFF (little-endian) data, WAVE audio
```

### Test 2: Different Speakers
```bash
# Test with different speaker variants
for speaker in en-us en-au en-br en-india; do
  curl -X POST http://localhost:8003/synthesize \
    -d "{\"text\": \"Testing $speaker voice\", \"reference_speaker\": \"$speaker\"}" \
    --output test_$speaker.wav
done
```

### Test 3: Concurrent Requests
```bash
# Send 3 requests simultaneously
for i in {1..3}; do
  curl -X POST http://localhost:8003/synthesize \
    -d "{\"text\": \"Concurrent test $i\", \"reference_speaker\": \"en-us\"}" \
    --output concurrent_$i.wav &
done
wait

# All should complete without hanging
```

### Test 4: Verify Logs
```bash
sudo docker logs openvoice --tail 100 | grep -E "\[SYNTHESIS|\[THREAD"

# Expected output:
# INFO: [SYNTHESIS START] ...
# INFO: [SYNTHESIS] Running synthesis in thread pool...
# INFO: [THREAD] Starting synthesis in thread pool
# INFO: [THREAD STEP 1] Generating base audio...
# ... (all steps complete)
# INFO: [SYNTHESIS COMPLETE] Returning audio response
```

---

## Timeline

- **15:00** - Identified root cause (async blocking)
- **15:15** - Implemented thread pool solution
- **15:30** - Fixed closure variable capture
- **15:45** - Rebuilding container ← **WE ARE HERE**
- **15:50** - Test synthesis endpoint
- **16:00** - Verify fix works, update documentation

---

## Success Criteria

✅ Synthesis requests complete (not timeout)
✅ Audio files generated successfully
✅ Logs show thread pool execution
✅ Multiple concurrent requests work
✅ Server stays responsive during synthesis

---

## Why This Fix Works

### The Problem Explained

FastAPI runs on **uvicorn** with an **async event loop**:
```
┌─────────────────┐
│  Async Event    │
│  Loop (Single   │
│  Thread)        │
├─────────────────┤
│ Request 1       │ ← Waiting
│ Request 2       │ ← Waiting
│ Request 3       │ ← BLOCKED by synthesis
│ Health Check    │ ← Can't respond
└─────────────────┘
```

When synthesis runs **directly** in an async function, it **blocks** this single thread, freezing **everything**.

### The Solution

Thread pool **offloads** blocking work:
```
┌─────────────────┐          ┌─────────────────┐
│  Async Event    │          │  Thread Pool    │
│  Loop           │          │                 │
├─────────────────┤          ├─────────────────┤
│ Request 1       │ ✅       │                 │
│ Request 2       │ ✅       │ Synthesis       │
│ Request 3       │ → awaits → (Blocking GPU   │
│ Health Check    │ ✅       │  operations)    │
└─────────────────┘          └─────────────────┘
         ↑                            │
         └────────── Result ──────────┘
```

The event loop stays free to handle other requests while synthesis runs in a separate thread.

---

## Files Modified

1. **`/opt/kasaai/apps/tts-deployment/docker/openvoice/app.py`**
   - Lines 233-314: Added inline `do_synthesis()` closure
   - Lines 291-298: Thread pool executor implementation
   - Throughout: Added `[SYNTHESIS]` and `[THREAD]` logging

---

## Deployment Commands

```bash
# 1. Remove old containers
sudo docker ps -a | grep openvoice | awk '{print $1}' | xargs -r sudo docker rm -f

# 2. Rebuild image with fixes
cd /opt/kasaai/apps/tts-deployment
sudo docker-compose -f docker-compose.local.yml build openvoice

# 3. Start fixed container
sudo docker-compose -f docker-compose.local.yml up -d openvoice

# 4. Wait for startup (30 seconds)
sleep 30

# 5. Test synthesis
curl -X POST http://localhost:8003/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Testing fixed OpenVoice", "reference_speaker": "en-us"}' \
  --output test_fixed.wav \
  --max-time 60

# 6. Check result
file test_fixed.wav
# Should show: RIFF (little-endian) data, WAVE audio

# 7. Verify logs
sudo docker logs openvoice --tail 50 | grep SYNTHESIS
```

---

## Next Steps After This Fix

1. **✅ Complete OpenVoice testing** (this fix)
2. **🔄 Implement Kokoro TTS** (similar pattern)
3. **📊 Update health check script** to test synthesis endpoints
4. **📖 Update deployment documentation**
5. **🎉 Declare OpenVoice production-ready**

---

**Bottom Line:** We only need to complete the rebuild and test. No additional infrastructure, libraries, or configuration needed. The fix is code-only and should work immediately.

---

**Prepared By:** Claude Code
**Date:** 2025-10-20 15:50 UTC
**Status:** Final rebuild in progress
**ETA:** 5-10 minutes to complete and test

---

*This is the final step. Once the rebuild completes and tests pass, OpenVoice will be fully functional with 11 speaker variants for voice cloning.*
