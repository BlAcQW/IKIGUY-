# Hands-Free Mode Debugging Guide

## Overview
This guide helps debug the hands-free voice conversation mode where the assistant automatically resumes listening after speaking.

## How It Should Work

### User Flow
1. User clicks "Talk to Agent" → Opens conversation modal
2. User clicks mic button ONCE → Starts first recording
3. User speaks → "Hello, I need help"
4. Backend transcribes → Sends to LLM → Generates response
5. Backend speaks response → Plays audio to user
6. **Backend AUTO-TRIGGERS next recording** → User can speak again immediately
7. Repeat steps 3-6 until user clicks "Hang up"

### Technical Flow

#### Backend State Machine Flow
```
IDLE (initial)
  ↓ [user clicks mic]
LISTENING (recording user speech)
  ↓ [user stops speaking]
PROCESSING (transcribing + generating response)
  ↓ [LLM response ready]
SPEAKING (playing TTS audio)
  ↓ [audio complete]
IDLE (state_machine.stop_speaking() called)
  ↓ [hands-free check]
  ✅ should_auto_resume_listening() returns True
  ↓ [after pause]
LISTENING (auto-triggered - hands-free!)
```

#### Hands-Free Trigger Conditions
For `should_auto_resume_listening()` to return `True`:
1. ✅ `hands_free_mode = True` (enabled by default)
2. ✅ `conversation_state = IDLE` (set by stop_speaking())
3. ✅ `user_spoke_during_assistant = False` (reset by start_speaking())

#### Backend WebSocket Messages Sent
```json
// After audio playback completes:
{"type": "assistant_speaking_end", "data": "Assistant finished speaking"}

// Wait 1.0-1.2 seconds natural pause
{"type": "ready_to_listen", "data": "Your turn - I'm listening"}

// Wait 0.3-0.4 seconds prep pause
{"type": "start_recording", "data": "Listening... (speak naturally)"}
```

#### Frontend Handling
```typescript
case 'start_recording':
  // Auto-start recording if not already recording and not speaking
  if (!isRecordingRef.current && !isSpeakingRef.current) {
    setTimeout(() => startRecordingInternal(), 100);
  }
```

## Debug Logging Added

### Backend Logs to Watch For

#### 1. State Machine Logs
```bash
# When assistant starts speaking
🔊 start_speaking() called - setting user_spoke_during_assistant=False
🔄 Conversation state: idle → speaking

# When assistant finishes speaking
🔊 Assistant spoke for X.XXs
✅ stop_speaking() called - changing to IDLE. Current user_spoke_during_assistant=False
🔄 Conversation state: speaking → idle
```

#### 2. Hands-Free Mode Logs
```bash
# Checking if hands-free should trigger
🔍 Checking hands-free mode - state_machine: True, should_auto_resume: True
🔍 should_auto_resume_listening check: hands_free=True, state=idle, user_spoke_during=False → result=True

# If hands-free is enabled
🎤 ✅ Hands-free mode ENABLED: Auto-resuming listening after assistant spoke
⏱️  Pausing 1.0s before resuming listening...
📤 Sending 'ready_to_listen' message to frontend
⏱️  Pausing 0.3s for user preparation...
🎤 Calling state_machine.start_listening()...
📤 Sending 'start_recording' message to frontend to trigger auto-recording
✅ Hands-free mode: Messages sent, frontend should now auto-start recording

# If hands-free is disabled/skipped
⏭️  Hands-free mode skipped - Reason: state_machine=True, should_auto_resume=False
🔍 should_auto_resume_listening check: hands_free=True, state=idle, user_spoke_during=True → result=False
```

#### 3. Frontend Console Logs
```bash
[WS] 🔊 Assistant started speaking
[WS] ✅ Assistant finished speaking
[WS] 👂 Assistant ready to listen: Your turn - speak now
[WS] 🎤 Server requested start recording (hands-free): Listening... (speak naturally)
[WS] ✅ Auto-starting recording in hands-free mode
[WS] 🎤 Starting audio recording with PCM/WAV conversion...
```

## Testing Instructions

### 1. Prepare Terminal Windows
```bash
# Terminal 1: Watch backend logs
sudo journalctl -u kasaai-core-backend -f

# Terminal 2: Quick status check
sudo systemctl status kasaai-core-backend
```

### 2. Open Browser Console
- Open https://kasaai.ailabsafrica.com
- Press F12 → Console tab
- Filter for "[WS]" to see WebSocket messages

### 3. Test Scenario
1. Navigate to Voice Agent page
2. Click "Talk to Agent"
3. Click microphone button ONCE
4. Say: "Hello" (short phrase for quick test)
5. Wait for assistant response
6. **Watch logs carefully** - this is where hands-free should trigger
7. Check if recording auto-starts (mic button should show active)

### 4. What to Look For

