# cuDNN Persistent Fix - Avoiding Restart Issues

## Problem Statement

**User Question:** "how can we avoid the cuda restart cuDNN issues?"

The OpenVoice container experiences cuDNN library loading errors that cause seg segmentation faults during voice cloning operations. This issue persists across container restarts despite Dockerfile changes.

## Root Cause Analysis

### Why cuDNN Issues Persist

1. **Docker Layer Caching**
   - Docker caches build steps to speed up rebuilds
   - When Dockerfile changes (like adding cuDNN version pinning), only changed layers rebuild
   - If the cuDNN installation step hasn't changed in content, Docker uses the cached layer
   - This cached layer contains the OLD cuDNN version (9.14.0) instead of the pinned version (9.1.0)

2. **PyTorch-cuDNN Version Coupling**
   - PyTorch 2.9.0 is compiled against specific cuDNN version (9.1.0)
   - Using different cuDNN versions causes undefined symbols and segfaults
   - Error: `Unable to load any of {libcudnn_cnn.so.9.1.0...}`
   - Result: `Invalid handle. Cannot load symbol cudnnCreateConvolutionDescriptor`

3. **Runtime vs Build-Time Issues**
   - Health checks pass because they don't trigger heavy CUDA operations
   - Actual voice cloning triggers cuDNN operations that fail
   - Container reports "healthy" but crashes on real workloads

## Solutions

### Short-Term Fixes

#### 1. Force Rebuild Without Cache ✅
```bash
# Always use --no-cache when changing CUDA/cuDNN dependencies
sudo docker-compose -f docker-compose.local.yml build --no-cache openvoice
```

**Pros:**
- Ensures all layers rebuild fresh
- Guaranteed to apply Dockerfile changes
- Simple to execute

**Cons:**
- Time-consuming (10-15 minutes per rebuild)
- Downloads all packages again
- Wastes bandwidth

#### 2. Clean Docker Build Cache
```bash
# Remove all build cache
sudo docker builder prune -a -f

# Then rebuild
sudo docker-compose -f docker-compose.local.yml build openvoice
```

**Pros:**
- Ensures no stale layers exist
- Can be automated

**Cons:**
- Affects all Docker builds, not just OpenVoice
- Still requires full rebuild

### Medium-Term Solutions

#### 3. Use Pre-Built PyTorch Docker Images with Matching cuDNN

**Recommended Approach:**

Update `Dockerfile` to use official PyTorch images that include matching cuDNN:

```dockerfile
# Instead of:
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

# Use:
FROM pytorch/pytorch:2.0.1-cuda12.1-cudnn8-runtime

# Or for development:
FROM pytorch/pytorch:2.0.1-cuda12.1-cudnn8-devel
```

**Benefits:**
- PyTorch team ensures cuDNN compatibility
- No manual version pinning required
- Reduces build time (PyTorch pre-installed)
- Battle-tested configurations

**Trade-offs:**
- Larger base image size
- Specific to PyTorch ecosystem
- Less control over exact versions

**Implementation:**
```dockerfile
FROM pytorch/pytorch:2.0.1-cuda12.1-cudnn8-devel

WORKDIR /app

# Install system dependencies (no Python/pip needed)
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Clone OpenVoice
RUN git clone https://github.com/myshell-ai/OpenVoice.git /app/OpenVoice

# Install OpenVoice dependencies
WORKDIR /app/OpenVoice
RUN pip install -e .

# Install API dependencies
RUN pip install fastapi uvicorn soundfile

# Rest of Dockerfile...
```

#### 4. Pin ALL CUDA Library Versions

Update Dockerfile to pin every CUDA component:

```dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

# Pin exact versions of ALL CUDA libraries
RUN apt-get update && apt-get install -y \
    libcudnn9-cuda-12=9.1.0.70-1 \
    libcudnn9-dev-cuda-12=9.1.0.70-1 \
    cuda-nvrtc-12-1=12.1.105-1 \
    cuda-nvrtc-dev-12-1=12.1.105-1 \
    libnvidia-compute-525=525.147.05-0ubuntu1 \
    && apt-mark hold \
        libcudnn9-cuda-12 \
        libcudnn9-dev-cuda-12 \
        cuda-nvrtc-12-1 \
        cuda-nvrtc-dev-12-1 \
        libnvidia-compute-525 \
    && rm -rf /var/lib/apt/lists/*
```

#### 5. Create Verification Script

Add cuDNN verification to container startup:

```python
# /app/verify_cudnn.py
import torch
import subprocess

def verify_cudnn():
    """Verify cuDNN is properly loaded before starting server."""
    print("="*60)
    print("VERIFYING CUDA/cuDNN CONFIGURATION")
    print("="*60)

    # Check CUDA available
    print(f"CUDA available: {torch.cuda.is_available()}")

    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"cuDNN version: {torch.backends.cudnn.version()}")
        print(f"cuDNN enabled: {torch.backends.cudnn.enabled}")

        # Try a simple CUDA operation
        try:
            x = torch.rand(5, 5).cuda()
            y = torch.rand(5, 5).cuda()
            z = x @ y
            print("✅ Basic CUDA operations working")
        except Exception as e:
            print(f"❌ CUDA operations failed: {e}")
            return False

        # Try a cuDNN operation (convolution)
        try:
            import torch.nn as nn
            conv = nn.Conv2d(3, 64, 3).cuda()
            x = torch.rand(1, 3, 32, 32).cuda()
            y = conv(x)
            print("✅ cuDNN convolution working")
        except Exception as e:
            print(f"❌ cuDNN operations failed: {e}")
            return False

    print("="*60)
    return True

if __name__ == "__main__":
    if not verify_cudnn():
        print("❌ cuDNN verification failed - container not ready")
        exit(1)
    print("✅ cuDNN verification passed - starting server")
```

