# InkWave Q&A Enhancement - Reusability Assessment

**Date**: December 3, 2025
**Assessment Type**: Pre-Implementation Review
**Scope**: Voice Q&A enhancements with voiceagent capabilities

---

## Executive Summary

After comprehensive review of existing implementations, **75-80% of planned features already exist** in InkWave or @shared. This dramatically reduces implementation scope.

### What Already Exists ✅

1. **WebRTC Transport** - Fully implemented
   - Backend: `/opt/kasaai/apps/inkwave/backend/app/api/websocket/webrtc_signaling.py`
   - Frontend hook: `/opt/kasaai/apps/inkwave/frontend/src/hooks/useWebRTCVoiceChat.ts`
   - Signaling protocol: SDP offer/answer + ICE candidates

2. **Transport Toggle UI** - Fully implemented
   - Component: `VoiceBookChat.tsx` (line 70: `transportMode` state)
   - Switch between WebSocket and WebRTC in real-time
   - Shared connection state management

3. **Book Voice Settings API** - Fully implemented
   - CRUD endpoints: GET/PUT/DELETE `/books/{book_id}/voice-settings`
   - Service: `book_voice_settings_service.py`
   - Models: `book_voice_settings.py`
   - MongoDB persistence with user-book scoping

4. **WebRTC Infrastructure in @shared**
   - SignalingManager: `/opt/kasaai/apps/shared/webrtc/manager.py` (488 lines)
   - WebRTCSignalingHandler: `/opt/kasaai/apps/shared/webrtc/handler.py` (464 lines)
   - Models: `/opt/kasaai/apps/shared/webrtc/models.py` (464 lines)
   - Reusable, production-ready, fully tested

5. **LLM Provider Service in @shared**
   - Unified service: `/opt/kasaai/apps/shared/services/llm_provider_service.py`
   - Multi-provider support: Gemini, OpenAI, Anthropic, Ollama
   - Streaming chat with billing integration
   - Health monitoring and failover
   - Routes: `/opt/kasaai/apps/shared/routes/llm_routes.py`

6. **Voice Configuration Components in @shared**
   - Full component library: `/opt/kasaai/apps/shared/frontend/components/voice-settings/`
   - Components (10+): VoiceSettingsPanel, ComprehensiveTTSSelector, LLMModelSelector, etc.
   - Hooks (10+): useVoiceSettings, useTTSProvider, useLLMModel, etc.
   - All production-ready with proper error handling

7. **Audio Queue & Playback**
   - AudioQueue class in useVoiceWebRTC.ts
   - Sequential playback of streaming TTS chunks
   - Barge-in support (clear queue)

---

## What Needs to Be Created ❌

### 1. Enhanced RAG Service (Moderate Effort)
**File**: `/opt/kasaai/apps/inkwave/backend/app/services/rag_service.py`

**Changes Needed**:
```python
# Add parameters to query_book_stream()
async def query_book_stream(
    book_id: str,
    question: str,
    user_profile: Dict,
    llm_provider: str = "gemini",  # NEW: Allow provider selection
    llm_model: str = "gemini-2.5-flash",  # NEW: Allow model selection
    system_prompt: Optional[str] = None,  # NEW: Custom system prompt
) -> AsyncIterator[str]:
    # Replace hardcoded Gemini client with LLMProviderService
    from apps.shared.services.llm_provider_service import LLMProviderService

    llm_service = LLMProviderService()

    # Use specified provider instead of hardcoded Gemini
    async for chunk in llm_service.chat_stream(...):
        yield chunk
```

**Estimate**: 2-3 hours

---

### 2. Enhanced WebSocket Handler (Minor Effort)
**File**: `/opt/kasaai/apps/inkwave/backend/app/api/websocket/voice_chat.py`

**Changes Needed**:
```python
class VoiceChatSession:
    def __init__(self, ...):
        # ADD: LLM configuration fields
        self.llm_provider = "gemini"
        self.llm_model = "gemini-2.5-flash"
        self.system_prompt = None

    async def handle_init(self, data: dict):
        # ADD: Extract LLM settings from init message
        llm_settings = data.get("llm_settings", {})
        self.llm_provider = llm_settings.get("provider", "gemini")
        self.llm_model = llm_settings.get("model", "gemini-2.5-flash")
        self.system_prompt = llm_settings.get("system_prompt")

        # Load book-specific settings if not provided
        if not llm_settings:
            book_settings = await self.load_book_settings()
            self.llm_provider = book_settings.get("llm_provider", "gemini")
            # etc.

    async def handle_text_message(self, text: str):
        # PASS LLM settings to RAG service
        async for chunk in rag_service.query_book_stream(
            book_id=self.book_id,
            question=text,
            user_profile=self.user_profile,
            llm_provider=self.llm_provider,  # NEW
            llm_model=self.llm_model,  # NEW
            system_prompt=self.system_prompt,  # NEW
        ):
            yield chunk
```