#### ✅ Success Indicators
- Backend logs show all hands-free mode messages
- Frontend console shows `[WS] ✅ Auto-starting recording in hands-free mode`
- Microphone button automatically becomes active after assistant speaks
- No need to click mic button again

#### ❌ Failure Indicators
- Backend logs show `⏭️  Hands-free mode skipped`
- `should_auto_resume_listening` returns `False`
- Check which condition failed:
  - `hands_free=False` → hands-free mode disabled (shouldn't happen)
  - `state!=idle` → state machine not in IDLE state
  - `user_spoke_during=True` → user interrupted assistant

## Common Issues

### Issue 1: `user_spoke_during_assistant = True`
**Symptom:** Hands-free skipped with `user_spoke_during=True`

**Cause:** User clicked mic or spoke while assistant was talking

**Solution:** This is expected behavior! Only happens if user interrupts.

### Issue 2: State Machine Not Reaching IDLE
**Symptom:** Hands-free skipped with `state!=idle`

**Cause:** Something preventing `stop_speaking()` from being called

**Debug:**
```bash
# Check if start_speaking was called
grep "start_speaking() called" /var/log/...

# Check if stop_speaking was called
grep "stop_speaking() called" /var/log/...
```

### Issue 3: Messages Not Reaching Frontend
**Symptom:** Backend sends messages but frontend doesn't receive

**Cause:** WebSocket connection issue

**Debug:**
```javascript
// In browser console
console.log('WebSocket state:', wsRef.current?.readyState);
// 0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED
```

### Issue 4: Frontend Not Auto-Starting Recording
**Symptom:** Frontend receives `start_recording` but doesn't start

**Cause:** State checks preventing auto-start

**Debug:**
```bash
# Frontend should log:
[WS] 🎤 Server requested start recording (hands-free)
[WS] ✅ Auto-starting recording in hands-free mode  # ← Should see this

# If you see this instead:
[WS] ⏭️  Skipping auto-start - isRecording: true, isSpeaking: true
# Then the frontend thinks it's already recording or speaking
```

## Code Locations

### Backend Files
- State Machine: `/opt/kasaai/apps/core_backend/backend/services/conversation_state_machine.py`
  - Line 180-188: `should_auto_resume_listening()`
  - Line 131-139: `start_speaking()`
  - Line 141-154: `stop_speaking()`

- WebSocket Handler: `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/websocket_chat.py`
  - Line 708: Call `start_speaking()`
  - Line 728: Call `stop_speaking()`
  - Line 737-772: Hands-free mode logic

### Frontend Files
- WebSocket Hook: `/opt/kasaai/apps/b2c-portal/src/hooks/useWebSocketChat.ts`
  - Line 120-134: Handle `start_recording` message
  - Line 297-395: `startRecordingInternal()` function

## Next Steps

1. **Run the test** following the instructions above
2. **Collect logs** from both backend and frontend
3. **Share logs** showing the exact moment after assistant finishes speaking
4. **Identify** which condition is failing in `should_auto_resume_listening()`

## Expected Log Sequence (Success)

```bash
# Backend
[timestamp] 🔊 start_speaking() called - setting user_spoke_during_assistant=False
[timestamp] 🔄 Conversation state: idle → speaking
[timestamp] 🔊 Assistant spoke for 3.45s
[timestamp] ✅ stop_speaking() called - changing to IDLE. Current user_spoke_during_assistant=False
[timestamp] 🔄 Conversation state: speaking → idle
[timestamp] 🔍 should_auto_resume_listening check: hands_free=True, state=idle, user_spoke_during=False → result=True
[timestamp] 🎤 ✅ Hands-free mode ENABLED: Auto-resuming listening after assistant spoke
[timestamp] ⏱️  Pausing 1.0s before resuming listening...
[timestamp] 📤 Sending 'ready_to_listen' message to frontend
[timestamp] ⏱️  Pausing 0.3s for user preparation...
[timestamp] 🎤 Calling state_machine.start_listening()...
[timestamp] 🔄 Conversation state: idle → listening
[timestamp] 📤 Sending 'start_recording' message to frontend to trigger auto-recording
[timestamp] ✅ Hands-free mode: Messages sent, frontend should now auto-start recording

# Frontend
[timestamp] [WS] 🔊 Assistant started speaking
[timestamp] [WS] ✅ Assistant finished speaking
[timestamp] [WS] 👂 Assistant ready to listen: Your turn - speak now
[timestamp] [WS] 🎤 Server requested start recording (hands-free): Listening... (speak naturally)
[timestamp] [WS] ✅ Auto-starting recording in hands-free mode
[timestamp] [WS] 🎤 Starting audio recording with PCM/WAV conversion...
[timestamp] [WS] 🔒 Requesting microphone access...
[timestamp] [WS] ✅ Microphone access granted
```

## Contact
If you see this exact log sequence ↑ but it still doesn't work, there's a different issue. Share the logs and we'll investigate further.
