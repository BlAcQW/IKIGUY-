# Transcription Display Fix - Speech-to-Text Showing Immediately

## Issue
Users had to click the stop button before seeing any speech-to-text transcription. No interim text appeared while speaking.

## Root Cause
The backend was only processing **partial transcriptions** (interim results while speaking) after:
- **5 seconds** (5 audio chunks) had passed, AND
- Only on **even chunk counts** (6, 8, 10, etc.)

This meant:
- Speaking for 3-4 seconds → No transcription shown
- Speaking for 5 seconds → Still no transcription (waiting for even chunk)
- Speaking for 6 seconds → First transcription appears
- Click stop → Final transcription appears

## The Fix

### Location
`core_backend/backend/routes/voice_engine/websocket_chat.py:414-424`

### Changes Made

**Before:**
```python
# Only process partial transcriptions every 5 chunks (5 seconds) for smoother updates
if len(audio_buffer) >= 5 and len(audio_buffer) % 2 == 0:  # Every 5+ chunks, process on even counts
    transcription_result = await process_audio_buffer(websocket, audio_buffer.copy(), assistant, partial=True)
    if transcription_result and transcription_result != last_transcription[0]:
        last_transcription[0] = transcription_result
```

**After:**
```python
# Show partial transcriptions for better user feedback
# Process at 3 chunks, then every 2 chunks after (3, 5, 7, 9...)
buffer_len = len(audio_buffer)
should_process = buffer_len == 3 or (buffer_len > 3 and buffer_len % 2 == 1)

if should_process:
    logger.info(f"📝 Processing partial transcription ({buffer_len} chunks in buffer)")
    transcription_result = await process_audio_buffer(websocket, audio_buffer.copy(), assistant, partial=True)
    if transcription_result and transcription_result != last_transcription[0]:
        logger.info(f"📤 Sending partial transcription: '{transcription_result[:50]}...'")
        last_transcription[0] = transcription_result
```

### What Changed
1. **First transcription at 3 seconds** instead of 5 seconds
2. **Removed even/odd restriction** - now processes at chunks 3, 5, 7, 9, 11...
3. **Added logging** to track when transcriptions are processed and sent

## Expected Behavior Now

### Timeline
- **0-2 seconds**: User speaks, no transcription yet (collecting audio)
- **3 seconds**: First partial transcription appears 🎯
- **5 seconds**: Updated transcription with more words
- **7 seconds**: Another update if still speaking
- **Click stop**: Final complete transcription

### User Experience
✅ Transcription appears while speaking (after 3 seconds)
✅ Updates every 2 seconds while speaking continues
✅ Provides real-time feedback that speech is being recognized
✅ Final transcription still appears when stop is clicked

## Testing Instructions

### 1. Open Browser Console
```
F12 → Console tab
```

### 2. Monitor Backend Logs
In terminal:
```bash
sudo journalctl -u kasaai-core-backend -f | grep -E "(📝|📤|Processing partial|Sending partial)"
```

### 3. Test the Feature
1. Navigate to Voice Agent page
2. Click "Talk to Agent"
3. Click mic button to start recording
4. **Speak for 4-5 seconds continuously** (e.g., "Hello, how are you doing today?")
5. **Watch for transcription to appear WHILE speaking** (around 3-4 seconds in)
6. Continue speaking → transcription should update
7. Click stop → final complete transcription appears

### 4. What to Observe

**Backend Logs:**
```
📝 Processing partial transcription (3 chunks in buffer)
📤 Sending partial transcription: 'Hello how are...'
📝 Processing partial transcription (5 chunks in buffer)
📤 Sending partial transcription: 'Hello how are you doing...'
```

**Frontend Console:**
```
[WS] 🎤 Transcription: "Hello how are" (final: false)
[WS] 🎤 Transcription: "Hello how are you doing" (final: false)
[WS] 🎤 Transcription: "Hello how are you doing today" (final: true)
```

**UI:**
- Text should appear in the chat/transcription area WHILE you're still speaking
- Text should update as you continue speaking
- Final complete text appears when you click stop

## Technical Details

### Audio Chunk Processing
- Each chunk = 1 second of audio
- Frontend sends chunks every 1000ms (1 second)
- Backend accumulates chunks in audio_buffer
- Processing happens at strategic intervals

### Partial vs Final Transcriptions
- **Partial (`is_final: false`)**: Interim results while speaking, may change
- **Final (`is_final: true`)**: Complete transcription when audio ends

### Performance Optimization
- Not processing every single chunk to avoid lag
- Processing at 3, 5, 7, 9... chunks balances responsiveness with performance
- Each transcription uses a copy of the buffer to avoid race conditions

## Validation

### Success Criteria
✅ Transcription appears within 3-4 seconds of speaking
✅ Transcription updates while speaking continues
✅ No need to click stop to see initial transcription
✅ Final transcription is complete and accurate
✅ No lag or stuttering during recording

### Common Issues
❌ **Still no transcription after 4 seconds**
   - Check backend logs for processing messages
   - Verify audio chunks are being sent (check frontend logs)
   - Ensure microphone permissions granted

❌ **Transcription appears but is garbled**
   - This fix doesn't affect transcription quality
   - Check audio input quality
   - Verify correct ASR model is loaded

❌ **Transcription appears, disappears, reappears**
   - Frontend state management issue
   - Check browser console for errors
   - Verify `onTranscription` callback is updating UI correctly

## Files Modified
1. `core_backend/backend/routes/voice_engine/websocket_chat.py` (lines 414-424)

## Related Documents
- `HANDS_FREE_MODE_DEBUG_GUIDE.md` - Hands-free mode flow and debugging
- `DEEPGRAM_TRANSCRIBER_FIX.md` - Deepgram integration fixes
- `ROUTER_ASSISTANT_FIX.md` - Router assistant language detection