Update `CMD` in Dockerfile:
```dockerfile
CMD python3 /app/verify_cudnn.py && python3 /app/app.py
```

### Long-Term Solutions

#### 6. Multi-Stage Docker Build

Create optimized, reproducible builds:

```dockerfile
# Stage 1: Builder
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04 AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    python3.10 python3-pip git wget curl

# Install Python packages
RUN pip3 install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
RUN git clone https://github.com/myshell-ai/OpenVoice.git /app/OpenVoice
WORKDIR /app/OpenVoice
RUN pip3 install -e .

# Stage 2: Runtime
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Copy Python environment from builder
COPY --from=builder /usr/local/lib/python3.10 /usr/local/lib/python3.10
COPY --from=builder /app/OpenVoice /app/OpenVoice

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Pin cuDNN runtime (not dev)
RUN apt-get update && apt-get install -y \
    libcudnn9-cuda-12=9.1.0.70-1 \
    && apt-mark hold libcudnn9-cuda-12 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# Rest of setup...
```

**Benefits:**
- Smaller final image
- Reproducible builds
- Separates build vs runtime dependencies

#### 7. Container Image Tagging Strategy

```bash
# Build with explicit version tags
docker build -t openvoice:cudnn-9.1.0-2025-10-20 .
docker tag openvoice:cudnn-9.1.0-2025-10-20 openvoice:latest

# In docker-compose:
services:
  openvoice:
    image: openvoice:cudnn-9.1.0-2025-10-20
```

**Benefits:**
- Rollback capability
- Clear version tracking
- Prevents accidental cache usage

## Current Fix in Progress

### Discovered Root Cause (2025-10-20 16:30 UTC)

The issue was NOT just about version pinning. The nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04 base image comes with **cuDNN 8.9.0 pre-installed**. When we installed cuDNN 9.1.0 alongside it, **both versions coexisted**, creating library conflicts.

**Evidence:**
```bash
$ dpkg -l | grep cudnn
ii  libcudnn8                8.9.0.131-1+cuda12.1    # From base image
ii  libcudnn8-dev            8.9.0.131-1+cuda12.1    # From base image
ii  libcudnn9-cuda-12        9.1.0.70-1              # We installed this
ii  libcudnn9-dev-cuda-12    9.1.0.70-1              # We installed this
```

PyTorch tried to load cuDNN but found the wrong version in the library path.

**Fix Applied:**
Updated Dockerfile to **remove cuDNN 8** before installing cuDNN 9:
```dockerfile
# Remove cuDNN 8 that comes with base image, install cuDNN 9.1.0
RUN apt-get update && \
    apt-get remove -y libcudnn8 libcudnn8-dev && \
    apt-get install -y \
        libcudnn9-cuda-12=9.1.0.70-1 \
        libcudnn9-dev-cuda-12=9.1.0.70-1 \
    && apt-mark hold libcudnn9-cuda-12 libcudnn9-dev-cuda-12 \
    && ldconfig \
    && rm -rf /var/lib/apt/lists/*
```

Currently running (as of 2025-10-20):
```bash
sudo docker-compose -f docker-compose.local.yml build --no-cache openvoice
```

This will ensure ONLY cuDNN 9.1.0 is present, eliminating the library conflict.

## Recommended Approach

### Immediate (Now)
1. ✅ Complete --no-cache rebuild (in progress)
2. ✅ Verify cuDNN version in logs after rebuild
3. ✅ Test voice cloning with smallest file first

### Next Deployment (Within 1 week)
1. Migrate to official PyTorch Docker image (Solution #3)
2. Add cuDNN verification script (Solution #5)
3. Implement image tagging strategy (Solution #7)

### Future Improvements (Next month)
1. Implement multi-stage builds (Solution #6)
2. Document exact version matrix (PyTorch, CUDA, cuDNN)
3. Add automated tests for CUDA operations in CI/CD

## Prevention Checklist

When updating CUDA/cuDNN dependencies:

- [ ] Always use `--no-cache` flag
- [ ] Pin exact package versions
- [ ] Use `apt-mark hold` to prevent upgrades
- [ ] Add verification script to test CUDA operations
- [ ] Document version matrix
- [ ] Tag container images with versions
- [ ] Test with real workload (not just health check)

## Version Matrix

Current known-working combination:
- **Base Image:** nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04
- **cuDNN Version:** 9.1.0.70-1 (for CUDA 12.1)
- **PyTorch:** 2.0.x compiled for CUDA 12.1
- **Python:** 3.10

## Monitoring

Add to container logs to detect issues:

```python
# In app.py startup
import torch
import logging

logger = logging.getLogger(__name__)

logger.info(f"PyTorch version: {torch.__version__}")
logger.info(f"CUDA available: {torch.cuda.is_available()}")
logger.info(f"CUDA version: {torch.version.cuda}")
logger.info(f"cuDNN version: {torch.backends.cudnn.version()}")

if torch.backends.cudnn.version() != 9010:  # 9.1.0 = 9010
    logger.warning(f"⚠️  Expected cuDNN 9.1.0 but got {torch.backends.cudnn.version()}")
```

## Summary

**Root Cause:** Docker layer caching + PyTorch-cuDNN version mismatch

**Short-term Fix:** `--no-cache` rebuilds (current approach)

**Best Long-term Fix:** Use official PyTorch Docker images with matching cuDNN

**Prevention:** Version pinning + verification scripts + image tagging

---

**Last Updated:** October 20, 2025
**Status:** --no-cache rebuild in progress to resolve current issue
