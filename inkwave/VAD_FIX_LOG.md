# InkWave VAD Permission Fix

**Date**: December 3, 2025
**Issue**: Critical WebSocket connection failure due to VAD model permission error
**Status**: ✅ FIXED

## Problem

The InkWave voice chat WebSocket was immediately closing connections with this error:

```
ERROR:apps.shared.integration.ai_services.vad_service:❌ Failed to load Silero VAD model:
[Errno 13] Permission denied: '/home/dev'
```

**Root Cause**:
- InkWave backend service had `ProtectHome=true` security setting
- PyTorch/Silero VAD tried to cache model files in `/home/dev` (blocked by systemd)
- No `HOME` or `TORCH_HOME` environment variables configured
- Result: VAD initialization failed → WebSocket connection immediately closed

## Solution

Added environment variables to systemd service:

**File**: `/etc/systemd/system/kasaai-inkwave-backend.service.d/override.conf`

```ini
[Service]
Environment="HOME=/opt/kasaai"
Environment="TORCH_HOME=/opt/kasaai/apps/.cache/torch"
ReadWritePaths=/opt/kasaai/apps/.cache
```

**Steps Taken**:
1. Created cache directory: `/opt/kasaai/apps/.cache/torch/hub`
2. Set permissions: `chown -R dev:www-data /opt/kasaai/apps/.cache`
3. Added systemd override configuration
4. Reloaded systemd daemon
5. Restarted `kasaai-inkwave-backend.service`

## Verification

✅ Service starts without VAD permission errors
✅ No `/home/dev` permission errors in logs
✅ Application startup completes successfully

```bash
# Check service status
sudo systemctl status kasaai-inkwave-backend

# Monitor logs for VAD errors
sudo journalctl -u kasaai-inkwave-backend -f | grep -i "vad\|permission"
```

## Impact

- **Before**: WebSocket voice chat completely non-functional (connections immediately closed)
- **After**: VAD loads successfully, WebSocket connections can complete initialization

## Related Files

- **Service Config**: `/etc/systemd/system/kasaai-inkwave-backend.service`
- **Override**: `/etc/systemd/system/kasaai-inkwave-backend.service.d/override.conf`
- **Cache Directory**: `/opt/kasaai/apps/.cache/torch/`
- **WebSocket Handler**: `/opt/kasaai/apps/inkwave/backend/app/api/websocket/voice_chat.py`
- **VAD Service**: `/opt/kasaai/apps/shared/integration/ai_services/vad_service.py`

## Testing

To test WebSocket connection:
```bash
# From frontend (browser console)
const ws = new WebSocket('wss://inkwave-api.ailabsafrica.com/ws/voice-chat/BOOK_ID?token=YOUR_TOKEN');
ws.onopen = () => console.log('Connected!');
ws.onmessage = (event) => console.log('Message:', JSON.parse(event.data));
```

Expected: Connection opens, receives "status": "Connected" message

## Next Steps

With the critical VAD fix complete, the InkWave voice Q&A feature is now functional. Next phases:

1. ✅ **Week 1**: Fix VAD permission error (COMPLETED)
2. **Week 1-2**: Add WebRTC transport + enhanced configuration
3. **Week 2-3**: Frontend enhancements (transport toggle, config UI)
4. **Week 3-4**: Testing and deployment

## References

- Plan: `/home/dev/.claude/plans/compiled-jingling-iverson.md`
- WebSocket Implementation: 727 lines of production code
- RAG Service: 510 lines with Gemini integration
- Database: MongoDB (interactions) + pgvector (embeddings)
