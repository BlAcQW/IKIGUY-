# WebRTC First Message - Testing Guide

## Quick Test Checklist

Use this guide to verify the proper WebRTC first message implementation is working correctly.

---

## Prerequisites

1. **Backend running**: `sudo systemctl status kasaai-core-backend`
2. **Frontend built**: Latest build deployed (2025-11-22)
3. **Voice assistant configured**: At least one assistant with first_message settings

---

## Test 1: Assistant Speaks First (Predefined Message)

### Setup
1. Navigate to Voice Agent configuration
2. Set the following:
   - **First Message Mode**: "Assistant speaks first"
   - **First Message**: "Hello! I'm your AI assistant. How can I help you today?"
   - **TTS Provider**: Any provider (e.g., elevenlabs, openai, melotts)
   - **TTS Voice**: Any available voice

### Test Procedure
1. Click "Talk to Assistant" button
2. Open Browser Developer Tools (F12)
3. Go to Network tab
4. Allow microphone access
5. Wait for connection to establish

### Expected Results ✅

**Browser Console Logs:**
```
[RTC] 🔗 Initiating WebRTC connection...
[RTC] 🎤 Requesting microphone access...
[RTC] ✅ Microphone access granted
[RTC] 📝 Creating WebRTC offer...
[RTC] 📥 Received answer from server
[RTC] ✅ WebRTC connection established
[RTC] 📡 Data channel opened
[RTC] 💬 Text response: Hello! I'm your AI assistant...
[RTC] 🔊 Audio chunk received (XXXX bytes)
[RTC] 🔊 Audio chunk received (XXXX bytes)
...
[AudioQueue] 📥 Enqueued chunk (queue size: X)
[AudioQueue] 🔊 Playing chunk (X remaining in queue)
```

**Browser Network Tab:**
- ✅ POST to `/voice/webrtc/offer` (WebRTC SDP exchange)
- ❌ NO POST to `/voice/webrtc/first-message` (HTTP endpoint removed!)

**Audio Playback:**
- ✅ Greeting plays smoothly within 1 second
- ✅ No gaps or stuttering
- ✅ Clear audio quality

**Backend Logs:**
```bash
sudo journalctl -u kasaai-core-backend -f | grep -E "(🎬|⚡|✅.*streaming)"
```

Expected output:
```
🎬 Streaming first message for assistant: {assistant_id}
💬 First message text sent: 'Hello! I'm your AI assistant...'
⚡ First audio chunk latency: 0.287s
🔊 Streamed audio chunk #1
🔊 Streamed audio chunk #2
...
✅ First message streaming complete | Chunks: 12 | First chunk: 0.287s | Total: 2.145s
```

### Success Criteria
- [ ] No HTTP call to `/first-message` endpoint
- [ ] Audio plays within 1 second of connection
- [ ] Logs show first chunk latency < 500ms
- [ ] Smooth playback without gaps
- [ ] Data channel messages visible in console

---

## Test 2: Assistant Waits for User

### Setup
1. Navigate to Voice Agent configuration
2. Set the following:
   - **First Message Mode**: "Assistant waits for user"
   - **First Message**: (any text, will be ignored)

### Test Procedure
1. Click "Talk to Assistant" button
2. Wait for connection to establish
3. Observe console and UI

### Expected Results ✅

**Browser Console Logs:**
```
[RTC] 🔗 Initiating WebRTC connection...
[RTC] ✅ WebRTC connection established
[RTC] 📡 Data channel opened
```

**NO Audio Playback:**
- ✅ Silent - no greeting plays
- ✅ Microphone ready for user input
- ✅ Status shows "Your turn - speak now"

**Backend Logs:**
```
🤫 Assistant waiting for user to speak first
```

### Success Criteria
- [ ] No audio plays automatically
- [ ] Connection establishes successfully
- [ ] Microphone is active and ready
- [ ] No TTS generation in logs

---

## Test 3: Assistant Speaks First (Model-Generated)

### Setup
1. Navigate to Voice Agent configuration
2. Set the following:
   - **First Message Mode**: "Assistant speaks first with model-generated message"
   - **First Message**: (leave empty or add guidance like "Be friendly and professional")
   - **LLM Provider**: Configured and working
   - **TTS Provider**: Any provider

### Test Procedure
1. Click "Talk to Assistant" button
2. Wait for connection to establish
3. Observe greeting content

### Expected Results ✅

**Browser Console Logs:**
```
[RTC] ✅ WebRTC connection established
[RTC] 📡 Data channel opened
[RTC] 💬 Text response: Good morning! I'm here to assist you with...
[RTC] 🔊 Audio chunk received (XXXX bytes)
...
```

**Audio Playback:**
- ✅ AI-generated greeting plays
- ✅ Greeting is contextually relevant to system prompt
- ✅ Different each time (not predefined)