**Estimate**: 1-2 hours

---

### 3. Configuration Panel UI Component (Reuse @shared)
**File**: `/opt/kasaai/apps/inkwave/frontend/src/components/VoiceConfigPanel.tsx` (NEW)

**Implementation**: Import and configure shared components
```tsx
import {
  VoiceSettingsPanel,
  LLMModelSelector,
  ComprehensiveTTSSelector,
  ASRProviderSelector
} from '@shared/components/voice-settings';

export default function VoiceConfigPanel({ bookId, onSave, onClose }) {
  const { settings, updateSettings } = useBookVoiceSettings(bookId);

  return (
    <VoiceSettingsPanel
      settings={settings}
      onUpdate={updateSettings}
      tabs={['LLM', 'Voice', 'Transcriber']}
      showAdvanced={true}
      onSave={onSave}
      onReset={() => clearBookSettings(bookId)}
    />
  );
}
```

**Estimate**: 1 hour (mostly wiring, components already exist)

---

### 4. Book Voice Settings Hook (Simple)
**File**: `/opt/kasaai/apps/inkwave/frontend/src/hooks/useBookVoiceSettings.ts` (NEW)

**Implementation**: API client wrapper
```typescript
export function useBookVoiceSettings(bookId: string) {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadSettings = async () => {
    const response = await fetch(`/api/v1/books/${bookId}/voice-settings`);
    const data = await response.json();
    setSettings(data.voice_settings);
  };

  const updateSettings = async (updates) => {
    await fetch(`/api/v1/books/${bookId}/voice-settings`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
    await loadSettings();
  };

  return { settings, loading, updateSettings, clearSettings };
}
```

**Estimate**: 30 minutes

---

### 5. Integration: Configuration Panel into VoiceBookChat (Minor)
**File**: `/opt/kasaai/apps/inkwave/frontend/src/components/VoiceBookChat.tsx`

**Changes Needed**:
```tsx
import VoiceConfigPanel from './VoiceConfigPanel';

export default function VoiceBookChat({ bookId, ... }) {
  const [showSettings, setShowSettings] = useState(false);  // EXISTS (line 71)
  const { settings } = useBookVoiceSettings(bookId);  // NEW

  // Pass LLM settings to hooks
  const wsChat = useWebSocketVoiceChat({
    bookId,
    voiceSettings,
    llmSettings: settings?.llm_settings,  // NEW
    onTranscription: ...
  });

  return (
    <>
      {/* Settings button - ADD */}
      <button onClick={() => setShowSettings(true)}>
        <Settings />
      </button>

      {/* Settings panel modal - ADD */}
      {showSettings && (
        <VoiceConfigPanel
          bookId={bookId}
          onClose={() => setShowSettings(false)}
        />
      )}

      {/* Existing chat UI */}
      ...
    </>
  );
}
```

**Estimate**: 1 hour

---

## Revised Implementation Plan

### Phase 1: Backend LLM Configuration (Day 1)
1. ✅ Enhance `rag_service.py` to accept LLM provider parameters
2. ✅ Enhance `voice_chat.py` to extract and pass LLM settings
3. ✅ Test with different providers (Gemini, GPT-4o)

**Time**: 3-4 hours

---

### Phase 2: Frontend Configuration UI (Day 2)
1. ✅ Create `useBookVoiceSettings.ts` hook
2. ✅ Create `VoiceConfigPanel.tsx` component (import @shared components)
3. ✅ Integrate into `VoiceBookChat.tsx`
4. ✅ Add Settings button to UI

**Time**: 2-3 hours

---

### Phase 3: Testing (Day 3)
1. ✅ Test configuration persistence
2. ✅ Test LLM provider switching
3. ✅ Test voice settings changes
4. ✅ Test WebSocket with config
5. ✅ Test WebRTC with config

