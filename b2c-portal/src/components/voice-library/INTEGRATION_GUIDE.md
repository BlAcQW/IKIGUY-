# Voice Library Components - Integration Guide

## Overview

This guide explains how to integrate the centralized voice library components into KasaAI applications (InkWave, ChurchFlow, StudyFlow, EventFlow).

The voice library provides:
- **VoicePicker**: Dropdown selector for choosing a voice
- **VoiceCard**: Card display for a single voice with preview
- **VoiceFilters**: Filter controls for browsing voices
- **VoiceGallery**: Complete voice browsing interface
- **useVoiceLibrary**: React hook for voice library API

## Quick Start

### 1. Copy Required Files

Copy these files from `b2c-portal` to your app:

```bash
# From /opt/kasaai/apps/b2c-portal/src/

# Components (copy to your app's components directory)
cp -r components/voice-library/ /path/to/your-app/src/components/

# Hook (copy to your app's hooks directory)
cp hooks/useVoiceLibrary.ts /path/to/your-app/src/hooks/

# Auth utils (if not already present)
cp lib/auth-utils.ts /path/to/your-app/src/lib/
```

### 2. Install Dependencies

Ensure your app has these dependencies:

```json
{
  "dependencies": {
    "react": "^18.x",
    "lucide-react": "latest",
    "@radix-ui/react-select": "latest",
    "@radix-ui/react-checkbox": "latest"
  }
}
```

### 3. Update API Configuration

Update your app's API configuration to point to the voice library endpoint:

```typescript
// src/config/api-config.ts or similar
export const API_ENDPOINTS = {
  // ... other endpoints
  voiceLibrary: `${API_BASE_URL}/api/voice-library`,
};
```

## Component Usage

### VoicePicker

Simple voice selection dropdown:

```tsx
import { VoicePicker } from '@/components/voice-library';
import { useState } from 'react';

function MyComponent() {
  const [selectedVoiceId, setSelectedVoiceId] = useState<string>();

  return (
    <VoicePicker
      value={selectedVoiceId}
      onChange={(voiceId, voice) => {
        setSelectedVoiceId(voiceId);
        console.log('Selected voice:', voice);
      }}
      filters={{ language: 'en', gender: 'female' }}
      showPreview={true}
    />
  );
}
```

**Props:**
- `value?: string` - Selected voice ID
- `onChange?: (voiceId: string, voice?: Voice) => void` - Selection handler
- `filters?: VoiceFiltersData` - Pre-applied filters
- `placeholder?: string` - Placeholder text
- `showPreview?: boolean` - Show preview button (default: true)

### VoiceCard

Display a voice in a card format:

```tsx
import { VoiceCard } from '@/components/voice-library';

function MyComponent({ voice }) {
  return (
    <VoiceCard
      voice={voice}
      onSelect={(voice) => console.log('Selected:', voice)}
      onFavorite={(voiceId, isFavorite) => {
        // Handle favorite toggle
      }}
      isFavorite={false}
      isSelected={false}
      showActions={true}
      showStats={true}
    />
  );
}
```

**Props:**
- `voice: Voice` - Voice data object
- `onSelect?: (voice: Voice) => void` - Click handler
- `onFavorite?: (voiceId: string, isFavorite: boolean) => void` - Favorite toggle
- `isFavorite?: boolean` - Is voice favorited
- `isSelected?: boolean` - Is voice selected
- `showActions?: boolean` - Show action buttons
- `showStats?: boolean` - Show statistics
- `compact?: boolean` - Compact display mode

### VoiceFilters

Filter controls for voice browsing:

```tsx
import { VoiceFilters } from '@/components/voice-library';
import { useState } from 'react';

function MyComponent() {
  const [filters, setFilters] = useState({});

  return (
    <VoiceFilters
      filters={filters}
      onChange={(newFilters) => setFilters(newFilters)}
      showSearch={true}
      showAdvanced={false}
      compact={false}
    />
  );
}
```

