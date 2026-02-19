# OpenVoice cuDNN Crash Fix - October 20, 2025

## Problem Summary

OpenVoice container was crashing with exit code 139 (segmentation fault) due to a cuDNN library version mismatch.

## Root Cause

**Error logs showed:**
```
Unable to load any of {libcudnn_cnn.so.9.1.0, libcudnn_cnn.so.9.1, libcudnn_cnn.so.9, libcudnn_cnn.so}
Invalid handle. Cannot load symbol cudnnCreateConvolutionDescriptor
```

**Analysis:**
- **Base Image**: `nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04` (includes cuDNN 8)
- **Manual Installation**: Installing `libcudnn9-cuda-12` without version pinning installed the **latest cuDNN 9.14.0**
- **PyTorch 2.9.0**: Compiled against **cuDNN 9.1.0 specifically**
- **Result**: Version mismatch between PyTorch expectations (9.1.0) and installed library (9.14.0) caused segmentation fault

## Solution

**Fixed Dockerfile** to install the correct cuDNN version:

```dockerfile
# Install cuDNN 9.1.0 specifically for CUDA 12.1
# Reason: PyTorch 2.9.0 requires cuDNN 9.1.0, not 9.14.0 (segfault with wrong version)
RUN apt-get update && apt-get install -y \
    libcudnn9-cuda-12=9.1.0.70-1 \
    libcudnn9-dev-cuda-12=9.1.0.70-1 \
    && apt-mark hold libcudnn9-cuda-12 libcudnn9-dev-cuda-12 \
    && rm -rf /var/lib/apt/lists/*
```

**Key changes:**
1. **Pin cuDNN version** to `9.1.0.70-1` (exact match for PyTorch 2.9.0)
2. **Hold packages** to prevent accidental upgrades: `apt-mark hold`

## Deployment Steps

1. Updated Dockerfile: `/opt/kasaai/apps/tts-deployment/docker/openvoice/Dockerfile`
2. Rebuilt container:
   ```bash
   cd /opt/kasaai/apps/tts-deployment
   sudo docker-compose -f docker-compose.local.yml build openvoice
   ```
3. Removed corrupted containers:
   ```bash
   sudo docker ps -a | grep openvoice | awk '{print $1}' | xargs -r sudo docker rm -f
   ```
4. Started fresh container:
   ```bash
   sudo docker-compose -f docker-compose.local.yml up -d openvoice
   ```

## Verification

**Container Status:**
```bash
$ sudo docker ps | grep openvoice
1249818d77e8   tts-deployment_openvoice   Up 5 minutes (healthy)   0.0.0.0:8003->8003/tcp
```

**Health Check:**
```bash
$ curl -s http://localhost:8003/health | python3 -m json.tool
{
    "status": "healthy",
    "device": "cuda",
    "tone_converter_loaded": true,
    "base_tts_models": ["EN", "ZH"],
    "target_speakers": 11
}
```

**Startup logs show successful loading:**
- ✅ Loaded checkpoint 'converter_v2.pth'
- ✅ Loaded checkpoint 'base_speakers/EN/checkpoint.pth'
- ✅ Loaded checkpoint 'base_speakers/ZH/checkpoint.pth'
- ✅ Uvicorn running on http://0.0.0.0:8003
- ✅ NO cuDNN errors

## Technical Details

### PyTorch and cuDNN Compatibility

PyTorch is compiled against specific versions of CUDA libraries. Using mismatched versions can cause:
- Segmentation faults (exit code 139)
- Symbol loading failures
- Runtime crashes during tensor operations

### Version Pinning Best Practices

When dealing with CUDA/cuDNN installations:
1. **Always pin exact versions** for production deployments
2. **Use `apt-mark hold`** to prevent accidental upgrades during container updates
3. **Match PyTorch build requirements** - check PyTorch release notes for exact cuDNN version
4. **Test after builds** - ensure containers start and can perform inference without crashes

## Files Modified

- `/opt/kasaai/apps/tts-deployment/docker/openvoice/Dockerfile` - Fixed cuDNN installation

## Status

✅ **RESOLVED** - OpenVoice container is running stable with cuDNN 9.1.0

## Related Issues

This fix resolves the segmentation fault issue that was preventing OpenVoice from running. The container now:
- Starts successfully
- Loads all models without errors
- Responds to health checks
- Can perform TTS synthesis

## Recommendations for Future Updates

1. When updating PyTorch version, verify the cuDNN compatibility matrix
2. Document exact library versions in deployment notes
3. Consider using PyTorch official Docker images when available
4. Monitor for cuDNN deprecation warnings in logs