**Time**: 2-3 hours

---

### Phase 4: Documentation & Polish (Day 4)
1. ✅ Update README
2. ✅ Add usage examples
3. ✅ Write unit tests
4. ✅ Update TASKS.md

**Time**: 2 hours

---

## Total Revised Effort Estimate

**Original Plan**: 80 hours (4 weeks)
**Revised Estimate**: 10-12 hours (1.5-2 days)

**Reduction**: 85% less work due to existing infrastructure

---

## Dependencies Already Satisfied

### Python Packages
- ✅ `fastapi` - Web framework
- ✅ `websockets` - WebSocket support
- ✅ `aiortc` - WebRTC for Python
- ✅ `pydantic` - Data validation
- ✅ `motor` - MongoDB async driver

### TypeScript Packages
- ✅ `react` - UI framework
- ✅ `framer-motion` - Animations
- ✅ `lucide-react` - Icons
- ✅ Native WebRTC APIs - Built into browsers

---

## File Inventory

### Backend Files

**Already Exist (No Changes)**:
- `/opt/kasaai/apps/shared/webrtc/handler.py` - Signaling handler
- `/opt/kasaai/apps/shared/webrtc/manager.py` - Session management
- `/opt/kasaai/apps/shared/services/llm_provider_service.py` - LLM service
- `/opt/kasaai/apps/inkwave/backend/app/api/routes/book_voice_settings.py` - Settings API
- `/opt/kasaai/apps/inkwave/backend/app/api/websocket/webrtc_signaling.py` - WebRTC endpoint

**Modify (Minor Changes)**:
- `/opt/kasaai/apps/inkwave/backend/app/services/rag_service.py` - Add LLM params
- `/opt/kasaai/apps/inkwave/backend/app/api/websocket/voice_chat.py` - Add LLM config

**Create (New Files)**:
- None needed for backend!

---

### Frontend Files

**Already Exist (No Changes)**:
- `/opt/kasaai/apps/shared/frontend/components/voice-settings/` - All config components
- `/opt/kasaai/apps/shared/frontend/hooks/` - All config hooks
- `/opt/kasaai/apps/inkwave/frontend/src/components/VoiceBookChat.tsx` - Chat component
- `/opt/kasaai/apps/inkwave/frontend/src/hooks/useWebRTCVoiceChat.ts` - WebRTC hook
- `/opt/kasaai/apps/inkwave/frontend/src/hooks/useWebSocketVoiceChat.ts` - WebSocket hook

**Modify (Minor Changes)**:
- `/opt/kasaai/apps/inkwave/frontend/src/components/VoiceBookChat.tsx` - Add settings button/panel

**Create (New Files)**:
- `/opt/kasaai/apps/inkwave/frontend/src/components/VoiceConfigPanel.tsx` - Wrapper for @shared components
- `/opt/kasaai/apps/inkwave/frontend/src/hooks/useBookVoiceSettings.ts` - API client hook

---

## Key Insights

1. **Reusability is High**: 75-80% of code already exists
2. **WebRTC Fully Implemented**: No WebRTC work needed
3. **@shared Library is Mature**: Production-ready components available
4. **Book Settings Already Done**: CRUD API and service complete
5. **Main Gap**: LLM provider configuration (not UI, just wiring)

---

## Risk Assessment

### Low Risk ✅
- Reusing @shared components (proven across multiple apps)
- WebRTC already working in InkWave
- Book settings API battle-tested

### Medium Risk ⚠️
- LLM provider switching (test with multiple providers)
- Ensuring billing works with different providers

### Mitigation
- Test with Gemini (current), GPT-4o (new), Anthropic (new)
- Verify wallet deductions accurate
- Fallback to Gemini if provider fails

---

## Conclusion

The InkWave Q&A feature is **significantly more advanced** than initially assessed. Most "planned" features already exist:

- ✅ WebRTC transport - COMPLETE
- ✅ Transport toggle - COMPLETE
- ✅ Book voice settings API - COMPLETE
- ⚠️ LLM configuration - NEEDS WIRING (not implementation)
- ⚠️ Config UI - NEEDS INTEGRATION (components exist)

**Recommendation**: Proceed with minimal scope - wire existing components together rather than building new infrastructure.

**Updated Timeline**: 1.5-2 days (vs. original 4 weeks)
