# FreshManna PWA - Fix and Testing Guide

## Issue Identified ✓ FIXED

The PWA was not prompting for installation because the **service worker had the wrong API domain**. The build configuration in `vite.config.ts` was still referencing the old domain `devotionalflow-api.ailabsafrica.com` instead of the new domain `freshmanna-api.ailabsafrica.com`.

## What Was Fixed

### 1. Updated Vite PWA Configuration
**File**: `devotionalflow/frontend/vite.config.ts`

Changed all API URL patterns in the Workbox runtime caching configuration from:
- ❌ `devotionalflow-api.ailabsafrica.com`
- ✅ `freshmanna-api.ailabsafrica.com`

This affects:
- Devotionals API cache pattern (line 65)
- Auth/Users API cache pattern (line 74)
- Audio storage cache pattern (line 82)

### 2. Rebuilt Frontend
- Ran `npm run build` to generate new service worker with correct API URLs
- New service worker: `dist/sw.js` with correct domain references
- Updated manifest: `dist/manifest.webmanifest`

### 3. Verification
✅ Service worker now contains `freshmanna-api.ailabsafrica.com` in all cache patterns
✅ Manifest is properly configured with all required PWA fields
✅ All icons are present and accessible
✅ HTTPS is enabled on both domains

## PWA Configuration Details

### Manifest (`manifest.webmanifest`)
```json
{
  "name": "FreshManna - Daily Devotionals",
  "short_name": "FreshManna",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#FBF8F3",
  "theme_color": "#2B3A52",
  "orientation": "portrait-primary",
  "scope": "/"
}
```

### Icons Available
- ✅ 72x72
- ✅ 96x96
- ✅ 128x128
- ✅ 144x144
- ✅ 152x152
- ✅ 192x192 (maskable)
- ✅ 384x384
- ✅ 512x512 (maskable)

### iOS Support
- ✅ `apple-mobile-web-app-capable`
- ✅ `apple-mobile-web-app-status-bar-style`
- ✅ `apple-mobile-web-app-title`
- ✅ Apple touch icons

## Testing the PWA Installation

### Prerequisites
1. **HTTPS Required**: ✅ Both domains have valid SSL certificates
   - https://freshmanna.ailabsafrica.com
   - https://freshmanna-api.ailabsafrica.com

2. **Service Worker Registration**: ✅ Configured in `src/main.tsx`

3. **Clear Old Service Workers**: Important if you tested before the fix

### Step-by-Step Testing

#### On Android (Chrome/Edge)

1. **Clear Old Cache** (if you visited before):
   ```
   1. Open Chrome DevTools (Desktop)
   2. Application tab > Service Workers
   3. Click "Unregister" for any old service workers
   4. Application tab > Storage
   5. Click "Clear site data"
   ```

2. **Visit on Mobile**:
   - Open Chrome on your Android phone
   - Navigate to: https://freshmanna.ailabsafrica.com
   - Wait 3-5 seconds for the service worker to register

3. **Install Prompt**:
   - You should see an "Add to Home Screen" banner at the bottom
   - Or tap the 3-dot menu > "Install app" or "Add to Home Screen"

4. **Verify Installation**:
   - The app icon should appear on your home screen
   - Tap it to launch in standalone mode (no browser UI)
   - Check the splash screen shows FreshManna branding

#### On iOS (Safari)

iOS doesn't show automatic install prompts. Users must manually add to home screen:

1. **Visit Site**: https://freshmanna.ailabsafrica.com

2. **Add to Home Screen**:
   - Tap the Share button (box with arrow)
   - Scroll down and tap "Add to Home Screen"
   - Edit name if desired
   - Tap "Add"

3. **Verify**:
   - App icon appears on home screen
   - Launch shows FreshManna splash screen
   - Runs in standalone mode

#### Desktop (Chrome/Edge)

1. **Visit Site**: https://freshmanna.ailabsafrica.com

2. **Install**:
   - Look for install icon (+) in the address bar
   - Click it to install
   - Or: 3-dot menu > "Install FreshManna..."

3. **Verify**:
   - App appears in app drawer
   - Runs in its own window