**Props:**
- `filters: VoiceFiltersData` - Current filters
- `onChange: (filters: VoiceFiltersData) => void` - Filter change handler
- `showSearch?: boolean` - Show search input
- `showAdvanced?: boolean` - Show advanced filters
- `compact?: boolean` - Compact display mode

### VoiceGallery

Complete voice browsing interface:

```tsx
import { VoiceGallery } from '@/components/voice-library';

function VoiceBrowsePage() {
  return (
    <VoiceGallery
      onVoiceSelect={(voice) => {
        console.log('Selected voice:', voice);
        // Handle selection (e.g., navigate to voice details)
      }}
      selectedVoiceId={undefined}
      showFilters={true}
      showStats={true}
      showActions={true}
      defaultLayout="grid"
      defaultFilters={{ language: 'en' }}
      pageSize={20}
    />
  );
}
```

**Props:**
- `onVoiceSelect?: (voice: Voice) => void` - Voice selection handler
- `selectedVoiceId?: string` - Currently selected voice ID
- `showFilters?: boolean` - Show filter controls
- `showStats?: boolean` - Show voice statistics
- `showActions?: boolean` - Show action buttons
- `defaultLayout?: 'grid' | 'list'` - Initial layout
- `defaultFilters?: VoiceFiltersData` - Initial filters
- `pageSize?: number` - Items per page (default: 20)

## Hook Usage

### useVoiceLibrary

React hook for voice library API operations:

```tsx
import { useVoiceLibrary } from '@/hooks/useVoiceLibrary';

function MyComponent() {
  const {
    fetchVoices,
    getVoice,
    createVoice,
    updateVoice,
    deleteVoice,
    addToFavorites,
    removeFromFavorites,
    getFavorites,
    rateVoice,
    recordUsage,
  } = useVoiceLibrary();

  // Fetch voices with filters
  const loadVoices = async () => {
    const data = await fetchVoices(
      { language: 'en', gender: 'female' },
      0,  // skip
      20  // limit
    );
    console.log('Voices:', data.voices);
  };

  // Get single voice
  const loadVoice = async (voiceId: string) => {
    const voice = await getVoice(voiceId);
    console.log('Voice:', voice);
  };

  // Add to favorites
  const favorite = async (voiceId: string) => {
    await addToFavorites(voiceId);
  };

  // Rate voice
  const rate = async (voiceId: string) => {
    await rateVoice(voiceId, 5, 'Excellent voice!');
  };

  return <div>...</div>;
}
```

## Integration Examples

### Example 1: InkWave - Audiobook Narration

Add voice selection to audiobook creation:

```tsx
// pages/CreateAudiobook.tsx
import { VoicePicker } from '@/components/voice-library';
import { useState } from 'react';

export function CreateAudiobook() {
  const [narratorVoiceId, setNarratorVoiceId] = useState<string>();

  return (
    <div>
      <h2>Create Audiobook</h2>

      {/* Other form fields... */}

      <div className="mb-4">
        <label className="block mb-2">Narrator Voice</label>
        <VoicePicker
          value={narratorVoiceId}
          onChange={(voiceId) => setNarratorVoiceId(voiceId)}
          filters={{
            categories: ['Narration', 'Audiobook'],
            language: 'en'
          }}
          showPreview={true}
        />
      </div>

      {/* Submit button... */}
    </div>
  );
}
```

### Example 2: ChurchFlow - Announcement Voice

Select voice for church announcements:

```tsx
// components/AnnouncementSettings.tsx
import { VoiceGallery } from '@/components/voice-library';

export function AnnouncementSettings() {
  const handleVoiceSelect = (voice) => {
    // Save voice preference for announcements
    localStorage.setItem('announcement_voice_id', voice.voice_id);
  };

  return (
    <div>
      <h2>Select Announcement Voice</h2>
      <VoiceGallery
        onVoiceSelect={handleVoiceSelect}
        defaultFilters={{
          categories: ['Professional', 'Announcements'],
          tone: 'Warm'
        }}
        defaultLayout="grid"
      />
    </div>
  );
}
```

