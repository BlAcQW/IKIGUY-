# Voice Conversation Testing Guide

**Date:** 2025-11-06
**Backend Status:** ✅ Running with all fixes deployed
**Frontend Status:** ✅ Built and deployed with WebSocket validation fixes
**Test URL:** https://kasaai.ailabsafrica.com/voice-agent

## Critical Fixes Deployed

### 1. Hands-Free Auto-Resume Fix
- **Problem:** Agent only picked up first sentence, then stopped listening
- **Root Cause:** State machine logic error in `stop_speaking()`
- **Fix:** State properly transitions to IDLE, then WebSocket handler manages auto-resume
- **Expected:** Continuous conversation without clicking button after first sentence

### 2. Akan/Twi Conversation Smoothness
- **Problem:** Conversations felt choppy and unnatural for Akan/Twi
- **Optimizations Added:**
  - Higher silence threshold (900 vs 800)
  - Longer silence detection (1 second vs 0.5s)
  - Extended pause before auto-resume (1.6s vs 1.3s)
- **Expected:** Natural conversation flow with proper turn-taking

### 3. WebSocket Connection Validation Fix
- **Problem:** WebSocket connection failing with ReadyState 3 (CLOSED)
- **Root Cause:** Hook tried to connect without validating assistant ID was provided
- **Fix Applied:**
  - Added validation in `useWebSocketChat` hook to check assistantId before connecting
  - Enhanced `handleStartConversation` to validate assistant has valid ID before opening modal
  - Clear error messages shown to user if assistant not selected or invalid
- **Expected:** Clear error messages if assistant not properly selected, successful connection with valid assistant

### 4. Dynamic Language Switching
- **Problem:** Assistant doesn't switch TTS voice when asked to speak different language
- **Root Cause:** Language was set once from config and never changed dynamically
- **Fix Applied:**
  - Added automatic language detection on LLM responses (Twi vs English)
  - Dynamic TTS model/voice switching based on detected language
  - Enhanced system prompt with explicit language switching instructions
  - Switches between XTTS (English) and Akan MMS (Twi) automatically
- **Expected:** When user says "speak English" or "speak Twi", assistant responds AND speaks in that language

---

## Test 1: Hands-Free Conversation Flow (English)

### Setup:
1. Open https://kasaai.ailabsafrica.com/voice-agent in Chrome/Edge
2. Select an **English** assistant
3. Allow microphone permissions

### Test Steps:

#### Step 1: Initial Connection
- [ ] Click "Talk to Assistant" button **once**
- [ ] Verify: Status shows "Connecting..."
- [ ] Verify: Status changes to "Connected" or "Listening"
- [ ] Verify: Microphone indicator shows it's recording

#### Step 2: First Sentence
- [ ] Say clearly: **"Hello"**
- [ ] Expected: After ~0.5s silence, recording stops automatically
- [ ] Expected: Status shows "Processing..."
- [ ] Expected: Assistant responds with greeting
- [ ] Expected: You hear assistant voice speaking

#### Step 3: Auto-Resume (CRITICAL TEST)
- [ ] Wait for assistant to finish speaking
- [ ] Expected: **Green "Your turn - Speak now" banner appears**
- [ ] Expected: After ~1.3s total pause, recording **auto-starts**
- [ ] Expected: Microphone indicator turns red again
- [ ] Expected: No button clicking required!

#### Step 4: Second Sentence
- [ ] Say: **"How are you?"**
- [ ] Expected: After ~0.5-1s silence, recording stops automatically
- [ ] Expected: Assistant responds
- [ ] Expected: After response, auto-resumes listening again

#### Step 5: Continue Conversation
- [ ] Have 3-5 more exchanges
- [ ] Verify: Each time, recording auto-resumes after assistant speaks
- [ ] Verify: Green "Your turn" indicator shows each time
- [ ] Verify: No manual button pressing needed

### Expected Console Logs (F12 → Console):
```
[WS] 🔴 Auto-stopping recording due to silence detection
[WS] 🔊 Assistant speaking
[WS] 👂 Assistant ready to listen: Your turn - speak now
[WS] 🎤 Server requested start recording (hands-free): Listening...
[WS] ✅ Auto-starting recording in hands-free mode
```

