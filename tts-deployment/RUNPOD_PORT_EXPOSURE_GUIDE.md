# How to Expose Ports on RunPod

## Method 1: Via Web UI (Easiest)

1. Go to: https://www.runpod.io/console/pods
2. Find pod: **jzfmzviw26huka**
3. Click **"Edit Pod"** or **"Edit Template"**
4. Find field: **"Expose HTTP Ports (Max 10)"**
5. Add ports: `8010,8011,8012` (comma-separated)
6. Click **Save**
7. Wait 1-2 minutes for proxy to update

## Exposed URLs After Saving

```
F5-TTS API:       https://jzfmzviw26huka-8010.proxy.runpod.net
F5-TTS Gradio UI: https://jzfmzviw26huka-8011.proxy.runpod.net
Moshi/Kyutai:     https://jzfmzviw26huka-8012.proxy.runpod.net
```

## Method 2: Via GraphQL API (Programmatic)

Unfortunately, RunPod doesn't provide a mutation to update HTTP ports on a running pod via GraphQL.  
You must **edit the pod configuration** via the web UI.

##  Method 3: Recreate Pod with Ports

If editing doesn't work, you can:
1. Note your current pod settings
2. Stop the pod
3. Create new pod with ports: `8010,8011,8012` in HTTP Ports field
4. Start new pod

## Important Notes

- Services MUST bind to `0.0.0.0` (not `127.0.0.1`)
- Our nginx on RunPod is already listening on 0.0.0.0:8010 and 0.0.0.0:8011 ✅
- 100-second timeout limit (Cloudflare)
- Max 10 HTTP ports per pod

## Current Setup Status

✅ Port 8010 - nginx listening (F5-TTS API)
✅ Port 8011 - nginx listening (F5-TTS Gradio)  
✅ Services bound to 0.0.0.0  
❌ Ports NOT in RunPod HTTP Ports list → Add them via Edit Pod!
