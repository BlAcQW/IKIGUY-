# @kasaai/ui-hooks

Shared React hooks for the KasaAI platform. Provides reusable logic for AI provider management, organization switching, authentication, and more.

## Installation

```bash
# From your app directory
npm install ../../shared/ui-hooks
# or
yarn add ../../shared/ui-hooks
```

## Hooks

### `useOrganizationSwitcher`

**NEW in v1.1.0!** - Hook for managing organization switching across all KasaAI apps.

**Features**:
- ✅ Organization state management
- ✅ Universal admin support (access all organizations)
- ✅ Automatic context switching
- ✅ LocalStorage persistence
- ✅ Auto-refresh capability
- ✅ Role-based access control
- ✅ Error handling
- ✅ TypeScript support

**Basic Usage:**
```tsx
import { useOrganizationSwitcher } from '@kasaai/ui-hooks';

function OrganizationSelector() {
  const {
    currentOrg,
    organizations,
    allOrganizations,
    isUniversalAdmin,
    switchOrg,
    isLoading
  } = useOrganizationSwitcher({
    apiUrl: 'https://api.ailabsafrica.com',
    onSwitch: (org) => console.log('Switched to:', org.display_name)
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h2>Current: {currentOrg?.display_name}</h2>

      <select value={currentOrg?.id || ''} onChange={(e) => switchOrg(e.target.value)}>
        {organizations.map(({ organization }) => (
          <option key={organization.id} value={organization.id}>
            {organization.display_name}
          </option>
        ))}
      </select>

      {isUniversalAdmin && (
        <div>
          <h3>All Organizations (Universal Admin):</h3>
          {allOrganizations.map(org => (
            <button key={org.id} onClick={() => switchOrg(org.id)}>
              {org.display_name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
```

**Advanced Usage with Auto-Refresh:**
```tsx
const { currentOrg, switchOrg } = useOrganizationSwitcher({
  apiUrl: 'https://api.ailabsafrica.com',
  enableAllOrganizations: true,
  refreshInterval: 60000, // Refresh every 60 seconds
  onSwitch: (org) => {
    // Update global state, invalidate queries, etc.
    console.log('Organization switched to:', org.display_name);
  }
});
```