### Success Criteria:
- ✅ Auto-resume works after **every** assistant response
- ✅ Green indicator appears before each auto-resume
- ✅ Conversation feels natural and continuous
- ✅ No need to press button after initial start

### If It Fails:
Check backend logs:
```bash
sudo journalctl -u kasaai-core-backend -n 50 --no-pager | grep -E "hands-free|auto-resuming|ready_to_listen|start_recording"
```

---

## Test 2: Twi/Akan Conversation Smoothness

### Setup:
1. Open https://kasaai.ailabsafrica.com/voice-agent
2. Select an assistant with **Twi/Akan** language
3. Verify assistant settings show language as "tw", "twi", or "akan"

### Test Steps:

#### Step 1: Initial Greeting (Twi)
- [ ] Click "Talk to Assistant" once
- [ ] Say in Twi: **"Maakye"** (Good morning)
- [ ] Expected: After ~1.0s silence (longer than English), recording stops
- [ ] Expected: Assistant responds in Twi
- [ ] Note: Silence detection should allow natural pauses

#### Step 2: Auto-Resume with Akan Timing
- [ ] Wait for assistant to finish
- [ ] Expected: **Green banner appears**
- [ ] Expected: After ~1.6s pause (longer than English), auto-starts
- [ ] Note: The longer pause feels more natural for Twi conversations

#### Step 3: Longer Twi Phrase
- [ ] Say: **"Me ho yɛ"** (I am fine) - with natural pause
- [ ] Verify: Doesn't cut off mid-phrase
- [ ] Verify: 1 second silence detection allows completion
- [ ] Expected: Full phrase captured before processing

#### Step 4: Rapid Exchanges
- [ ] Have quick back-and-forth in Twi
- [ ] Say short responses: "Aane" (Yes), "Dabi" (No), "Ɛyɛ" (Okay)
- [ ] Verify: Each short utterance is detected properly
- [ ] Verify: Auto-resume timing feels natural, not rushed

#### Step 5: Mixed Speech Patterns
- [ ] Speak with varying speeds
- [ ] Include natural pauses between words
- [ ] Verify: System doesn't cut off during pauses
- [ ] Verify: Waits for actual silence (1 second)

### Akan/Twi-Specific Timing:
| Parameter | English | Akan/Twi |
|-----------|---------|----------|
| Silence Threshold | 800 | **900** |
| Silence Duration | 0.5s | **1.0s** |
| Auto-Resume Pause | 1.3s | **1.6s** |

### Expected Backend Logs:
```
🔇 Short utterance detected, processing immediately...
🔊 Assistant spoke for X.XXs
🎤 Hands-free mode: Auto-resuming listening after assistant spoke
```

### Success Criteria:
- ✅ Conversations feel natural, not choppy
- ✅ System allows for natural pauses in Akan speech
- ✅ Doesn't cut off mid-phrase
- ✅ Auto-resume timing feels appropriate (not rushed)
- ✅ Short utterances detected properly

### If It Fails:
1. Check assistant language is set correctly (should be "tw" or "akan")
2. Check backend logs for language detection:
```bash
sudo journalctl -u kasaai-core-backend -n 100 --no-pager | grep -E "Akan\|Twi\|language"
```

---

## Test 3: Visual Ready Indicator

### Test Steps:
- [ ] Have conversation (English or Twi)
- [ ] Watch for **green pulsing banner** after assistant speaks
- [ ] Verify: Shows "Your turn - Speak now" message
- [ ] Verify: Has microphone icon
- [ ] Verify: Has animated green dot (pulsing)
- [ ] Verify: Auto-hides after ~2 seconds
- [ ] Verify: Only shows when assistant is done speaking

### Location in UI:
- Appears **above the message area**
- **Below the error banner** (if any errors)
- Full width, centered text
- Green background with border

---

## Test 4: Interruption/Barge-In