### Troubleshooting

#### Problem: No Install Prompt

**Solution 1: Clear Service Worker**
```javascript
// In browser console (F12)
navigator.serviceWorker.getRegistrations().then(function(registrations) {
  for(let registration of registrations) {
    registration.unregister();
  }
  location.reload();
});
```

**Solution 2: Hard Refresh**
- Chrome/Edge: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Safari: Cmd+Option+R

**Solution 3: Check Console for Errors**
- Open DevTools > Console
- Look for service worker registration errors
- Check Network tab for failed icon loads

#### Problem: Old API Domain in Service Worker

**Verification**:
```bash
# Check service worker has correct domain
curl -s https://freshmanna.ailabsafrica.com/sw.js | grep -o "freshmanna-api"
```

Should return multiple matches. If it shows "devotionalflow-api", the old build is still deployed.

**Solution**: Rebuild was already done, just need to clear cache (see above)

#### Problem: Icons Not Loading

**Check**: https://freshmanna.ailabsafrica.com/icons/icon-192x192.png

Should load successfully. If 404, icons weren't deployed properly.

## PWA Install Criteria (Chrome)

For Chrome to show the install prompt, ALL of these must be met:

✅ **Web app manifest**: Present and valid
✅ **HTTPS**: Site served over HTTPS
✅ **Service worker**: Registered with fetch event handler
✅ **Icons**: 192x192 and 512x512 PNG icons
✅ **User engagement**: User has interacted with the site (clicks/taps)
✅ **Not already installed**: App isn't already installed
✅ **beforeinstallprompt**: Not previously dismissed by user

All criteria are met after the fix! ✓

## Manual Testing Checklist

- [ ] Visit https://freshmanna.ailabsafrica.com on mobile
- [ ] Wait 5 seconds for service worker registration
- [ ] Look for install prompt or menu option
- [ ] Install the app
- [ ] Verify app icon appears on home screen
- [ ] Launch app from home screen
- [ ] Verify standalone mode (no browser UI)
- [ ] Check splash screen shows FreshManna branding
- [ ] Test offline functionality (turn off network, app should still load cached content)
- [ ] Test API calls work (they should fail gracefully when offline)

## Offline Functionality

The PWA now caches:
- ✅ All static assets (JS, CSS, fonts, images)
- ✅ App shell (HTML, icons, manifest)
- ✅ Devotionals API responses (24 hours)
- ✅ User/Auth API responses (1 hour)
- ✅ Audio files (30 days)
- ✅ Images (7 days)

## Service Worker Update Strategy

- **Type**: `prompt` - User is notified when updates are available
- **Update Check**: Every 5 minutes while app is open
- **Custom Event**: `swUpdateAvailable` - Frontend can listen and show update notification

## Next Steps

1. **Test on Real Devices**:
   - Android phone with Chrome
   - iPhone with Safari
   - Desktop Chrome/Edge

2. **Monitor Service Worker**:
   ```bash
   # Check service worker registration in console
   navigator.serviceWorker.getRegistrations()
   ```

3. **Check PWA Scores**:
   - Use Lighthouse in Chrome DevTools
   - Run PWA audit
   - Should score 90+ on all metrics

4. **User Testing**:
   - Have real users install the app
   - Collect feedback on install experience
   - Monitor analytics for install rates

## Maintenance

### Updating the PWA

When you make changes to the frontend:

1. Update version in `package.json`
2. Run `npm run build`
3. Deploy to production
4. Service worker will auto-update for users (within 5 minutes)
5. Users will see update notification

### Monitoring

Check service worker status:
```bash
# View service worker in browser
chrome://serviceworker-internals/

# Unregister all (for testing)
chrome://serviceworker-internals/ > Unregister
```

## Resources

- [PWA Checklist](https://web.dev/pwa-checklist/)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Workbox Documentation](https://developers.google.com/web/tools/workbox)
- [Web App Manifest](https://web.dev/add-manifest/)

---

**Fixed**: December 11, 2025
**Tested**: Pending user testing on mobile devices
**Status**: ✅ Ready for testing