**Options:**
- `apiUrl`: Base API URL (default: https://api.ailabsafrica.com)
- `onSwitch`: Callback when organization is switched
- `enableAllOrganizations`: Enable fetching all organizations for universal admins (default: true)
- `refreshInterval`: Auto-refresh interval in milliseconds (default: null)
- `getAccessToken`: Custom function to get access token
- `isUniversalAdmin`: Override universal admin check

**Returns:**
- `currentOrg`: Current active organization
- `organizations`: User's organization memberships
- `allOrganizations`: All organizations (universal admin only)
- `isLoading`: Loading state for user's organizations
- `isLoadingAll`: Loading state for all organizations
- `isUniversalAdmin`: Whether current user is universal admin
- `currentRole`: Current user's role in active organization
- `switchOrg`: Function to switch organizations
- `refreshOrganizations`: Function to refresh user's organizations
- `refreshAllOrganizations`: Function to refresh all organizations
- `error`: Error state

---

### `useAIProvider`

Generic hook for managing AI providers (TTS, LLM, ASR, Vision, Embedding, Multimodal).

**Features**:
- ✅ Provider state management
- ✅ Auto-refresh with configurable interval
- ✅ Provider selection
- ✅ Filter by status (online, offline, degraded)
- ✅ Filter by capability (voiceCloning, streaming, etc.)
- ✅ Error handling
- ✅ Loading states
- ✅ TypeScript support

#### Basic Usage

```tsx
import { useAIProvider } from '@kasaai/ui-hooks';

function TTSLab() {
  const {
    providers,
    selectedProvider,
    setSelectedProvider,
    loading,
    error,
    refetch
  } = useAIProvider('tts');

  if (loading) return <div>Loading providers...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h1>TTS Lab</h1>

      {/* Provider Selection */}
      <select
        value={selectedProvider?.id || ''}
        onChange={(e) => {
          const provider = providers[e.target.value];
          setSelectedProvider(provider);
        }}
      >
        <option value="">Select a provider</option>
        {Object.values(providers).map((provider) => (
          <option key={provider.id} value={provider.id}>
            {provider.icon} {provider.name} ({provider.status})
          </option>
        ))}
      </select>

      <button onClick={refetch}>Refresh</button>

      {/* Selected Provider Info */}
      {selectedProvider && (
        <div>
          <h2>{selectedProvider.name}</h2>
          <p>{selectedProvider.description}</p>
          <p>Status: {selectedProvider.status}</p>
          <p>Response Time: {selectedProvider.responseTime}ms</p>
        </div>
      )}
    </div>
  );
}
```

#### With Options

```tsx
import { useAIProvider } from '@kasaai/ui-hooks';

function LLMLab() {
  const {
    providers,
    selectedProvider,
    setSelectedProvider,
    loading,
    error,
    getOnlineProviders
  } = useAIProvider('llm', {
    apiUrl: 'https://api.ailabsafrica.com',
    refreshInterval: 60000, // 1 minute
    autoRefresh: true,
    initialProviderId: 'llama_32_3b',
    onProviderChange: (provider) => {
      console.log('Selected provider changed:', provider?.name);
    },
    onProvidersLoaded: (providers) => {
      console.log(`Loaded ${Object.keys(providers).length} providers`);
    },
    onError: (error) => {
      console.error('Provider error:', error);
      // Send to error tracking service
    }
  });

  const onlineProviders = getOnlineProviders();

  return (
    <div>
      <h1>LLM Lab</h1>
      <p>Online Providers: {onlineProviders.length}</p>
      {/* ... rest of component */}
    </div>
  );
}
```

#### Filtering Providers

```tsx
import { useAIProvider } from '@kasaai/ui-hooks';

function TTSVoiceCloning() {
  const {
    providers,
    getProvidersByCapability,
    getProvidersByStatus
  } = useAIProvider('tts');

  // Get only providers with voice cloning
  const voiceCloningProviders = getProvidersByCapability('voiceCloning');

  // Get only online providers
  const onlineProviders = getProvidersByStatus('online');

  // Combine filters
  const onlineVoiceCloningProviders = voiceCloningProviders.filter(
    (p) => p.status === 'online'
  );

  return (
    <div>
      <h2>Voice Cloning Providers</h2>
      {onlineVoiceCloningProviders.map((provider) => (
        <div key={provider.id}>
          {provider.icon} {provider.name}
        </div>
      ))}
    </div>
  );
}
```

#### Manual Provider Selection

```tsx
import { useAIProvider } from '@kasaai/ui-hooks';

function ProviderSelector() {
  const {
    providers,
    selectedProvider,
    selectProviderById
  } = useAIProvider('tts');

  return (
    <div>
      <button onClick={() => selectProviderById('coqui_xtts')}>
        Use Coqui XTTS
      </button>
      <button onClick={() => selectProviderById('melotts')}>
        Use MeloTTS
      </button>

      {selectedProvider && <p>Selected: {selectedProvider.name}</p>}
    </div>
  );
}
```

#### With Health Indicators

```tsx
import { useAIProvider } from '@kasaai/ui-hooks';

function ProviderCard({ provider }) {
  const statusColors = {
    online: 'green',
    offline: 'red',
    degraded: 'orange',
    building: 'blue',
    maintenance: 'yellow'
  };

  return (
    <div className="provider-card">
      <div
        className="status-indicator"
        style={{ backgroundColor: statusColors[provider.status] }}
      />
      <h3>{provider.icon} {provider.name}</h3>
      <p>{provider.description}</p>

      {provider.responseTime && (
        <p>Response Time: {provider.responseTime.toFixed(0)}ms</p>
      )}

      {provider.lastChecked && (
        <p>Last Checked: {new Date(provider.lastChecked).toLocaleTimeString()}</p>
      )}

      <div className="capabilities">
        {provider.capabilities.voiceCloning && <span>🎙️ Voice Cloning</span>}
        {provider.capabilities.multiLanguage && <span>🌍 Multi-Language</span>}
        {provider.capabilities.streaming && <span>📡 Streaming</span>}
      </div>
    </div>
  );
}

function ProviderGrid() {
  const { providers, loading } = useAIProvider('tts');

  if (loading) return <div>Loading...</div>;

  return (
    <div className="provider-grid">
      {Object.values(providers).map((provider) => (
        <ProviderCard key={provider.id} provider={provider} />
      ))}
    </div>
  );
}
```

## API Reference

### `useAIProvider(providerType, options?)`

#### Parameters

- `providerType: ProviderType` - Type of provider: `'tts' | 'llm' | 'asr' | 'vision' | 'embedding' | 'multimodal'`
- `options?: UseAIProviderOptions` - Optional configuration

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiUrl` | `string` | `process.env.VITE_API_URL \|\| 'http://localhost:8000'` | API base URL |
| `refreshInterval` | `number` | `60000` | Auto-refresh interval in milliseconds |
| `autoRefresh` | `boolean` | `true` | Enable auto-refresh |
| `initialProviderId` | `string` | `undefined` | Initial provider ID to select |
| `onProviderChange` | `(provider) => void` | `undefined` | Callback when selection changes |
| `onProvidersLoaded` | `(providers) => void` | `undefined` | Callback when providers are fetched |
| `onError` | `(error) => void` | `undefined` | Callback on error |

#### Returns

| Property | Type | Description |
|----------|------|-------------|
| `providers` | `Record<string, AIProvider>` | Map of all providers by ID |
| `selectedProvider` | `AIProvider \| null` | Currently selected provider |
| `setSelectedProvider` | `(provider) => void` | Set the selected provider |
| `selectProviderById` | `(id) => void` | Select provider by ID |
| `loading` | `boolean` | Loading state |
| `error` | `Error \| null` | Error state |
| `refetch` | `() => Promise<void>` | Manually refresh providers |
| `getProvidersByStatus` | `(status) => AIProvider[]` | Get providers by status |
| `getProvidersByCapability` | `(capability) => AIProvider[]` | Get providers by capability |
| `getOnlineProviders` | `() => AIProvider[]` | Get online providers |

## TypeScript Types

### `AIProvider`

```typescript
interface AIProvider {
  id: string;
  name: string;
  provider_type: ProviderType;
  endpoint: string;
  status: ProviderStatus;
  capabilities: ProviderCapabilities;
  description: string;
  icon: string;
  languages: number;
  languageList: string[];
  metadata?: Record<string, any>;
  lastChecked?: string;
  responseTime?: number;
}
```

### `ProviderCapabilities`

```typescript
interface ProviderCapabilities {
  // Generic
  multiLanguage?: boolean;
  streaming?: boolean;
  realtime?: boolean;

  // TTS-specific
  voiceCloning?: boolean;
  speedControl?: boolean;
  pitchControl?: boolean;
  multiSpeaker?: boolean;
  emotionControl?: boolean;

  // LLM-specific
  functionCalling?: boolean;
  reasoning?: boolean;
  codeGeneration?: boolean;
  vision?: boolean;
  culturalContext?: boolean;

  // ASR-specific
  diarization?: boolean;
  timestamps?: boolean;
  wordLevelTimestamps?: boolean;
  punctuation?: boolean;

  // Custom
  [key: string]: boolean | undefined;
}
```

### `ProviderStatus`

```typescript
type ProviderStatus = 'online' | 'offline' | 'degraded' | 'building' | 'maintenance';
```

### `ProviderType`

```typescript
type ProviderType = 'tts' | 'llm' | 'asr' | 'vision' | 'embedding' | 'multimodal';
```

## Best Practices

### 1. Use TypeScript

```tsx
import type { AIProvider } from '@kasaai/ui-hooks';

interface Props {
  onProviderSelect: (provider: AIProvider) => void;
}
```

### 2. Handle Loading and Error States

```tsx
const { providers, loading, error } = useAIProvider('tts');

if (loading) return <LoadingSpinner />;
if (error) return <ErrorMessage error={error} />;
if (Object.keys(providers).length === 0) return <EmptyState />;
```

### 3. Use Callbacks for Side Effects

```tsx
useAIProvider('tts', {
  onProviderChange: (provider) => {
    // Track analytics
    analytics.track('provider_selected', {
      provider_id: provider?.id,
      provider_name: provider?.name
    });
  },
  onError: (error) => {
    // Send to error tracking
    sentry.captureException(error);
  }
});
```

### 4. Cleanup on Unmount

The hook automatically cleans up intervals and abort controllers. No manual cleanup needed.

### 5. Disable Auto-Refresh When Not Needed

```tsx
// Only fetch once, no auto-refresh
const { providers } = useAIProvider('tts', {
  autoRefresh: false
});
```

### 6. Use Memoization for Filters

```tsx
import { useMemo } from 'react';

const { providers } = useAIProvider('tts');

const onlineProviders = useMemo(
  () => Object.values(providers).filter(p => p.status === 'online'),
  [providers]
);
```

## Environment Variables

Set these in your `.env` file:

```env
VITE_API_URL=https://api.ailabsafrica.com
```

Or pass directly to the hook:

```tsx
useAIProvider('tts', {
  apiUrl: 'https://api.ailabsafrica.com'
});
```

## Authentication

The hook automatically reads the auth token from localStorage:

```typescript
// Token keys checked (in order):
// 1. 'supabase_token'
// 2. 'auth_token'
```

Ensure your auth system stores the token in one of these keys.

## Testing

```tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useAIProvider } from '@kasaai/ui-hooks';

test('fetches providers on mount', async () => {
  const { result } = renderHook(() => useAIProvider('tts', {
    autoRefresh: false
  }));

  expect(result.current.loading).toBe(true);

  await waitFor(() => {
    expect(result.current.loading).toBe(false);
  });

  expect(Object.keys(result.current.providers).length).toBeGreaterThan(0);
});
```

## Examples

See the `examples/` directory for complete working examples:
- `TTSLab.tsx` - TTS provider management
- `LLMLab.tsx` - LLM model management
- `ASRLab.tsx` - ASR provider management

## Contributing

When adding new hooks:
1. Create hook in `src/useYourHook.ts`
2. Export from `src/index.ts`
3. Add types to `src/types.ts`
4. Update this README
5. Add tests
6. Run `npm run build` to generate dist files

## License

MIT