### Test Steps:
- [ ] Start conversation
- [ ] While assistant is speaking, press record button
- [ ] Expected: Assistant stops speaking immediately
- [ ] Expected: Your speech is captured
- [ ] Expected: System responds to your interruption

---

## Test 5: Dynamic Language Switching

### Setup:
1. Open https://kasaai.ailabsafrica.com/voice-agent
2. Select any assistant (English or Twi configured)
3. Start conversation

### Test Steps:

#### Step 1: Start in English
- [ ] Say: **"Hello, how are you?"**
- [ ] Expected: Assistant responds in English
- [ ] Expected: You hear English voice (XTTS or configured English TTS)
- [ ] Note: Clear English pronunciation

#### Step 2: Request Twi
- [ ] Say: **"Please speak Twi now"** or **"Kasa Twi"**
- [ ] Expected: Assistant acknowledges and responds in Twi
- [ ] Expected: Voice automatically switches to Akan MMS
- [ ] Expected: Hear Twi pronunciation with proper accent
- [ ] Check console for: `🔄 Language switch detected: en → tw`

#### Step 3: Continue in Twi
- [ ] Say in Twi: **"Ɛte sɛn?"** (How are you?)
- [ ] Expected: Assistant continues responding in Twi
- [ ] Expected: Maintains Akan MMS voice
- [ ] Verify: Conversation flows naturally in Twi

#### Step 4: Switch Back to English
- [ ] Say: **"Speak English please"**
- [ ] Expected: Assistant acknowledges and switches to English
- [ ] Expected: Voice switches back to English TTS (XTTS)
- [ ] Check console for: `🔄 Language switch detected: tw → en`

#### Step 5: Multiple Quick Switches
- [ ] Say: **"Kasa Twi"** (Speak Twi)
- [ ] Wait for Twi response
- [ ] Say: **"Now English"**
- [ ] Wait for English response
- [ ] Verify: Each switch is detected and applied correctly
- [ ] Verify: No delay or confusion in language switching

### Expected Backend Logs:
```bash
🌐 Detected response language: tw (original: en)
🔄 Language switch detected: en → tw
🔄 Switching TTS model to Akan MMS for Twi response
📢 Using TTS model: akan-mms
```

Or for reverse:
```bash
🌐 Detected response language: en (original: tw)
🔄 Language switch detected: tw → en
🔄 Switching TTS model to XTTS for English response
📢 Using TTS model: xtts
```

### Success Criteria:
- ✅ Language detection works automatically on every response
- ✅ TTS voice switches to match detected language
- ✅ English responses use English voice (XTTS or configured)
- ✅ Twi responses use Akan voice (Akan MMS)
- ✅ Switches happen seamlessly without user intervention
- ✅ No lag or delay in voice switching

### If It Fails:

1. **Check backend logs for language detection:**
```bash
sudo journalctl -u kasaai-core-backend -f | grep -E "Detected response language|Language switch|Switching TTS"
```

2. **Verify system prompt includes language instructions:**
```bash
sudo journalctl -u kasaai-core-backend -n 100 | grep "LANGUAGE SWITCHING"
```

3. **Check TTS model selection:**
```bash
sudo journalctl -u kasaai-core-backend -f | grep "Using TTS model"
```

---

## Troubleshooting Guide

### Issue: Auto-resume doesn't work after first sentence

**Check:**
1. Backend logs for state machine transitions:
```bash
sudo journalctl -u kasaai-core-backend -f | grep -E "conversation_state|should_auto_resume"
```

2. Frontend console for WebSocket messages:
- Should see: `ready_to_listen`
- Should see: `start_recording`

3. State machine is in IDLE:
```bash
sudo journalctl -u kasaai-core-backend -n 20 | grep "IDLE"
```

### Issue: Twi/Akan conversations feel choppy

**Check:**
1. Assistant language setting:
- Open browser DevTools → Application → Local Storage
- Check assistant configuration has `language: "tw"` or `language: "akan"`

2. Backend detects Akan language:
```bash
sudo journalctl -u kasaai-core-backend -f | grep "Akan"
```

