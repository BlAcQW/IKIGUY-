# @kasaai/shared-frontend

Shared frontend components, hooks, and services for KasaAI applications.

## Installation

Add to your app's `package.json`:

```json
{
  "dependencies": {
    "@kasaai/shared-frontend": "file:../../shared/frontend"
  }
}
```

Then run:
```bash
npm install
```

## Usage

### Hooks

```typescript
import {
  useTTSProvider,
  useASRProvider,
  useLLMModel,
  useVoiceSettings
} from '@kasaai/shared-frontend/hooks';

// In your component
const { selectedProvider, synthesize } = useTTSProvider();
const { settings, updateSettings } = useVoiceSettings(userId, orgId);
```

### Components

```typescript
import {
  VoiceSettingsPanel,
  TTSProviderSelector,
  ASRProviderSelector
} from '@kasaai/shared-frontend/components';

// In your component
<VoiceSettingsPanel
  userId={user.id}
  organizationId={user.organization_id}
  onSave={handleSave}
  onCancel={handleCancel}
/>
```

### Types

```typescript
import type {
  VoiceSettings,
  TTSSettings,
  ASRSettings,
  LLMSettings
} from '@kasaai/shared-frontend/types';
```

## Structure

```
shared/frontend/
├── hooks/               # React hooks for voice services
├── components/          # Reusable UI components
│   └── voice-settings/  # Voice settings components
├── services/            # API clients and services
├── types/              # TypeScript type definitions
└── __tests__/          # Test files
```

## Development

### Adding New Components

1. Create component in appropriate directory
2. Export from directory's `index.ts`
3. Add tests in `__tests__/`
4. Update this README

### Testing

```bash
npm test
```

## Components Reference

### VoiceSettingsPanel
Main component for managing all voice settings.

**Props:**
- `userId: string` - Current user ID
- `organizationId: string` - Current organization ID
- `onSave: (settings: VoiceSettings) => Promise<void>` - Save callback
- `onCancel: () => void` - Cancel callback
- `showAdvanced?: boolean` - Show advanced settings
- `readonly?: boolean` - Read-only mode

### TTSProviderSelector
Select TTS provider and voice.

**Props:**
- `selectedProviderId: string | null`
- `onProviderChange: (id: string) => void`
- `selectedVoiceId: string | null`
- `onVoiceChange: (id: string) => void`
- `speed: number`
- `onSpeedChange: (speed: number) => void`
- `pitch: number`
- `onPitchChange: (pitch: number) => void`

### ASRProviderSelector
Select ASR provider and language.

**Props:**
- `selectedProviderId: string | null`
- `onProviderChange: (id: string) => void`
- `selectedLanguage: string`
- `onLanguageChange: (language: string) => void`

### LLMModelSelector
Select LLM model and parameters.

**Props:**
- `selectedModelId: string | null`
- `onModelChange: (id: string) => void`
- `temperature: number`
- `onTemperatureChange: (temp: number) => void`
- `maxTokens: number`
- `onMaxTokensChange: (tokens: number) => void`

## Hooks Reference

### useTTSProvider
Manage TTS provider state and operations.

**Returns:**
- `selectedProvider: TTSProvider | null`
- `setSelectedProvider: (id: string) => void`
- `providers: Record<string, TTSProvider>`
- `isLoading: boolean`
- `error: string | null`
- `synthesize: (request: SynthesisRequest) => Promise<Blob | null>`
- `getLanguages: () => Promise<string[]>`
- `getSpeakers: (language?: string) => Promise<string[]>`
- `checkHealth: () => Promise<boolean>`

### useASRProvider
Manage ASR provider state and operations.

**Returns:**
- `selectedProvider: ASRProvider | null`
- `setSelectedProvider: (id: string) => void`
- `providers: Record<string, ASRProvider>`
- `isLoading: boolean`
- `error: string | null`
- `transcribe: (request: TranscriptionRequest) => Promise<TranscriptionResult | null>`
- `getLanguages: (providerId: string) => Promise<string[]>`

### useLLMModel
Manage LLM model state and operations.

**Returns:**
- `selectedModel: LLMProvider | null`
- `setSelectedModel: (id: string) => void`
- `providers: Record<string, LLMProvider>`
- `isLoading: boolean`
- `error: string | null`
- `chat: (request: ChatRequest) => Promise<ChatResponse | null>`
- `chatStream: (request: ChatRequest, onChunk: (chunk: string) => void) => Promise<void>`

### useVoiceSettings
Manage user voice preferences.

**Parameters:**
- `userId: string`
- `organizationId: string`

**Returns:**
- `settings: VoiceSettings | null`
- `isLoading: boolean`
- `error: string | null`
- `updateSettings: (partial: Partial<VoiceSettings>) => Promise<void>`
- `resetToDefaults: () => Promise<void>`
- `resetToOrgDefaults: () => Promise<void>`

## License

PRIVATE - KasaAI Internal Use Only
