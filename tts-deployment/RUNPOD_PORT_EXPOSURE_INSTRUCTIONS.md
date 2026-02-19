# 🚨 ACTION REQUIRED: Expose Ports on RunPod Dashboard

## Current Status

✅ **RunPod Setup Complete:**
- Nginx configured on RunPod (ports 8010, 8011 listening)
- F5-TTS API running on localhost:8002 → proxied to 8010
- F5-TTS Gradio UI running on localhost:8003 → proxied to 8011
- Local server nginx configs updated to use RunPod URLs

❌ **Missing Step: Port Exposure**
The ports are NOT yet exposed publicly in RunPod dashboard.

## How to Expose Ports on RunPod

### Step 1: Go to RunPod Dashboard
1. Visit: https://www.runpod.io/console/pods
2. Find your pod: **jzfmzviw26huka-644113c7**
3. Click on the pod to open its details

### Step 2: Add HTTP Services
1. Look for the "HTTP Services" section (same area where Port 8888 for Jupyter is shown)
2. Click "Add Port" or similar button
3. Add these two ports:
   - **Port 8010** (F5-TTS API)
   - **Port 8011** (F5-TTS Gradio UI)

### Step 3: Save and Wait
1. Save the changes
2. Wait 1-2 minutes for RunPod to configure the proxy
3. The public URLs will appear automatically

### Expected Public URLs

Once exposed, these URLs will work:
```
F5-TTS API:
https://jzfmzviw26huka-644113c7-8010.proxy.runpod.net

F5-TTS Gradio UI:
https://jzfmzviw26huka-644113c7-8011.proxy.runpod.net
```

### Step 4: Test the URLs

After exposing, test with:
```bash
# Test API
curl https://jzfmzviw26huka-644113c7-8010.proxy.runpod.net/health

# Test Gradio UI (should return HTML)
curl -I https://jzfmzviw26huka-644113c7-8011.proxy.runpod.net/
```

## Once Ports Are Exposed

Then your domains will work automatically:
- https://f5tts.ailabsafrica.com (API)
- https://f5tts-ui.ailabsafrica.com (Gradio UI)

## Current Verification

Local tests on RunPod pod show services are running:
```bash
✅ Port 8010 listening (nginx)
✅ Port 8011 listening (nginx)  
✅ F5-TTS API responding on localhost:8010
✅ F5-TTS Gradio responding on localhost:8011
```

Just need to expose them publicly! 🚀