**Backend Logs:**
```
🤖 Generating first message with LLM...
👋 Generated greeting: 'Good morning! I'm here to assist you with...'
⚡ First audio chunk latency: 0.8XXs
✅ First message streaming complete | Chunks: XX | First chunk: 0.8XXs | Total: 3.XXXs
```

### Success Criteria
- [ ] Greeting is AI-generated (not predefined)
- [ ] Greeting is relevant and coherent
- [ ] First chunk latency < 1000ms
- [ ] Smooth audio playback
- [ ] Different greeting each connection

---

## Test 4: Error Handling - Empty First Message

### Setup
1. Navigate to Voice Agent configuration
2. Set the following:
   - **First Message Mode**: "Assistant speaks first"
   - **First Message**: "" (completely empty)

### Test Procedure
1. Click "Talk to Assistant" button
2. Attempt to establish connection

### Expected Results ✅

**Browser Console Logs:**
```
[RTC] ✅ WebRTC connection established
[RTC] 📡 Data channel opened
[RTC] ❌ Server error: first_message_mode is 'assistant_speaks_first' but first_message is empty
```

**User Visible Error:**
- ✅ Error message appears in UI
- ✅ Clear description of the problem
- ✅ Connection does NOT silently fall back

**Backend Logs:**
```
❌ CRITICAL: first_message_mode is 'assistant_speaks_first' but first_message is empty
ValueError: first_message_mode is 'assistant_speaks_first' but first_message is empty
```

### Success Criteria
- [ ] Error is visible to user (not hidden)
- [ ] Backend logs show "CRITICAL" error
- [ ] No silent fallback behavior
- [ ] Clear error message explaining the issue

---

## Test 5: Error Handling - TTS Provider Failure

### Setup
1. Temporarily break TTS provider:
   - Option A: Change TTS API key to invalid value
   - Option B: Select provider that's not configured
   - Option C: Disable network access to TTS service

2. Set first message mode to "Assistant speaks first"

### Test Procedure
1. Click "Talk to Assistant" button
2. Wait for connection to establish

### Expected Results ✅

**Browser Console Logs:**
```
[RTC] ✅ WebRTC connection established
[RTC] 📡 Data channel opened
[RTC] ❌ Server error: First message TTS failed: [provider error details]
```

**User Visible Error:**
- ✅ Error message appears in UI
- ✅ Details about TTS failure
- ✅ No silent fallback

**Backend Logs:**
```
❌ CRITICAL: First message TTS failed: [detailed error]
[Full stack trace]
```

### Success Criteria
- [ ] TTS errors are visible to user
- [ ] Backend logs include full stack trace
- [ ] No silent fallback behavior
- [ ] User can see what went wrong

---

## Test 6: Latency Comparison (WebRTC vs WebSocket)

### Purpose
Verify that WebRTC first message is faster than WebSocket equivalent.

### Test Procedure
1. **WebRTC Test**:
   - Set up assistant with first message
   - Click "Talk to Assistant" (WebRTC mode)
   - Note backend log: `⚡ First audio chunk latency: X.XXXs`

2. **WebSocket Test** (for comparison):
   - Use same assistant
   - Test via WebSocket mode
   - Note latency from logs

### Expected Results ✅

**Typical Latencies:**
- WebRTC first chunk: **200-400ms**
- WebSocket first chunk: **300-500ms**

**Backend Logs:**
```
# WebRTC
⚡ First audio chunk latency: 0.287s
✅ First message streaming complete | Chunks: 12 | First chunk: 0.287s | Total: 2.145s

# WebSocket (for comparison)
✅ First message TTS completed: 2.345s
```

### Success Criteria
- [ ] WebRTC latency is competitive
- [ ] First chunk arrives in < 500ms
- [ ] Real-time streaming confirmed
- [ ] Latency is logged for monitoring

---

## Test 7: Multiple TTS Providers

### Purpose
Verify first message works with different TTS providers.

### Test Procedure
Test each TTS provider:
1. **ElevenLabs**
   - Set TTS Provider: elevenlabs
   - Set voice to any ElevenLabs voice
   - Test first message

2. **OpenAI TTS**
   - Set TTS Provider: openai
   - Set voice to "alloy" or "nova"
   - Test first message

3. **MeloTTS**
   - Set TTS Provider: melotts
   - Set voice to any MeloTTS voice
   - Test first message

4. **Coqui XTTS**
   - Set TTS Provider: coqui
   - Set voice to any cloned voice
   - Test first message

### Expected Results ✅

**All Providers:**
- ✅ First message streams successfully
- ✅ Audio quality matches provider expectations
- ✅ Latency logged for each provider
- ✅ No provider-specific errors

