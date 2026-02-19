# InkWave PWA Features Documentation

## Overview

InkWave is a fully-featured Progressive Web App (PWA) that can be installed on mobile and desktop devices for a native app-like experience. This document details all PWA capabilities and features.

## What is a PWA?

A Progressive Web App combines the best of web and mobile apps:
- **Installable**: Add to home screen like a native app
- **Offline Support**: Works without internet connection
- **Fast**: Cached assets load instantly
- **Reliable**: Always loads, even on flaky networks
- **Engaging**: Full-screen experience, push notifications

## Features

### 1. App Installation

#### Desktop (Chrome, Edge, Brave)
1. Visit https://inkwave.ailabsafrica.com
2. Look for the install icon in the address bar
3. Click "Install" in the prompt that appears
4. The app opens in its own window

#### Android (Chrome, Firefox, Samsung Internet)
1. Visit https://inkwave.ailabsafrica.com
2. Tap the three-dot menu
3. Select "Add to Home Screen" or "Install App"
4. The app icon appears on your home screen

#### iOS (Safari)
1. Visit https://inkwave.ailabsafrica.com
2. Tap the Share button (box with arrow)
3. Scroll down and tap "Add to Home Screen"
4. Tap "Add" in the top right

#### Automatic Install Prompt
- After 30 seconds of usage, a banner appears prompting installation
- The banner can be dismissed and won't show again for that session
- Stored in localStorage to prevent repeated prompts

### 2. Offline Support

#### Service Worker Caching Strategy

**Static Assets** (Cache-First):
- App shell (HTML, CSS, JavaScript)
- Icons and images
- Fonts
- Strategy: Serve from cache, update in background

**API Requests** (Network-First):
- Book metadata
- User data
- Reading progress
- Strategy: Try network first, fall back to cache if offline

**Audio Files** (Cache-First with Limits):
- Audiobook chunks
- TTS-generated audio
- Strategy: Serve from cache, automatic cleanup at 500MB
- Oldest files removed when limit exceeded

#### What Works Offline?
- ✅ Browse previously loaded books
- ✅ Play cached audiobook chapters
- ✅ View library and reading history
- ✅ Access user profile
- ❌ Search for new books (requires internet)
- ❌ Download new chapters (requires internet)
- ❌ Voice chat Q&A (requires internet)

### 3. Cache Management

#### Automatic Cache Cleanup
- Audio cache limited to 500MB
- Oldest files removed first when limit reached
- Static assets cached indefinitely (small size)

#### Manual Cache Management
Navigate to Profile → Offline Storage section:

**View Cache Status**:
- Number of cached audio files
- Total audio cache size
- Number of static assets
- Total static cache size

**Clear Cache**:
- Button to clear all cached data
- Confirmation dialog prevents accidental deletion
- Useful for troubleshooting or freeing up space

### 4. Update Notifications

#### Automatic Updates
- Service worker checks for updates every hour
- New version detected automatically
- Blue banner appears at top of screen

#### Manual Update
1. Click "Update Now" in the banner
2. App reloads with new version
3. All changes immediately available

### 5. Offline Indicator

#### Visual Feedback
- **Orange banner** when offline: "You're offline - some features may be limited"
- **Green banner** when back online: "Back online!" (disappears after 3 seconds)
- Banner appears at top of screen, doesn't block content

### 6. App Shortcuts

When installed, long-press the app icon (or right-click on desktop) to access:
- **My Library**: Jump directly to your library
- **Browse Books**: Go to the browse page

## Technical Implementation

### Manifest File
Location: `/public/manifest.webmanifest`

```json
{
  "name": "InkWave - Interactive AI Audiobooks",
  "short_name": "InkWave",
  "description": "Your AI-powered audiobook companion with voice Q&A",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#030712",
  "theme_color": "#7c3aed",
  "orientation": "portrait-primary",
  "icons": [
    { "src": "/icons/icon-72x72.png", "sizes": "72x72" },
    { "src": "/icons/icon-192x192.png", "sizes": "192x192" },
    { "src": "/icons/icon-512x512.png", "sizes": "512x512" }
  ]
}
```

### Service Worker
Location: `/public/sw.js`

**Cache Version**: 3
- Static cache: `inkwave-static-v3`
- Audio cache: `inkwave-audio-v1` (preserved across updates)
- API cache: `inkwave-v3`

**Event Handlers**:
- `install`: Pre-cache static assets
- `activate`: Clean up old caches
- `fetch`: Intercept network requests, apply caching strategy
- `message`: Handle commands from app (clear cache, check status)

### React Hook
Location: `/src/hooks/usePWA.ts`

**Exports**:
```typescript
const {
  isInstallable,      // Can app be installed?
  isInstalled,        // Is app running in standalone mode?
  isOffline,          // Is device offline?
  hasUpdate,          // Is new version available?
  cacheStatus,        // Cache size and file count
  promptInstall,      // Show install prompt
  applyUpdate,        // Reload with new version
  getCacheStatus,     // Fetch cache statistics
  clearCache,         // Delete all cached data
  isCached,           // Check if URL is cached
  cacheAudio,         // Cache audio file for offline
} = usePWA();
```

## Components

### PWAInstallPrompt
- Appears after 30 seconds on non-installed browsers
- Dismissible with "X" button
- Different UI for iOS (share button instructions)
- Automatic for Chrome/Edge (uses native beforeinstallprompt)

### PWAUpdateBanner
- Blue gradient banner at top
- "Update Now" button
- Dismissible with "X"
- Only shows when update available

### OfflineBanner
- Orange when offline
- Green when back online (auto-dismisses after 3s)
- Fixed at top, doesn't block header