3. Should see in logs:
```
Language-specific pauses (Akan/Twi needs slightly longer for natural feel)
```

### Issue: Green indicator doesn't appear

**Check:**
1. Frontend console for errors
2. Check WebSocket connection:
```javascript
// In browser console
console.log('WebSocket connected:', !!window.wsConnection)
```

3. Check if `ready_to_listen` message received:
```bash
sudo journalctl -u kasaai-core-backend -f | grep "ready_to_listen"
```

---

## Backend Health Check

Before testing, verify backend is healthy:

```bash
# Check service status
sudo systemctl status kasaai-core-backend

# Check if listening on port
sudo lsof -i :30027

# Check health endpoint
curl http://localhost:30027/health

# Watch live logs during testing
sudo journalctl -u kasaai-core-backend -f
```

---

## Testing Checklist

### English Conversation:
- [ ] First sentence detected and responded to
- [ ] Auto-resume works for 2nd, 3rd, 4th+ sentences
- [ ] Green "Your turn" indicator appears
- [ ] No button pressing after initial start
- [ ] Silence detection ~0.5-1s feels responsive
- [ ] Can interrupt assistant

### Twi/Akan Conversation:
- [ ] Longer silence detection (1s) allows natural speech
- [ ] Auto-resume pause (1.6s) feels natural
- [ ] Doesn't cut off mid-phrase
- [ ] Short utterances detected properly
- [ ] Conversation feels smooth, not choppy
- [ ] Language-specific timing applied

### UI/UX:
- [ ] Green ready indicator shows clearly
- [ ] Auto-hides after 2 seconds
- [ ] Microphone icon animates during recording
- [ ] Status messages are clear
- [ ] Error messages display properly

---

## Performance Expectations

### Response Time (English):
- Silence detection: 0.5-1.0s
- STT processing: 0.2-0.5s
- LLM generation: 0.5-1.0s
- TTS generation: 0.3-0.7s
- Auto-resume pause: 1.3s
- **Total:** ~2.5-4.5s per exchange

### Response Time (Akan/Twi):
- Silence detection: 1.0s
- STT processing: 0.3-0.7s (Akan Whisper)
- LLM generation: 0.5-1.0s
- TTS generation: 0.4-0.8s (Akan TTS)
- Auto-resume pause: 1.6s
- **Total:** ~3.8-5.1s per exchange

---

## Files Modified (Reference)

1. `core_backend/backend/services/conversation_state_machine.py` - Fixed stop_speaking()
2. `core_backend/backend/routes/voice_engine/websocket_chat.py` - Added Akan/Twi optimizations + dynamic language switching
3. `core_backend/backend/middleware/__init__.py` - Created to fix backend startup
4. `core_backend/backend/routes/feedback.py` - Fixed incorrect import paths
5. `b2c-portal/src/components/voice-agent/VoiceConversationWS.tsx` - Visual indicator
6. `b2c-portal/src/hooks/useWebSocketChat.ts` - Added assistantId validation, enhanced message handling
7. `b2c-portal/src/pages/VoiceAgent.tsx` - Enhanced assistant selection validation

---

## Success Indicators

If everything works correctly, you should experience:

1. **Continuous conversation** without manual intervention
2. **Natural timing** appropriate for the language
3. **Clear turn-taking** with visual feedback
4. **Smooth flow** without awkward pauses or cutoffs
5. **Reliable auto-resume** after every assistant response

---

## Next Steps If Issues Found

1. **Capture logs** during the problematic interaction
2. **Screenshot** of any error messages or unexpected UI
3. **Note exact steps** that reproduce the issue
4. **Browser console logs** (F12 → Console → Copy all)
5. **Backend logs** during the test session

**Report issues with this information for rapid debugging.**

---

**Last Updated:** 2025-11-06 16:50 GMT
**Backend Version:** Running on port 30027 (commit c9910763 with dynamic language switching)
**Frontend Version:** Built with WebSocket connection validation
**Status:** ✅ Ready for testing - All critical issues addressed + Language switching implemented
