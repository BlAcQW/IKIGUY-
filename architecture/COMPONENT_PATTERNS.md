# AI Labs Component Patterns Guide

**Purpose**: This guide documents reusable patterns for building AI Lab interfaces (TTS/LLM/ASR) across all platform applications.

**Philosophy**: We share **patterns and logic**, not UI components. Each app implements its own components tailored to its audience and UX needs.

---

## Architecture Overview

### What IS Shared

✅ **Backend Services** (`@apps/shared/integration/ai_services/`)
- `AIProviderService` - Base provider management
- `ProviderRegistry` - Centralized provider configs
- `HealthMonitorService` - Automated health monitoring

✅ **React Hooks** (`@apps/shared/ui-hooks/`)
- `useAIProvider` - Provider state management
- `useProviderHealth` - Health monitoring
- (Other hooks TBD)

✅ **API Contracts** (TypeScript types)
- `AIProvider`, `ProviderCapabilities`, `ProviderStatus`
- Ensures type safety across apps

### What is NOT Shared

❌ **UI Components** - Each app implements its own
❌ **Styling** - Tailored to app's design system
❌ **Layouts** - App-specific user flows

---

## Core Patterns

### 1. Provider Sidebar Pattern

**Purpose**: Display list of available AI providers with status indicators

**API Design**:
```tsx
interface ProviderSidebarProps {
  providers: Record<string, AIProvider>;
  selectedId: string | null;
  onSelect: (providerId: string) => void;
  type: 'tts' | 'llm' | 'asr';
  isLoading?: boolean;
  onRefresh?: () => void;
}
```

**Features**:
- Provider list with icons and names
- Status badges (online/offline/building)
- Filter/search functionality
- Refresh button
- Auto-refresh indicator

**Implementation Template**:

```tsx
// @apps/[your-app]/src/components/[lab]-lab/ProviderSidebar.tsx

import React, { useState } from 'react';
import { AIProvider } from '@apps/shared/integration/ai_services';

interface ProviderSidebarProps {
  providers: Record<string, AIProvider>;
  selectedId: string | null;
  onSelect: (providerId: string) => void;
  type: 'tts' | 'llm' | 'asr';
  isLoading?: boolean;
  onRefresh?: () => void;
}

export const ProviderSidebar: React.FC<ProviderSidebarProps> = ({
  providers,
  selectedId,
  onSelect,
  type,
  isLoading,
  onRefresh,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const providerList = Object.values(providers).filter((provider) =>
    provider.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-64 bg-white border-r border-gray-200">
      {/* Header */}
      <div className="p-4 border-b">
        <h2 className="font-semibold text-lg">
          {type === 'tts' && '🎙️ TTS Providers'}
          {type === 'llm' && '💬 LLM Models'}
          {type === 'asr' && '🎤 ASR Providers'}
        </h2>

        {/* Search */}
        <input
          type="text"
          placeholder="Search..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="mt-2 w-full px-3 py-1 border rounded"
        />

        {/* Refresh Button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="mt-2 w-full px-3 py-1 bg-blue-500 text-white rounded"
          >
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </button>
        )}
      </div>

      {/* Provider List */}
      <div className="overflow-y-auto">
        {providerList.map((provider) => (
          <button
            key={provider.id}
            onClick={() => onSelect(provider.id)}
            className={`
              w-full p-3 text-left border-b hover:bg-gray-50 transition
              ${selectedId === provider.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''}
            `}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">{provider.icon}</span>
                <div>
                  <div className="font-medium">{provider.name}</div>
                  <div className="text-xs text-gray-500">
                    {provider.languages} languages
                  </div>
                </div>
              </div>

              {/* Status Badge */}
              <span
                className={`
                  px-2 py-1 text-xs rounded-full
                  ${provider.status === 'online' && 'bg-green-100 text-green-800'}
                  ${provider.status === 'offline' && 'bg-red-100 text-red-800'}
                  ${provider.status === 'building' && 'bg-yellow-100 text-yellow-800'}
                `}
              >
                {provider.status === 'online' && '🟢'}
                {provider.status === 'offline' && '🔴'}
                {provider.status === 'building' && '🟡'}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
```