### PWACacheSettings
- Integrated into Profile page settings
- Shows cache statistics (files, size)
- Refresh and Clear buttons
- Helpful tip about 500MB limit

## Browser Support

### Full Support (All Features)
- ✅ Chrome/Chromium (desktop & mobile)
- ✅ Edge (desktop & mobile)
- ✅ Brave (desktop & mobile)
- ✅ Samsung Internet (mobile)
- ✅ Opera (desktop & mobile)

### Partial Support
- ⚠️ Safari (iOS): No install prompt, manual Add to Home Screen
- ⚠️ Firefox (desktop): No install prompt yet (coming soon)
- ⚠️ Safari (macOS): No install support

### Service Worker Support
All modern browsers support service workers for offline functionality, even if install prompts aren't available.

## Testing PWA Features

### Desktop Testing
1. Open Chrome DevTools (F12)
2. Go to Application tab
3. Check:
   - Manifest section (verify properties)
   - Service Workers section (verify registration)
   - Cache Storage section (inspect cached files)
4. Simulate offline: Network tab → Throttling → Offline

### Mobile Testing
1. Chrome DevTools → More tools → Remote devices
2. Connect Android device via USB
3. Inspect InkWave tab
4. Test offline by enabling Airplane Mode

### Lighthouse Audit
1. Chrome DevTools → Lighthouse tab
2. Select "Progressive Web App" category
3. Run audit
4. Should score 90+ for PWA features

## Performance Metrics

### Cache Sizes (Typical)
- Static assets: ~2-5 MB (app shell, icons)
- API responses: ~0.5-2 MB (book metadata)
- Audio files: Up to 500 MB (user-dependent)

### Load Times
- **First visit**: 2-3 seconds (download assets)
- **Repeat visit**: <1 second (from cache)
- **Offline**: <500ms (instant from cache)

### Storage Limits
- Desktop: Up to 80% of disk space (browser managed)
- Mobile: Varies by device (typically 50-500 MB for PWAs)
- InkWave enforces 500 MB audio cache limit

## Troubleshooting

### App Won't Install
**Symptoms**: No install prompt appears
**Solutions**:
1. Ensure site is on HTTPS (required for PWAs)
2. Check manifest.json is accessible
3. Clear browser cache and reload
4. Try a different browser
5. For iOS: Use "Add to Home Screen" manually

### Service Worker Not Updating
**Symptoms**: Old version persists after update
**Solutions**:
1. Close all InkWave tabs
2. Wait 24 hours (automatic cleanup)
3. Clear browser cache manually
4. Click "Update Now" in banner if shown

### Offline Content Not Available
**Symptoms**: Content doesn't load offline
**Solutions**:
1. Verify content was cached while online
2. Check cache status in Profile → Offline Storage
3. Audio files only cached when explicitly downloaded
4. Some content requires internet (search, new books)

### Cache Full / Storage Errors
**Symptoms**: "QuotaExceededError" in console
**Solutions**:
1. Go to Profile → Offline Storage
2. Click "Clear Cache"
3. Reload the app
4. Audio cache auto-cleans at 500 MB

## Future Enhancements

### Planned Features
- [ ] Background audio sync
- [ ] Offline reading progress sync
- [ ] Push notifications for new releases
- [ ] Share target API (share content to InkWave)
- [ ] Periodic background sync
- [ ] Advanced offline mode toggle

### Under Consideration
- Pre-download entire books for offline
- Offline reading analytics
- Download queue management
- Custom cache size limits
- Background fetch for large audio files

## Security & Privacy

### HTTPS Requirement
- PWAs require secure context (HTTPS)
- All InkWave traffic is encrypted
- Service worker only activates on HTTPS

### Data Storage
- All cached data stored locally on device
- No sensitive data cached (passwords, tokens)
- Cache cleared when app uninstalled
- Respects browser private/incognito mode

### Permissions
InkWave PWA requests:
- **Storage**: Cache content for offline access
- **Notifications** (optional): Update alerts
- No location, camera, or microphone access required

## Developer Resources

### Key Files
```
/public/
  ├── manifest.webmanifest    # PWA manifest
  ├── sw.js                   # Service worker
  └── icons/                  # App icons (all sizes)

/src/
  ├── hooks/
  │   └── usePWA.ts           # PWA React hook
  ├── components/
  │   ├── PWAInstallPrompt.tsx      # Install banner
  │   ├── PWAUpdateBanner.tsx       # Update notification
  │   ├── OfflineIndicator.tsx      # Offline status
  │   └── PWACacheSettings.tsx      # Cache management UI
  └── main.tsx                # Service worker registration
```

### Service Worker Registration
```typescript
// /src/main.tsx
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js')
      .then(registration => {
        console.log('SW registered:', registration.scope);

        // Check for updates every hour
        setInterval(() => {
          registration.update();
        }, 60 * 60 * 1000);
      })
      .catch(error => {
        console.log('SW registration failed:', error);
      });
  });
}
```

### Cache Audio Programmatically
```typescript
import { usePWA } from '../hooks/usePWA';

function BookPlayer() {
  const { cacheAudio, isCached } = usePWA();

  const handleDownload = async (audioUrl: string, bookId: string) => {
    await cacheAudio(audioUrl, bookId);
    const cached = await isCached(audioUrl);
    console.log('Cached:', cached); // true
  };
}
```

## Support

For PWA-related issues:
1. Check browser console for errors
2. Run Lighthouse PWA audit
3. Verify manifest.json and sw.js are accessible
4. Report issues to development team

---

**Last Updated**: 2025-12-03
**PWA Version**: 3.0
**Service Worker Version**: 3
**Manifest Version**: 1.0