### Example 3: StudyFlow - Tutor Voice

Select personalized tutor voice:

```tsx
// pages/TutorSettings.tsx
import { VoiceCard } from '@/components/voice-library';
import { useVoiceLibrary } from '@/hooks/useVoiceLibrary';
import { useEffect, useState } from 'react';

export function TutorSettings() {
  const { fetchVoices } = useVoiceLibrary();
  const [tutorVoices, setTutorVoices] = useState([]);

  useEffect(() => {
    loadTutorVoices();
  }, []);

  const loadTutorVoices = async () => {
    const data = await fetchVoices(
      {
        categories: ['Education', 'Tutoring'],
        featured: true
      },
      0,
      10
    );
    setTutorVoices(data.voices);
  };

  return (
    <div>
      <h2>Choose Your Tutor Voice</h2>
      <div className="grid grid-cols-2 gap-4">
        {tutorVoices.map((voice) => (
          <VoiceCard
            key={voice.voice_id}
            voice={voice}
            onSelect={(v) => {
              // Save as tutor voice preference
              saveTutorVoice(v.voice_id);
            }}
            showActions={true}
            showStats={false}
          />
        ))}
      </div>
    </div>
  );
}
```

### Example 4: EventFlow - Event Greeting

Custom voice for event greetings:

```tsx
// components/EventVoiceSetup.tsx
import { VoicePicker } from '@/components/voice-library';
import { useVoiceLibrary } from '@/hooks/useVoiceLibrary';

export function EventVoiceSetup({ eventId }) {
  const { recordUsage } = useVoiceLibrary();
  const [greetingVoice, setGreetingVoice] = useState();

  const handleVoiceChange = async (voiceId, voice) => {
    setGreetingVoice(voiceId);

    // Record that this voice is being used for an event
    await recordUsage(voiceId);

    // Save to event settings
    await updateEventSettings(eventId, { greeting_voice_id: voiceId });
  };

  return (
    <div>
      <label>Event Greeting Voice</label>
      <VoicePicker
        value={greetingVoice}
        onChange={handleVoiceChange}
        filters={{
          categories: ['Conversational', 'Greetings'],
          visibility: 'public'
        }}
      />
    </div>
  );
}
```

## TypeScript Types

All components are fully typed. Import types as needed:

```typescript
import type { Voice, VoiceFiltersData } from '@/hooks/useVoiceLibrary';

// Voice object structure
interface Voice {
  voice_id: string;
  name: string;
  description?: string;
  characteristics?: {
    gender?: 'male' | 'female' | 'neutral';
    language?: string;
    accent?: string;
    dialect?: string;
    tone?: string;
    pace?: string;
  };
  metadata?: {
    featured?: boolean;
    verified?: boolean;
    tags?: string[];
    categories?: string[];
  };
  stats?: {
    views?: number;
    uses?: number;
    favorites?: number;
    rating?: {
      average?: number;
      count?: number;
    };
  };
  files?: {
    preview?: {
      url?: string;
    };
  };
}

// Filter options
interface VoiceFiltersData {
  search?: string;
  gender?: string;
  language?: string;
  accent?: string;
  categories?: string[];
  featured?: boolean;
  verified?: boolean;
  visibility?: 'public' | 'organization' | 'private';
}
```

## Styling

Components use Tailwind CSS and shadcn/ui components. Ensure your app has:

1. **Tailwind CSS** configured
2. **shadcn/ui** components installed:
   - Button
   - Card
   - Select
   - Input
   - Checkbox
   - Badge
   - Separator
   - Alert

If components are not styled correctly, copy the shadcn/ui components from b2c-portal:

```bash
cp -r /opt/kasaai/apps/b2c-portal/src/components/ui/ /path/to/your-app/src/components/
```

## Authentication

Components use `getAuthHeaders()` from `@/lib/auth-utils.ts`. Ensure this function returns proper authentication headers for your app:

```typescript
// lib/auth-utils.ts
export async function getAuthHeaders(): Promise<Record<string, string>> {
  // Get your app's authentication token
  const token = await getAccessToken();

  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
}
```

## API Configuration

Update your API base URL to point to the core backend:

```typescript
// config/api-config.ts
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://api.ailabsafrica.com';

export const API_ENDPOINTS = {
  voiceLibrary: `${API_BASE_URL}/api/voice-library`,
};
```

## Environment Variables

Add to your `.env` file:

```bash
REACT_APP_API_URL=https://api.ailabsafrica.com
```

## Testing

Test the integration:

```tsx
// Test page
import { VoiceGallery } from '@/components/voice-library';

export function TestVoiceLibrary() {
  return (
    <div className="p-8">
      <h1 className="text-2xl mb-4">Voice Library Test</h1>
      <VoiceGallery onVoiceSelect={(v) => console.log('Selected:', v)} />
    </div>
  );
}
```

## Troubleshooting

### Issue: Components not rendering

**Solution**: Check if all shadcn/ui dependencies are installed:
```bash
npm install @radix-ui/react-select @radix-ui/react-checkbox lucide-react
```

### Issue: API calls failing

**Solution**: Verify API_BASE_URL is correct and authentication headers are being sent:
```typescript
console.log('API URL:', API_BASE_URL);
console.log('Auth headers:', await getAuthHeaders());
```

### Issue: Voices not loading

**Solution**: Check browser console for errors. Verify MongoDB voice_library collection has data:
```bash
mongosh
use kasaai_core
db.voice_library.countDocuments()
```

### Issue: TypeScript errors

**Solution**: Ensure types are properly imported:
```typescript
import type { Voice } from '@/hooks/useVoiceLibrary';
```

## Best Practices

1. **Reuse Components**: Use VoicePicker for simple selections, VoiceGallery for browsing
2. **Filter Appropriately**: Pre-filter voices based on use case (e.g., narration vs conversation)
3. **Record Usage**: Call `recordUsage()` when a voice is actually used in your app
4. **Cache Favorites**: Load favorites once and cache for better performance
5. **Error Handling**: Always wrap API calls in try-catch blocks
6. **Loading States**: Show loading indicators while fetching voices
7. **Preview Audio**: Always enable preview buttons for better UX

## Migration from Legacy Voice Systems

If your app currently has its own voice selection system:

1. **Identify Current Voice Selection UI**: Find where users select voices
2. **Replace with VoicePicker**: Swap old component with VoicePicker
3. **Update API Calls**: Replace old voice API calls with useVoiceLibrary hook
4. **Migrate Voice IDs**: Map old voice IDs to new centralized voice_library IDs
5. **Test Thoroughly**: Ensure all voice selection flows still work

## Support

For issues or questions:
- Check logs: `sudo journalctl -u kasaai-core-backend -f | grep voice.library`
- Test API directly: `curl https://api.ailabsafrica.com/api/voice-library/`
- Review voice library service: `@shared/services/voice_library_service.py`

## Related Documentation

- [Voice Library Architecture](../../../../shared/services/VOICE_ARCHITECTURE.md)
- [Voice Library Hetzner Backup](../../../../shared/services/VOICE_LIBRARY_HETZNER_BACKUP.md)
- [useVoiceLibrary Hook](../../hooks/useVoiceLibrary.ts)
- [Voice Library API Routes](../../../../core_backend/backend/routes/voice_library.py)

## Changelog

### Version 1.0.0 (2025-11-08)
- Initial release
- VoicePicker component
- VoiceCard component
- VoiceFilters component
- VoiceGallery component
- useVoiceLibrary hook
- Complete integration guide