---

### 2. Provider Settings Panel Pattern

**Purpose**: Display provider details, capabilities, and health information

**API Design**:
```tsx
interface ProviderSettingsPanelProps {
  provider: AIProvider;
  onHealthCheck: () => Promise<boolean>;
  children?: React.ReactNode; // For lab-specific content
}
```

**Features**:
- Provider information grid
- Capabilities display
- Health check button
- Response time metrics
- Extensible for lab-specific settings

**Implementation Template**:

```tsx
// @apps/[your-app]/src/components/[lab]-lab/ProviderSettingsPanel.tsx

import React, { useState } from 'react';
import { AIProvider } from '@apps/shared/integration/ai_services';

interface ProviderSettingsPanelProps {
  provider: AIProvider;
  onHealthCheck: () => Promise<boolean>;
  children?: React.ReactNode;
}

export const ProviderSettingsPanel: React.FC<ProviderSettingsPanelProps> = ({
  provider,
  onHealthCheck,
  children,
}) => {
  const [checking, setChecking] = useState(false);

  const handleHealthCheck = async () => {
    setChecking(true);
    const healthy = await onHealthCheck();
    alert(healthy ? '✓ Provider is healthy' : '✗ Provider is not responding');
    setChecking(false);
  };

  return (
    <div className="p-6 space-y-6">
      <h2 className="text-2xl font-bold">Provider Settings</h2>

      {/* Provider Info Card */}
      <div className="bg-white rounded-lg border p-6 space-y-4">
        <div>
          <h3 className="text-lg font-semibold">{provider.name}</h3>
          <p className="text-gray-600 mt-2">{provider.description}</p>
        </div>

        {/* Info Grid */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div>
            <p className="text-sm text-gray-500">Status</p>
            <p className="font-medium">
              {provider.status === 'online' && '🟢 Online'}
              {provider.status === 'offline' && '🔴 Offline'}
              {provider.status === 'building' && '🟡 Building'}
            </p>
          </div>

          <div>
            <p className="text-sm text-gray-500">Endpoint</p>
            <p className="font-mono text-sm truncate">{provider.endpoint}</p>
          </div>

          <div>
            <p className="text-sm text-gray-500">Languages</p>
            <p className="font-medium">{provider.languages} supported</p>
          </div>

          <div>
            <p className="text-sm text-gray-500">Response Time</p>
            <p className="font-medium">
              {provider.responseTime ? `${provider.responseTime.toFixed(0)}ms` : 'N/A'}
            </p>
          </div>
        </div>

        {/* Capabilities Grid */}
        <div className="pt-4 border-t">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Capabilities</h4>
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(provider.capabilities).map(([key, value]) => {
              if (typeof value !== 'boolean') return null;
              return (
                <div
                  key={key}
                  className={`
                    flex items-center space-x-2 px-3 py-2 rounded-lg
                    ${value ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-400'}
                  `}
                >
                  <span>{value ? '✓' : '✗'}</span>
                  <span className="text-sm capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Health Check */}
        <div className="pt-4 border-t">
          <button
            onClick={handleHealthCheck}
            disabled={checking}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {checking ? 'Checking...' : 'Run Health Check'}
          </button>
        </div>

        {/* Custom Content */}
        {children}
      </div>
    </div>
  );
};
```

---

### 3. Health Indicator Pattern

**Purpose**: Consistent status display across all labs

**API Design**:
```tsx
interface HealthIndicatorProps {
  status: 'online' | 'offline' | 'building' | 'degraded';
  lastChecked?: Date;
  responseTime?: number;
  size?: 'sm' | 'md' | 'lg';
}
```

**Implementation Template**:

```tsx
// @apps/[your-app]/src/components/shared/HealthIndicator.tsx

import React from 'react';

interface HealthIndicatorProps {
  status: 'online' | 'offline' | 'building' | 'degraded';
  lastChecked?: Date;
  responseTime?: number;
  size?: 'sm' | 'md' | 'lg';
}

export const HealthIndicator: React.FC<HealthIndicatorProps> = ({
  status,
  lastChecked,
  responseTime,
  size = 'md',
}) => {
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  const statusConfig = {
    online: { bg: 'bg-green-100', text: 'text-green-800', icon: '🟢', label: 'Online' },
    offline: { bg: 'bg-red-100', text: 'text-red-800', icon: '🔴', label: 'Offline' },
    building: { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: '🟡', label: 'Building' },
    degraded: { bg: 'bg-orange-100', text: 'text-orange-800', icon: '🟠', label: 'Degraded' },
  };

  const config = statusConfig[status];

  return (
    <div className="flex items-center space-x-2">
      <span
        className={`
          inline-flex items-center rounded-full font-medium
          ${config.bg} ${config.text} ${sizeClasses[size]}
        `}
        title={
          lastChecked
            ? `Last checked: ${lastChecked.toLocaleString()}${
                responseTime ? ` (${responseTime.toFixed(0)}ms)` : ''
              }`
            : undefined
        }
      >
        <span className="mr-1">{config.icon}</span>
        {config.label}
      </span>

      {responseTime !== undefined && size !== 'sm' && (
        <span className="text-xs text-gray-500">{responseTime.toFixed(0)}ms</span>
      )}
    </div>
  );
};
```

---

## Shared Hooks

### useAIProvider Hook

**Location**: `@apps/shared/ui-hooks/useAIProvider.ts`

**Purpose**: Manage AI provider state and API calls

**API Design**:
```tsx
interface UseAIProviderOptions {
  type: 'tts' | 'llm' | 'asr';
  endpoint: string;
  defaultProvider?: string;
  autoRefresh?: boolean;
  refreshInterval?: number; // milliseconds
}

interface UseAIProviderReturn {
  provider: AIProvider | null;
  providers: Record<string, AIProvider>;
  isLoading: boolean;
  error: string | null;
  selectProvider: (id: string) => void;
  refreshProviders: (force?: boolean) => Promise<void>;
  checkHealth: () => Promise<boolean>;
}
```

**Usage**:
```tsx
import { useAIProvider } from '@apps/shared/ui-hooks';

const TTSLab = () => {
  const {
    provider,
    providers,
    isLoading,
    selectProvider,
    refreshProviders,
    checkHealth,
  } = useAIProvider({
    type: 'tts',
    endpoint: '/api/tts/providers',
    autoRefresh: true,
    refreshInterval: 60000, // 60 seconds
  });

  // Use provider data...
};
```

---

## Lab-Specific Patterns

### TTS Lab

**Additional Components**:
- `SynthesizePanel` - Text input + synthesis controls
- `VoiceCloningPanel` - Audio upload + cloning interface
- `VoiceLibrary` - Browse/manage cloned voices

**Specialized Hooks**:
- `useTTSSynthesize` - Handle synthesis API calls
- `useVoiceCloning` - Handle voice cloning workflow

### LLM Lab

**Additional Components**:
- `ChatPanel` - Chat interface with message history
- `ModelParametersPanel` - Temperature, top_p controls

**Specialized Hooks**:
- `useLLMChat` - Handle chat API with streaming
- `useChatHistory` - Manage conversation state

### ASR Lab

**Additional Components**:
- `TranscriptionPanel` - File upload + transcription display
- `LiveTranscriptionPanel` - Microphone recording
- `TranscriptEditor` - Edit/export transcripts

**Specialized Hooks**:
- `useASRTranscribe` - Handle transcription API
- `useMicrophone` - Manage audio recording

---

## Integration Example

### Complete TTS Lab Implementation

```tsx
// @apps/[your-app]/src/pages/TTSLab.tsx

import React, { useState } from 'react';
import { useAIProvider } from '@apps/shared/ui-hooks';
import { DashboardSidebar } from '@/components/dashboard/DashboardSidebar';
import { ProviderSidebar } from '@/components/tts-lab/ProviderSidebar';
import { ProviderSettingsPanel } from '@/components/tts-lab/ProviderSettingsPanel';
import { SynthesizePanel } from '@/components/tts-lab/SynthesizePanel';

const TTSLab = () => {
  const {
    provider,
    providers,
    isLoading,
    selectProvider,
    refreshProviders,
    checkHealth,
  } = useAIProvider({
    type: 'tts',
    endpoint: '/api/tts/providers',
    autoRefresh: true,
  });

  const [activeTab, setActiveTab] = useState<'synthesize' | 'settings'>('synthesize');

  return (
    <div className="flex h-screen">
      <DashboardSidebar />

      <ProviderSidebar
        providers={providers}
        selectedId={provider?.id || null}
        onSelect={selectProvider}
        type="tts"
        isLoading={isLoading}
        onRefresh={() => refreshProviders(true)}
      />

      <div className="flex-1">
        {/* Tabs */}
        <div className="border-b">
          <button
            onClick={() => setActiveTab('synthesize')}
            className={activeTab === 'synthesize' ? 'border-b-2 border-blue-500' : ''}
          >
            Synthesize
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={activeTab === 'settings' ? 'border-b-2 border-blue-500' : ''}
          >
            Settings
          </button>
        </div>

        {/* Content */}
        {activeTab === 'synthesize' && provider && (
          <SynthesizePanel provider={provider} />
        )}

        {activeTab === 'settings' && provider && (
          <ProviderSettingsPanel provider={provider} onHealthCheck={checkHealth} />
        )}
      </div>
    </div>
  );
};

export default TTSLab;
```

---

## Voice Lab Patterns

### Overview

Voice Lab functionality includes:
- **Audio Utilities**: Shared functions for audio manipulation
- **Voice Hooks**: React hooks for transcription, synthesis, and chat
- **Assistant Management**: API client for voice assistant CRUD operations
- **WebSocket Chat**: Real-time voice conversation handling

### 1. Audio Utilities Pattern

**Purpose**: Centralized audio manipulation functions

**Location**: `@apps/b2c-portal/src/lib/audio-utils.ts` (reusable pattern)

**Core Functions**:

```typescript
import {
  blobToBase64,
  base64ToBlob,
  playAudioBase64,
  downloadAudioBlob,
  downloadAudioBase64,
  getAudioDuration,
  formatDuration,
  canRecordAudio,
  canPlayAudio
} from '@/lib/audio-utils';

// Convert audio formats
const base64 = await blobToBase64(audioBlob);
const blob = base64ToBlob(base64, 'audio/wav');

// Play audio with events
await playAudioBase64(base64, {
  onEnded: () => console.log('Finished'),
  onError: (err) => console.error('Error:', err),
  volume: 1.0
});

// Download audio
downloadAudioBlob(blob, 'recording.wav');

// Get metadata
const duration = await getAudioDuration(base64);
console.log(formatDuration(duration)); // "2:34"

// Check capabilities
if (canRecordAudio()) {
  // Enable recording
}
```

**Implementation Template**:

Create similar utilities in your app by copying the pattern from `audio-utils.ts`.

### 2. Voice Transcription Hook Pattern

**Purpose**: Reusable hook for Speech-to-Text (ASR)

**API Design**:
```typescript
interface UseVoiceTranscriptionReturn {
  transcribe: (audioBlob: Blob, options?: TranscriptionOptions) => Promise<TranscriptionResult>;
  isTranscribing: boolean;
  result: TranscriptionResult | null;
  error: Error | null;
  clearResult: () => void;
}
```

**Usage Example**:

```typescript
import { useVoiceTranscription } from '@/hooks/useVoiceTranscription';

function AudioRecorder() {
  const { transcribe, isTranscribing, result, error } = useVoiceTranscription();
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);

  const handleTranscribe = async () => {
    if (!audioBlob) return;

    try {
      const transcription = await transcribe(audioBlob, {
        language: 'tw',
        dialect: 'asante',
        model: 'akan-whisper',
        enhanceText: true
      });

      console.log('Original:', transcription.text);
      console.log('Enhanced:', transcription.enhancedText);
      console.log('Confidence:', transcription.confidence);
    } catch (err) {
      console.error('Transcription failed:', err);
    }
  };

  return (
    <div>
      {/* Audio recording UI */}
      <button onClick={handleTranscribe} disabled={isTranscribing}>
        {isTranscribing ? 'Transcribing...' : 'Transcribe'}
      </button>

      {result && (
        <div className="mt-4 p-4 bg-gray-100 rounded">
          <p className="font-semibold">Transcription:</p>
          <p>{result.text}</p>
          {result.enhancedText && (
            <>
              <p className="font-semibold mt-2">Enhanced:</p>
              <p>{result.enhancedText}</p>
            </>
          )}
          <p className="text-sm text-gray-600 mt-2">
            Confidence: {(result.confidence * 100).toFixed(1)}%
          </p>
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-100 text-red-800 rounded">
          Error: {error.message}
        </div>
      )}
    </div>
  );
}
```

### 3. Voice Synthesis Hook Pattern

**Purpose**: Reusable hook for Text-to-Speech (TTS)

**API Design**:
```typescript
interface UseVoiceSynthesisReturn {
  synthesize: (text: string, options?: SynthesisOptions) => Promise<SynthesisResult>;
  play: (audioBase64: string) => Promise<void>;
  stop: () => void;
  isSynthesizing: boolean;
  isPlaying: boolean;
  result: SynthesisResult | null;
  error: Error | null;
  clearResult: () => void;
}
```

**Usage Example**:

```typescript
import { useVoiceSynthesis } from '@/hooks/useVoiceSynthesis';

function TextToSpeech() {
  const {
    synthesize,
    play,
    stop,
    isSynthesizing,
    isPlaying,
    result,
    error
  } = useVoiceSynthesis();

  const [text, setText] = useState('');

  const handleSpeak = async () => {
    if (!text.trim()) return;

    try {
      // Synthesize
      const synthesis = await synthesize(text, {
        model: 'akan-mms',
        language: 'tw',
        speed: 1.0,
        dialect: 'asante'
      });

      // Play audio
      await play(synthesis.audioBase64);
    } catch (err) {
      console.error('Synthesis failed:', err);
    }
  };

  return (
    <div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter text to speak..."
        className="w-full p-2 border rounded"
        rows={4}
      />

      <div className="mt-4 flex gap-2">
        <button
          onClick={handleSpeak}
          disabled={isSynthesizing || isPlaying || !text.trim()}
          className="px-4 py-2 bg-blue-500 text-white rounded"
        >
          {isSynthesizing ? 'Synthesizing...' : isPlaying ? 'Playing...' : 'Speak'}
        </button>

        {isPlaying && (
          <button
            onClick={stop}
            className="px-4 py-2 bg-red-500 text-white rounded"
          >
            Stop
          </button>
        )}
      </div>

      {result && (
        <div className="mt-4 text-sm text-gray-600">
          Duration: {result.duration?.toFixed(2)}s |
          Processing: {result.processingTime?.toFixed(2)}s
        </div>
      )}

      {error && (
        <div className="mt-4 p-4 bg-red-100 text-red-800 rounded">
          Error: {error.message}
        </div>
      )}
    </div>
  );
}
```

### 4. WebSocket Voice Chat Pattern

**Purpose**: Real-time voice conversation with streaming

**API Design**:
```typescript
interface UseWebSocketChatOptions {
  assistantId: string;
  onTranscription?: (text: string, isFinal: boolean) => void;
  onTextResponse?: (text: string) => void;
  onAudioChunk?: (audioData: string) => void;
  onAudioComplete?: (metadata: any) => void;
  onError?: (error: string) => void;
  onStatusChange?: (status: string) => void;
}

interface UseWebSocketChatReturn {
  isConnected: boolean;
  isRecording: boolean;
  connect: () => void;
  disconnect: () => void;
  sendTextMessage: (text: string) => void;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  playAudio: (base64Audio: string) => Promise<void>;
  updateConfig: (config: any) => void;
}
```

**Usage Example**:

```typescript
import { useWebSocketChat } from '@/hooks/useWebSocketChat';

function VoiceChat({ assistantId }: { assistantId: string }) {
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('');
  const [status, setStatus] = useState('');

  const {
    isConnected,
    isRecording,
    connect,
    disconnect,
    sendTextMessage,
    startRecording,
    stopRecording
  } = useWebSocketChat({
    assistantId,
    onTranscription: (text, isFinal) => {
      setTranscript(text);
      if (isFinal) {
        console.log('Final transcription:', text);
      }
    },
    onTextResponse: (text) => {
      setResponse(text);
    },
    onAudioComplete: (metadata) => {
      console.log('Audio complete:', metadata);
    },
    onError: (error) => {
      console.error('Error:', error);
    },
    onStatusChange: (newStatus) => {
      setStatus(newStatus);
    }
  });

  return (
    <div className="p-4">
      {/* Status */}
      <div className="mb-4 flex items-center justify-between">
        <span className="flex items-center">
          <span
            className={`w-3 h-3 rounded-full mr-2 ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          {status || (isConnected ? 'Connected' : 'Disconnected')}
        </span>

        <button
          onClick={isConnected ? disconnect : connect}
          className="px-4 py-2 bg-gray-200 rounded"
        >
          {isConnected ? 'Disconnect' : 'Connect'}
        </button>
      </div>

      {/* Chat Messages */}
      <div className="mb-4 p-4 bg-gray-100 rounded min-h-[200px]">
        {transcript && (
          <div className="mb-2">
            <span className="font-semibold">You:</span> {transcript}
          </div>
        )}
        {response && (
          <div className="mb-2">
            <span className="font-semibold">Assistant:</span> {response}
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex gap-2">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={!isConnected}
          className={`px-6 py-3 rounded ${
            isRecording
              ? 'bg-red-500 hover:bg-red-600'
              : 'bg-blue-500 hover:bg-blue-600'
          } text-white disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isRecording ? '⏹ Stop Recording' : '🎤 Start Recording'}
        </button>

        <input
          type="text"
          placeholder="Type a message..."
          onKeyPress={(e) => {
            if (e.key === 'Enter' && e.currentTarget.value) {
              sendTextMessage(e.currentTarget.value);
              e.currentTarget.value = '';
            }
          }}
          disabled={!isConnected}
          className="flex-1 px-4 py-2 border rounded"
        />
      </div>
    </div>
  );
}
```

### 4.1. Barge-in Pattern (Interrupt Assistant Speech)

**Purpose**: Allow users to interrupt the assistant while it's speaking

**Key Features**:
- Automatic barge-in when user starts recording
- Manual stop button for explicit interruption
- Visual feedback showing speaking state
- Audio queue management
- Backend signal for barge-in coordination

**Implementation Requirements**:

1. **Hook State Management**:
```typescript
// In useWebSocketChat hook
const [isSpeaking, setIsSpeaking] = useState(false);
const currentAudioRef = useRef<HTMLAudioElement | null>(null);

// Track speaking state during playback
const playAudio = async (base64Audio: string) => {
  setIsSpeaking(true);
  const audio = new Audio(url);
  currentAudioRef.current = audio;

  return new Promise<void>((resolve) => {
    audio.onended = () => {
      currentAudioRef.current = null;
      setIsSpeaking(false);
      resolve();
    };
    audio.play();
  });
};

// Stop speaking function
const stopSpeaking = () => {
  if (currentAudioRef.current) {
    currentAudioRef.current.pause();
    currentAudioRef.current.currentTime = 0;
    currentAudioRef.current = null;
  }
  setIsSpeaking(false);
  sendMessage('barge_in', null); // Signal backend
};
```

2. **Component Integration**:
```typescript
// In VoiceConversationWS component
const {
  isRecording,
  isSpeaking,
  startRecording,
  stopRecording,
  stopSpeaking
} = useWebSocketChat({ assistantId });

// Automatic barge-in
const toggleRecording = () => {
  if (isRecording) {
    stopRecording();
  } else {
    // Stop assistant when user starts speaking
    if (isSpeaking) {
      console.log('User starting to speak - triggering barge-in');
      stopSpeaking();
      // Clear audio queue
      audioQueueRef.current = [];
      isPlayingRef.current = false;
    }
    startRecording();
  }
};

// Manual barge-in
const handleStopSpeaking = () => {
  stopSpeaking();
  audioQueueRef.current = [];
  isPlayingRef.current = false;
};
```

3. **Visual Feedback**:
```typescript
{/* Status indicator */}
{(isRecording || isSpeaking) && (
  <div className="px-4 py-3 border-t">
    <div className="flex items-center gap-3">
      <div className="text-sm font-medium">
        {isRecording && <span className="text-red-500">🎤 Recording...</span>}
        {isSpeaking && !isRecording && <span className="text-primary">🔊 Speaking...</span>}
      </div>
      <div className="flex-1 h-8 bg-muted rounded-full overflow-hidden relative">
        <div
          className={`h-full transition-all ${isRecording ? 'bg-red-500' : 'bg-primary'}`}
          style={{ width: `${isRecording ? audioEnergy : 50}%` }}
        />
        {isSpeaking && !isRecording && (
          <div className="absolute inset-0 bg-primary/50 animate-pulse" />
        )}
      </div>
    </div>
  </div>
)}

{/* Manual stop button - only visible when speaking */}
{isSpeaking && (
  <button
    onClick={handleStopSpeaking}
    className="p-4 rounded-full bg-orange-500 hover:bg-orange-600 text-white transition-colors animate-pulse"
    title="Stop Speaking (Barge-in)"
  >
    <Square className="w-6 h-6" />
  </button>
)}
```

**Backend Protocol**:
```typescript
// WebSocket message to signal barge-in
{
  type: 'barge_in',
  data: null
}
```

**Best Practices**:
1. Always clear audio queue when barge-in occurs to prevent delayed playback
2. Use distinct visual styling (orange) for stop button vs recording (red)
3. Provide both automatic and manual barge-in for different user preferences
4. Add pulsing animation to make stop button attention-grabbing
5. Properly cleanup audio references to prevent memory leaks
6. Send backend signal to coordinate barge-in across the system

### 5. Assistant API Client Pattern

**Purpose**: Centralized API client for assistant management

**API Design**:
```typescript
class AssistantApiClient {
  async fetchAssistants(options?: FetchAssistantsOptions): Promise<Assistant[]>;
  async getAssistant(id: string): Promise<Assistant>;
  async createAssistant(data: CreateAssistantData): Promise<Assistant>;
  async updateAssistant(id: string, updates: Partial<Assistant>): Promise<Assistant>;
  async deleteAssistant(id: string): Promise<void>;
  async activateAssistant(id: string): Promise<void>;
  async deactivateAssistant(id: string): Promise<void>;
  async testAssistant(id: string, testInput?: string): Promise<TestResult>;
}
```

**Usage Example**:

```typescript
import { assistantApiClient } from '@/services/assistant-api-client';

function AssistantManager() {
  const [assistants, setAssistants] = useState<Assistant[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch assistants
  useEffect(() => {
    const loadAssistants = async () => {
      setLoading(true);
      try {
        const data = await assistantApiClient.fetchAssistants({
          activeOnly: false
        });
        setAssistants(data);
      } catch (error) {
        console.error('Failed to load assistants:', error);
      } finally {
        setLoading(false);
      }
    };

    loadAssistants();
  }, []);

  // Create new assistant
  const handleCreate = async () => {
    try {
      const newAssistant = await assistantApiClient.createAssistant({
        name: 'New Assistant',
        system_prompt: 'You are a helpful assistant.',
        language: 'en',
        transcribe_model: 'akan-whisper',
        llm_model: 'gemini-2.5-flash',
        tts_model: 'akan-mms'
      });

      setAssistants([...assistants, newAssistant]);
    } catch (error) {
      console.error('Failed to create assistant:', error);
    }
  };

  // Delete assistant
  const handleDelete = async (id: string) => {
    try {
      await assistantApiClient.deleteAssistant(id);
      setAssistants(assistants.filter(a => a.id !== id));
    } catch (error) {
      console.error('Failed to delete assistant:', error);
    }
  };

  // Test assistant
  const handleTest = async (id: string) => {
    try {
      const result = await assistantApiClient.testAssistant(
        id,
        'Hello, how are you?'
      );
      console.log('Test response:', result.test_output);
      console.log('Response time:', result.response_time);
    } catch (error) {
      console.error('Test failed:', error);
    }
  };

  return (
    <div>
      <button onClick={handleCreate} className="mb-4">
        Create Assistant
      </button>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div className="grid gap-4">
          {assistants.map((assistant) => (
            <div key={assistant.id} className="p-4 border rounded">
              <h3 className="font-semibold">{assistant.name}</h3>
              <p className="text-sm text-gray-600">{assistant.system_prompt}</p>
              <div className="mt-2 flex gap-2">
                <button
                  onClick={() => handleTest(assistant.id)}
                  className="px-3 py-1 bg-blue-500 text-white rounded text-sm"
                >
                  Test
                </button>
                <button
                  onClick={() => handleDelete(assistant.id)}
                  className="px-3 py-1 bg-red-500 text-white rounded text-sm"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Best Practices

### 1. Type Safety

Always import types from shared package:
```tsx
import type { AIProvider, ProviderCapabilities, ProviderStatus } from '@apps/shared/integration/ai_services';
```

### 2. Error Handling

Wrap API calls in try-catch:
```tsx
const handleRefresh = async () => {
  try {
    await refreshProviders(true);
    toast.success('Providers refreshed');
  } catch (error) {
    toast.error('Failed to refresh providers');
    console.error(error);
  }
};
```

### 3. Loading States

Always show loading indicators:
```tsx
{isLoading && <LoadingSpinner />}
{!isLoading && providers && <ProviderList />}
```

### 4. Accessibility

Use semantic HTML and ARIA labels:
```tsx
<button
  aria-label={`Select ${provider.name}`}
  aria-pressed={selectedId === provider.id}
>
  {provider.name}
</button>
```

---

## Testing

### Component Testing

```tsx
import { render, screen, waitFor } from '@testing-library/react';
import { ProviderSidebar } from './ProviderSidebar';

test('renders provider list', async () => {
  const mockProviders = {
    'coqui': { id: 'coqui', name: 'Coqui TTS', ... },
  };

  render(
    <ProviderSidebar
      providers={mockProviders}
      selectedId={null}
      onSelect={() => {}}
      type="tts"
    />
  );

  await waitFor(() => {
    expect(screen.getByText('Coqui TTS')).toBeInTheDocument();
  });
});
```

### Hook Testing

```tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useAIProvider } from '@apps/shared/ui-hooks';

test('fetches providers on mount', async () => {
  const { result } = renderHook(() =>
    useAIProvider({ type: 'tts', endpoint: '/api/tts/providers' })
  );

  await waitFor(() => {
    expect(result.current.isLoading).toBe(false);
    expect(Object.keys(result.current.providers).length).toBeGreaterThan(0);
  });
});
```

---

## Migration Guide

### Migrating Existing Labs

1. **Install shared packages**:
   ```bash
   # In your app directory
   npm install @apps/shared/integration @apps/shared/ui-hooks
   ```

2. **Replace provider logic**:
   ```tsx
   // Before
   const [providers, setProviders] = useState({});
   useEffect(() => {
     fetch('/api/providers').then(...)
   }, []);

   // After
   const { providers, isLoading } = useAIProvider({ type: 'tts', endpoint: '/api/tts/providers' });
   ```

3. **Update component props**:
   ```tsx
   // Use shared types
   import type { AIProvider } from '@apps/shared/integration/ai_services';

   interface MyComponentProps {
     provider: AIProvider; // Instead of custom type
   }
   ```

4. **Test thoroughly**: Ensure all functionality works as expected

---

## Support & Questions

For questions or contributions to these patterns:
1. Check existing implementations in `@apps/b2c-portal/src/` for reference
2. Consult shared service documentation in `@apps/shared/integration/ai_services/`
3. Create issue or PR with improvements to patterns

---

**Last Updated**: 2025-10-24
**Version**: 1.0.0