**Provider-Specific Notes:**
- ElevenLabs: Typically fastest (200-300ms)
- OpenAI: Fast and reliable (250-400ms)
- MeloTTS: Good quality (300-500ms)
- Coqui: Slower but high quality (500-800ms)

### Success Criteria
- [ ] All configured providers work
- [ ] Latency within expected range
- [ ] No provider breaks the flow
- [ ] Audio quality is acceptable

---

## Automated Test Script

### Backend Log Monitoring

Create a terminal session to monitor first message streaming:

```bash
#!/bin/bash
# Watch WebRTC first message streaming in real-time

echo "🔍 Monitoring WebRTC first message streaming..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sudo journalctl -u kasaai-core-backend -f | grep --line-buffered -E "(🎬|⚡|🔊|✅.*streaming|❌.*CRITICAL)"
```

Save as `/tmp/watch_webrtc_first_message.sh` and run:
```bash
chmod +x /tmp/watch_webrtc_first_message.sh
/tmp/watch_webrtc_first_message.sh
```

---

## Common Issues & Solutions

### Issue 1: No Audio Plays
**Symptoms:**
- Connection establishes
- No audio playback
- No console errors

**Debug:**
1. Check browser console for data channel messages
2. Verify TTS provider is configured correctly
3. Check backend logs for TTS errors
4. Verify first_message field is not empty

**Solution:**
- Ensure TTS provider has valid API key
- Check TTS provider health endpoint
- Verify assistant has first_message configured

---

### Issue 2: High Latency
**Symptoms:**
- First chunk takes > 1 second
- Slow audio playback start

**Debug:**
1. Check backend logs for latency measurements
2. Verify TTS provider performance
3. Check network latency to TTS service

**Solution:**
- Try different TTS provider
- Check TTS service health
- Verify network connectivity

---

### Issue 3: Data Channel Not Opening
**Symptoms:**
- WebRTC connects
- No data channel messages
- Error: "Data channel not available"

**Debug:**
1. Check browser console for WebRTC errors
2. Verify FastRTC version
3. Check backend logs for startup_fn errors

**Solution:**
- Ensure FastRTC is installed: `pip list | grep fastrtc`
- Restart backend: `sudo systemctl restart kasaai-core-backend`
- Check firewall rules for WebRTC ports

---

## Performance Benchmarks

### Expected Latencies (Predefined First Message)

| TTS Provider | First Chunk | Total Duration | Quality |
|--------------|------------|----------------|---------|
| ElevenLabs   | 200-300ms  | 1.5-2.5s      | Excellent |
| OpenAI TTS   | 250-400ms  | 2.0-3.0s      | Excellent |
| MeloTTS      | 300-500ms  | 2.5-4.0s      | Good |
| Coqui XTTS   | 500-800ms  | 3.0-5.0s      | Excellent |

### Expected Latencies (Model-Generated First Message)

Add ~300-500ms for LLM generation time.

| LLM + TTS    | First Chunk | Total Duration |
|--------------|------------|----------------|
| GPT-4 + ElevenLabs | 600-800ms | 2.5-3.5s |
| Claude + OpenAI    | 700-900ms | 3.0-4.0s |

---

## Test Report Template

Copy this template to document your testing:

```markdown
# WebRTC First Message Test Report

**Date**: YYYY-MM-DD
**Tester**: Your Name
**Backend Version**: Git commit hash
**Frontend Version**: Build timestamp

## Test Results

### Test 1: Assistant Speaks First (Predefined)
- [ ] PASS / [ ] FAIL
- First chunk latency: ___ms
- Total duration: ___s
- Notes: ___

### Test 2: Assistant Waits for User
- [ ] PASS / [ ] FAIL
- Notes: ___

### Test 3: Model-Generated Message
- [ ] PASS / [ ] FAIL
- First chunk latency: ___ms
- Notes: ___

### Test 4: Empty First Message Error
- [ ] PASS / [ ] FAIL
- Error visible to user: [ ] YES / [ ] NO
- Notes: ___

### Test 5: TTS Failure Error
- [ ] PASS / [ ] FAIL
- Error visible to user: [ ] YES / [ ] NO
- Notes: ___

### Test 6: Latency Benchmark
- WebRTC first chunk: ___ms
- WebSocket comparison: ___ms
- Notes: ___

### Test 7: TTS Provider Compatibility
- ElevenLabs: [ ] PASS / [ ] FAIL (___ms)
- OpenAI: [ ] PASS / [ ] FAIL (___ms)
- MeloTTS: [ ] PASS / [ ] FAIL (___ms)
- Coqui: [ ] PASS / [ ] FAIL (___ms)

## Issues Found
1. ___
2. ___

## Overall Status
- [ ] ALL TESTS PASSED
- [ ] SOME TESTS FAILED (details above)

## Recommendations
___
```

---

**Ready to Test!** 🚀

Follow the tests in order, document results, and verify that the proper implementation is working as expected.
